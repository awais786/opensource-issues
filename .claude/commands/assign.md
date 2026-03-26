# /assign

Assign an open source issue to a team member and create a Taiga card.

## Usage
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

---

## Step 1 — Parse arguments

From `$ARGUMENTS` identify:
- **dev**: github handle (jawad-khan, valkrypton, awais786, aznszn)
- **category** (optional)
- **filter** (optional)
- **fresh** flag (optional)

---

## Step 2 — Load data

Read `data/devs.json` and find the dev by github handle (case-insensitive).
If not found, list available devs and stop.

Check freshness of `data/by_category/` — use the mtime of any file there.
If stale (> 24h) or `fresh` flag set, run:
```bash
GITHUB_TOKEN=$GITHUB_PERSONAL_ACCESS_TOKEN python3 fetch_issues.py
```
Tell the user before starting (takes 2-3 min).

Then read only the category files the dev prefers — e.g. for valkrypton read:
- `data/by_category/database_orm.json`
- `data/by_category/py_tools.json`
- `data/by_category/py_core.json`
- `data/by_category/search.json` (if exists)

These are small files (7–43 issues each) — read them all directly.

---

## Step 3 — Filter

From the issues array, keep only issues where:
1. `category` is in the dev's `preferred_categories`
2. No label or title word matches the dev's `avoid` list
3. No label or title contains: frontend, css, javascript, typescript, react, docker, kubernetes
4. URL is not already in `data/assignments.json`
5. If category argument given → keep only matching category
6. If filter argument given → keep only issues with that flag true (`is_bug`, `is_feature`, `is_good_first_issue`)

---

## Step 4 — Score and rank

Score each remaining issue mentally:
- +3 if `is_good_first_issue`
- +2 if `is_help_wanted`
- +3 if `comments == 0`, +2 if `comments < 5`
- +2 if `is_bug`
- +2 if `priority` is critical or high
- +1 if updated within last 14 days
- -2 if `comments > 15`
- -2 if created more than 1 year ago

Present the **top 10** as a table:

```
Top issues for @valkrypton (Ali Tariq):

 #  Repo              Title                                        Type      Pri     💬
──  ────────────────  ───────────────────────────────────────────  ────────  ──────  ──
 1  meilisearch       ...                                          🐛 bug    HIGH     0
 2  ...

Pick a number (1–10), or 0 to cancel:
```

**Stop and wait for the user to pick.**

---

## Step 5 — Guardrail check

Once the user picks an issue, check these rules **before** creating the Taiga card:

**BLOCKS (stop, do not proceed):**
- Dev's `availability` is not `"available"`
- Dev already has ≥ 5 assignments with status `assigned` or `in_progress` in `data/assignments.json`
- Issue `category` contains a word from the dev's `avoid` list
- Zero skill overlap between dev's `skills` and the category's required skills

**WARNINGS (ask "Proceed anyway?"):**
- Only 1 skill matched (weak fit)
- `comments > 10` (competitive issue)
- Issue not updated in > 30 days (possibly stale)

Show guardrail results clearly before proceeding.

---

## Step 6 — Create Taiga card

Run:
```bash
python3 taiga/card.py \
  --repo "REPO" \
  --number NUMBER \
  --title "TITLE" \
  --url "URL" \
  --priority PRIORITY \
  --category CATEGORY \
  --taiga-id TAIGA_ID \
  [--is-bug] [--is-gfi]
```

Fill in all values from the chosen issue and dev profile.

---

## Step 7 — Save to assignments.json

Append a new entry to `data/assignments.json`:
```json
{
  "url": "...",
  "repo": "...",
  "number": 123,
  "title": "...",
  "assignee": "github_handle",
  "assignee_name": "Full Name",
  "status": "assigned",
  "assigned_at": "<ISO timestamp>",
  "taiga_us_url": "https://projects.arbisoft.com/...",
  "priority": "...",
  "category": "..."
}
```

Read the existing file, append the new entry, write it back.

---

## Step 8 — Report

```
✅ Assignment complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Issue   : [repo#number] title
Dev     : Full Name (@github_handle)
Taiga   : ✓ <url>
Saved   : data/assignments.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
