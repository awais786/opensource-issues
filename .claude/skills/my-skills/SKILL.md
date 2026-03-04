---
name: pick-issue
description: Fetch open issues from the Django ecosystem hub and suggest the best ones for a Python/Django expert to fix. Use when the user asks to find issues, pick a ticket, or wants contribution suggestions.
disable-model-invocation: false
allowed-tools: WebFetch
argument-hint: [category] [filter: good-first|bugs|all]
---

You are helping a Python/Django expert find the best open source issues to contribute to.

## User Profile
See [profile.md](profile.md) for expertise, preferred categories, and repos/labels to skip.

## Steps

1. Fetch the live issues data:
   - `https://awais786.github.io/opensource-issues/data/issues.json`

2. Apply filters from profile.md (skip repos, skip labels, focus on preferred categories).

3. Score each remaining issue:
   - +3 if `is_good_first_issue: true`
   - +2 if `is_help_wanted: true`
   - +2 if `comments < 5` (low competition)
   - +1 if updated within last 30 days (still active)
   - +1 if `priority: "low"` or `"medium"` (well-scoped)
   - -1 if `comments > 15` (likely stalled or complex)

4. If $ARGUMENTS specifies a category (e.g. `rest_api`) or filter (`good-first`, `bugs`, `all`), apply it on top. Otherwise use all preferred categories.

5. Present the top 5–8 issues sorted by score descending:

   | # | Repo | Issue | Type | Priority | Comments | Score | Why Pick This |
   |---|------|-------|------|----------|----------|-------|---------------|

6. End with a single top recommendation: which issue to start with and why.

> **Tip:** For a deeper analysis with issue verification, use the `issue-picker` agent instead.
