"""Discord REST API 클라이언트 — 메시지 pagination 수집 및 전송."""

from __future__ import annotations

import json
import mimetypes
import time
from pathlib import Path
from typing import Iterable

import requests


class DiscordAPIError(Exception):
    """Raised for any Discord REST failure the caller is expected to surface.

    ``status`` is the HTTP status code when the failure originated from a
    real response (None for other cases like unexpected body shape).
    ``hint`` is a short user-facing remediation suggestion, ready to be
    printed next to the error message.
    """

    def __init__(self, message: str, *, status: int | None = None, hint: str | None = None):
        super().__init__(message)
        self.status = status
        self.hint = hint


_HINT_BY_STATUS = {
    401: "The bot token looks invalid or was revoked. "
         "Re-issue it in the Discord Developer Portal → Bot → Reset Token, "
         "then update .claude/secrets/discord-huddle.env. See docs/SETUP.md.",
    403: "The bot does not have permission in this channel. "
         "Re-invite with View Channels / Read Message History / Send Messages, "
         "or check channel-level permission overrides. See docs/SETUP.md §2.",
    404: "Channel or resource not found. "
         "Double-check DISCORD_CHANNEL_ID in .claude/secrets/discord-huddle.env.",
    429: "Rate-limited by Discord. The plugin already sleeps between requests; "
         "if this persists, another process may be hammering the same token.",
}


def _raise_for_response(resp: requests.Response, *, action: str) -> None:
    """Turn an HTTP failure into a DiscordAPIError with a user-friendly hint.

    ``action`` is a short noun phrase ("fetch messages", "post message") used
    in the error message so the caller sees which operation failed.
    """
    if resp.ok:
        return
    hint = _HINT_BY_STATUS.get(resp.status_code)
    # Discord returns JSON error bodies; extract the message where possible.
    detail = ""
    try:
        body = resp.json()
        if isinstance(body, dict):
            detail = body.get("message") or ""
    except ValueError:
        pass
    detail_suffix = f" — {detail}" if detail else ""
    raise DiscordAPIError(
        f"HTTP {resp.status_code} while trying to {action}{detail_suffix}",
        status=resp.status_code,
        hint=hint,
    )


class DiscordClient:
    BASE = "https://discord.com/api/v10"
    PAGE_LIMIT = 100
    REQUEST_TIMEOUT = 30.0

    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bot {self.bot_token}",
            "User-Agent": "agent-system-discord-huddle (py-requests)",
        }

    def fetch_all_new(self, channel_id: str, last_id: str | None) -> list[dict]:
        """last_id 이후의 모든 메시지를 시간 오름차순으로 반환.

        Discord API는 한 번에 최대 100개, `after=<id>` 페이지네이션.
        응답은 역시간순이지만 돌려줄 때는 시간 오름차순으로 정렬한다.

        첫 실행 (last_id=None) 시: `after="0"`으로 호출하여 채널 처음부터 끝까지 수집.
        (after 파라미터 없이 호출하면 Discord는 최신 100개만 반환하므로 과거 메시지를 놓친다.)
        """
        url = f"{self.BASE}/channels/{channel_id}/messages"
        collected: list[dict] = []
        cursor = last_id or "0"
        while True:
            params: dict[str, object] = {"limit": self.PAGE_LIMIT, "after": cursor}
            resp = requests.get(
                url, headers=self._headers(), params=params, timeout=self.REQUEST_TIMEOUT
            )
            _raise_for_response(resp, action="fetch channel messages")
            page = resp.json()
            if not isinstance(page, list):
                raise DiscordAPIError(f"unexpected response: {page!r}")
            if not page:
                break
            collected.extend(page)
            # after pagination: 다음 cursor = 현재 페이지에서 가장 큰 id
            # Discord IDs는 snowflake(시간 포함)라 수치 정렬 == 시간 정렬
            cursor = max(page, key=lambda m: int(m["id"]))["id"]
            time.sleep(0.2)  # 레이트리밋 여유

        collected.sort(key=lambda m: int(m["id"]))
        return collected

    def post_message(
        self,
        channel_id: str,
        content: str,
        attachments: list[Path] | None = None,
    ) -> dict:
        """POST a new message to a channel.

        - content: text body (can be empty string if attachments exist).
        - attachments: list of local file Paths. If provided, uses multipart/form-data.
        Returns the created message JSON.
        """
        if len(content) > 2000:
            raise DiscordAPIError(
                f"content exceeds Discord limit: {len(content)} chars (max 2000)"
            )

        url = f"{self.BASE}/channels/{channel_id}/messages"

        if not attachments:
            resp = requests.post(
                url,
                headers={**self._headers(), "Content-Type": "application/json"},
                json={"content": content},
                timeout=self.REQUEST_TIMEOUT,
            )
            _raise_for_response(resp, action="post message")
            return resp.json()

        if len(attachments) > 10:
            raise DiscordAPIError(
                f"too many attachments: {len(attachments)} (Discord max is 10)"
            )

        names = [p.name for p in attachments]
        payload = {
            "content": content,
            "attachments": [
                {"id": i, "filename": name} for i, name in enumerate(names)
            ],
        }

        files: list[tuple] = [
            ("payload_json", (None, json.dumps(payload), "application/json"))
        ]
        for i, path in enumerate(attachments):
            mime, _ = mimetypes.guess_type(str(path))
            if mime is None:
                mime = "application/octet-stream"
            files.append((f"files[{i}]", (path.name, path.read_bytes(), mime)))

        resp = requests.post(
            url,
            headers=self._headers(),
            files=files,
            timeout=self.REQUEST_TIMEOUT,
        )
        _raise_for_response(resp, action="post message with attachments")
        return resp.json()
