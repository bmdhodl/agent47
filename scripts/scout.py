#!/usr/bin/env python3
"""Fully automated scout: find targets, classify, post comments, log results.

Run by the scout GitHub Actions workflow. Requires GH_TOKEN env var (or gh CLI auth).

Flow:
  1. Generate scout_context.json from pyproject.toml
  2. Search GitHub for relevant issues (last 7 days)
  3. Dedup: skip issues where bmdhodl already commented
  4. Classify each issue (loop / cost / debug) by keywords
  5. Post a comment with the right template (max 3 per run)
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
MAX_COMMENTS_PER_RUN = 3
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


def search_issues(query: str, cutoff: str, limit: int = 5, repo: str | None = None) -> list[dict]:
    """Search GitHub for open issues matching query created after cutoff."""
    args = ["search", "issues", query, "--sort", "created", "--order", "desc",
            "--limit", str(limit), "--state", "open", "--created", f">={cutoff}",
            "--json", "title,url,repository,number,commentsCount,createdAt"]
    if repo:
        args.extend(["--repo", repo])
    return gh(*args, json_output=True) or []


def already_commented(issue_url: str) -> bool:
    """Check if bmdhodl has already commented on this issue."""
    # Extract owner/repo and issue number from URL
    # URL format: https://github.com/owner/repo/issues/123
    parts = issue_url.rstrip("/").split("/")
    if len(parts) < 5:
        return True  # skip malformed
    owner_repo = f"{parts[-4]}/{parts[-3]}"
    number = parts[-1]

    comments = gh("api", f"repos/{owner_repo}/issues/{number}/comments",
                   "--jq", f'[.[] | select(.user.login == "{OUR_USER}")] | length',
                   json_output=False)
    try:
        return int(comments.strip()) > 0
    except (ValueError, AttributeError):
        return True  # err on the side of not posting


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
    """Render a comment template for the given category using current context."""
    version = ctx["version"]
    install = ctx["install_cmd"]
    repo_url = ctx["repo_url"]
    s = ctx["snippets"]

    if category == "loop":
        return (
            f"I built an open-source guard for exactly this — detects repeated tool calls "
            f"and kills the run before it burns your budget.\n\n"
            f"```python\n{s['loop_guard']}\n```\n\n"
            f"Works with LangChain too:\n\n"
            f"```python\n{s['langchain']}\n```\n\n"
            f"Zero dependencies, v{version}. `{install}`\n\n"
            f"{repo_url}\n\n"
            f"Happy to help debug your specific loop if you share more details."
        )
    elif category == "cost":
        return (
            f"Had the same problem. Built a budget guard that kills runs at a dollar threshold:\n\n"
            f"```python\n{s['budget_guard']}\n```\n\n"
            f"Also auto-estimates cost per LLM call (OpenAI, Anthropic, Gemini, Mistral) "
            f"so you can see exactly how much each agent run costs. "
            f"Zero deps, v{version}: `{install}`\n\n"
            f"{repo_url}"
        )
    else:  # debug
        return (
            f"I built AgentGuard for this — it traces every reasoning step and tool call, "
            f"then gives you a report + Gantt timeline in your browser:\n\n"
            f"```bash\n"
            f"agentguard report traces.jsonl   # summary table with cost\n"
            f"agentguard view traces.jsonl     # Gantt timeline in browser\n"
            f"```\n\n"
            f"Also has dollar cost per call, loop detection, and budget guards. "
            f"Works with LangChain or any custom agent. v{version}: `{install}`\n\n"
            f"{repo_url}"
        )


def post_comment(issue_url: str, body: str) -> bool:
    """Post a comment on a GitHub issue. Returns True on success."""
    parts = issue_url.rstrip("/").split("/")
    owner_repo = f"{parts[-4]}/{parts[-3]}"
    number = parts[-1]
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
        f"**Comments posted:** {len(posted)} | **Skipped (already commented):** {skipped}\n",
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

    for target in all_targets:
        if len(posted) >= MAX_COMMENTS_PER_RUN:
            break

        url = target.get("url", "")
        title = target.get("title", "")
        comment_count = target.get("commentsCount", 0)

        # Skip noisy threads
        if comment_count > MAX_ISSUE_COMMENTS:
            skipped += 1
            continue

        # Skip if we already commented
        if already_commented(url):
            skipped += 1
            continue

        # Classify and post
        category = classify(title)
        comment = render_comment(category, ctx)

        print(f"Posting '{category}' comment on: {title}")
        print(f"  URL: {url}")

        if post_comment(url, comment):
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
