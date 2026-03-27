---
description: Run the multi-agent issue triage swarm — finds, analyses, and assigns open source issues to the Arbisoft team
---

# Swarm — Issue Triage

**IMPORTANT: Before doing anything else, use the AskUserQuestion tool to present these two questions to the user. Wait for their answers before proceeding.**

Ask the user:

**Question 1 — Ecosystem** (header: "Ecosystem", single select):
- `All` — Triage all repos across every category
- `AI` — ai_skills: LiteLLM, LlamaIndex, LangChain, Chroma, MCP
- `Django` — django_core: Django framework and official packages
- `Python` — py_core / py_tools / py_web

**Question 2 — Developer** (header: "Developer", single select):
- `Whole team` — Assign across awais786, jawad-khan, valkrypton, aznszn
- `awais786` — Awais · Django, DRF, pytest, auth, LiteLLM (senior)
- `jawad-khan` — Jawad · Django, Wagtail, LangChain, RAG (mid)
- `valkrypton / aznszn` — Ali or Azan · Rust/Meilisearch/search (mid)

Once the user answers, map their selections to flags and run the pipeline below.

---

## Step 0 — Run Python Filter (you do this via Bash)

Map user selections to CLI args:
- Ecosystem: `all` | `ai` | `django` | `python`
- Dev filter: omit for whole team, or `--dev GITHUB_HANDLE` for single dev

Run:
```bash
python3 /Users/awais.qureshi/Documents/devstack/opensource-issues/swarm_filter.py \
  --ecosystem <ecosystem> \
  [--dev <github_handle>] \
  --top 3
```

This outputs compact JSON with pre-filtered, scored, and dev-matched issues.
**Do not read data/issues.json directly** — the script handles all filtering.

---

## Stage 1 — ComplexityAnalyzer (you do this)

For each issue in the script output, estimate:
- `complexity`: low / medium / high
- `effort_days`: integer
- `reasoning`: one sentence

Base on: body_preview content, is_bug vs is_feature, comment count, labels, priority.

---

## Stage 2 — FixSuggester (you do this)

For each issue, produce:
- `approach`: 2-3 sentence fix description
- `files_likely`: file patterns to change
- `skills_needed`: list of skills required

---

## Stage 3 — DevAssigner (you do this)

The script already pre-matched issues to devs. Validate and confirm assignments:

**Team:**
- **awais786** (Awais) — Django, DRF, pytest, auth, Celery, LiteLLM, AI — senior
- **jawad-khan** (Jawad) — Django, Wagtail, LangChain, RAG, Anthropic SDK — mid
- **valkrypton** (Ali) — Rust, Django, Meilisearch, Diesel ORM — mid
- **aznszn** (Azan) — Python, JS, Meilisearch, Wagtail, search — mid

**Rules:**
- High complexity or auth/security → prefer senior (awais786)
- Low complexity → prefer mid devs
- Max 2 issues per dev in final output

---

## Output

Print a markdown report:

### Issue Assignments

| # | Issue | URL | Repo | Complexity | Effort | Assigned To |
|---|-------|-----|------|------------|--------|-------------|

- **Issue** column: plain title (no link)
- **URL** column: full GitHub URL as plain text so it can be copied and also used directly in `Make a PR for <url>`

### Top Pick

Single best issue+dev pair with explanation.

---

## Stage 4 — Save to Taiga (you do this via Bash)

First check for any pending entries (taiga_us_url is null) from previous cloud runs:
```bash
python3 -c "
import json
data = json.load(open('data/assignments.json'))
pending = [a for a in data if not a.get('taiga_us_url')]
print(json.dumps(pending, indent=2))
"
```

For each assigned issue (new + any pending with null taiga_us_url), create a Taiga card. Look up the dev's `taiga_id` from `data/devs.json`.

```bash
python3 /Users/awais.qureshi/Documents/devstack/opensource-issues/taiga/card.py \
  --repo "<owner/repo>" \
  --number <issue_number> \
  --title "<issue title>" \
  --url "<issue_url>" \
  --priority <low|medium|high|critical> \
  --category "<category>" \
  --taiga-id <dev_taiga_id> \
  [--is-bug]
```

Run one command per issue. After each, update the matching entry in `data/assignments.json` with the returned Taiga URL.

---

After Taiga cards are created, prompt:

> **Assignments saved to Taiga.** Say `Make a PR for <url>` to start implementing the top pick now, or pick a different issue from the table above.
