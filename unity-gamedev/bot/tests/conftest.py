"""Test helpers for unity-gamedev."""
from pathlib import Path

import pytest


@pytest.fixture
def fake_unity_project(tmp_path: Path) -> Path:
    """Create a minimal Unity-shaped project: Assets/ + ProjectSettings/."""
    (tmp_path / "Assets").mkdir()
    (tmp_path / "ProjectSettings").mkdir()
    (tmp_path / "Builds").mkdir()
    return tmp_path
