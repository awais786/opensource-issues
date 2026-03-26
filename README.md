# Open Source Issue Hub

A live dashboard tracking open issues across 160+ open source projects across Django, Python, React, Rust, and AI ecosystems — updated daily via GitHub Actions and served as a static site via GitHub Pages.

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
├── taiga/
│   ├── __init__.py              # Taiga REST API client (TaigaClient)
│   └── card.py                  # CLI: create a Taiga user story (called by /assign)
├── index.html                   # Generated dashboard (served by GitHub Pages)
├── data/
│   ├── repos.json               # Single source of truth: all repos & categories
│   ├── devs.json                # Team roster with skills and Taiga IDs
│   ├── issues.json              # All fetched issues (auto-generated, 24h TTL)
│   ├── by_category/             # Issues split by category (for agent reads)
│   ├── assignments.json         # Assignment history (url, assignee, taiga_us_url)
│   ├── stats.json               # Aggregate statistics (auto-generated)
│   └── issues_by_repo.json      # Issues grouped by repo (auto-generated)
├── rules/
│   └── contribution.md          # PR & commit standards for agents
├── .github/workflows/
│   ├── fetch-issues.yml         # Daily automation workflow
│   └── deploy-pages.yml         # GitHub Pages deployment
└── .claude/
    ├── settings.local.json      # Claude Code tool permissions + env vars
    ├── commands/
    │   ├── assign.md            # /assign — agentic issue assignment to a dev
    │   └── swarm.md             # /swarm — triage issues across the whole team
    ├── skills/pick-issue/
    │   ├── SKILL.md             # Skill: find & recommend the best issue to work on
    │   └── profile.md           # Your expertise, preferences, and skip lists
    └── agents/make-pr/
        └── AGENT.md             # Agent: implement a fix and prepare a PR
```

## Setup

### 1. Fork / clone this repo

### 2. Enable GitHub Pages
Go to **Settings → Pages → Source** and set it to **Deploy from branch: `main`, folder: `/ (root)`**.

### 3. Trigger the first run
Go to **Actions → Fetch Issues & Update Dashboard → Run workflow**.

This fetches issues from all repos, generates `index.html`, and commits everything back. GitHub Pages picks it up automatically. After that it runs daily at 06:00 UTC.

### 4. (Optional) Customize the repo list
Edit `data/repos.json` — the single source of truth for all tracked repos.

### 5. (Optional) Enable GitHub MCP for Claude Code

If you use **Claude Code**, you can connect the GitHub MCP server so Claude can read issues, create PRs, and interact with GitHub directly from the CLI.

**Requires:** GitHub Copilot (Free tier is enough — available at github.com/features/copilot)

Add this to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "github": {
      "type": "http",
      "url": "https://api.githubcopilot.com/mcp/",
      "headers": {
        "Authorization": "Bearer ${GITHUB_PERSONAL_ACCESS_TOKEN}"
      }
    }
  },
  "env": {
    "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_pat_here"
  }
}
```

**No Copilot?** Use the free local alternative instead:

```json
{
  "mcpServers": {
    "github": {
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_github_pat_here"
      }
    }
  }
}
```

This gives Claude the same GitHub tools — no Copilot subscription needed.

## Raw JSON API

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
| BerriAI/litellm | LLM proxy & unified API |
| run-llama/llama_index | LlamaIndex RAG framework |
| chroma-core/chroma | Open-source embedding database |
| langchain-ai/langchain | LangChain framework |
| modelcontextprotocol/python-sdk | MCP Python SDK |

---

## Agentic Contribution Workflow

This repo ships a full **agentic pipeline** for finding, assigning, and implementing open source contributions.

```
/assign @dev  →  pick issue  →  Make a PR for <url>  →  review-pr  →  commit & push
```

---

### `/assign` — Issue Assignment

Claude reads issues from `data/by_category/`, scores and filters them for the dev's skills, presents the top 10, runs guardrails, creates a Taiga card, and saves to `data/assignments.json`.

**Usage (inside Claude Code):**
```
/assign @jawad-khan
/assign @valkrypton bug
/assign @aznszn django
/assign @awais786 ai fresh
```

**Arguments:**
- `@dev` — GitHub handle (required)
- `category` — optional filter: django, python, ai, rest, auth, search, celery, orm, testing
- `filter` — optional: bug, feature, gfi
- `fresh` — force re-fetch even if cache is < 24h

**Guardrails (checked before creating Taiga card):**

| Rule | Action |
|------|--------|
| Dev not available | BLOCK |
| Dev has ≥ 5 open assignments | BLOCK |
| Issue in dev's avoid list | BLOCK |
| Zero skill overlap | BLOCK |
| Only 1 skill matched | WARN |
| Issue has > 10 comments | WARN |
| Issue not updated in > 30 days | WARN |

**Team roster:** Edit `data/devs.json` to add/update developers and their skills.

---

### `/swarm` — Bulk Team Triage

Assigns the best available issues across the whole team in one pass.

**Usage:**
```
/swarm                      # triage all devs
/swarm django               # Django ecosystem only
/swarm AI                   # AI repos only
/swarm awais786             # one dev only
```

---

### `/pick-issue` Skill

Finds clean, unassigned issues tailored to a single developer's profile.

**Usage:**
```
/pick-issue           # Django ecosystem (default)
/pick-issue django    # Django/Python repos
/pick-issue AI        # AI repos (litellm, llama_index, chroma, langchain)
/pick-issue AI MCP    # AI repos with MCP preference
```

**What it does:**
1. Fetches issues from hub or GitHub API depending on ecosystem
2. Filters based on your profile (`skills/pick-issue/profile.md`)
3. Scores issues by freshness, comment count, labels
4. Verifies top 15 via live GitHub API — discards assigned, closed, or in-progress
5. Presents top 5 guaranteed clean issues + top recommendation

---

### `make-pr` Agent

Give it an issue URL and it implements the fix autonomously, then hands off for you to commit.

**Usage:**
```
Make a PR for https://github.com/owner/repo/issues/123
```

**What it does:**
1. Validates issue is open, unassigned, no duplicate PRs
2. Checks if fork exists, clones repo, syncs with upstream
3. Reads CONTRIBUTING.md, installs deps, studies recent merged PRs
4. Explores codebase, creates feature branch, implements minimal fix
5. Shows diff and asks for approval
6. Commits locally and runs `review-pr` before handing off push commands

---

### Contribution Memory

All tools share a persistent memory file that tracks worked issues, team notes, and workflow rules. Already-worked issues are automatically skipped when finding new ones.

```
~/.claude/projects/<project-hash>/memory/MEMORY.md
```

Assignments are also tracked in `data/assignments.json` — used by `/assign` to prevent duplicate assignments.

### Personalizing Your Profile

Edit `.claude/skills/pick-issue/profile.md` to customize:
- Your skills and comfort areas
- Preferred issue categories
- Repos and labels to skip

Edit `data/devs.json` to manage the team roster for `/swarm`.

---

## Contributing

PRs welcome to:
- Add repos to `data/repos.json`
- Improve the dashboard (`build_site.py`)
- Improve the fetch/classification logic (`fetch_issues.py`)
