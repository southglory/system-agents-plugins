from pathlib import Path
import pytest


@pytest.fixture
def tmp_project(tmp_path):
    """Simulate a project root with plugin-standard runtime and summary dirs."""
    (tmp_path / ".system-agents" / "discord-huddle" / "raw" / "attachments").mkdir(parents=True)
    (tmp_path / ".system-agents" / "discord-huddle" / "inbox").mkdir(parents=True)
    (tmp_path / "docs" / "discord-huddle-summaries" / "attachments").mkdir(parents=True)
    (tmp_path / ".claude" / "secrets").mkdir(parents=True)
    return tmp_path


@pytest.fixture
def tmp_data_dir(tmp_project):
    return tmp_project / ".system-agents" / "discord-huddle"


@pytest.fixture
def tmp_summary_dir(tmp_project):
    return tmp_project / "docs" / "discord-huddle-summaries"


@pytest.fixture
def fake_env(tmp_project):
    """Fake secrets file with test token/channel."""
    env_file = tmp_project / ".claude" / "secrets" / "discord-huddle.env"
    env_file.write_text(
        "DISCORD_BOT_TOKEN=test_bot_token_123\n"
        "DISCORD_CHANNEL_ID=999888777\n",
        encoding="utf-8",
    )
    return env_file
