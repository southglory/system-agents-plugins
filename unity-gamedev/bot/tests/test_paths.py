"""Tests for unity_lib.paths."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BOT_DIR = HERE.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from unity_lib.paths import ProjectRootError, resolve_project_root


def test_explicit_arg_wins(fake_unity_project, tmp_path, monkeypatch):
    monkeypatch.delenv("SYSTEM_AGENTS_PROJECT_ROOT", raising=False)
    # cwd is somewhere else; explicit should still win
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)

    got = resolve_project_root(explicit=fake_unity_project)
    assert got == fake_unity_project.resolve()


def test_env_var_is_used(fake_unity_project, tmp_path, monkeypatch):
    monkeypatch.setenv("SYSTEM_AGENTS_PROJECT_ROOT", str(fake_unity_project))
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)

    got = resolve_project_root()
    assert got == fake_unity_project.resolve()


def test_override_dict_wins_over_env(fake_unity_project, tmp_path, monkeypatch):
    # Process env points somewhere fake; override dict points to the real project
    monkeypatch.setenv("SYSTEM_AGENTS_PROJECT_ROOT", str(tmp_path / "does-not-exist"))
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.chdir(other)

    got = resolve_project_root(overrides={"SYSTEM_AGENTS_PROJECT_ROOT": str(fake_unity_project)})
    assert got == fake_unity_project.resolve()


def test_cwd_walk_finds_unity_project(fake_unity_project, monkeypatch):
    """If cwd is inside Assets/ we still detect the project root by walking up."""
    monkeypatch.delenv("SYSTEM_AGENTS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(fake_unity_project / "Assets")

    got = resolve_project_root()
    assert got == fake_unity_project.resolve()


def test_cwd_walk_requires_both_markers(tmp_path, monkeypatch):
    """A directory with Assets/ but no ProjectSettings/ is NOT a Unity project."""
    monkeypatch.delenv("SYSTEM_AGENTS_PROJECT_ROOT", raising=False)
    fake = tmp_path / "fake"
    (fake / "Assets").mkdir(parents=True)
    # Intentionally no ProjectSettings/
    monkeypatch.chdir(fake)

    with pytest.raises(ProjectRootError):
        resolve_project_root()


def test_raises_when_nothing_resolves(tmp_path, monkeypatch):
    monkeypatch.delenv("SYSTEM_AGENTS_PROJECT_ROOT", raising=False)
    monkeypatch.chdir(tmp_path)

    with pytest.raises(ProjectRootError) as exc:
        resolve_project_root()
    msg = str(exc.value).lower()
    assert "project root" in msg
    # The error mentions all three escape hatches so the user knows where to look.
    assert "system_agents_project_root" in msg
    assert "--project-root" in msg
    assert "assets/" in msg


def test_explicit_nondir_raises(tmp_path):
    missing = tmp_path / "nope"
    with pytest.raises(ProjectRootError):
        resolve_project_root(explicit=missing)
