"""
Taiga API client for the Arbisoft Open Source project board.

Board : https://projects.arbisoft.com/project/arbisoft-open-source-projects/kanban
Project ID : 46

Statuses:
  278 New  →  279 Ready  →  280 In progress  →  281 Ready for test  →  282 Done

Usage:
    from taiga import TaigaClient
    client = TaigaClient(token="...")
    us = client.create_user_story(issue, assignee_taiga_id)
"""

import json
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

TAIGA_BASE       = "https://projects.arbisoft.com/api/v1"
TAIGA_PROJECT_ID = 46

STATUS_NEW         = 278
STATUS_READY       = 279
STATUS_IN_PROGRESS = 280
STATUS_REVIEW      = 281
STATUS_DONE        = 282


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

@dataclass
class TaigaClient:
    token: str

    def __post_init__(self):
        self._ssl = ssl.create_default_context()
        self._ssl.check_hostname = False
        self._ssl.verify_mode = ssl.CERT_NONE

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type":  "application/json",
        }

    def _request(self, method: str, path: str, payload: dict | None = None) -> dict | list | None:
        url  = f"{TAIGA_BASE}/{path.lstrip('/')}"
        data = json.dumps(payload).encode() if payload else None
        req  = urllib.request.Request(url, data=data, headers=self._headers(), method=method)
        try:
            with urllib.request.urlopen(req, context=self._ssl, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            body = e.read().decode()
            raise RuntimeError(f"Taiga API {method} {path} → HTTP {e.code}: {body}") from e
        except Exception as e:
            raise RuntimeError(f"Taiga API {method} {path} → {e}") from e

    # ------------------------------------------------------------------
    # User stories
    # ------------------------------------------------------------------

    def create_user_story(self, issue: dict, assignee_taiga_id: int | None = None) -> dict:
        """Create a user story on the kanban board and return the created object."""
        subject     = f"[{issue['repo']}#{issue['number']}] {issue['title']}"
        description = (
            f"**GitHub Issue:** [{issue['url']}]({issue['url']})\n\n"
            f"**Priority:** {issue.get('priority', 'low').upper()}\n"
            f"**Category:** {issue.get('category', '')}\n\n"
            f"{issue.get('body_preview', '')}"
        )

        payload: dict = {
            "project":     TAIGA_PROJECT_ID,
            "subject":     subject[:255],
            "description": description,
            "status":      STATUS_READY,
            "swimlane":    43,  # Tickets
            "tags":        _build_tags(issue),
        }
        if assignee_taiga_id:
            payload["assigned_to"] = assignee_taiga_id

        return self._request("POST", "/userstories", payload)

    def get_user_story(self, us_id: int) -> dict:
        return self._request("GET", f"/userstories/{us_id}")

    def update_status(self, us_id: int, status_id: int, version: int) -> dict:
        """Move a user story to a new kanban column. version must be current."""
        return self._request("PATCH", f"/userstories/{us_id}", {
            "status":  status_id,
            "version": version,
        })

    def assign(self, us_id: int, taiga_user_id: int, version: int) -> dict:
        """Reassign a user story to a different team member."""
        return self._request("PATCH", f"/userstories/{us_id}", {
            "assigned_to": taiga_user_id,
            "version":     version,
        })

    def list_user_stories(self, status_id: int | None = None) -> list:
        path = f"/userstories?project={TAIGA_PROJECT_ID}"
        if status_id:
            path += f"&status={status_id}"
        return self._request("GET", path) or []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_tags(issue: dict) -> list[list[str]]:
    """Build Taiga tags from issue metadata. Format: [[name, color_or_null]]"""
    tags = []
    priority = issue.get("priority", "low")
    priority_colors = {
        "critical": "#e74c3c",
        "high":     "#e67e22",
        "medium":   "#f1c40f",
        "low":      "#2ecc71",
    }
    tags.append([priority, priority_colors.get(priority)])

    if issue.get("is_bug"):              tags.append(["bug",              "#e74c3c"])
    if issue.get("is_feature"):          tags.append(["feature",          "#3498db"])
    if issue.get("is_good_first_issue"): tags.append(["good-first-issue", "#2ecc71"])
    if issue.get("is_help_wanted"):      tags.append(["help-wanted",      "#9b59b6"])

    cat = issue.get("category", "")
    if cat:
        tags.append([cat.replace("_", "-"), None])

    return tags


def _settings() -> dict:
    """Read .claude/settings.local.json, return {} on any error."""
    import json
    from pathlib import Path
    settings_path = Path(__file__).resolve().parent.parent / ".claude" / "settings.local.json"
    try:
        return json.loads(settings_path.read_text()).get("env", {})
    except (FileNotFoundError, KeyError, ValueError):
        return {}


def _fetch_token(username: str, password: str) -> str:
    """Fetch a fresh Taiga auth token using username/password."""
    import json
    payload = json.dumps({"type": "normal", "username": username, "password": password}).encode()
    req = urllib.request.Request(
        f"{TAIGA_BASE}/auth",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ssl_ctx = ssl.create_default_context()
    ssl_ctx.check_hostname = False
    ssl_ctx.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, context=ssl_ctx, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("auth_token", "")
    except Exception as e:
        raise RuntimeError(f"Taiga auth failed: {e}") from e


def client_from_env() -> TaigaClient:
    """Create a TaigaClient, fetching a fresh token from credentials if available."""
    env = _settings()
    username = os.environ.get("TAIGA_USERNAME") or env.get("TAIGA_USERNAME", "")
    password = os.environ.get("TAIGA_PASSWORD") or env.get("TAIGA_PASSWORD", "")

    if username and password:
        token = _fetch_token(username, password)
    else:
        token = os.environ.get("TAIGA_TOKEN") or env.get("TAIGA_TOKEN", "")

    if not token:
        raise RuntimeError(
            "Set TAIGA_USERNAME+TAIGA_PASSWORD or TAIGA_TOKEN in environment or .claude/settings.local.json"
        )
    return TaigaClient(token=token)
