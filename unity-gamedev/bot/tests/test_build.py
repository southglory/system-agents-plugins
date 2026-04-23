"""Tests for unity_lib.build (construction logic only — no unity-cli call)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
BOT_DIR = HERE.parent
if str(BOT_DIR) not in sys.path:
    sys.path.insert(0, str(BOT_DIR))

from unity_lib.build import build_location, UnityBuildError, run_unity_build, _cs_code, DEFAULT_TARGET


def test_build_location_windows_default(fake_unity_project):
    p = build_location(fake_unity_project, "MyGame", DEFAULT_TARGET)
    assert p == fake_unity_project / "Builds" / "MyGame.exe"


def test_build_location_osx_gives_app(fake_unity_project):
    p = build_location(fake_unity_project, "MyGame", "StandaloneOSX")
    assert p.name == "MyGame.app"


def test_build_location_linux_no_ext(fake_unity_project):
    p = build_location(fake_unity_project, "MyGame", "StandaloneLinux64")
    assert p.name == "MyGame"


def test_build_location_unknown_target_falls_back_to_exe(fake_unity_project):
    p = build_location(fake_unity_project, "X", "SomeConsole_XYZ")
    assert p.suffix == ".exe"


def test_cs_code_embeds_output_name_and_scenes():
    cs = _cs_code(
        scenes=["Assets/Scenes/A.unity", "Assets/Scenes/B.unity"],
        output_path="Builds/MyGame.exe",
        target="StandaloneWindows64",
    )
    assert "Assets/Scenes/A.unity" in cs
    assert "Assets/Scenes/B.unity" in cs
    assert "Builds/MyGame.exe" in cs
    assert "BuildTarget.StandaloneWindows64" in cs


def test_run_unity_build_requires_at_least_one_scene(fake_unity_project):
    with pytest.raises(UnityBuildError) as exc:
        run_unity_build(
            project_root=fake_unity_project,
            scenes=[],
            output_name="MyGame",
        )
    assert "at least one scene" in str(exc.value).lower()


def test_run_unity_build_surfaces_subprocess_failure(fake_unity_project, monkeypatch):
    """If unity-cli returns nonzero, we raise UnityBuildError with stderr."""
    import unity_lib.build as build_mod

    class FakeResult:
        returncode = 1
        stdout = ""
        stderr = "unity-cli not running"

    monkeypatch.setattr(build_mod.subprocess, "run", lambda *a, **kw: FakeResult())

    with pytest.raises(UnityBuildError) as exc:
        run_unity_build(
            project_root=fake_unity_project,
            scenes=["Assets/Scenes/Main.unity"],
            output_name="MyGame",
        )
    assert "unity-cli" in str(exc.value)
    assert "not running" in str(exc.value)


def test_run_unity_build_requires_result_succeeded(fake_unity_project, monkeypatch):
    """A zero-exit run that doesn't report Succeeded is still a failure."""
    import unity_lib.build as build_mod

    class FakeResult:
        returncode = 0
        stdout = "result=Failed size=0MB time=0.5s errors=2"
        stderr = ""

    monkeypatch.setattr(build_mod.subprocess, "run", lambda *a, **kw: FakeResult())

    with pytest.raises(UnityBuildError):
        run_unity_build(
            project_root=fake_unity_project,
            scenes=["Assets/Scenes/Main.unity"],
            output_name="MyGame",
        )


def test_run_unity_build_returns_expected_path_on_success(fake_unity_project, monkeypatch):
    import unity_lib.build as build_mod

    class FakeResult:
        returncode = 0
        stdout = "result=Succeeded size=50MB time=10s errors=0"
        stderr = ""

    monkeypatch.setattr(build_mod.subprocess, "run", lambda *a, **kw: FakeResult())

    got = run_unity_build(
        project_root=fake_unity_project,
        scenes=["Assets/Scenes/Main.unity"],
        output_name="MyGame",
        target=DEFAULT_TARGET,
    )
    assert got == fake_unity_project / "Builds" / "MyGame.exe"
