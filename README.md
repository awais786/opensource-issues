# Django Issue Hub

A live dashboard tracking open issues across 100+ Django ecosystem projects — updated daily via GitHub Actions and served as a static site via GitHub Pages.

**Live site:** `https://<your-username>.github.io/<repo-name>/`

## What It Does

- Fetches open issues from 100+ repos: Django core, DRF, Wagtail, Celery, Open edX, and more
- Classifies issues by priority, type (bug/feature/security), and contributor-friendliness
- Generates a filterable, searchable static HTML dashboard
- Commits the data JSON files so anyone can consume the raw API

## Repository Structure

```
.
├── fetch_issues.py              # GitHub API fetcher (runs as GitHub Action)
├── build_site.py                # Static site generator
├── index.html                   # Generated dashboard (served by GitHub Pages)
├── data/
│   ├── repos.json               # Repo list and category config
│   ├── issues.json              # All fetched issues (auto-generated)
│   ├── stats.json               # Aggregate statistics (auto-generated)
│   └── issues_by_repo.json      # Issues grouped by repo (auto-generated)
└── .github/workflows/
    └── fetch-issues.yml         # Daily automation workflow
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
Edit `data/repos.json` to add, remove, or reorganize repos and categories.

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

# Open index.html in your browser
open index.html
```

## Categories

17 categories covering the full Django ecosystem:

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

## Contributing

PRs welcome to add repos to `data/repos.json` or improve the dashboard.
