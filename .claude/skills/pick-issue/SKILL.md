---
name: pick-issue
description: Find and recommend clean open source issues to work on from Django, Python, or AI ecosystems. Verifies each issue is open, unassigned, and has no in-progress PR. Use when the user asks to find issues, pick a ticket, or wants contribution suggestions.
disable-model-invocation: false
allowed-tools: WebFetch
argument-hint: [ecosystem: django|python|ai|all] [filter: good-first|bugs|all]
---

You are helping a Python/Django expert find the best open source issues to contribute to.

## User Profile
See [profile.md](profile.md) for expertise, preferred categories, and repos/labels to skip.

## Ecosystem Detection

Check `$ARGUMENTS` for ecosystem hints:
- If it contains `ai`, `AI`, `llm`, `LLM` → fetch AI repos directly (see Step 1b)
- If it contains `python` → focus on `py_core`, `py_web`, `py_tools` categories
- Default → Django preferred categories from profile.md

## Steps

### Step 0 — Skip Already-Worked Issues
Check the `## Contribution History` section in MEMORY.md (loaded automatically into context).
Any issue URL listed there must be **discarded immediately** — do not recommend, score, or verify it.

### Step 1a — Fetch Hub Issues
Fetch: `https://awais786.github.io/opensource-issues/data/issues.json`

### Step 1b — Fetch AI Issues (only when ecosystem = "ai")
Fetch these in parallel:
- `https://api.github.com/repos/run-llama/llama_index/issues?state=open&per_page=20&sort=created&direction=desc`
- `https://api.github.com/repos/BerriAI/litellm/issues?state=open&per_page=20&sort=created&direction=desc`
- `https://api.github.com/repos/chroma-core/chroma/issues?state=open&per_page=15&sort=created&direction=desc`
- `https://api.github.com/repos/langchain-ai/langchain/issues?state=open&labels=good+first+issue&per_page=15`

Filter out pull requests (items with `pull_request` field).

### Step 2 — Filter
Apply from profile.md:
- Skip repos in skip list
- Skip issues with excluded labels
- Also skip labels: `question`, `invalid`, `wontfix`, `stale`, `duplicate`

If `$ARGUMENTS` specifies a category or filter, apply it on top.

### Step 3 — Score
- +3 if `is_good_first_issue: true`
- +2 if `is_help_wanted: true`
- +3 if `comments == 0` (no competition)
- +2 if `comments < 5`
- +1 if updated within last 14 days
- +1 if `is_bug: true`
- +1 if `priority: "low"` or `"medium"`
- -1 if `comments > 15`
- -2 if `created_at` more than 1 year ago

### Step 4 — Verify Top Candidates (always, no exceptions)

Take the **top 15 scored issues** and verify each via GitHub API in parallel:
```
https://api.github.com/repos/<owner>/<repo>/issues/<number>
```

**Discard an issue if ANY of these are true:**
- `state` is not `"open"`
- `assignees` array is non-empty (someone claimed it)
- `pull_request` field exists in the response (it's a PR not an issue)
- Body or comments mention a linked PR like "fixes #", "closes #", or "PR #" pointing to an open PR

Check for linked PRs explicitly:
```
https://api.github.com/repos/<owner>/<repo>/issues/<number>/timeline
```
If any event has `event: "cross-referenced"` and the source is an open pull request → discard.

Only proceed with issues confirmed **open + unassigned + no linked PRs**.

### Step 5 — Present Top 5 (verified clean only)

| # | Repo | Issue | Type | Comments | Score | Link |
|---|------|-------|------|----------|-------|------|

All issues in this table are guaranteed: open, unassigned, no in-progress PRs.

### Step 6 — Top Recommendation
Single best pick with: why it fits your skills, concrete approach, estimated scope (small/medium/large), and direct GitHub link.

> **To implement:** say `"Make a PR for <issue-url>"`
