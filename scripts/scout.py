#!/usr/bin/env python3
"""Fully automated scout: find targets, classify, post comments, log results.

Run by the scout GitHub Actions workflow. Requires GH_TOKEN env var (or gh CLI auth).

Flow:
  1. Generate scout_context.json from pyproject.toml
  2. Search GitHub for relevant issues (last 7 days)
  3. Filter: skip non-Python repos, already-commented, noisy threads, irrelevant content
  4. Classify each issue (loop / cost / debug) by keywords
  5. Post a short, human comment (max 1 per run)
  6. Close old scout issues, create summary issue with what was posted
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from typing import Any

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUR_REPO = "bmdhodl/agent47"
OUR_USER = "bmdhodl"
MAX_COMMENTS_PER_RUN = 1
MAX_ISSUE_COMMENTS = 10  # skip noisy threads
SEARCH_DAYS = 7
REPO_SEARCH_DAYS = 14

# Repos to search with broader queries
TARGET_REPOS = [
    "langchain-ai/langchain",
    "crewAIInc/crewAI",
    "microsoft/autogen",
    "google/adk-python",
    "langchain-ai/langgraph",
]

# Search queries for general search
SEARCH_QUERIES = [
    ("agent infinite loop", "Agent Infinite Loops"),
    ("agent loop tool call", "Tool Call Loops"),
    ("agent runaway cost", "Runaway Costs"),
    ("agent budget exceeded", "Budget Issues"),
    ("agent retry loop", "Retry Loops"),
]

# Keywords for classification
LOOP_KEYWORDS = ["loop", "infinite", "repeat", "recursion", "stuck", "cycling", "retry"]
COST_KEYWORDS = ["cost", "budget", "expensive", "billing", "spending", "price", "token usage", "money", "$"]
# If neither matches → debugging/observability template

# Languages that signal the issue is NOT Python-related
SKIP_LANGUAGES = {
    "typescript", "javascript", "rust", "go", "golang", "java",
    "c#", "csharp", "swift", "kotlin", "ruby", "php", "dart", "flutter",
}

# Repo-level languages we'll comment on (Python or unknown)
ALLOWED_REPO_LANGUAGES = {"Python", "Jupyter Notebook", None}


def gh(*args: str, json_output: bool = False) -> Any:
    """Run a gh CLI command. Returns parsed JSON if json_output=True, else stdout string."""
    cmd = ["gh"] + list(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        return [] if json_output else ""
    if json_output:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return []
    return result.stdout.strip()


def load_context() -> dict:
    """Load scout_context.json."""
    path = os.path.join(REPO_ROOT, "docs", "outreach", "scout_context.json")
    with open(path) as f:
        return json.load(f)


def parse_issue_url(url: str) -> tuple[str, str] | None:
    """Extract (owner/repo, number) from a GitHub issue URL.

    Returns None for malformed URLs.
    """
    parts = url.rstrip("/").split("/")
    if len(parts) < 5:
        return None
    return f"{parts[-4]}/{parts[-3]}", parts[-1]


def get_repo_language(owner_repo: str) -> str | None:
    """Get the primary language of a repo via GitHub API."""
    result = gh("api", f"repos/{owner_repo}", "--jq", ".language")
    lang = result.strip() if result else None
    if lang == "null" or lang == "":
        return None
    return lang


def search_issues(query: str, cutoff: str, limit: int = 5, repo: str | None = None) -> list[dict]:
    """Search GitHub for open issues matching query created after cutoff."""
    args = ["search", "issues", query, "--sort", "created", "--order", "desc",
            "--limit", str(limit), "--state", "open", "--created", f">={cutoff}",
            "--json", "title,url,body,repository,number,commentsCount,createdAt"]
    if repo:
        args.extend(["--repo", repo])
    return gh(*args, json_output=True) or []


def already_commented(owner_repo: str, number: str) -> bool:
    """Check if bmdhodl has already commented on this issue.

    Uses --paginate to check ALL comment pages, not just the first 30.
    """
    result = gh("api", f"repos/{owner_repo}/issues/{number}/comments",
                "--paginate", "--jq",
                f'[.[] | select(.user.login == "{OUR_USER}")] | length')
    try:
        return int(result.strip()) > 0
    except (ValueError, AttributeError):
        return True  # err on the side of not posting


def is_relevant(issue: dict) -> bool:
    """Check if issue is relevant (Python-related or language-neutral).

    Reads both title and body. If another language is explicitly mentioned
    and Python is not, skip it.
    """
    body = (issue.get("body") or "").lower()
    title = (issue.get("title") or "").lower()
    text = title + " " + body

    # If Python is explicitly mentioned, always relevant
    if "python" in text:
        return True

    # If another language is mentioned and Python isn't, skip
    for lang in SKIP_LANGUAGES:
        if lang in text:
            return False

    return True  # language-neutral issues are fair game


def classify(title: str) -> str:
    """Classify an issue as 'loop', 'cost', or 'debug' based on title keywords."""
    title_lower = title.lower()
    loop_score = sum(1 for kw in LOOP_KEYWORDS if kw in title_lower)
    cost_score = sum(1 for kw in COST_KEYWORDS if kw in title_lower)

    if loop_score > cost_score:
        return "loop"
    if cost_score > loop_score:
        return "cost"
    if loop_score > 0:
        return "loop"
    return "debug"


def render_comment(category: str, ctx: dict) -> str:
    """Render a short, human comment for the given category.

    Rules: no code blocks, no install commands, no version numbers.
    Casual dev tone. Max 3 sentences. Just the repo link.
    """
    repo_url = ctx["repo_url"]

    if category == "loop":
        return (
            "ran into the same thing. i ended up writing a small guard that watches "
            "for repeated tool calls and kills the loop automatically — saved me a "
            f"bunch of debugging time. it's called agentguard: {repo_url}\n\n"
            "happy to help if you want a hand with your specific case."
        )
    elif category == "cost":
        return (
            "been there. i wrote a budget guard that caps spend per run so this "
            "can't happen — it just stops the agent when you hit a dollar threshold. "
            f"check out agentguard if useful: {repo_url}"
        )
    else:  # debug
        return (
            "if it helps, i built a lightweight tracer that captures every step + "
            "tool call and gives you a timeline view. makes it way easier to see "
            f"what the agent is actually doing. it's called agentguard: {repo_url}"
        )


def post_comment(owner_repo: str, number: str, body: str) -> bool:
    """Post a comment on a GitHub issue. Returns True on success."""
    result = gh("issue", "comment", number, "--repo", owner_repo, "--body", body)
    return result is not None


def close_old_scout_issues() -> None:
    """Close all open scout issues in our repo."""
    issues = gh("issue", "list", "--label", "scout", "--state", "open",
                "--repo", OUR_REPO, "--json", "number", json_output=True) or []
    for issue in issues:
        gh("issue", "close", str(issue["number"]), "--repo", OUR_REPO,
           "--comment", "Superseded by today's automated scout run.")


def create_summary_issue(posted: list[dict], skipped: int, total: int, ctx: dict) -> None:
    """Create a summary issue logging what the scout did."""
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    version = ctx["version"]

    lines = [
        f"# Scout Run — {date}\n",
        f"**SDK version:** v{version} | **Targets found:** {total} | "
        f"**Comments posted:** {len(posted)} | **Skipped:** {skipped}\n",
    ]

    if posted:
        lines.append("## Comments posted\n")
        for p in posted:
            lines.append(f"- [{p['title']}]({p['url']}) — `{p['category']}` template")
        lines.append("")

    if not posted:
        lines.append("No new comments posted (all targets already covered or none found).\n")

    lines.append(f"---\n*Automated scout run. Templates from v{version}.*")
    body = "\n".join(lines)

    title = f"Scout: {len(posted)} comments posted, {total} targets ({date})"
    gh("issue", "create", "--repo", OUR_REPO, "--title", title,
       "--body", body, "--label", "scout")


def main() -> None:
    # 1. Generate context
    subprocess.run([sys.executable, os.path.join(REPO_ROOT, "scripts", "update_scout_context.py")],
                   check=True)
    ctx = load_context()

    # 2. Search for targets
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=SEARCH_DAYS)).strftime("%Y-%m-%dT00:00:00Z")
    cutoff_repo = (now - timedelta(days=REPO_SEARCH_DAYS)).strftime("%Y-%m-%dT00:00:00Z")

    all_targets: list[dict] = []
    seen_urls: set[str] = set()

    # General searches
    for query, _label in SEARCH_QUERIES:
        results = search_issues(query, cutoff)
        for r in results:
            url = r.get("url", "")
            repo_name = r.get("repository", {}).get("nameWithOwner", "")
            if url not in seen_urls and repo_name != OUR_REPO:
                seen_urls.add(url)
                all_targets.append(r)

    # Repo-specific searches
    for repo in TARGET_REPOS:
        results = search_issues("loop OR cost OR retry OR guardrail", cutoff_repo, limit=3, repo=repo)
        for r in results:
            url = r.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                all_targets.append(r)

    print(f"Found {len(all_targets)} unique targets")

    # 3. Filter, classify, and post
    posted: list[dict] = []
    skipped = 0
    # Cache repo language lookups to avoid redundant API calls
    repo_lang_cache: dict[str, str | None] = {}

    for target in all_targets:
        if len(posted) >= MAX_COMMENTS_PER_RUN:
            break

        url = target.get("url", "")
        title = target.get("title", "")
        comment_count = target.get("commentsCount", 0)

        parsed = parse_issue_url(url)
        if not parsed:
            skipped += 1
            continue
        owner_repo, number = parsed

        # Skip noisy threads
        if comment_count > MAX_ISSUE_COMMENTS:
            print(f"  Skipping (noisy, {comment_count} comments): {title}")
            skipped += 1
            continue

        # Check repo language — only post on Python repos
        if owner_repo not in repo_lang_cache:
            repo_lang_cache[owner_repo] = get_repo_language(owner_repo)
        repo_lang = repo_lang_cache[owner_repo]
        if repo_lang not in ALLOWED_REPO_LANGUAGES:
            print(f"  Skipping (repo language: {repo_lang}): {title}")
            skipped += 1
            continue

        # Check issue content relevance
        if not is_relevant(target):
            print(f"  Skipping (non-Python content): {title}")
            skipped += 1
            continue

        # Skip if we already commented
        if already_commented(owner_repo, number):
            skipped += 1
            continue

        # Classify and post
        category = classify(title)
        comment = render_comment(category, ctx)

        print(f"Posting '{category}' comment on: {title}")
        print(f"  URL: {url}")

        if post_comment(owner_repo, number, comment):
            posted.append({"title": title, "url": url, "category": category})
        else:
            print(f"  Failed to post comment")

    print(f"\nDone: {len(posted)} posted, {skipped} skipped, {len(all_targets)} total targets")

    # 4. Close old scout issues and create summary
    close_old_scout_issues()

    if all_targets:
        create_summary_issue(posted, skipped, len(all_targets), ctx)


if __name__ == "__main__":
    main()
