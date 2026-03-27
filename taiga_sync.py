#!/usr/bin/env python3
"""
taiga_sync.py — Create Taiga cards for assignments where taiga_us_url is null.

Called by GitHub Actions when assignments.json is updated by claude.ai trigger.

Usage:
    python3 taiga_sync.py
"""
import json
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

from taiga import client_from_env

ASSIGNMENTS_PATH = BASE / "data" / "assignments.json"
DEVS_PATH = BASE / "data" / "devs.json"


def main():
    assignments = json.loads(ASSIGNMENTS_PATH.read_text())
    devs = {d["github"]: d for d in json.loads(DEVS_PATH.read_text())}

    pending = [a for a in assignments if not a.get("taiga_us_url")]

    if not pending:
        print("No pending assignments — all Taiga cards already created.")
        return

    print(f"Found {len(pending)} pending assignments, creating Taiga cards...")

    try:
        client = client_from_env()
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    updated = False
    for entry in assignments:
        if entry.get("taiga_us_url"):
            continue

        dev = devs.get(entry.get("assignee", ""), {})
        taiga_id = dev.get("taiga_id")

        issue = {
            "repo":                entry.get("repo", ""),
            "number":              entry.get("number", 0),
            "title":               entry.get("title", ""),
            "url":                 entry.get("url", ""),
            "priority":            entry.get("priority", "low"),
            "category":            entry.get("category", ""),
            "is_bug":              entry.get("is_bug", False),
            "is_good_first_issue": entry.get("is_good_first_issue", False),
            "is_feature":          entry.get("is_feature", False),
            "is_help_wanted":      entry.get("is_help_wanted", False),
            "body_preview":        entry.get("body_preview", ""),
        }

        try:
            us = client.create_user_story(issue, taiga_id)
            ref = us.get("ref")
            taiga_us_url = f"https://projects.arbisoft.com/project/arbisoft-open-source-projects/us/{ref}"
            entry["taiga_us_url"] = taiga_us_url
            print(f"Created: {taiga_us_url} → [{entry['assignee']}] {entry['title'][:60]}")
            updated = True
        except Exception as e:
            print(f"WARNING: Failed for {entry['url']}: {e}", file=sys.stderr)

    if updated:
        ASSIGNMENTS_PATH.write_text(json.dumps(assignments, indent=2))
        print(f"\nUpdated {ASSIGNMENTS_PATH}")


if __name__ == "__main__":
    main()
