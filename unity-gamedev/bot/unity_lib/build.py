"""Unity build via unity-cli exec.

``run_unity_build`` constructs a BuildPlayerOptions invocation and executes
it through ``unity-cli exec``. No project-specific names are hardcoded:
scenes, output filename, and build target all come from the caller.

Requires:
  - Unity Editor running with unity-cli connected (`unity-cli status = ready`).
  - ``unity-cli`` on PATH.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Sequence


DEFAULT_TARGET = "StandaloneWindows64"


class UnityBuildError(RuntimeError):
    """Raised when the Unity build step fails."""


def _log(msg: str) -> None:
    import sys
    print(msg, file=sys.stderr)


def build_location(project_root: Path, output_name: str, target: str) -> Path:
    """Return the on-disk output path the build will produce.

    - StandaloneWindows64 → Builds/{output_name}.exe
    - StandaloneOSX      → Builds/{output_name}.app
    - StandaloneLinux64  → Builds/{output_name}
    """
    ext = {
        "StandaloneWindows64": ".exe",
        "StandaloneWindows": ".exe",
        "StandaloneOSX": ".app",
        "StandaloneLinux64": "",
        "StandaloneLinux": "",
    }.get(target, ".exe")
    return project_root / "Builds" / f"{output_name}{ext}"


def _cs_code(scenes: Sequence[str], output_path: str, target: str) -> str:
    scenes_literal = ", ".join(f'"{s}"' for s in scenes)
    return (
        "var options = new BuildPlayerOptions();"
        f"options.scenes = new string[] {{ {scenes_literal} }};"
        f'options.locationPathName = "{output_path}";'
        f"options.target = BuildTarget.{target};"
        "options.options = BuildOptions.None;"
        "var report = BuildPipeline.BuildPlayer(options);"
        "var s = report.summary;"
        'return string.Format("result={0} size={1}MB time={2}s errors={3}", '
        "s.result, s.totalSize / 1024 / 1024, s.totalTime.TotalSeconds, s.totalErrors);"
    )


def run_unity_build(
    project_root: Path,
    scenes: Sequence[str],
    output_name: str,
    target: str = DEFAULT_TARGET,
    timeout: float = 600.0,
) -> Path:
    """Invoke unity-cli to run BuildPlayer. Returns the path to the built binary.

    Raises UnityBuildError on failure. The stderr log line will carry
    unity-cli's own stdout for diagnostics.
    """
    if not scenes:
        raise UnityBuildError("at least one scene must be supplied (via --scene)")

    built = build_location(project_root, output_name, target)
    # Unity wants a forward-slash relative path under the project root.
    try:
        rel = built.relative_to(project_root).as_posix()
    except ValueError:
        rel = built.as_posix()

    _log(f"[publish] running Unity build → {rel}")
    cs = _cs_code(scenes=scenes, output_path=rel, target=target)
    result = subprocess.run(
        ["unity-cli", "exec", cs],
        cwd=str(project_root),
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise UnityBuildError(f"unity-cli exec failed: {result.stderr.strip()}")
    out = result.stdout.strip()
    _log(f"[publish] {out}")
    if "result=Succeeded" not in out:
        raise UnityBuildError(f"Unity build did not succeed: {out}")
    return built
