---
name: claim-ticket
description: Dev claims a specific GitHub issue — posts comment, sets up local context, prepares to fix
type: dev
triggers:
  - "claim #"
  - "claim ticket"
  - "i'll take #"
  - "assign me #"
  - "working on #"
---

# Skill: claim-ticket

## When to activate
When a dev says they want to work on a specific issue.

## Procedure

1. **Parse** the issue number and repo from the message.
   - If repo not specified: check memory for recently picked issues or ask "Which repo?"

2. **Read the issue** via GitHub MCP:
   - Title, body, all comments
   - Labels, existing assignees
   - Linked PRs (is it already being worked on?)

3. **Check for conflicts**:
   - If already assigned to someone else: warn "This issue is assigned to @<user>. Claim anyway? (y/n)"
   - If a PR is already open: "There's already a PR (#<n>) for this. Do you want to take it over?"

4. **Claim**:
   - Post GitHub comment: "Picking this up — will submit a PR. /devteam-pilot"
   - Add GitHub assignee (if PAT has permission)

5. **Load context**:
   - Read `CONTRIBUTING.md` of the repo
   - Read the files mentioned in the issue body
   - Summarize: what needs to change, where, and why

6. **Output**:
```
Claimed #<number> in <org/repo>
Title: <title>

CONTEXT
  Relevant files: <list>
  What to fix: <1-2 sentence summary>
  Effort estimate: <LOW/MEDIUM/HIGH>

NEXT STEP
  Run `/fix #<number> <org/repo>` to start the fix.
```

## Notes
- Always read the issue before claiming — don't claim blindly
- If effort is HIGH: flag it to Lead before proceeding
