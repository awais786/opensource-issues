#!/usr/bin/env python3
"""
Create a Taiga user story and move it to Ready.

Usage:
    python3 taiga/card.py --repo owner/repo --number 123 --title "..." \
        --url https://... --priority high --category py_tools --taiga-id 355
"""

import argparse
import os
import sys

sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))
from taiga import TaigaClient, STATUS_READY


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo",     required=True)
    parser.add_argument("--number",   required=True, type=int)
    parser.add_argument("--title",    required=True)
    parser.add_argument("--url",      required=True)
    parser.add_argument("--priority", default="medium")
    parser.add_argument("--category", default="")
    parser.add_argument("--taiga-id", required=True, type=int, dest="taiga_id")
    parser.add_argument("--is-bug",   action="store_true", dest="is_bug")
    parser.add_argument("--is-gfi",   action="store_true", dest="is_gfi")
    args = parser.parse_args()

    token = os.environ.get("TAIGA_TOKEN", "")
    if not token:
        print("ERROR: TAIGA_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    issue = {
        "repo":                args.repo,
        "number":              args.number,
        "title":               args.title,
        "url":                 args.url,
        "priority":            args.priority,
        "category":            args.category,
        "is_bug":              args.is_bug,
        "is_good_first_issue": args.is_gfi,
        "is_feature":          False,
        "is_help_wanted":      False,
    }

    client = TaigaClient(token=token)
    us = client.create_user_story(issue, args.taiga_id)
    client.update_status(us["id"], STATUS_READY, us["version"])
    ref = us.get("ref")
    print(f"https://projects.arbisoft.com/project/arbisoft-open-source-projects/us/{ref}")


if __name__ == "__main__":
    main()
