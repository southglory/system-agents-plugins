import json
from pathlib import Path

import pytest

from discord_lib.api import DiscordClient


FIXTURES = Path(__file__).parent / "fixtures"


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


@pytest.fixture
def fake_requests(monkeypatch):
    calls = []

    page1 = json.loads((FIXTURES / "discord_messages_page1.json").read_text(encoding="utf-8"))
    page2 = json.loads((FIXTURES / "discord_messages_page2.json").read_text(encoding="utf-8"))

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append({"url": url, "params": params, "headers": headers})
        after = (params or {}).get("after")
        if after == "0" or after is None:
            return _FakeResponse(page1)
        # after=최신 id → 빈 배열
        return _FakeResponse(page2)

    import discord_lib.api as mod
    monkeypatch.setattr(mod.requests, "get", fake_get)
    return calls


def test_fetch_all_new_paginates_until_empty(fake_requests):
    client = DiscordClient(bot_token="tok")
    msgs = client.fetch_all_new(channel_id="ch1", last_id="0")
    # 시간 오름차순 (A, B, C)
    assert [m["id"] for m in msgs] == [
        "1000000000000000001",
        "1000000000000000002",
        "1000000000000000003",
    ]
    # 2번 호출 (첫 페이지 + 빈 페이지)
    assert len(fake_requests) == 2


def test_fetch_all_new_sends_auth(fake_requests):
    DiscordClient(bot_token="tok").fetch_all_new(channel_id="ch1", last_id=None)
    assert fake_requests[0]["headers"]["Authorization"] == "Bot tok"


def test_fetch_all_new_initial_uses_after_zero(fake_requests):
    """첫 실행(last_id=None) 시 채널 처음부터 긁어오도록 after='0'을 보낸다."""
    DiscordClient(bot_token="tok").fetch_all_new(channel_id="ch1", last_id=None)
    assert fake_requests[0]["params"]["after"] == "0"
