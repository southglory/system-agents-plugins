import pytest
from pathlib import Path

from discord_lib.config import Config, ConfigError


def test_load_reads_all_keys(fake_env, tmp_project):
    cfg = Config.load(secrets_path=fake_env, project_root=tmp_project)
    assert cfg.bot_token == "test_bot_token_123"
    assert cfg.channel_id == "999888777"
    assert cfg.project_root == tmp_project.resolve()
    # Default subpaths are resolved relative to project_root
    assert cfg.data_dir == (tmp_project / ".system-agents" / "discord-huddle").resolve()
    assert cfg.summary_dir == (tmp_project / "docs" / "discord-huddle-summaries").resolve()


def test_load_honors_process_env_overrides(fake_env, tmp_project, monkeypatch):
    """Process-level env vars still work (backward compatible)."""
    monkeypatch.delenv("DISCORD_HUDDLE_DATA_DIR", raising=False)
    monkeypatch.delenv("DISCORD_HUDDLE_SUMMARY_DIR", raising=False)
    monkeypatch.setenv("DISCORD_HUDDLE_DATA_DIR", "custom/data")
    monkeypatch.setenv("DISCORD_HUDDLE_SUMMARY_DIR", "custom/summaries")
    cfg = Config.load(secrets_path=fake_env, project_root=tmp_project)
    assert cfg.data_dir == (tmp_project / "custom" / "data").resolve()
    assert cfg.summary_dir == (tmp_project / "custom" / "summaries").resolve()


def test_load_honors_dotenv_overrides(tmp_project, monkeypatch):
    """Path overrides placed inside the secrets .env must be honored.

    This is the primary install path: users set DISCORD_HUDDLE_DATA_DIR etc.
    in .claude/secrets/discord-huddle.env next to the bot token, never in
    the process env.
    """
    # Ensure no leakage from the host environment
    monkeypatch.delenv("DISCORD_HUDDLE_DATA_DIR", raising=False)
    monkeypatch.delenv("DISCORD_HUDDLE_SUMMARY_DIR", raising=False)

    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=tok\n"
        "DISCORD_CHANNEL_ID=42\n"
        "DISCORD_HUDDLE_DATA_DIR=runtime/from-env\n"
        "DISCORD_HUDDLE_SUMMARY_DIR=notes/from-env\n",
        encoding="utf-8",
    )
    cfg = Config.load(secrets_path=env_file, project_root=tmp_project)
    assert cfg.data_dir == (tmp_project / "runtime" / "from-env").resolve()
    assert cfg.summary_dir == (tmp_project / "notes" / "from-env").resolve()


def test_dotenv_override_wins_over_process_env(tmp_project, monkeypatch):
    """When both .env and process env set the same key, .env wins.

    Rationale: the plugin's contract is 'your secrets file is authoritative'.
    Stale host env vars should not silently override a user's deliberate .env.
    """
    monkeypatch.setenv("DISCORD_HUDDLE_DATA_DIR", "from-process-env")

    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=tok\n"
        "DISCORD_CHANNEL_ID=42\n"
        "DISCORD_HUDDLE_DATA_DIR=from-dotenv\n",
        encoding="utf-8",
    )
    cfg = Config.load(secrets_path=env_file, project_root=tmp_project)
    assert cfg.data_dir == (tmp_project / "from-dotenv").resolve()


def test_dotenv_project_root_is_honored(tmp_path, monkeypatch):
    """SYSTEM_AGENTS_PROJECT_ROOT set in .env can re-point the project root
    even when the secrets file was loaded from the original root."""
    monkeypatch.delenv("SYSTEM_AGENTS_PROJECT_ROOT", raising=False)

    # Original "project" holds the secrets file; it has a .claude dir so the
    # cwd-walk fallback in resolve_project_root() will find it during the
    # second Config.load() call below (which has no explicit project_root).
    original = tmp_path / "original"
    (original / ".claude" / "secrets").mkdir(parents=True)

    # Target the user actually wants paths resolved against
    target = tmp_path / "actual-project"
    (target / ".claude").mkdir(parents=True)

    # Pin cwd to `original` so cwd-walk lands there deterministically, both
    # on CI (where $PWD has no .claude ancestor) and locally when pytest is
    # run from a checkout that happens to sit under a project with .claude.
    monkeypatch.chdir(original)

    env_file = original / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=tok\n"
        "DISCORD_CHANNEL_ID=42\n"
        f"SYSTEM_AGENTS_PROJECT_ROOT={target}\n",
        encoding="utf-8",
    )
    cfg = Config.load(secrets_path=env_file, project_root=original)
    # Explicit project_root arg still wins — so it stays 'original' until the
    # caller removes the arg. This test asserts that contract.
    assert cfg.project_root == original.resolve()

    # Now without the explicit arg: dotenv override should kick in.
    cfg2 = Config.load(secrets_path=env_file)
    assert cfg2.project_root == target.resolve()


def test_load_fails_without_token(tmp_project):
    env = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env.write_text("DISCORD_CHANNEL_ID=x\n", encoding="utf-8")
    with pytest.raises(ConfigError) as exc:
        Config.load(secrets_path=env, project_root=tmp_project)
    assert "DISCORD_BOT_TOKEN" in str(exc.value)


def test_load_fails_missing_file(tmp_project):
    missing = tmp_project / ".claude" / "secrets" / "nope.env"
    with pytest.raises(ConfigError) as exc:
        Config.load(secrets_path=missing, project_root=tmp_project)
    assert "not found" in str(exc.value).lower()
