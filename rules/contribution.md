# Contribution Standards

## Commit Format (REQUIRED)
```
<type>: <short description>

<optional body — why, not what>
```
Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

**WRONG:** `fixed the thing`, `update`, `wip`
**RIGHT:** `fix: handle empty string input in user validator`

## Branch Naming
```
fix/issue-<number>-<short-slug>
feat/issue-<number>-<short-slug>
```
Example: `fix/issue-301-video-upload-timeout`

## PR Rules
- One issue per PR — never bundle unrelated fixes
- PR title = commit message format (`fix: ...`)
- Always link the issue: `Closes #<number>`
- Tests required for every bug fix
- No WIP PRs submitted upstream (use draft if needed)
- Rebase on upstream main before submitting — no merge commits

## Code Rules
- Only change what the issue describes — no opportunistic refactoring
- Match the style of the surrounding code in the repo
- If you add a function, add a test for it
- Never hardcode secrets or tokens

## Upstream Etiquette
- Read CONTRIBUTING.md before touching any repo
- Respond to maintainer review comments within 48h
- If a PR goes stale (5+ days no response): ping politely once, then escalate to Lead
- Accept maintainer style preferences even if you disagree

## Pre-Submit Checklist
- [ ] Tests pass locally
- [ ] No linting errors
- [ ] Commit messages are clean
- [ ] PR description is filled in (not template defaults)
- [ ] Issue is linked in PR body
- [ ] Branch is rebased on upstream main
