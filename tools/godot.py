"""Run the pinned Godot editor with native arguments and workspace-local user data."""

import subprocess
import sys

from common import ROOT, entrypoint, godot_environment, godot_path, versions


def main() -> int:
    pins = versions()
    engine = godot_path(ROOT, pins)
    return subprocess.call(
        [str(engine), "--path", str(ROOT), *sys.argv[1:]],
        cwd=ROOT,
        env=godot_environment(ROOT / "reports/runtime", ROOT, pins),
    )


if __name__ == "__main__":
    entrypoint(main)
