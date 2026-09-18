"""Announce a published stable SDK release through the subscriber service.

Subscriber addresses and provider credentials never enter this repository.
"""

import argparse
import json
import os
import re
import urllib.request


ENDPOINT = "https://bmdpat.com/api/newsletter/send"
REPOSITORY = "bmdhodl/agent47"


class NoRedirects(urllib.request.HTTPRedirectHandler):
    """Never forward release or GitHub credentials to a redirected endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


urlopen = urllib.request.build_opener(NoRedirects()).open


def get_json(url, token=None):
    headers = {"Accept": "application/json", "User-Agent": "AgentGuard-release-email"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urlopen(urllib.request.Request(url, headers=headers), timeout=30) as response:
        return json.load(response)


def build_payload(tag, release, package):
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Only stable vMAJOR.MINOR.PATCH releases can be announced")
    version = tag[1:]
    release_url = f"https://github.com/{REPOSITORY}/releases/tag/{tag}"
    if (release.get("tag_name") != tag or release.get("draft") is not False
            or release.get("prerelease") is not False or not release.get("published_at")
            or release.get("html_url") != release_url):
        raise ValueError("A matching published stable GitHub release is required")
    files = package.get("urls", [])
    if (package.get("info", {}).get("version") != version or not files
            or any(item.get("yanked", False) for item in files)):
        raise ValueError("The matching non-yanked PyPI package must be available first")
    return {
        "audience": "agentguard",
        "release_tag": tag,
        "campaign_key": f"agentguard-release:{tag}",
        "slug": f"agentguard-release-{version.replace('.', '-')}",
        "subject": f"AgentGuard {version} is out",
        "preview": "Release notes and the command to upgrade.",
        "markdown": (
            f"I released AgentGuard {version}.\n\n"
            f"[Read what changed in {version}]({release_url}).\n\n"
            "## Upgrade\n\n"
            f"```bash\npip install --upgrade agentguard47=={version}\n```\n\n"
            f"[View the package on PyPI](https://pypi.org/project/agentguard47/{version}/).\n\n"
            "You signed up for AgentGuard updates. I'll send a note when a new stable version ships.\n\n"
            "Patrick"
        ),
    }


def send(payload, key):
    if not key:
        raise ValueError("AGENTGUARD_RELEASE_API_KEY is required")
    request = urllib.request.Request(
        ENDPOINT, data=json.dumps(payload).encode(), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urlopen(request, timeout=120) as response:
        result = json.load(response)
    if result.get("ok") is not True:
        raise RuntimeError("Release email service reported an incomplete send")
    # Do not print errors or recipient data into a public Actions log.
    return {name: result[name] for name in
            ("ok", "dry_run", "total", "accepted", "already_sent", "recipient_count")
            if name in result}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Validate audience without sending")
    args = parser.parse_args()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.tag):
        parser.error("Only stable vMAJOR.MINOR.PATCH releases can be announced")
    release = get_json(f"https://api.github.com/repos/{REPOSITORY}/releases/tags/{args.tag}", os.environ.get("GH_TOKEN"))
    package = get_json(f"https://pypi.org/pypi/agentguard47/{args.tag[1:]}/json")
    payload = build_payload(args.tag, release, package)
    payload["dry_run"] = args.dry_run
    print(json.dumps(send(payload, os.environ.get("AGENTGUARD_RELEASE_API_KEY"))))


if __name__ == "__main__":
    main()
