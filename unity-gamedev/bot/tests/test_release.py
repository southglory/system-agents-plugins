"""Tests for unity_lib.release (zip logic unit-tested; gh flow monkeypatched)."""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BOT_DIR = HERE.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from unity_lib.release import ReleaseError, make_zip, create_release


def test_make_zip_produces_archive_with_all_files(fake_unity_project):
    builds = fake_unity_project / "Builds"
    (builds / "MyGame.exe").write_bytes(b"binary content")
    (builds / "MyGame_Data").mkdir()
    (builds / "MyGame_Data" / "sharedassets.bundle").write_bytes(b"data")

    dist = fake_unity_project / "dist"
    zip_path = make_zip(builds, dist, "MyGame", "v0.1.0")

    assert zip_path.is_file()
    assert zip_path.name == "MyGame_v0.1.0.zip"
    assert zip_path.parent == dist.resolve() or zip_path.parent == dist

    with zipfile.ZipFile(zip_path) as zf:
        names = set(zf.namelist())
    assert "MyGame.exe" in names
    assert any(n.startswith("MyGame_Data/") for n in names)


def test_make_zip_errors_when_builds_dir_missing(tmp_path):
    with pytest.raises(ReleaseError):
        make_zip(tmp_path / "not-there", tmp_path / "dist", "X", "v1")


def test_make_zip_creates_dist_if_missing(fake_unity_project):
    builds = fake_unity_project / "Builds"
    (builds / "a.txt").write_text("x", encoding="utf-8")
    dist = fake_unity_project / "dist-new"
    assert not dist.exists()

    zip_path = make_zip(builds, dist, "X", "v1")
    assert zip_path.parent == dist.resolve() or zip_path.parent == dist
    assert zip_path.is_file()


def _fake_subprocess_factory(returncode: int, stdout: str, stderr: str):
    class _R:
        def __init__(self, rc, so, se):
            self.returncode = rc
            self.stdout = so
            self.stderr = se
    def fake(cmd, *args, **kwargs):
        return _R(returncode, stdout, stderr)
    return fake


def test_create_release_happy_path(fake_unity_project, monkeypatch):
    """gh release create + gh release view both return 0; URL comes out."""
    import unity_lib.release as rel_mod

    # Minimal FSM: first call = 'gh release create' → ok, second = 'gh release view' → json with URL
    calls = []

    def fake_run(cmd, *args, **kwargs):
        calls.append(cmd)
        class R: pass
        r = R()
        r.returncode = 0
        if "view" in cmd:
            r.stdout = '{"url": "https://github.com/foo/bar/releases/tag/v1"}'
        else:
            r.stdout = ""
        r.stderr = ""
        return r

    monkeypatch.setattr(rel_mod.subprocess, "run", fake_run)

    zip_path = fake_unity_project / "dist" / "X_v1.zip"
    zip_path.parent.mkdir()
    zip_path.write_bytes(b"zip")

    url = create_release(
        project_root=fake_unity_project,
        tag="v1",
        zip_path=zip_path,
        notes="hello",
        title="",
    )
    assert url == "https://github.com/foo/bar/releases/tag/v1"
    # notes file written
    assert (fake_unity_project / "dist" / ".notes_v1.md").is_file()


def test_create_release_falls_back_to_upload_when_tag_exists(fake_unity_project, monkeypatch):
    """First create fails with 'already exists'; upload --clobber then view URL."""
    import unity_lib.release as rel_mod

    step = {"i": 0}

    def fake_run(cmd, *args, **kwargs):
        step["i"] += 1
        class R: pass
        r = R()
        if step["i"] == 1:
            # release create — fails with 'already exists'
            r.returncode = 1
            r.stdout = ""
            r.stderr = "HTTP 422: Validation Failed — already exists"
        elif step["i"] == 2:
            # release upload --clobber — succeeds
            r.returncode = 0
            r.stdout = ""
            r.stderr = ""
        else:
            # release view
            r.returncode = 0
            r.stdout = '{"url": "https://example.com/rel/v2"}'
            r.stderr = ""
        return r

    monkeypatch.setattr(rel_mod.subprocess, "run", fake_run)

    zip_path = fake_unity_project / "dist" / "X_v2.zip"
    zip_path.parent.mkdir()
    zip_path.write_bytes(b"zip")

    url = create_release(fake_unity_project, "v2", zip_path, "notes", "title")
    assert url == "https://example.com/rel/v2"


def test_create_release_surfaces_gh_failure(fake_unity_project, monkeypatch):
    import unity_lib.release as rel_mod

    def fake_run(cmd, *args, **kwargs):
        class R: pass
        r = R()
        r.returncode = 1
        r.stdout = ""
        r.stderr = "authentication required"
        return r

    monkeypatch.setattr(rel_mod.subprocess, "run", fake_run)

    zip_path = fake_unity_project / "dist" / "X_v3.zip"
    zip_path.parent.mkdir()
    zip_path.write_bytes(b"zip")

    with pytest.raises(ReleaseError) as exc:
        create_release(fake_unity_project, "v3", zip_path, "", "")
    assert "auth" in str(exc.value).lower()
