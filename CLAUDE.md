# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Issue Hub is a static dashboard tracking open issues across 160+ open source projects (Django, Python, React, Rust, AI ecosystems). It uses a fetch-and-build pipeline automated via GitHub Actions, served as a static site on GitHub Pages.

**Live site:** `https://awais786.github.io/opensource-issues/`

## Commands

```bash
# Fetch fresh issue data from GitHub API (requires GITHUB_TOKEN env var)
GITHUB_TOKEN=your_token python fetch_issues.py

# Regenerate index.html from cached JSON data (no token needed)
python build_site.py

# View the generated site locally
open index.html
```

There are no tests, linting configs, or package managers in this project.

## Architecture

The pipeline has two independent stages:

1. **Fetch** (`fetch_issues.py`) — Queries GitHub API for open issues across all repos defined in `data/repos.json`, classifies each issue (bug/feature/security/good-first-issue, priority level), and writes output to:
   - `data/issues.json` — flat array of all processed issues
   - `data/stats.json` — aggregate and per-category statistics
   - `data/issues_by_repo.json` — issues grouped by repo name
   - `data/by_category/` — issues split by category (used by `/assign` and agents)

2. **Build** (`build_site.py`) — Reads those JSON files and generates a single self-contained `index.html` with all CSS and JavaScript inlined. Client-side JS handles filtering (by category, type, priority) and full-text search.

GitHub Actions (`.github/workflows/fetch-issues.yml`) runs both scripts daily at 06:00 UTC and commits updated data files and `index.html` back to the repo.

## Key Files

- **`data/repos.json`** — Primary config: 28 categories across 5 ecosystems, 160+ repos. Edit to add/remove tracked repos.
- **`data/devs.json`** — Team roster with GitHub handles, skills, Taiga IDs, and availability flags.
- **`data/assignments.json`** — Persistent assignment history `{url, assignee, taiga_us_url}`. Used by `/assign` to prevent duplicates.
- **`fetch_issues.py`** — Tunable constants at the top: `MAX_ISSUES_PER_REPO`, `LOOKBACK_DAYS_NEW`, `ISSUE_MAX_AGE_DAYS`, `REQUEST_DELAY`.
- **`build_site.py`** — All HTML/CSS/JS lives here as Python string templates. `build_site()` is the entry point.
- **`index.html`** — Generated output; do not edit manually.

## Issue Schema

Each issue object in `data/issues.json` has:
- `repo`, `category`, `category_label`, `number`, `title`, `url`
- `author`, `author_avatar`, `created_at`, `updated_at`, `comments`
- `labels` (array), `body_preview` (first 400 chars)
- Boolean flags: `is_new`, `is_bug`, `is_feature`, `is_security`, `is_good_first_issue`, `is_help_wanted`
- `priority`: `"critical"` / `"high"` / `"medium"` / `"low"`

## Taiga Integration

The `taiga/` module provides a REST API client for the Arbisoft Open Source kanban board (Project ID: 46).

- **`taiga/__init__.py`** — `TaigaClient` dataclass; call `client_from_env()` to instantiate from `TAIGA_TOKEN` env var.
- **`taiga/card.py`** — CLI entry point; called by `/assign` to create user stories.
- Kanban statuses: `278 New → 279 Ready → 280 In progress → 281 Ready for test → 282 Done`
- Required env var: `TAIGA_TOKEN`

## Agentic Workflow (Claude Code Commands)

Commands live in `.claude/commands/`:

| Command | What it does |
|---|---|
| `/assign @dev [category] [filter] [fresh]` | Score & assign best issue to a dev; creates Taiga card; saves to `assignments.json` |
| `/swarm [ecosystem\|dev]` | Bulk triage — assigns best issues across the whole team in one pass |
| `/status` | Live snapshot of who's working on what, blockers, recent merges |

Skills live in `.claude/skills/`:
- **`pick-issue/`** — Finds clean, unassigned issues tailored to a developer's profile (`profile.md`)

Agents live in `.claude/agents/`:
- **`make-pr/`** — Given an issue URL, implements the fix autonomously, runs `review-pr`, and hands off push commands

**`/assign` guardrails** (checked before creating Taiga card):

| Rule | Action |
|------|--------|
| Dev not available | BLOCK |
| Dev has ≥ 5 open assignments | BLOCK |
| Issue in dev's avoid list | BLOCK |
| Zero skill overlap | BLOCK |
| Only 1 skill matched | WARN |
| Issue has > 10 comments | WARN |
| Issue not updated in > 30 days | WARN |

## Contribution Workflow

When making code changes to a fork/issue fix, always follow this sequence:

1. Implement the fix
2. Run the relevant tests to confirm they pass
3. Commit the changes
4. **Run `review-pr` agent before pushing** — get a PASS verdict before `git push`
5. Push only after review passes (or NEEDS WORK items are resolved)

## Team Members

Defined in `data/devs.json`. Current roster:
- **awais786** (Awais) — Django, DRF, pytest, auth, Celery, LiteLLM — senior
- **jawad-khan** (Jawad) — Django, Wagtail, LangChain, RAG — mid
- **valkrypton** (Ali) — Rust, Django, Meilisearch — mid
- **aznszn** (Azan) — Python, JS, Meilisearch, Wagtail — mid

## User Profile (for contribution agents)

Single source of truth referenced by `pick-issue` and `make-pr`.

**Expert in:** Python, Django ORM, Django REST Framework, Celery, pytest, auth/permissions
**Comfortable with:** Bug fixes, small features, writing tests, REST API work
**Avoid:** Deep C extensions, heavy frontend (JS/CSS/HTML), DevOps/infrastructure

**Preferred categories:** `django_core`, `rest_api`, `auth_security`, `database_orm`, `testing`, `task_queues`, `py_core`, `py_web`, `py_tools`, `logging_monitoring`, `ecommerce`, `ai_skills`
**Skip repos:** Wagtail (`wagtail/*`), Open edX (`openedx/*`, `edx/*`)
**Skip if title/labels contain:** `frontend`, `css`, `javascript`, `js`, `typescript`, `react`, `vue`, `angular`, `scss`, `sass`, `tailwind`, `webpack`, `docker`, `kubernetes`, `helm`, `terraform`, `ci/cd`, `nginx`, `aws`, `gcp`
