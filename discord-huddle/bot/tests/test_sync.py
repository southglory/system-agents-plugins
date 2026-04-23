from types import SimpleNamespace

import pytest

from discord_lib.storage import Storage
from discord_lib.sync import run_sync


class _StubClient:
    def __init__(self, messages):
        self._messages = messages
        self.calls = []

    def fetch_all_new(self, channel_id, last_id):
        self.calls.append((channel_id, last_id))
        return self._messages


def _msg(mid, ts, attachments=None):
    return {
        "id": mid,
        "content": f"msg {mid}",
        "timestamp": ts,
        "author": {"id": "u1", "username": "영광형"},
        "attachments": attachments or [],
        "reactions": [],
    }


def test_run_sync_persists_messages_and_updates_status(tmp_data_dir, tmp_summary_dir, monkeypatch):
    storage = Storage(tmp_data_dir, tmp_summary_dir)
    client = _StubClient([
        _msg("1", "2026-04-21T14:30:00.000000+00:00"),
        _msg("2", "2026-04-21T14:31:00.000000+00:00"),
    ])
    cfg = SimpleNamespace(channel_id="ch1", bot_token="t")

    stats = run_sync(cfg, client, storage)
    assert stats["new_messages"] == 2
    assert storage.get_read_status("ch1")["last_read"] == "2"

    # 같은 페이지 또 돌려도 중복 방지
    stats2 = run_sync(cfg, client, storage)
    assert stats2["new_messages"] == 0


def test_run_sync_downloads_attachments(tmp_data_dir, tmp_summary_dir, monkeypatch):
    storage = Storage(tmp_data_dir, tmp_summary_dir)

    captured = []

    def fake_download(self, url, msg_id, filename, timeout=30.0):
        captured.append((url, msg_id, filename))
        p = storage.raw_attach_dir / f"{msg_id}_{filename}"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"fake")
        return p

    monkeypatch.setattr(Storage, "download_attachment", fake_download)

    client = _StubClient([
        _msg("10", "2026-04-21T14:30:00.000000+00:00", attachments=[
            {"url": "https://cdn/a.png", "filename": "a.png", "id": "att1"},
        ])
    ])
    cfg = SimpleNamespace(channel_id="ch1", bot_token="t")

    stats = run_sync(cfg, client, storage)
    assert stats["new_messages"] == 1
    assert stats["new_attachments"] == 1
    assert captured == [("https://cdn/a.png", "10", "a.png")]
    # 메시지 JSONL에 local_path 기록됐는지 확인
    messages = storage.read_raw_after(None)
    assert messages[0]["attachments"][0]["local_path"] == "attachments/10_a.png"


def test_run_sync_continues_on_attachment_failure(tmp_data_dir, tmp_summary_dir, monkeypatch):
    storage = Storage(tmp_data_dir, tmp_summary_dir)

    def fake_download(self, url, msg_id, filename, timeout=30.0):
        raise RuntimeError("boom")

    monkeypatch.setattr(Storage, "download_attachment", fake_download)
    client = _StubClient([
        _msg("11", "2026-04-21T14:30:00.000000+00:00", attachments=[
            {"url": "https://cdn/b.png", "filename": "b.png", "id": "att2"},
        ])
    ])
    cfg = SimpleNamespace(channel_id="ch1", bot_token="t")

    stats = run_sync(cfg, client, storage)
    assert stats["new_messages"] == 1
    assert stats["failed_attachments"] == 1
    # 메시지 자체는 저장됨. local_path는 없음.
    messages = storage.read_raw_after(None)
    assert "local_path" not in messages[0]["attachments"][0]
