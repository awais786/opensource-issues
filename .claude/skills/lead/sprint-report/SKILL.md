---
name: sprint-report
description: Generates a weekly summary of team contributions — merged PRs, in-progress work, blockers, velocity
type: lead
triggers:
  - "weekly report"
  - "sprint report"
  - "weekly summary"
  - "what did we ship this week"
  - "team report"
---

# Skill: sprint-report

## When to activate
When the Lead asks for a weekly or sprint summary.

## Procedure

1. **GitHub MCP** — for the last 7 days across all repos in `config/repos.yaml`:
   - Merged PRs (filter by team members from memory)
   - Opened PRs still open
   - Issues closed (fixed)
   - Issues newly opened by team

2. **Build the report**:

```
WEEKLY REPORT — week of <date>
──────────────────────────────

SHIPPED (merged PRs)
  ✓ @alice  openedx/edx-val #301    Fix video upload timeout
  ✓ @bob    openedx/edx-search #278 Update ES mapping

IN REVIEW (open PRs)
  ⏳ @alice  openedx/edx-rbac #189   Waiting: maintainer review (3 days)

IN PROGRESS (no PR yet)
  🔧 @carol  openedx/credentials #340 Working on fix

BLOCKED
  ⛔ @bob   openedx/edx-search #278  CI flaky — upstream issue

METRICS
  PRs merged:   2
  PRs open:     1
  Issues fixed: 2
  Avg days open before merge: 4.5
```

3. Output directly in conversation.

## Notes
- Focus on facts, not opinions. Let the Lead draw conclusions.
- If data is sparse (team just started): note "Not enough history yet — check back next week."
