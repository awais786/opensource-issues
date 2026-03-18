"""
Multi-agent issue triage swarm for the Arbisoft open source team.

Pipeline:
  IssueFinder → ComplexityAnalyzer → FixSuggester → DevAssigner

Data sources (all local, no re-fetch needed):
  data/issues.json      — built by fetch_issues.py
  data/devs.json        — team roster with skills
  data/repos.json       — repo categories
  data/swarm_cache.json — persisted analysis (complexity + fix suggestions)
                          re-runs skip Claude calls for already-analysed issues
  MEMORY.md             — contribution history; worked issues are skipped

Output: markdown assignment report + ready-to-run "Make a PR" command
        for each assigned issue.

Run:
    python swarm.py                          # triage all issues
    python swarm.py --category django_core   # filter by category
    python swarm.py --dev awais786           # issues for one dev only
    python swarm.py --fetch                  # refresh issues first
    python swarm.py --fresh                  # ignore cache, re-analyse everything
    python swarm.py --output report.md       # save report to file
"""

import argparse
import anyio
import json
import re
import sys
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions, ResultMessage

ROOT          = Path(__file__).parent
ISSUES_JSON   = ROOT / "data" / "issues.json"
DEVS_JSON     = ROOT / "data" / "devs.json"
REPOS_JSON    = ROOT / "data" / "repos.json"
CACHE_JSON    = ROOT / "data" / "swarm_cache.json"
MEMORY_MD     = Path.home() / ".claude/projects/-Users-awais-qureshi-Documents-devstack-opensource-issues/memory/MEMORY.md"
ISSUES_URL    = "https://awais786.github.io/opensource-issues/data/issues.json"
CACHE_TTL_SEC = 86400  # 24 hours

# ---------------------------------------------------------------------------
# Agent system prompts
# ---------------------------------------------------------------------------

ISSUE_FINDER_PROMPT = """\
You are IssueFinder, the first stage of an open source triage swarm.

You receive a JSON array of issues from the hub and a team profile.

Filter to the best contribution candidates:
- Prefer: is_good_first_issue=true OR is_help_wanted=true
- Prefer: comments < 10 (low competition)
- Prefer: is_bug=true (clearer scope)
- Skip any issue whose title or labels contain:
  frontend, css, javascript, js, typescript, react, vue, angular,
  scss, webpack, docker, kubernetes, helm, terraform, nginx, aws, gcp
- Skip repos: wagtail/wagtail, openedx/*, edx/*

Return the top 8 issues as a JSON array with these fields only:
  repo, number, title, url, labels, is_bug, is_feature,
  is_good_first_issue, is_help_wanted, comments, priority, body_preview

Output ONLY the JSON array — no prose, no markdown fences.\
"""

COMPLEXITY_ANALYZER_PROMPT = """\
You are ComplexityAnalyzer, the second stage of an open source triage swarm.

You receive a JSON array of pre-filtered issues.

For each issue estimate:
  complexity : "low" | "medium" | "high"
  effort_days: integer (realistic working days for a mid-level Python dev)
  reasoning  : one sentence explaining your estimate

Base your estimate on:
- body_preview detail and length
- is_bug (usually lower) vs is_feature (usually higher)
- comments count — more comments often means more complex discussion
- labels (e.g. "needs-design", "breaking-change" → higher)

Return a JSON array, one object per issue, with fields:
  url, complexity, effort_days, reasoning

Output ONLY the JSON array — no prose, no markdown fences.\
"""

FIX_SUGGESTER_PROMPT = """\
You are FixSuggester, the third stage of an open source triage swarm.

You receive a JSON array of issues enriched with complexity estimates.

For each issue provide:
  approach           : 2-3 sentence description of HOW to fix it
  files_likely       : list of likely file/directory patterns to change
                       (e.g. ["models.py", "tests/", "serializers.py"])
  skills_needed      : list of specific skills required
                       (e.g. ["Django ORM", "pytest", "DRF serializers"])

Use title + body_preview + labels to infer the fix.
Do NOT browse external URLs — work only from provided data.

Return a JSON array, one object per issue, with fields:
  url, approach, files_likely, skills_needed

Output ONLY the JSON array — no prose, no markdown fences.\
"""

DEV_ASSIGNER_PROMPT = """\
You are DevAssigner, the final stage of an open source triage swarm.

You receive:
1. A JSON array of issues enriched with complexity + fix suggestion data.
2. A JSON array of developers with their skills and preferred categories.

Assignment rules:
- Match skills_needed against each dev's skills list (overlap wins)
- Prefer junior/mid devs for low-complexity issues (free up seniors)
- Prefer senior devs for high-complexity or auth/security issues
- Do NOT assign an issue to a dev whose "avoid" list overlaps with skills_needed
- Each dev should receive at most 2 assignments

Output a markdown report with:

## Issue Assignments

A table with columns:
  Issue | Repo | Complexity | Effort | Assigned To | GitHub | Reason

## Top Pick

The single best issue+dev pair. Include:
- Why this issue is the best fit right now
- A ready-to-run command in this exact format:

```
Make a PR for <issue_url>
```

No other text after the command block.\
"""

# ---------------------------------------------------------------------------
# Memory + Cache helpers
# ---------------------------------------------------------------------------

def load_worked_urls() -> set[str]:
    """Parse MEMORY.md and return all issue URLs already worked on."""
    if not MEMORY_MD.exists():
        return set()
    text = MEMORY_MD.read_text()
    # Find the Contribution History section and extract URLs
    section_match = re.search(r"## Contribution History(.+?)(?=\n## |\Z)", text, re.DOTALL)
    if not section_match:
        return set()
    return set(re.findall(r"https://github\.com/[^\s)]+/issues/\d+", section_match.group(1)))


def load_cache() -> dict[str, dict]:
    """Load persisted analysis from data/swarm_cache.json. Keys are issue URLs."""
    if not CACHE_JSON.exists():
        return {}
    try:
        return json.loads(CACHE_JSON.read_text())
    except json.JSONDecodeError:
        return {}


def save_cache(cache: dict[str, dict]) -> None:
    CACHE_JSON.write_text(json.dumps(cache, indent=2, default=str))


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

async def run_swarm(
    issues: list[dict],
    devs: list[dict],
    filter_dev: str | None = None,
    use_cache: bool = True,
) -> str:
    if filter_dev:
        devs = [d for d in devs if d["github"] == filter_dev or d["name"].lower() == filter_dev.lower()]
        if not devs:
            return f"No dev found matching '{filter_dev}' in data/devs.json"

    # ── Skip already-worked issues from MEMORY.md ─────────────────────────
    worked_urls = load_worked_urls()
    if worked_urls:
        before = len(issues)
        issues = [i for i in issues if i.get("url") not in worked_urls]
        skipped = before - len(issues)
        if skipped:
            print(f"   ⏭  Skipped {skipped} already-worked issues (from MEMORY.md)", flush=True)

    cache = load_cache() if use_cache else {}
    devs_json = json.dumps(devs, indent=2)

    # Haiku for fast filtering/analysis tasks; Opus only for the final reasoning stage
    opts_fast   = ClaudeAgentOptions(model="claude-haiku-4-5")
    opts_reason = ClaudeAgentOptions(model="claude-opus-4-6")

    # ── Stage 1: IssueFinder ──────────────────────────────────────────────
    print("🔍  Stage 1/4 — IssueFinder filtering issues…", flush=True)
    finder_result = ""
    async for msg in query(
        prompt=(
            f"SYSTEM: {ISSUE_FINDER_PROMPT}\n\n"
            f"Team profile (for context on what to prioritise):\n```json\n{devs_json}\n```\n\n"
            f"Issues ({len(issues)} total):\n```json\n{json.dumps(issues, indent=2, default=str)}\n```\n\n"
            "Return the top 8 candidate issues as a raw JSON array."
        ),
        options=opts_fast,
    ):
        if isinstance(msg, ResultMessage):
            finder_result = msg.result

    top_issues = _parse_json(finder_result, fallback=issues[:8])
    print(f"   → {len(top_issues)} issues selected", flush=True)

    # ── Stage 2: ComplexityAnalyzer (skip cached) ─────────────────────────
    print("📊  Stage 2/4 — ComplexityAnalyzer estimating effort…", flush=True)
    uncached = [i for i in top_issues if i.get("url") not in cache or "complexity" not in cache[i["url"]]]
    cached_count = len(top_issues) - len(uncached)
    if cached_count:
        print(f"   ↩  {cached_count} issues loaded from cache", flush=True)
    # Apply cached complexity data immediately
    for issue in top_issues:
        if issue.get("url") in cache:
            _apply_cache_entry(issue, cache[issue["url"]])

    if uncached:
        complexity_result = ""
        async for msg in query(
            prompt=(
                f"SYSTEM: {COMPLEXITY_ANALYZER_PROMPT}\n\n"
                f"Issues:\n```json\n{json.dumps(uncached, indent=2)}\n```\n\n"
                "Return complexity estimates as a raw JSON array."
            ),
            options=opts_fast,
        ):
            if isinstance(msg, ResultMessage):
                complexity_result = msg.result

        complexity_data = _parse_json(complexity_result, fallback=[])
        _merge_by_url(top_issues, complexity_data)
        # Persist to cache
        for c in complexity_data:
            url = c.get("url")
            if url:
                cache.setdefault(url, {}).update({k: v for k, v in c.items() if k != "url"})
        print(f"   → complexity estimated for {len(complexity_data)} new issues", flush=True)
    else:
        print("   → all complexity data from cache", flush=True)

    # ── Stage 3: FixSuggester (skip cached) ──────────────────────────────
    print("🔧  Stage 3/4 — FixSuggester drafting fix approaches…", flush=True)
    uncached_fix = [i for i in top_issues if i.get("url") not in cache or "approach" not in cache[i["url"]]]

    if uncached_fix:
        fix_result = ""
        async for msg in query(
            prompt=(
                f"SYSTEM: {FIX_SUGGESTER_PROMPT}\n\n"
                f"Issues:\n```json\n{json.dumps(uncached_fix, indent=2)}\n```\n\n"
                "Return fix suggestions as a raw JSON array."
            ),
            options=opts_fast,
        ):
            if isinstance(msg, ResultMessage):
                fix_result = msg.result

        fix_data = _parse_json(fix_result, fallback=[])
        _merge_by_url(top_issues, fix_data)
        # Persist to cache
        for f in fix_data:
            url = f.get("url")
            if url:
                cache.setdefault(url, {}).update({k: v for k, v in f.items() if k != "url"})
        print(f"   → fix suggestions for {len(fix_data)} new issues", flush=True)
    else:
        # Apply cached fix data
        for issue in top_issues:
            if issue.get("url") in cache:
                _apply_cache_entry(issue, cache[issue["url"]])
        print("   → all fix suggestions from cache", flush=True)

    # Save updated cache
    save_cache(cache)
    print(f"   💾 Cache saved to data/swarm_cache.json ({len(cache)} entries)", flush=True)

    # ── Stage 4: DevAssigner ──────────────────────────────────────────────
    print("👤  Stage 4/4 — DevAssigner matching issues to developers…", flush=True)
    final_report = ""
    async for msg in query(
        prompt=(
            f"SYSTEM: {DEV_ASSIGNER_PROMPT}\n\n"
            f"Issues (with complexity + fix data):\n```json\n{json.dumps(top_issues, indent=2)}\n```\n\n"
            f"Developers:\n```json\n{devs_json}\n```\n\n"
            "Produce the full assignment report."
        ),
        options=opts_reason,
    ):
        if isinstance(msg, ResultMessage):
            final_report = msg.result

    return final_report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_json(text: str, fallback):
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        end = next((i for i in range(len(lines)-1, 0, -1) if lines[i].strip() == "```"), len(lines))
        text = "\n".join(lines[1:end])
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("["), text.rfind("]")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end+1])
            except json.JSONDecodeError:
                pass
    return fallback


def _merge_by_url(base: list[dict], additions: list[dict]) -> None:
    lookup = {a["url"]: a for a in additions if "url" in a}
    for item in base:
        extra = lookup.get(item.get("url"), {})
        for k, v in extra.items():
            if k not in item:
                item[k] = v


def _apply_cache_entry(issue: dict, entry: dict) -> None:
    for k, v in entry.items():
        if k not in issue:
            issue[k] = v


def load_issues(force_fresh: bool = False) -> list:
    """
    Load issues with a 24h cache backed by the GitHub Pages URL.
    - Fresh if file is missing, older than 24h, or force_fresh=True.
    - Otherwise reads from disk immediately.
    """
    import time
    import urllib.request

    needs_fetch = force_fresh
    if not needs_fetch:
        if not ISSUES_JSON.exists():
            needs_fetch = True
        else:
            age = time.time() - ISSUES_JSON.stat().st_mtime
            if age > CACHE_TTL_SEC:
                needs_fetch = True
                print(f"   ↻  issues.json is {int(age/3600)}h old — fetching fresh copy…", flush=True)

    if needs_fetch:
        print(f"   ⬇  Downloading issues from {ISSUES_URL}…", flush=True)
        try:
            with urllib.request.urlopen(ISSUES_URL, timeout=15) as resp:
                data = resp.read()
            ISSUES_JSON.parent.mkdir(parents=True, exist_ok=True)
            ISSUES_JSON.write_bytes(data)
            print(f"   ✓  Saved to {ISSUES_JSON}", flush=True)
        except Exception as e:
            if ISSUES_JSON.exists():
                print(f"   ⚠  Fetch failed ({e}) — using cached copy", flush=True)
            else:
                print(f"ERROR: Could not fetch issues and no local cache exists: {e}", file=sys.stderr)
                sys.exit(1)

    return json.loads(ISSUES_JSON.read_text())


def load_json(path: Path, label: str) -> list | dict:
    if not path.exists():
        print(f"ERROR: {path} not found. {label}", file=sys.stderr)
        sys.exit(1)
    return json.loads(path.read_text())


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Multi-agent issue triage swarm")
    parser.add_argument("--fetch",    action="store_true", help="Run fetch_issues.py first")
    parser.add_argument("--fresh",    action="store_true", help="Ignore cache, re-analyse all issues")
    parser.add_argument("--category", default=None, help="Filter issues by category (e.g. django_core)")
    parser.add_argument("--dev",      default=None, help="Filter devs by github handle or name")
    parser.add_argument("--output",   default=None, help="Save report to this file")
    args = parser.parse_args()

    issues: list = load_issues(force_fresh=args.fresh or args.fetch)
    devs:   list = load_json(DEVS_JSON, "Create data/devs.json with your team roster.")

    if args.category:
        issues = [i for i in issues if i.get("category") == args.category]
        if not issues:
            print(f"No issues found for category '{args.category}'")
            sys.exit(1)

    print(f"Loaded {len(issues)} issues, {len(devs)} devs\n")

    report = anyio.run(run_swarm, issues, devs, args.dev, not args.fresh)

    print("\n" + "=" * 70)
    print(report)
    print("=" * 70)

    if args.output:
        Path(args.output).write_text(report)
        print(f"\nReport saved to {args.output}")


if __name__ == "__main__":
    main()
