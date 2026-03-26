#!/usr/bin/env python3
"""
swarm_filter.py — Pre-filter and score issues for the swarm command.

Usage:
    python swarm_filter.py [--ecosystem all|ai|django|python] [--dev GITHUB_HANDLE] [--top N]

Outputs compact JSON: top N scored issues per dev, ready for Claude to assign.
"""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent
DATA = BASE / "data"
MEMORY_FILE = Path.home() / ".claude/projects/-Users-awais-qureshi-Documents-devstack-opensource-issues/memory/MEMORY.md"

SKIP_LABELS = {
    "frontend", "css", "javascript", "js", "typescript", "react", "vue",
    "angular", "scss", "sass", "tailwind", "webpack", "docker", "kubernetes",
    "helm", "terraform", "ci/cd", "nginx", "aws", "gcp",
}

SKIP_REPOS = {"wagtail/wagtail"}
SKIP_REPO_PREFIXES = ("openedx/", "edx/")

ECOSYSTEM_CATEGORIES = {
    "ai": ["ai_skills"],
    "django": ["django_core", "rest_api", "auth_security", "database_orm", "testing", "task_queues"],
    "python": ["py_core", "py_web", "py_tools", "py_packaging", "logging_monitoring"],
    "all": None,  # no filter
}


def load_worked_urls() -> set:
    """Extract already-worked GitHub issue URLs from MEMORY.md."""
    if not MEMORY_FILE.exists():
        return set()
    text = MEMORY_FILE.read_text()
    return set(re.findall(r"https://github\.com/[^\s)>\]]+/issues/\d+", text))


def score_issue(issue: dict) -> int:
    score = 0
    if issue.get("is_good_first_issue"):
        score += 3
    if issue.get("is_help_wanted"):
        score += 2
    comments = issue.get("comments", 0)
    if comments == 0:
        score += 3
    elif comments < 5:
        score += 2
    if comments > 15:
        score -= 1
    if issue.get("is_bug"):
        score += 1
    updated = issue.get("updated_at", "")
    if updated:
        try:
            dt = datetime.fromisoformat(updated.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - dt).days
            if age_days <= 14:
                score += 1
        except ValueError:
            pass
    return score


def is_skippable(issue: dict, skip_titles: set) -> bool:
    repo = issue.get("repo", "")
    if repo in SKIP_REPOS:
        return True
    if any(repo.startswith(p) for p in SKIP_REPO_PREFIXES):
        return True
    title_lower = issue.get("title", "").lower()
    labels = [l.lower() for l in issue.get("labels", [])]
    combined = title_lower + " " + " ".join(labels)
    if any(kw in combined for kw in SKIP_LABELS):
        return True
    if issue.get("url") in skip_titles:
        return True
    return False


def dev_skill_match(issue: dict, dev: dict) -> int:
    """Count how many dev skills appear in issue skills_needed (approximated from labels/category)."""
    dev_skills = {s.lower() for s in dev.get("skills", [])}
    category = issue.get("category", "").lower()
    labels = [l.lower() for l in issue.get("labels", [])]
    issue_text = category + " " + " ".join(labels)
    return sum(1 for skill in dev_skills if skill in issue_text)


def filter_and_score(issues: list, categories: list | None, worked_urls: set) -> list:
    results = []
    for issue in issues:
        if issue.get("comments", 0) >= 10:
            continue
        if categories and issue.get("category") not in categories:
            continue
        if is_skippable(issue, worked_urls):
            continue
        issue["_score"] = score_issue(issue)
        results.append(issue)
    return sorted(results, key=lambda x: x["_score"], reverse=True)


def assign_to_devs(issues: list, devs: list, dev_filter: str | None, top_per_dev: int) -> dict:
    """Assign top issues to devs, max top_per_dev per dev."""
    if dev_filter:
        devs = [d for d in devs if d["github"] == dev_filter]

    assignments = {dev["github"]: [] for dev in devs}
    assigned_urls = set()

    # Two passes: first prioritize preferred categories, then fill remaining slots
    for dev in devs:
        preferred = set(dev.get("preferred_categories", []))
        avoid = {a.lower() for a in dev.get("avoid", [])}

        preferred_issues = [
            i for i in issues
            if i.get("url") not in assigned_urls
            and i.get("category") in preferred
            and not any(a in (i.get("title", "").lower() + " ".join(i.get("labels", []))) for a in avoid)
        ]
        for issue in preferred_issues[:top_per_dev]:
            assignments[dev["github"]].append(issue)
            assigned_urls.add(issue["url"])

    # Fill any dev who got fewer than top_per_dev
    for dev in devs:
        slots = top_per_dev - len(assignments[dev["github"]])
        if slots <= 0:
            continue
        avoid = {a.lower() for a in dev.get("avoid", [])}
        remaining = [
            i for i in issues
            if i.get("url") not in assigned_urls
            and not any(a in (i.get("title", "").lower() + " ".join(i.get("labels", []))) for a in avoid)
        ]
        for issue in remaining[:slots]:
            assignments[dev["github"]].append(issue)
            assigned_urls.add(issue["url"])

    return assignments


def compact_issue(issue: dict) -> dict:
    """Return only fields Claude needs — strips bulk fields."""
    return {
        "url": issue.get("url"),
        "title": issue.get("title"),
        "repo": issue.get("repo"),
        "category": issue.get("category"),
        "labels": issue.get("labels", []),
        "comments": issue.get("comments", 0),
        "is_bug": issue.get("is_bug", False),
        "is_feature": issue.get("is_feature", False),
        "is_good_first_issue": issue.get("is_good_first_issue", False),
        "is_help_wanted": issue.get("is_help_wanted", False),
        "priority": issue.get("priority"),
        "body_preview": issue.get("body_preview", "")[:200],  # trim to 200 chars
        "updated_at": issue.get("updated_at"),
        "_score": issue.get("_score", 0),
    }


def main():
    parser = argparse.ArgumentParser(description="Pre-filter issues for swarm")
    parser.add_argument("--ecosystem", default="all", choices=["all", "ai", "django", "python"])
    parser.add_argument("--dev", default=None, help="GitHub handle to filter to one dev")
    parser.add_argument("--top", type=int, default=3, help="Max issues per dev (default 3)")
    args = parser.parse_args()

    issues_path = DATA / "issues.json"
    devs_path = DATA / "devs.json"

    if not issues_path.exists():
        print(json.dumps({"error": f"issues.json not found at {issues_path}"}))
        sys.exit(1)

    issues = json.loads(issues_path.read_text())
    devs = json.loads(devs_path.read_text())

    categories = ECOSYSTEM_CATEGORIES.get(args.ecosystem)
    worked_urls = load_worked_urls()

    filtered = filter_and_score(issues, categories, worked_urls)
    assignments = assign_to_devs(filtered, devs, args.dev, args.top)

    output = {
        "ecosystem": args.ecosystem,
        "total_issues_scanned": len(issues),
        "total_candidates": len(filtered),
        "assignments": {
            dev: [compact_issue(i) for i in issues_list]
            for dev, issues_list in assignments.items()
        },
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
