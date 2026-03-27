#!/usr/bin/env python3
"""
swarm_assign.py — Full automation: filter issues, assign to devs, create Taiga cards.

Usage:
    python3 swarm_assign.py [--ecosystem all|ai|django|python] [--top N]

Reads:  data/issues.json, data/devs.json, data/assignments.json
Writes: data/assignments.json (appends new entries with taiga_us_url)
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).parent

sys.path.insert(0, str(BASE))
from swarm_filter import filter_and_score, assign_to_devs, compact_issue, load_worked_urls, ECOSYSTEM_CATEGORIES
from taiga import client_from_env


def load_existing_urls(assignments_path: Path) -> set:
    if not assignments_path.exists():
        return set()
    try:
        data = json.loads(assignments_path.read_text())
        return {a["url"] for a in data if "url" in a}
    except (ValueError, KeyError):
        return set()


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--ecosystem", default="all", choices=["all", "ai", "django", "python"])
    parser.add_argument("--top", type=int, default=3)
    args = parser.parse_args()

    issues_path = BASE / "data" / "issues.json"
    devs_path = BASE / "data" / "devs.json"
    assignments_path = BASE / "data" / "assignments.json"

    issues = json.loads(issues_path.read_text())
    devs = json.loads(devs_path.read_text())
    existing_urls = load_existing_urls(assignments_path)
    worked_urls = load_worked_urls() | existing_urls

    categories = ECOSYSTEM_CATEGORIES.get(args.ecosystem)
    filtered = filter_and_score(issues, categories, worked_urls)
    assignments = assign_to_devs(filtered, devs, None, args.top)

    # Load existing assignments
    existing = json.loads(assignments_path.read_text()) if assignments_path.exists() else []

    # Connect to Taiga
    try:
        client = client_from_env()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    new_entries = []
    dev_map = {d["github"]: d for d in devs}

    for github_handle, issue_list in assignments.items():
        dev = dev_map.get(github_handle, {})
        for issue in issue_list:
            if issue["url"] in existing_urls:
                continue

            # Create Taiga card
            taiga_us_url = None
            try:
                full_issue = {
                    "repo":                issue["repo"],
                    "number":              int(issue["url"].split("/")[-1]),
                    "title":               issue["title"],
                    "url":                 issue["url"],
                    "priority":            issue.get("priority", "low"),
                    "category":            issue.get("category", ""),
                    "is_bug":              issue.get("is_bug", False),
                    "is_good_first_issue": issue.get("is_good_first_issue", False),
                    "is_feature":          issue.get("is_feature", False),
                    "is_help_wanted":      issue.get("is_help_wanted", False),
                    "body_preview":        issue.get("body_preview", ""),
                }
                us = client.create_user_story(full_issue, dev.get("taiga_id"))
                ref = us.get("ref")
                taiga_us_url = f"https://projects.arbisoft.com/project/arbisoft-open-source-projects/us/{ref}"
                print(f"Created Taiga card: {taiga_us_url}")
            except Exception as e:
                print(f"WARNING: Taiga card creation failed for {issue['url']}: {e}", file=sys.stderr)

            entry = {
                "url":           issue["url"],
                "repo":          issue["repo"],
                "number":        int(issue["url"].split("/")[-1]),
                "title":         issue["title"],
                "assignee":      github_handle,
                "assignee_name": dev.get("name", github_handle),
                "status":        "assigned",
                "assigned_at":   datetime.now(timezone.utc).isoformat(),
                "taiga_us_url":  taiga_us_url,
                "priority":      issue.get("priority", "low"),
                "category":      issue.get("category", ""),
            }
            new_entries.append(entry)
            print(f"Assigned: [{github_handle}] {issue['title'][:60]}")

    if new_entries:
        existing.extend(new_entries)
        assignments_path.write_text(json.dumps(existing, indent=2))
        print(f"\nSaved {len(new_entries)} new assignments to {assignments_path}")
    else:
        print("No new assignments — all top issues already assigned.")


if __name__ == "__main__":
    main()
