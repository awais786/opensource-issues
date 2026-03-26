---
name: team-status
description: Shows a live snapshot of team activity — in-progress work, open issues, blocked items, recent merges
type: lead
triggers:
  - "status"
  - "team status"
  - "what's the team working on"
  - "what is everyone doing"
  - "show me the team"
---

# Skill: team-status

## When to activate
When the Lead asks for a team overview, uses `/status`, or asks what the team is working on.

## Procedure

1. **Read memory** for team member list and current assignments
2. **GitHub MCP** — for each team member:
   - Open PRs they've authored in any repo from `config/repos.yaml`
   - Issues assigned to them
   - PRs merged in the last 7 days
3. **Build the report**:

```
TEAM STATUS — <today's date>
─────────────────────────────

IN PROGRESS
  @<dev>  #<n>  <org/repo>  <issue title>  <PR: open/draft/none>

OPEN / UNASSIGNED (top picks from /pick scoring)
  #<n>  <org/repo>  <title>  <labels>

MERGED THIS WEEK
  @<dev>  #<n>  <org/repo>  <title>  ✓ merged

BLOCKED
  @<dev>  #<n>  <reason>
```

4. Output the report directly in the conversation. Do not save to a file.

## Notes
- "Blocked" = PR open for 5+ days with no maintainer response, or CI failing > 24h
- If no memory for team members: ask "Who's on your team? I'll remember them."
