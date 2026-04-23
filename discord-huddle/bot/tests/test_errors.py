"""Tests for user-facing error rendering (F5)."""
from __future__ import annotations

import pytest

from discord_lib.api import DiscordAPIError, _raise_for_response


class _Resp:
    def __init__(self, status, body=None):
        self.status_code = status
        self._body = body

    @property
    def ok(self):
        return self.status_code < 400

    def json(self):
        if self._body is None:
            raise ValueError("no json")
        return self._body


def test_raise_for_response_no_op_on_ok():
    _raise_for_response(_Resp(200), action="fetch")  # should not raise


def test_401_has_token_hint():
    with pytest.raises(DiscordAPIError) as exc_info:
        _raise_for_response(_Resp(401), action="fetch")
    err = exc_info.value
    assert err.status == 401
    assert "fetch" in str(err)
    assert err.hint is not None
    assert "Reset Token" in err.hint


def test_403_has_permission_hint():
    with pytest.raises(DiscordAPIError) as exc_info:
        _raise_for_response(_Resp(403), action="post message"),
    err = exc_info.value
    assert err.status == 403
    assert err.hint is not None
    assert "permission" in err.hint.lower() or "invite" in err.hint.lower()


def test_404_channel_hint():
    with pytest.raises(DiscordAPIError) as exc_info:
        _raise_for_response(_Resp(404), action="fetch")
    err = exc_info.value
    assert err.status == 404
    assert "DISCORD_CHANNEL_ID" in err.hint


def test_429_rate_limit_hint():
    with pytest.raises(DiscordAPIError) as exc_info:
        _raise_for_response(_Resp(429), action="fetch")
    assert exc_info.value.hint is not None
    assert "rate" in exc_info.value.hint.lower() or "Rate" in exc_info.value.hint


def test_unknown_status_still_raises_without_hint():
    with pytest.raises(DiscordAPIError) as exc_info:
        _raise_for_response(_Resp(418), action="brew coffee")
    err = exc_info.value
    assert err.status == 418
    assert err.hint is None
    assert "brew coffee" in str(err)


def test_error_message_includes_discord_detail_when_provided():
    """If Discord's error body has 'message', include it in the thrown exception."""
    resp = _Resp(401, body={"message": "401: Unauthorized"})
    with pytest.raises(DiscordAPIError) as exc_info:
        _raise_for_response(resp, action="fetch")
    assert "401: Unauthorized" in str(exc_info.value)


def test_cmd_sync_prints_friendly_on_401(tmp_project, monkeypatch, capsys):
    """End-to-end: cmd_sync catches DiscordAPIError and emits hint, no traceback."""
    import discord_lib.api as api_mod
    import discord_collab as cli_mod

    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=bad\nDISCORD_CHANNEL_ID=111\n",
        encoding="utf-8",
    )

    class _FailingResp:
        status_code = 401
        ok = False
        def json(self): return {"message": "401: Unauthorized"}
    monkeypatch.setattr(api_mod.requests, "get", lambda *a, **kw: _FailingResp())

    rc = cli_mod.main(["sync", "--project-root", str(tmp_project)])
    err = capsys.readouterr().err
    assert rc == 1
    assert "error:" in err
    assert "401" in err
    # Hint must be present and reference token reset / SETUP
    assert "hint" in err
    assert ("Reset Token" in err) or ("SETUP.md" in err)
    # No Python traceback leaking through
    assert "Traceback" not in err
