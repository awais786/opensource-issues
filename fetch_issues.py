#!/usr/bin/env python3
"""
Django Issue Hub — Issue Fetcher
=================================
Fetches open issues from 100+ Django ecosystem repos via GitHub API.
Designed to run as a GitHub Action on a daily schedule.

Outputs:
  - data/issues.json          (full issue data)
  - data/stats.json           (aggregate statistics)
  - data/issues_by_repo.json  (grouped by repo)
"""

import json
import os
import sys
import time
import logging
import urllib.request
import urllib.error
import urllib.parse
import ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
DATA_DIR = Path(__file__).parent / "data"
REPOS_FILE = DATA_DIR / "repos.json"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
MAX_ISSUES_PER_REPO = 30          # Cap per repo to keep data manageable
LOOKBACK_DAYS_NEW = 7             # "New" = opened in last 7 days
REQUEST_DELAY = 0.5               # Seconds between API calls (rate-limit friendly)

GOOD_FIRST_ISSUE_LABELS = [
    "good first issue", "good-first-issue", "easy", "beginner",
    "starter", "first-timers-only", "help wanted", "up-for-grabs",
]

# ---------------------------------------------------------------------------
# GitHub API Client
# ---------------------------------------------------------------------------
class GitHub:
    BASE = "https://api.github.com"

    def __init__(self, token: str):
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DjangoIssueHub/1.0",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"
        self.ssl_ctx = ssl.create_default_context()
        self.remaining = 5000

    def get(self, path: str, params: dict | None = None) -> list | dict:
        url = f"{self.BASE}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        req = urllib.request.Request(url, headers=self.headers)
        try:
            with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=30) as resp:
                self.remaining = int(resp.headers.get("X-RateLimit-Remaining", 0))
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 403:
                log.warning(f"  ⚠ Rate limited ({self.remaining} remaining)")
                if self.remaining < 10:
                    reset = int(e.headers.get("X-RateLimit-Reset", 0))
                    wait = max(reset - int(time.time()), 60)
                    log.warning(f"  ⏳ Waiting {wait}s for rate limit reset...")
                    time.sleep(wait)
                return []
            elif e.code == 404:
                log.warning(f"  ⚠ Not found: {path}")
                return []
            else:
                log.error(f"  ✗ HTTP {e.code}: {path}")
                return []
        except Exception as e:
            log.error(f"  ✗ Failed: {path} — {e}")
            return []

    def get_repo_info(self, owner_repo: str) -> dict:
        return self.get(f"/repos/{owner_repo}") or {}

    def get_open_issues(self, owner_repo: str, per_page: int = 30) -> list:
        """Fetch open issues (excludes PRs)."""
        items = self.get(f"/repos/{owner_repo}/issues", {
            "state": "open",
            "sort": "created",
            "direction": "desc",
            "per_page": per_page,
        })
        if not isinstance(items, list):
            return []
        return [i for i in items if "pull_request" not in i]

    def get_issue_count(self, owner_repo: str) -> int:
        """Quick count of open issues from repo info."""
        info = self.get_repo_info(owner_repo)
        return info.get("open_issues_count", 0) if isinstance(info, dict) else 0


# ---------------------------------------------------------------------------
# Issue Processing
# ---------------------------------------------------------------------------

def classify_issue(labels: list[str]) -> dict:
    """Classify issue by type and difficulty."""
    lower = [l.lower() for l in labels]

    is_bug = any(x in l for l in lower for x in ["bug", "defect", "error", "regression"])
    is_feature = any(x in l for l in lower for x in ["enhancement", "feature", "proposal"])
    is_security = any(x in l for l in lower for x in ["security", "vulnerability", "cve"])
    is_good_first = any(x in l for l in lower for x in GOOD_FIRST_ISSUE_LABELS)
    is_help_wanted = any("help wanted" in l or "help-wanted" in l for l in lower)

    if is_security:
        priority = "critical"
    elif is_bug:
        priority = "high"
    elif is_feature:
        priority = "medium"
    else:
        priority = "low"

    return {
        "priority": priority,
        "is_bug": is_bug,
        "is_feature": is_feature,
        "is_security": is_security,
        "is_good_first_issue": is_good_first,
        "is_help_wanted": is_help_wanted,
    }


def process_issue(raw: dict, repo: str, category: str, category_label: str) -> dict:
    """Transform raw GitHub issue to our schema."""
    labels = [l.get("name", "") for l in raw.get("labels", [])]
    created = raw.get("created_at", "")
    classification = classify_issue(labels)

    # Is this "new" (within lookback window)?
    is_new = False
    if created:
        try:
            created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            cutoff = datetime.now(timezone.utc) - timedelta(days=LOOKBACK_DAYS_NEW)
            is_new = created_dt > cutoff
        except ValueError:
            pass

    body = raw.get("body") or ""
    preview = body[:400].replace("\n", " ").strip()
    if len(body) > 400:
        preview += "..."

    return {
        "id": raw["id"],
        "repo": repo,
        "category": category,
        "category_label": category_label,
        "number": raw["number"],
        "title": raw["title"],
        "url": raw["html_url"],
        "author": raw.get("user", {}).get("login", "unknown"),
        "author_avatar": raw.get("user", {}).get("avatar_url", ""),
        "created_at": created,
        "updated_at": raw.get("updated_at", ""),
        "comments": raw.get("comments", 0),
        "labels": labels,
        "body_preview": preview,
        "is_new": is_new,
        **classification,
    }


# ---------------------------------------------------------------------------
# Main Fetcher
# ---------------------------------------------------------------------------

def fetch_all():
    """Main entry: fetch issues from all repos, write JSON files."""

    # Load repo config
    with open(REPOS_FILE) as f:
        config = json.load(f)

    categories = config["categories"]

    # De-duplicate repos (some may appear in multiple categories)
    repo_to_category = {}
    for cat_key, cat_data in categories.items():
        for repo in cat_data["repos"]:
            if repo not in repo_to_category:
                repo_to_category[repo] = (cat_key, cat_data["label"])

    unique_repos = list(repo_to_category.keys())
    total = len(unique_repos)
    log.info(f"🚀 Fetching issues from {total} repos across {len(categories)} categories")

    gh = GitHub(TOKEN)
    all_issues = []
    issues_by_repo = {}
    repo_stats = {}

    for idx, repo in enumerate(unique_repos, 1):
        cat_key, cat_label = repo_to_category[repo]
        log.info(f"  [{idx}/{total}] {repo} ({cat_label})")

        raw_issues = gh.get_open_issues(repo, per_page=MAX_ISSUES_PER_REPO)
        processed = [process_issue(r, repo, cat_key, cat_label) for r in raw_issues]
        all_issues.extend(processed)
        issues_by_repo[repo] = processed

        # Repo-level stats
        repo_info = gh.get_repo_info(repo)
        repo_stats[repo] = {
            "category": cat_key,
            "category_label": cat_label,
            "total_open_issues": repo_info.get("open_issues_count", len(processed)) if isinstance(repo_info, dict) else len(processed),
            "stars": repo_info.get("stargazers_count", 0) if isinstance(repo_info, dict) else 0,
            "forks": repo_info.get("forks_count", 0) if isinstance(repo_info, dict) else 0,
            "description": repo_info.get("description", "") if isinstance(repo_info, dict) else "",
            "fetched_issues": len(processed),
            "new_issues": sum(1 for i in processed if i["is_new"]),
            "bugs": sum(1 for i in processed if i["is_bug"]),
            "features": sum(1 for i in processed if i["is_feature"]),
            "good_first_issues": sum(1 for i in processed if i["is_good_first_issue"]),
            "help_wanted": sum(1 for i in processed if i["is_help_wanted"]),
        }

        if gh.remaining < 50:
            log.warning(f"  ⚠ API rate limit low ({gh.remaining}). Increasing delay.")
            time.sleep(5)
        else:
            time.sleep(REQUEST_DELAY)

    # ---------------------------------------------------------------------------
    # Aggregate Stats
    # ---------------------------------------------------------------------------
    now = datetime.now(timezone.utc).isoformat()
    stats = {
        "generated_at": now,
        "lookback_days_new": LOOKBACK_DAYS_NEW,
        "total_repos": total,
        "total_issues_fetched": len(all_issues),
        "total_new_issues": sum(1 for i in all_issues if i["is_new"]),
        "total_bugs": sum(1 for i in all_issues if i["is_bug"]),
        "total_features": sum(1 for i in all_issues if i["is_feature"]),
        "total_security": sum(1 for i in all_issues if i["is_security"]),
        "total_good_first_issues": sum(1 for i in all_issues if i["is_good_first_issue"]),
        "total_help_wanted": sum(1 for i in all_issues if i["is_help_wanted"]),
        "by_priority": {
            "critical": sum(1 for i in all_issues if i["priority"] == "critical"),
            "high": sum(1 for i in all_issues if i["priority"] == "high"),
            "medium": sum(1 for i in all_issues if i["priority"] == "medium"),
            "low": sum(1 for i in all_issues if i["priority"] == "low"),
        },
        "by_category": {},
        "repos": repo_stats,
    }

    for cat_key, cat_data in categories.items():
        cat_issues = [i for i in all_issues if i["category"] == cat_key]
        stats["by_category"][cat_key] = {
            "label": cat_data["label"],
            "icon": cat_data["icon"],
            "total_repos": len(cat_data["repos"]),
            "total_issues": len(cat_issues),
            "new_issues": sum(1 for i in cat_issues if i["is_new"]),
            "good_first_issues": sum(1 for i in cat_issues if i["is_good_first_issue"]),
        }

    # ---------------------------------------------------------------------------
    # Write output files
    # ---------------------------------------------------------------------------
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with open(DATA_DIR / "issues.json", "w") as f:
        json.dump(all_issues, f, indent=2, default=str)
    log.info(f"📄 Wrote data/issues.json ({len(all_issues)} issues)")

    with open(DATA_DIR / "stats.json", "w") as f:
        json.dump(stats, f, indent=2, default=str)
    log.info(f"📄 Wrote data/stats.json")

    with open(DATA_DIR / "issues_by_repo.json", "w") as f:
        json.dump(issues_by_repo, f, indent=2, default=str)
    log.info(f"📄 Wrote data/issues_by_repo.json")

    log.info(f"\n✅ Done! {len(all_issues)} issues from {total} repos")
    log.info(f"   🆕 New (last {LOOKBACK_DAYS_NEW}d): {stats['total_new_issues']}")
    log.info(f"   🐛 Bugs: {stats['total_bugs']}")
    log.info(f"   ✨ Features: {stats['total_features']}")
    log.info(f"   🟢 Good First Issues: {stats['total_good_first_issues']}")


if __name__ == "__main__":
    fetch_all()
