"""Tests for DiscordClient.post_message and run_post."""

import json
from pathlib import Path

import pytest

import discord_lib.api as api_mod
from discord_lib.api import DiscordAPIError, DiscordClient
from discord_lib.post import run_post


class _FakeResponse:
    def __init__(self, body, status=200):
        self._body = body
        self.status_code = status

    @property
    def ok(self):
        return self.status_code < 400

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._body


def test_post_message_json_body_without_attachments(monkeypatch):
    calls = []

    def fake_post(url, headers=None, json=None, files=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json, "files": files})
        return _FakeResponse({"id": "999", "content": "hi"})

    monkeypatch.setattr(api_mod.requests, "post", fake_post)

    client = DiscordClient(bot_token="testtoken")
    result = client.post_message(channel_id="ch42", content="hi")

    assert len(calls) == 1
    call = calls[0]
    assert call["url"] == f"{DiscordClient.BASE}/channels/ch42/messages"
    assert call["headers"]["Authorization"] == "Bot testtoken"
    assert call["json"] == {"content": "hi"}
    assert call["files"] is None
    assert result == {"id": "999", "content": "hi"}


def test_post_message_multipart_with_attachments(monkeypatch, tmp_path):
    file_a = tmp_path / "image.png"
    file_a.write_bytes(b"\x89PNG\r\n")
    file_b = tmp_path / "data.txt"
    file_b.write_text("hello", encoding="utf-8")

    calls = []

    def fake_post(url, headers=None, json=None, files=None, timeout=None):
        calls.append({"url": url, "headers": headers, "json": json, "files": files})
        return _FakeResponse({"id": "1001"})

    monkeypatch.setattr(api_mod.requests, "post", fake_post)

    client = DiscordClient(bot_token="tok")
    result = client.post_message(
        channel_id="ch1", content="look at this", attachments=[file_a, file_b]
    )

    assert len(calls) == 1
    call = calls[0]
    assert call["files"] is not None

    # Build a dict from the files list for easier lookup
    files_dict = {}
    for entry in call["files"]:
        field_name = entry[0]
        files_dict[field_name] = entry[1]

    assert "payload_json" in files_dict
    payload_raw = files_dict["payload_json"][1]
    payload = json.loads(payload_raw)
    assert payload["content"] == "look at this"
    assert len(payload["attachments"]) == 2
    assert payload["attachments"][0] == {"id": 0, "filename": "image.png"}
    assert payload["attachments"][1] == {"id": 1, "filename": "data.txt"}

    assert "files[0]" in files_dict
    assert "files[1]" in files_dict
    assert files_dict["files[0]"][0] == "image.png"
    assert files_dict["files[1]"][0] == "data.txt"

    assert result == {"id": "1001"}


def test_post_message_rejects_too_many_attachments(tmp_path, monkeypatch):
    # Provide a no-op fake post so network isn't called
    monkeypatch.setattr(api_mod.requests, "post", lambda *a, **kw: None)

    files = []
    for i in range(11):
        p = tmp_path / f"file{i}.txt"
        p.write_text(f"content {i}")
        files.append(p)

    client = DiscordClient(bot_token="tok")
    with pytest.raises(DiscordAPIError, match="too many attachments"):
        client.post_message(channel_id="ch1", content="text", attachments=files)


def test_post_message_rejects_too_long_content(monkeypatch):
    monkeypatch.setattr(api_mod.requests, "post", lambda *a, **kw: None)

    client = DiscordClient(bot_token="tok")
    long_content = "x" * 2001
    with pytest.raises(DiscordAPIError, match="content exceeds Discord limit"):
        client.post_message(channel_id="ch1", content=long_content)


def test_run_post_validates_file_exists(tmp_path):
    missing = tmp_path / "ghost.png"

    class _FakeConfig:
        channel_id = "ch1"

    class _FakeClient:
        def post_message(self, *a, **kw):
            raise AssertionError("should not be called")

    with pytest.raises(FileNotFoundError, match="ghost.png"):
        run_post(_FakeConfig(), _FakeClient(), "hello", [missing])
