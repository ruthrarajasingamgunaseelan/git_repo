#!/usr/bin/env python3
"""Poll a GitHub repo and run PR-Agent on every new or updated open PR.

Run inside the same virtualenv where pr-agent[github] is installed, with the
same environment variables you already use for the manual command, plus:

    export REPO=<owner>/<repo>          # e.g. ruthrarajasingamgunaseelan/git_repo
    python auto_review.py

Optional env vars:
    POLL_SECONDS   seconds between checks (default 60)
    COMMANDS       comma-separated PR-Agent commands (default "review")
    STATE_FILE     where reviewed PRs are remembered (default reviewed.json)
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO = os.environ["REPO"]
TOKEN = os.environ["GITHUB__USER_TOKEN"]
POLL = int(os.environ.get("POLL_SECONDS", "60"))
COMMANDS = [c.strip() for c in os.environ.get("COMMANDS", "review").split(",") if c.strip()]
STATE_FILE = os.environ.get("STATE_FILE", "reviewed.json")


def load_state():
    try:
        with open(STATE_FILE) as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(sorted(state), f)


def open_prs():
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/pulls?state=open&per_page=50",
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def main():
    state = load_state()
    print(f"Watching {REPO} every {POLL}s, commands: {COMMANDS}", flush=True)
    while True:
        try:
            for pr in open_prs():
                if pr.get("draft"):
                    continue
                # Key includes the head commit, so new pushes get re-reviewed.
                # Comments posted by PR-Agent do not change the head commit,
                # so there is no review loop.
                key = f"{pr['number']}:{pr['head']['sha']}"
                if key in state:
                    continue
                url = pr["html_url"]
                print(f"Reviewing {url}", flush=True)
                ok = True
                for cmd in COMMANDS:
                    result = subprocess.run(
                        [sys.executable, "-m", "pr_agent.cli", "--pr_url", url, cmd]
                    )
                    ok = ok and result.returncode == 0
                if ok:
                    state.add(key)
                    save_state(state)
                else:
                    print(f"Command failed for {url}; will retry next round.", flush=True)
        except Exception as e:  # network hiccup, tunnel down, rate limit...
            print(f"Poll error: {e}", flush=True)
        time.sleep(POLL)


if __name__ == "__main__":
    main()
