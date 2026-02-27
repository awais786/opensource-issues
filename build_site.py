#!/usr/bin/env python3
"""
Django Issue Hub — Static Site Builder
========================================
Generates a beautiful static HTML dashboard from the fetched issue data.
Output goes to docs/ for GitHub Pages deployment.
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR
DATA_DIR = ROOT / "data"


def load_json(path: Path) -> dict | list:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def build_site():
    stats = load_json(DATA_DIR / "stats.json")
    all_issues = load_json(DATA_DIR / "issues.json")
    repos_config = load_json(DATA_DIR / "repos.json")

    if not stats:
        print("⚠ No stats.json found. Run fetch_issues.py first.")
        # Generate with placeholder data for initial deploy
        stats = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_repos": 108,
            "total_issues_fetched": 0,
            "total_new_issues": 0,
            "total_bugs": 0,
            "total_features": 0,
            "total_good_first_issues": 0,
            "total_help_wanted": 0,
            "total_security": 0,
            "by_priority": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            "by_category": {},
            "repos": {},
        }

    if not isinstance(all_issues, list):
        all_issues = []

    categories = repos_config.get("categories", {}) if repos_config else {}

    # --- Build category cards ---
    category_cards_html = ""
    for cat_key, cat_data in categories.items():
        cat_stats = stats.get("by_category", {}).get(cat_key, {})
        total = cat_stats.get("total_issues", 0)
        new = cat_stats.get("new_issues", 0)
        gfi = cat_stats.get("good_first_issues", 0)
        num_repos = cat_stats.get("total_repos", len(cat_data.get("repos", [])))

        category_cards_html += f"""
        <div class="cat-card" data-category="{cat_key}">
            <div class="cat-icon">{cat_data.get('icon', '📦')}</div>
            <div class="cat-name">{cat_data.get('label', cat_key)}</div>
            <div class="cat-desc">{cat_data.get('description', '')}</div>
            <div class="cat-stats">
                <span>{num_repos} repos</span>
                <span>{total} issues</span>
                {f'<span class="new-badge">{new} new</span>' if new else ''}
                {f'<span class="gfi-badge">{gfi} good first</span>' if gfi else ''}
            </div>
        </div>"""

    # --- Build issue rows ---
    # Sort: new first, then by priority, then by date
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_issues = sorted(all_issues, key=lambda i: (
        0 if i.get("is_new") else 1,
        priority_order.get(i.get("priority", "low"), 4),
        i.get("created_at", ""),
    ), reverse=False)

    # For initial load, limit to newest 200
    display_issues = sorted_issues[:500]

    issue_rows_html = ""
    for iss in display_issues:
        labels_html = ""
        for label in iss.get("labels", [])[:3]:
            label_lower = label.lower()
            cls = "label"
            if any(k in label_lower for k in ["bug", "defect"]):
                cls += " label-bug"
            elif any(k in label_lower for k in ["enhancement", "feature"]):
                cls += " label-feature"
            elif any(k in label_lower for k in ["good first", "beginner", "easy"]):
                cls += " label-gfi"
            elif any(k in label_lower for k in ["security", "vulnerability"]):
                cls += " label-security"
            elif any(k in label_lower for k in ["help wanted"]):
                cls += " label-help"
            labels_html += f'<span class="{cls}">{label}</span>'

        new_tag = '<span class="new-tag">NEW</span>' if iss.get("is_new") else ""
        priority = iss.get("priority", "low")
        priority_dot = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(priority, "⚪")
        repo_short = iss.get("repo", "").split("/")[-1]

        issue_rows_html += f"""
        <tr class="issue-row" data-category="{iss.get('category', '')}" data-priority="{priority}"
            data-new="{str(iss.get('is_new', False)).lower()}"
            data-gfi="{str(iss.get('is_good_first_issue', False)).lower()}"
            data-repo="{iss.get('repo', '')}">
            <td class="col-priority">{priority_dot}</td>
            <td class="col-issue">
                <div class="issue-title">
                    {new_tag}
                    <a href="{iss.get('url', '#')}" target="_blank" rel="noopener">{iss.get('title', 'Untitled')}</a>
                </div>
                <div class="issue-meta">
                    <span class="repo-name">{iss.get('repo', '')}</span>
                    <span class="issue-num">#{iss.get('number', '')}</span>
                    <span>by {iss.get('author', 'unknown')}</span>
                    <span>💬 {iss.get('comments', 0)}</span>
                </div>
                <div class="issue-labels">{labels_html}</div>
            </td>
            <td class="col-category"><span class="cat-tag">{iss.get('category_label', '')}</span></td>
            <td class="col-date">{iss.get('created_at', '')[:10]}</td>
        </tr>"""

    # --- Top repos by issues ---
    repo_stats = stats.get("repos", {})
    top_repos = sorted(repo_stats.items(), key=lambda x: x[1].get("total_open_issues", 0), reverse=True)[:15]
    top_repos_html = ""
    for repo, rs in top_repos:
        bar_width = min(100, (rs.get("total_open_issues", 0) / max(1, top_repos[0][1].get("total_open_issues", 1))) * 100)
        top_repos_html += f"""
        <div class="repo-bar-row">
            <div class="repo-bar-name">{repo.split('/')[-1]}</div>
            <div class="repo-bar-track">
                <div class="repo-bar-fill" style="width:{bar_width}%"></div>
            </div>
            <div class="repo-bar-count">{rs.get('total_open_issues', 0)}</div>
        </div>"""

    # --- Render full HTML ---
    generated_at = stats.get("generated_at", "never")
    if isinstance(generated_at, str) and len(generated_at) > 10:
        generated_at = generated_at[:16].replace("T", " ") + " UTC"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Django Issue Hub — Open Issues Across the Django Ecosystem</title>
<meta name="description" content="Live dashboard tracking open issues across 100+ Django, DRF, Wagtail, Celery, Open edX and Python open-source projects. Find contribution opportunities.">
<meta property="og:title" content="Django Issue Hub">
<meta property="og:description" content="Track open issues across 100+ Django ecosystem repos">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,500;0,9..40,700;1,9..40,400&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root {{
    --bg: #0a0f1c;
    --surface: #111827;
    --surface2: #1a2236;
    --border: #1e2a42;
    --text: #e2e8f0;
    --text-muted: #7a8ba7;
    --accent: #22d3ee;
    --accent-glow: rgba(34, 211, 238, 0.15);
    --green: #10b981;
    --green-glow: rgba(16, 185, 129, 0.15);
    --orange: #f59e0b;
    --red: #ef4444;
    --purple: #a78bfa;
    --font: 'DM Sans', system-ui, sans-serif;
    --mono: 'JetBrains Mono', monospace;
}}

* {{ margin: 0; padding: 0; box-sizing: border-box; }}

body {{
    background: var(--bg);
    color: var(--text);
    font-family: var(--font);
    line-height: 1.6;
    min-height: 100vh;
}}

/* --- HEADER --- */
.hero {{
    position: relative;
    padding: 60px 24px 40px;
    text-align: center;
    overflow: hidden;
    border-bottom: 1px solid var(--border);
}}
.hero::before {{
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at 50% 0%, rgba(34,211,238,0.08) 0%, transparent 70%),
                radial-gradient(ellipse at 20% 100%, rgba(167,139,250,0.06) 0%, transparent 50%);
    pointer-events: none;
}}
.hero h1 {{
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 700;
    letter-spacing: -0.02em;
    position: relative;
}}
.hero h1 .accent {{ color: var(--accent); }}
.hero p {{
    color: var(--text-muted);
    font-size: 1.1rem;
    margin-top: 8px;
    position: relative;
}}
.hero .badge {{
    display: inline-block;
    background: var(--accent-glow);
    border: 1px solid rgba(34,211,238,0.3);
    color: var(--accent);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-family: var(--mono);
    margin-top: 16px;
    position: relative;
}}

/* --- STATS ROW --- */
.stats-row {{
    display: flex;
    gap: 12px;
    padding: 24px;
    max-width: 1200px;
    margin: 0 auto;
    flex-wrap: wrap;
    justify-content: center;
}}
.stat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 28px;
    text-align: center;
    flex: 1;
    min-width: 140px;
    max-width: 200px;
    transition: border-color 0.2s;
}}
.stat-card:hover {{ border-color: var(--accent); }}
.stat-val {{
    font-size: 2rem;
    font-weight: 700;
    font-family: var(--mono);
    line-height: 1.2;
}}
.stat-val.accent {{ color: var(--accent); }}
.stat-val.green {{ color: var(--green); }}
.stat-val.orange {{ color: var(--orange); }}
.stat-val.red {{ color: var(--red); }}
.stat-val.purple {{ color: var(--purple); }}
.stat-label {{
    color: var(--text-muted);
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    margin-top: 4px;
}}

/* --- CONTAINER --- */
.container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 24px;
}}

/* --- SECTION TITLES --- */
.section-title {{
    font-size: 1.3rem;
    font-weight: 600;
    margin: 40px 0 20px;
    display: flex;
    align-items: center;
    gap: 10px;
}}
.section-title::after {{
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
}}

/* --- CATEGORY GRID --- */
.cat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 14px;
    margin-bottom: 40px;
}}
.cat-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s;
}}
.cat-card:hover, .cat-card.active {{
    border-color: var(--accent);
    background: var(--surface2);
    transform: translateY(-2px);
    box-shadow: 0 4px 20px rgba(34,211,238,0.08);
}}
.cat-icon {{ font-size: 1.6rem; margin-bottom: 6px; }}
.cat-name {{ font-weight: 600; font-size: 1rem; }}
.cat-desc {{ color: var(--text-muted); font-size: 0.82rem; margin: 4px 0 10px; }}
.cat-stats {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    font-size: 0.75rem;
    font-family: var(--mono);
    color: var(--text-muted);
}}
.new-badge {{
    color: var(--accent);
    background: var(--accent-glow);
    padding: 1px 8px;
    border-radius: 10px;
}}
.gfi-badge {{
    color: var(--green);
    background: var(--green-glow);
    padding: 1px 8px;
    border-radius: 10px;
}}

/* --- FILTERS --- */
.filters {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 20px;
    align-items: center;
}}
.filter-btn {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-muted);
    padding: 6px 16px;
    border-radius: 20px;
    font-size: 0.85rem;
    font-family: var(--font);
    cursor: pointer;
    transition: all 0.15s;
}}
.filter-btn:hover {{ border-color: var(--accent); color: var(--text); }}
.filter-btn.active {{ background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }}
.search-input {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 8px 16px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-family: var(--font);
    width: 260px;
    outline: none;
    transition: border-color 0.2s;
}}
.search-input:focus {{ border-color: var(--accent); }}
.search-input::placeholder {{ color: var(--text-muted); }}

/* --- ISSUE TABLE --- */
.issue-table {{
    width: 100%;
    border-collapse: collapse;
}}
.issue-table thead th {{
    text-align: left;
    padding: 10px 12px;
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    background: var(--bg);
    z-index: 10;
}}
.issue-row {{
    border-bottom: 1px solid var(--border);
    transition: background 0.15s;
}}
.issue-row:hover {{ background: var(--surface); }}
.issue-row td {{ padding: 14px 12px; vertical-align: top; }}
.col-priority {{ width: 40px; text-align: center; font-size: 0.9rem; }}
.col-category {{ width: 140px; }}
.col-date {{ width: 100px; font-family: var(--mono); font-size: 0.82rem; color: var(--text-muted); }}

.issue-title a {{
    color: var(--text);
    text-decoration: none;
    font-weight: 500;
    transition: color 0.15s;
}}
.issue-title a:hover {{ color: var(--accent); }}
.issue-meta {{
    display: flex;
    gap: 12px;
    font-size: 0.78rem;
    color: var(--text-muted);
    margin-top: 4px;
    flex-wrap: wrap;
}}
.repo-name {{
    font-family: var(--mono);
    color: var(--purple);
    font-size: 0.78rem;
}}
.issue-num {{ font-family: var(--mono); }}
.new-tag {{
    display: inline-block;
    background: var(--accent);
    color: var(--bg);
    font-size: 0.65rem;
    font-weight: 700;
    padding: 1px 6px;
    border-radius: 4px;
    margin-right: 6px;
    vertical-align: middle;
    letter-spacing: 0.04em;
}}
.cat-tag {{
    font-size: 0.75rem;
    color: var(--text-muted);
    background: var(--surface2);
    padding: 2px 10px;
    border-radius: 10px;
    white-space: nowrap;
}}

/* Labels */
.issue-labels {{ display: flex; gap: 6px; flex-wrap: wrap; margin-top: 6px; }}
.label {{
    font-size: 0.7rem;
    padding: 2px 8px;
    border-radius: 10px;
    background: var(--surface2);
    color: var(--text-muted);
    border: 1px solid var(--border);
}}
.label-bug {{ border-color: rgba(239,68,68,0.4); color: var(--red); background: rgba(239,68,68,0.08); }}
.label-feature {{ border-color: rgba(167,139,250,0.4); color: var(--purple); background: rgba(167,139,250,0.08); }}
.label-gfi {{ border-color: rgba(16,185,129,0.4); color: var(--green); background: rgba(16,185,129,0.08); }}
.label-security {{ border-color: rgba(239,68,68,0.6); color: #fca5a5; background: rgba(239,68,68,0.12); }}
.label-help {{ border-color: rgba(245,158,11,0.4); color: var(--orange); background: rgba(245,158,11,0.08); }}

/* --- TOP REPOS BAR CHART --- */
.top-repos {{ margin: 30px 0; }}
.repo-bar-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 6px 0;
}}
.repo-bar-name {{
    width: 180px;
    text-align: right;
    font-family: var(--mono);
    font-size: 0.82rem;
    color: var(--text-muted);
    flex-shrink: 0;
}}
.repo-bar-track {{
    flex: 1;
    height: 20px;
    background: var(--surface);
    border-radius: 4px;
    overflow: hidden;
}}
.repo-bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--accent), var(--purple));
    border-radius: 4px;
    transition: width 0.8s ease;
}}
.repo-bar-count {{
    width: 50px;
    font-family: var(--mono);
    font-size: 0.85rem;
    color: var(--text);
    font-weight: 600;
}}

/* --- FOOTER --- */
.footer {{
    text-align: center;
    padding: 40px 24px;
    color: var(--text-muted);
    font-size: 0.82rem;
    border-top: 1px solid var(--border);
    margin-top: 60px;
}}
.footer a {{ color: var(--accent); text-decoration: none; }}

/* --- EMPTY STATE --- */
.empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}}
.empty-state .icon {{ font-size: 3rem; margin-bottom: 12px; }}

/* --- RESPONSIVE --- */
@media (max-width: 768px) {{
    .stats-row {{ gap: 8px; }}
    .stat-card {{ min-width: 100px; padding: 14px; }}
    .stat-val {{ font-size: 1.4rem; }}
    .col-category, .col-date {{ display: none; }}
    .repo-bar-name {{ width: 100px; font-size: 0.72rem; }}
    .search-input {{ width: 100%; }}
}}
</style>
</head>
<body>

<!-- HERO -->
<div class="hero">
    <h1>🐍 Django <span class="accent">Issue Hub</span></h1>
    <p>Live open issues across {stats.get('total_repos', 108)}+ Django ecosystem projects</p>
    <div class="badge">Updated: {generated_at}</div>
</div>

<!-- STATS -->
<div class="stats-row">
    <div class="stat-card">
        <div class="stat-val accent">{stats.get('total_repos', 0)}</div>
        <div class="stat-label">Repos Tracked</div>
    </div>
    <div class="stat-card">
        <div class="stat-val">{stats.get('total_issues_fetched', 0):,}</div>
        <div class="stat-label">Open Issues</div>
    </div>
    <div class="stat-card">
        <div class="stat-val green">{stats.get('total_new_issues', 0)}</div>
        <div class="stat-label">New This Week</div>
    </div>
    <div class="stat-card">
        <div class="stat-val orange">{stats.get('total_good_first_issues', 0)}</div>
        <div class="stat-label">Good First Issues</div>
    </div>
    <div class="stat-card">
        <div class="stat-val red">{stats.get('total_bugs', 0)}</div>
        <div class="stat-label">Bugs</div>
    </div>
    <div class="stat-card">
        <div class="stat-val purple">{stats.get('total_features', 0)}</div>
        <div class="stat-label">Feature Requests</div>
    </div>
</div>

<div class="container">

    <!-- CATEGORIES -->
    <div class="section-title">📂 Ecosystem Categories</div>
    <div class="cat-grid">{category_cards_html}</div>

    <!-- TOP REPOS -->
    <div class="section-title">📊 Top Repos by Open Issues</div>
    <div class="top-repos">{top_repos_html}</div>

    <!-- FILTERS -->
    <div class="section-title">🗂️ All Issues</div>
    <div class="filters">
        <input type="text" class="search-input" id="searchInput" placeholder="Search issues..." oninput="filterIssues()">
        <button class="filter-btn active" data-filter="all" onclick="setFilter(this)">All</button>
        <button class="filter-btn" data-filter="new" onclick="setFilter(this)">🆕 New</button>
        <button class="filter-btn" data-filter="gfi" onclick="setFilter(this)">🟢 Good First Issue</button>
        <button class="filter-btn" data-filter="bug" onclick="setFilter(this)">🐛 Bugs</button>
        <button class="filter-btn" data-filter="critical" onclick="setFilter(this)">🔴 Critical</button>
    </div>

    <!-- ISSUE TABLE -->
    <div style="overflow-x:auto;">
    <table class="issue-table">
        <thead>
            <tr>
                <th></th>
                <th>Issue</th>
                <th>Category</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody id="issueBody">
            {issue_rows_html if issue_rows_html else '<tr><td colspan="4"><div class="empty-state"><div class="icon">🚀</div><p>No issues fetched yet. Run the GitHub Action to populate data!</p></div></td></tr>'}
        </tbody>
    </table>
    </div>

</div>

<!-- FOOTER -->
<div class="footer">
    <p>
        <strong>Django Issue Hub</strong> — Open-source project tracking for the Django community<br>
        Data refreshed daily via GitHub Actions · <a href="https://github.com/YOUR_USERNAME/django-issue-hub">⭐ Star on GitHub</a> ·
        <a href="data/issues.json">📄 Raw JSON API</a>
    </p>
</div>

<script>
// --- Filtering logic ---
let activeFilter = 'all';
let activeCategory = null;

function setFilter(btn) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    activeFilter = btn.dataset.filter;
    activeCategory = null;
    document.querySelectorAll('.cat-card').forEach(c => c.classList.remove('active'));
    filterIssues();
}}

// Category card click
document.querySelectorAll('.cat-card').forEach(card => {{
    card.addEventListener('click', () => {{
        const cat = card.dataset.category;
        if (activeCategory === cat) {{
            activeCategory = null;
            card.classList.remove('active');
        }} else {{
            document.querySelectorAll('.cat-card').forEach(c => c.classList.remove('active'));
            card.classList.add('active');
            activeCategory = cat;
        }}
        filterIssues();
    }});
}});

function filterIssues() {{
    const search = document.getElementById('searchInput').value.toLowerCase();
    const rows = document.querySelectorAll('.issue-row');
    let visible = 0;

    rows.forEach(row => {{
        let show = true;

        // Category filter
        if (activeCategory && row.dataset.category !== activeCategory) show = false;

        // Button filter
        if (activeFilter === 'new' && row.dataset.new !== 'true') show = false;
        if (activeFilter === 'gfi' && row.dataset.gfi !== 'true') show = false;
        if (activeFilter === 'bug' && row.dataset.priority !== 'high') show = false;
        if (activeFilter === 'critical' && row.dataset.priority !== 'critical') show = false;

        // Search
        if (search && !row.textContent.toLowerCase().includes(search)) show = false;

        row.style.display = show ? '' : 'none';
        if (show) visible++;
    }});
}}
</script>
</body>
</html>"""

    # Write output to repo root (served directly by GitHub Pages)
    with open(ROOT / "index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ Static site built → index.html")
    print(f"   {len(display_issues)} issues rendered, {len(categories)} categories")


if __name__ == "__main__":
    build_site()
