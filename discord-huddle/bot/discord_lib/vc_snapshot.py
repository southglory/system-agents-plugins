"""Web page snapshot utilities.

Two helpers:

- ``find_latest_server_url`` — given a sessions directory whose children look
  like ``<session>/state/server-info`` JSON files, return the newest live URL.
  Useful for any tool that writes server metadata in this layout. The plugin
  itself does not assume any particular tool is producing those files.

- ``take_snapshot`` — render an arbitrary URL with headless Chromium and save a
  full-page PNG. Playwright import is deferred so the base plugin works without
  the optional ``playwright`` dependency when this function is not called.
"""

from __future__ import annotations

import json
from pathlib import Path


def find_latest_server_url(sessions_root: Path) -> str | None:
    """Return the newest live server URL from a sessions directory, or None.

    Expects layout::

        {sessions_root}/<session_name>/state/server-info     (JSON with "url")
        {sessions_root}/<session_name>/state/server-stopped  (optional marker)

    Sessions marked stopped are skipped. The newest live session's ``url`` is
    returned; ``None`` when the directory is missing, empty, or has no live
    session with a URL.
    """
    if not sessions_root.exists():
        return None
    server_info_files = list(sessions_root.glob("*/state/server-info"))
    if not server_info_files:
        return None

    # Sort by parent session dir mtime (newest first)
    server_info_files.sort(key=lambda p: p.parent.parent.stat().st_mtime, reverse=True)

    for info_path in server_info_files:
        stopped_marker = info_path.parent / "server-stopped"
        if stopped_marker.exists():
            continue
        try:
            data = json.loads(info_path.read_text(encoding="utf-8"))
            url = data.get("url")
            if url:
                return url
        except (json.JSONDecodeError, OSError):
            continue

    return None


def _get_sync_playwright():
    """Import and return sync_playwright (deferred so playwright is optional at import time)."""
    from playwright.sync_api import sync_playwright  # type: ignore
    return sync_playwright


def take_snapshot(
    url: str,
    dest_path: Path,
    viewport_width: int = 1280,
    viewport_height: int = 900,
) -> Path:
    """Render the URL with headless Chromium and save full-page PNG to dest_path.

    Uses playwright sync API. Waits for 'networkidle'. Timeout 15s.
    Returns dest_path.
    """
    sync_playwright = _get_sync_playwright()

    dest_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": viewport_width, "height": viewport_height},
            color_scheme="dark",
        )
        page.goto(url, wait_until="networkidle", timeout=15_000)
        # Some frame templates lock html/body to `height:100%; overflow:hidden`,
        # which prevents Playwright's full_page from capturing below the
        # viewport. Unlock all scroll containers so the document's real
        # scrollHeight is used. Historically discovered against a dashboard
        # with that CSS pattern; kept generic because others share it.
        page.evaluate(
            """
            (() => {
              const unlock = (el) => {
                if (!el || !el.style) return;
                el.style.height = 'auto';
                el.style.maxHeight = 'none';
                el.style.overflow = 'visible';
              };
              unlock(document.documentElement);
              unlock(document.body);
              document.querySelectorAll('main, .content, #claude-content, [data-scroll]')
                .forEach(unlock);
            })();
            """
        )
        page.screenshot(path=str(dest_path), full_page=True)
        browser.close()

    return dest_path
