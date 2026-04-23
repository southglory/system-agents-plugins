"""Discord 메시지 전송 — 텍스트 + 선택적 파일 첨부."""

from __future__ import annotations

from pathlib import Path


def run_post(config, client, content: str, attach_paths: list[Path]) -> dict:
    """Send a message (text + optional files) to config.channel_id.

    Validates each path exists and is a file.
    Returns the sent message dict.
    """
    for path in attach_paths:
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"attachment not found or not a file: {path}")

    return client.post_message(
        channel_id=config.channel_id,
        content=content,
        attachments=attach_paths if attach_paths else None,
    )
