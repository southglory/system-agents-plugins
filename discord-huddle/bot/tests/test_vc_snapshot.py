"""Tests for discord_lib.vc_snapshot and --vc-snapshot CLI flag."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from discord_lib.vc_snapshot import find_latest_server_url, take_snapshot


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_session(sessions_root: Path, name: str, url: str, mtime_offset: float = 0, stopped: bool = False) -> Path:
    """Create a fake session directory under ``sessions_root`` in the expected layout."""
    session_dir = sessions_root / name
    state_dir = session_dir / "state"
    state_dir.mkdir(parents=True)
    info = state_dir / "server-info"
    info.write_text(json.dumps({"url": url, "port": 8080}), encoding="utf-8")
    if stopped:
        (state_dir / "server-stopped").touch()
    # Adjust mtime so we can control ordering deterministically
    if mtime_offset != 0:
        new_mtime = session_dir.stat().st_mtime + mtime_offset
        import os
        os.utime(session_dir, (new_mtime, new_mtime))
    return session_dir


# ---------------------------------------------------------------------------
# find_latest_server_url tests
# ---------------------------------------------------------------------------

def test_returns_newest_live(tmp_path):
    """Newer live session wins."""
    sessions = tmp_path / "sessions"
    sessions.mkdir()

    _make_session(sessions, "older", url="http://localhost:3001", mtime_offset=-10)
    _make_session(sessions, "newer", url="http://localhost:3002", mtime_offset=0)

    result = find_latest_server_url(sessions)
    assert result == "http://localhost:3002"


def test_skips_stopped_and_falls_back_to_older(tmp_path):
    """If the newest session is stopped, the older live session wins."""
    sessions = tmp_path / "sessions"
    sessions.mkdir()

    _make_session(sessions, "older", url="http://localhost:3001", mtime_offset=-10)
    _make_session(sessions, "newer", url="http://localhost:3002", mtime_offset=0, stopped=True)

    result = find_latest_server_url(sessions)
    assert result == "http://localhost:3001"


def test_none_if_all_stopped(tmp_path):
    """Returns None when all sessions have server-stopped marker."""
    sessions = tmp_path / "sessions"
    sessions.mkdir()

    _make_session(sessions, "a", url="http://localhost:3001", stopped=True)
    _make_session(sessions, "b", url="http://localhost:3002", stopped=True)

    result = find_latest_server_url(sessions)
    assert result is None


def test_none_if_no_sessions(tmp_path):
    """Returns None when sessions root is empty."""
    sessions = tmp_path / "sessions"
    sessions.mkdir()

    result = find_latest_server_url(sessions)
    assert result is None


def test_none_if_sessions_dir_missing(tmp_path):
    """Returns None gracefully when the sessions directory doesn't exist."""
    sessions = tmp_path / "sessions"
    # Don't create it
    result = find_latest_server_url(sessions)
    assert result is None


# ---------------------------------------------------------------------------
# take_snapshot tests (mock playwright — no real browser)
# ---------------------------------------------------------------------------

def _make_playwright_mock():
    """Return (mock_sync_playwright_fn, mock_page, mock_browser) for reuse."""
    mock_page = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_chromium = MagicMock()
    mock_chromium.launch.return_value = mock_browser
    mock_playwright_instance = MagicMock()
    mock_playwright_instance.chromium = mock_chromium

    mock_context_manager = MagicMock()
    mock_context_manager.__enter__ = MagicMock(return_value=mock_playwright_instance)
    mock_context_manager.__exit__ = MagicMock(return_value=False)

    mock_sync_playwright_fn = MagicMock(return_value=mock_context_manager)
    return mock_sync_playwright_fn, mock_page, mock_browser


def test_take_snapshot_calls_playwright_and_returns_path(tmp_path):
    dest = tmp_path / "snap" / "out.png"
    mock_sync_playwright_fn, mock_page, mock_browser = _make_playwright_mock()

    with patch("discord_lib.vc_snapshot._get_sync_playwright", return_value=mock_sync_playwright_fn):
        result = take_snapshot("http://localhost:3000", dest)

    assert result == dest
    mock_page.goto.assert_called_once_with("http://localhost:3000", wait_until="networkidle", timeout=15_000)
    mock_page.screenshot.assert_called_once_with(path=str(dest), full_page=True)
    mock_browser.close.assert_called_once()


def test_take_snapshot_creates_parent_dirs(tmp_path):
    dest = tmp_path / "deep" / "nested" / "snap.png"
    mock_sync_playwright_fn, _, _ = _make_playwright_mock()

    with patch("discord_lib.vc_snapshot._get_sync_playwright", return_value=mock_sync_playwright_fn):
        take_snapshot("http://localhost:3000", dest)

    assert dest.parent.exists()


# ---------------------------------------------------------------------------
# cmd_post --vc-snapshot integration test
# ---------------------------------------------------------------------------

def test_cmd_post_uses_vc_snapshot_with_explicit_url(monkeypatch, tmp_project):
    """--vc-snapshot with --vc-url should capture a PNG and prepend it to attach list."""
    import discord_lib.api as api_mod
    import discord_collab as cli_mod

    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=test_tok\nDISCORD_CHANNEL_ID=111\n",
        encoding="utf-8",
    )

    def fake_take_snapshot(url, dest_path, **kwargs):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"\x89PNG stub")
        return dest_path

    monkeypatch.setattr(cli_mod, "take_snapshot", fake_take_snapshot)

    captured = {}

    def fake_run_post(cfg, client, content, attach_paths):
        captured["content"] = content
        captured["attach_paths"] = attach_paths
        return {"id": "777"}

    monkeypatch.setattr(cli_mod, "run_post", fake_run_post)
    monkeypatch.setattr(api_mod.requests, "post", lambda *a, **kw: None)

    rc = cli_mod.main([
        "post", "--message", "hello world",
        "--vc-snapshot", "--vc-url", "http://localhost:3000",
        "--project-root", str(tmp_project),
    ])

    assert rc == 0
    assert len(captured["attach_paths"]) == 1
    assert captured["attach_paths"][0].suffix == ".png"
    assert "(첨부: 현재 페이지 스냅샷)" in captured["content"]
    assert "vc-snapshots" in str(captured["attach_paths"][0])


def test_cmd_post_uses_sessions_dir_for_auto_detect(monkeypatch, tmp_project):
    """--vc-snapshot without --vc-url falls back to --vc-sessions-dir auto-detection."""
    import discord_lib.api as api_mod
    import discord_collab as cli_mod

    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=test_tok\nDISCORD_CHANNEL_ID=111\n",
        encoding="utf-8",
    )

    # Set up a fake sessions directory the plugin can auto-detect
    sessions = tmp_project / "custom-sessions"
    sessions.mkdir()
    _make_session(sessions, "live", url="http://127.0.0.1:4242")

    def fake_take_snapshot(url, dest_path, **kwargs):
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        dest_path.write_bytes(b"\x89PNG stub")
        return dest_path

    monkeypatch.setattr(cli_mod, "take_snapshot", fake_take_snapshot)

    captured = {}

    def fake_run_post(cfg, client, content, attach_paths):
        captured["url_was_used"] = True
        return {"id": "888"}

    monkeypatch.setattr(cli_mod, "run_post", fake_run_post)
    monkeypatch.setattr(api_mod.requests, "post", lambda *a, **kw: None)

    rc = cli_mod.main([
        "post", "--message", "ok",
        "--vc-snapshot", "--vc-sessions-dir", "custom-sessions",
        "--project-root", str(tmp_project),
    ])

    assert rc == 0
    assert captured["url_was_used"] is True


def test_cmd_post_fails_if_no_url_and_no_sessions_dir(monkeypatch, tmp_project, capsys):
    """Without --vc-url and without sessions dir configured, --vc-snapshot must error out."""
    import discord_collab as cli_mod

    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=test_tok\nDISCORD_CHANNEL_ID=111\n",
        encoding="utf-8",
    )
    # Ensure env var isn't bleeding in from the host process
    monkeypatch.delenv("VC_SESSIONS_DIR", raising=False)

    rc = cli_mod.main([
        "post", "--message", "x",
        "--vc-snapshot",
        "--project-root", str(tmp_project),
    ])
    err = capsys.readouterr().err
    assert rc == 2
    assert "--vc-url" in err
    assert "--vc-sessions-dir" in err or "VC_SESSIONS_DIR" in err
