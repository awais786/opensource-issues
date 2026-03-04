# Open Source Issue Hub

A live dashboard tracking open issues across 160+ open source projects across Django, Python, React, Rust, and AI Skills ecosystems — updated daily via GitHub Actions and served as a static site via GitHub Pages.

**Live site:** `https://awais786.github.io/opensource-issues/`

## What It Does

- Fetches open issues from 160+ repos across 5 ecosystems
- Classifies issues by priority, type (bug/feature/security), and contributor-friendliness
- Generates a filterable, searchable static HTML dashboard
- Commits data JSON files so anyone can consume the raw API

## Repository Structure

```
.
├── fetch_issues.py              # GitHub API fetcher (runs as GitHub Action)
├── build_site.py                # Static site generator
├── index.html                   # Generated dashboard (served by GitHub Pages)
├── data/
│   ├── repos.json               # Single source of truth: all repos & categories
│   ├── issues.json              # All fetched issues (auto-generated)
│   ├── stats.json               # Aggregate statistics (auto-generated)
│   └── issues_by_repo.json      # Issues grouped by repo (auto-generated)
├── .github/workflows/
│   ├── fetch-issues.yml         # Daily automation workflow
│   └── deploy-pages.yml         # GitHub Pages deployment
└── .claude/
    ├── skills/my-skills/        # Skill: pick the best issue to work on
    └── agents/
        ├── issue-picker/        # Agent: autonomously find & rank issues
        └── make-pr/             # Agent: autonomously create a PR
```

## Setup

### 1. Fork / clone this repo

### 2. Enable GitHub Pages
Go to **Settings → Pages → Source** and set it to **Deploy from branch: `main`, folder: `/ (root)`**.

### 3. Trigger the first run
Go to **Actions → Fetch Issues & Update Dashboard → Run workflow**.

This will fetch issues from all repos, generate `index.html`, and commit everything back to the repo. GitHub Pages will pick it up automatically.

After that, it runs automatically every day at 06:00 UTC.

### 4. (Optional) Customize the repo list
Edit `data/repos.json` — it is the single source of truth for all tracked repos. Add, remove, or reorganize repos and categories there.

## Raw JSON API

The data files are committed to the repo and served publicly:

| File | Description |
|------|-------------|
| `data/issues.json` | All issues (up to 30 per repo) |
| `data/stats.json` | Aggregate counts by category, priority, etc. |
| `data/issues_by_repo.json` | Issues grouped by repository |
| `data/repos.json` | Repo list with category metadata |

## Local Development

```bash
# Fetch fresh data (requires GITHUB_TOKEN env var)
GITHUB_TOKEN=your_token python fetch_issues.py

# Build the static site from cached data
python build_site.py

# Open in browser
open index.html
```

## Ecosystems & Categories

28 categories across 5 ecosystems:

### Django
| Category | Examples |
|----------|---------|
| Django Core | django/django, django/channels |
| REST & API | encode/django-rest-framework, tfranzel/drf-spectacular |
| GraphQL | graphql-python/graphene-django, strawberry-graphql/strawberry-django |
| CMS & Content | wagtail/wagtail, django-cms/django-cms |
| Open edX | openedx/edx-platform, openedx/credentials |
| Task Queues | celery/celery, rq/django-rq |
| Auth & Security | pennersr/django-allauth, jazzband/django-oauth-toolkit |
| Database & ORM | django-mptt/django-mptt, carltongibson/django-filter |
| Admin & UI | jazzband/django-debug-toolbar, farridav/django-jazzmin |
| Forms & Frontend | django-crispy-forms/django-crispy-forms, adamchainz/django-htmx |
| E-Commerce | django-oscar/django-oscar, saleor/saleor |
| Storage & Files | jschneier/django-storages |
| Config & DevOps | joke2k/django-environ, cookiecutter/cookiecutter-django |
| Testing | FactoryBoy/factory_boy, pytest-dev/pytest-django |
| Search | django-haystack/django-haystack |
| i18n & Geo | django-parler/django-parler, GeoNode/geonode |
| Logging & Monitoring | jazzband/django-silk |

### Python
| Category | Examples |
|----------|---------|
| Python Core | python/cpython, python/mypy |
| Packaging & Build | pypa/pip, pypa/hatch |
| Python Web | pallets/flask, tiangolo/fastapi |
| Dev Tools | astral-sh/ruff, astral-sh/uv |

### React
| Category | Examples |
|----------|---------|
| React Core | facebook/react, remix-run/react-router |
| Meta Frameworks | vercel/next.js, remix-run/remix |
| State Management | reduxjs/redux-toolkit, pmndrs/zustand |
| Build & Tooling | vitejs/vite, evanw/esbuild |

### Rust
| Category | Examples |
|----------|---------|
| Rust Core | rust-lang/rust, rust-lang/cargo |
| Async & Web | tokio-rs/tokio, tokio-rs/axum |
| CLI & Tooling | clap-rs/clap, BurntSushi/ripgrep |
| Serialization | serde-rs/serde |

### AI Skills
| Repo | Description |
|------|-------------|
| anthropics/skills | Official Claude skills repository |
| anthropics/claude-cookbooks | Official Anthropic cookbooks & examples |
| alirezarezvani/claude-skills | Domain expert skills (marketing, engineering, product) |
| K-Dense-AI/claude-scientific-skills | Scientific/research skills (ML, bioinformatics, chemistry) |
| daymade/claude-code-skills | Production-ready marketplace skills |
| ComposioHQ/awesome-claude-skills | Productivity & integration skills |
| travisvn/awesome-claude-skills | Curated awesome list |
| VoltAgent/awesome-agent-skills | Community-adopted agent skills |
| yusufkaraaslan/Skill_Seekers | Auto-generate skills from documentation |
| affaan-m/everything-claude-code | Hooks, observers, session management |
| hesreallyhim/awesome-claude-code | Curated Claude Code resources |

## Claude Code Skills & Agents

This repo ships two Claude Code skills and two agents for contribution workflows.

### Skills

#### `my-skills` — Pick an Issue
Fetches live issues from the hub, scores them based on your profile, and recommends the best ones to work on.

```
/my-skills
/my-skills rest_api good-first
/my-skills bugs
```

Scoring criteria: `good_first_issue`, `help_wanted`, low comment count (less competition), recently updated, scoped priority.

#### Profile (`skills/my-skills/profile.md`)
Defines your expertise and preferences — which categories to focus on, which repos/labels to skip. Edit this file to personalize issue recommendations.

---

### Agents

#### `issue-picker` — Autonomous Issue Finder
Fetches issues, filters and scores them, then verifies each is still open via the GitHub CLI before recommending. More thorough than the skill.

```
Use the issue-picker agent
```

#### `make-pr` — Autonomous PR Creator
Give it an issue URL and it will: analyze the issue, explore the target repo, create a branch, implement the fix, run tests, and open a PR.

```
Use the make-pr agent with https://github.com/owner/repo/issues/123
```

---

## Contributing

PRs welcome to:
- Add repos to `data/repos.json`
- Improve the dashboard (`build_site.py`)
- Improve the fetch/classification logic (`fetch_issues.py`)
