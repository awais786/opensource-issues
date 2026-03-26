# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Django Issue Hub is a static dashboard that tracks open issues across 100+ Django ecosystem projects. It uses a fetch-and-build pipeline automated via GitHub Actions, with the output served as a static site on GitHub Pages.

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

1. **Fetch** (`fetch_issues.py`) — Queries GitHub API for open issues across all repos defined in `data/repos.json`, classifies each issue (bug/feature/security/good-first-issue, priority level), and writes three JSON files:
   - `data/issues.json` — flat array of all processed issues
   - `data/stats.json` — aggregate and per-category statistics
   - `data/issues_by_repo.json` — issues grouped by repo name

2. **Build** (`build_site.py`) — Reads those JSON files and generates a single self-contained `index.html` with all CSS and JavaScript inlined. Client-side JS handles filtering (by category, type, priority) and full-text search.

GitHub Actions (`.github/workflows/fetch-issues.yml`) runs both scripts daily at 06:00 UTC and commits the updated data files and `index.html` back to the repo.

## Key Files

- **`data/repos.json`** — Primary configuration: 17 categories with 108 repos. Edit this to add/remove tracked repos.
- **`fetch_issues.py`** — Contains tunable constants at the top: `MAX_ISSUES_PER_REPO`, `LOOKBACK_DAYS_NEW`, `ISSUE_MAX_AGE_DAYS`, `REQUEST_DELAY`.
- **`build_site.py`** — All HTML/CSS/JS lives here as Python string templates. The `build_site()` function is the main entry point.
- **`index.html`** — Generated output; do not edit manually.

## Issue Schema

Each issue object in `data/issues.json` has:
- `repo`, `category`, `category_label`, `number`, `title`, `url`
- `author`, `author_avatar`, `created_at`, `updated_at`, `comments`
- `labels` (array), `body_preview` (first 400 chars)
- Boolean flags: `is_new`, `is_bug`, `is_feature`, `is_security`, `is_good_first_issue`, `is_help_wanted`
- `priority`: `"critical"` / `"high"` / `"medium"` / `"low"`

## Contribution Workflow

When making code changes to a fork/issue fix, always follow this sequence:

1. Implement the fix
2. Run the relevant tests to confirm they pass
3. Commit the changes
4. **Run `review-pr` agent before pushing** — get a PASS verdict before `git push`
5. Push only after review passes (or NEEDS WORK items are resolved)

## Team Management (Lead Layer)

Commands for managing the open source contribution team:

| Command / Skill | What it does |
|---|---|
| `/status` | Live snapshot — who's working on what, blockers, recent merges |
| `/assign #<n> <org/repo> @<dev>` | Assign a GitHub issue to a team member |
| `team-status` skill | Full team activity report |
| `sprint-report` skill | Weekly summary of contributions |
| `claim-ticket` skill | Dev claims and loads context for a specific issue |

### Team Members
- **awais786** (Awais) — Django, DRF, pytest, auth, Celery, LiteLLM — senior
- **jawad-khan** (Jawad) — Django, Wagtail, LangChain, RAG — mid
- **valkrypton** (Ali) — Rust, Django, Meilisearch — mid
- **aznszn** (Azan) — Python, JS, Meilisearch, Wagtail — mid

### Target Repos
Defined in `config/repos.yaml` — 30+ openedx repos ordered by dependency.

## User Profile (for contribution agents)

This is the single source of truth referenced by both the `pick-issue` skill and `make-pr` agent.

### Skills (what I can do)
- **Expert in:** Python, Django ORM, Django REST Framework, Celery, pytest, authentication/permissions
- **Comfortable with:** Bug fixes, small features, writing tests, REST API work
- **Avoid:** Deep C extensions, heavy frontend (JS/CSS/HTML), DevOps/infrastructure

### Preferences (what to filter on)
- **Preferred categories:** `django_core`, `rest_api`, `auth_security`, `database_orm`, `testing`, `task_queues`, `py_core`, `py_web`, `py_tools`, `logging_monitoring`, `ecommerce`, `ai_skills`
- **Skip repos:** Wagtail (`wagtail/*`), Open edX (`openedx/*`, `edx/*`)
- **Skip if title/labels contain:** `frontend`, `css`, `javascript`, `js`, `typescript`, `react`, `vue`, `angular`, `scss`, `sass`, `tailwind`, `webpack`, `docker`, `kubernetes`, `helm`, `terraform`, `ci/cd`, `nginx`, `aws`, `gcp`
