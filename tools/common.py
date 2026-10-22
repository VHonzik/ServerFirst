"""Small shared helpers for the repository's Python tools."""

from __future__ import annotations

import configparser
import hashlib
import json
import os
from pathlib import Path
import platform
import sys


ROOT = Path(__file__).resolve().parent.parent


def check_host() -> None:
    if sys.version_info < (3, 10):
        raise RuntimeError("Python 3.10+ is required. Select a newer Python interpreter.")
    if platform.system() != "Windows" or platform.machine().lower() not in ("x86_64", "amd64"):
        raise RuntimeError("Only Windows x64 is supported.")


def versions(root: Path = ROOT) -> dict:
    return json.loads((root / "tools/versions.json").read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def assert_hash(path: Path, expected: str) -> None:
    if not path.is_file():
        raise RuntimeError(f"Missing dependency: {path}. Run tools/setup.py with Python 3.10+.")
    if sha256(path) != expected:
        raise RuntimeError(
            f"Checksum mismatch: {path}. Inspect it, then remove that generated file "
            "and rerun tools/setup.py. It has not been overwritten."
        )


def content_hash(directory: Path) -> str:
    """Hash relative slash-separated names and file digests; ignore generated sidecars."""
    digest = hashlib.sha256()
    files = sorted(
        (path.relative_to(directory).as_posix(), path)
        for path in directory.rglob("*")
        if path.is_file() and path.suffix not in (".import", ".uid")
    )
    for name, path in files:
        digest.update(name.encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def verify_gut(directory: Path, pin: dict) -> None:
    metadata = configparser.ConfigParser()
    metadata.read(directory / "plugin.cfg", encoding="utf-8")
    installed = metadata.get("plugin", "version", fallback="").strip('"')
    if installed != pin["version"] or content_hash(directory) != pin["content_sha256"]:
        raise RuntimeError(
            f"GUT version/content mismatch: {directory}. Inspect it, then remove that "
            "generated directory and rerun tools/setup.py. It has not been overwritten."
        )


def verify_godot(directory: Path, pin: dict) -> None:
    for name, expected in pin["files"].items():
        path = directory / name
        if not path.is_file() or sha256(path) != expected:
            raise RuntimeError(
                f"Godot installation mismatch: {directory} ({name}). Inspect it, then remove "
                "that generated directory and rerun tools/setup.py. It has not been overwritten."
            )


def godot_path(root: Path, pins: dict) -> Path:
    pin = pins["godot"]
    directory = root / pin["directory"]
    verify_godot(directory, pin)
    return directory / pin["executable"]


def runtime_environment(directory: Path) -> dict[str, str]:
    environment = os.environ.copy()
    for key, child in (
        ("APPDATA", "roaming"),
        ("LOCALAPPDATA", "local"),
        ("TEMP", "temp"),
        ("TMP", "temp"),
    ):
        destination = directory / child
        destination.mkdir(parents=True, exist_ok=True)
        environment[key] = str(destination.resolve())
    return environment


def godot_environment(directory: Path, root: Path, pins: dict) -> dict[str, str]:
    environment = runtime_environment(directory)
    # Restricted Windows users cannot read the system certificate store. Use
    # Godot's own pinned CA bundle for these isolated tool processes instead.
    certificate = root / pins["ca_bundle"]["path"]
    assert_hash(certificate, pins["ca_bundle"]["sha256"])
    environment["GODOT_EDITOR_CUSTOM_FEATURES"] = "serverfirst_tools"
    editor = Path(environment["APPDATA"]) / "Godot"
    editor.mkdir(parents=True, exist_ok=True)
    minor = ".".join(pins["godot"]["version"].split(".")[:2])
    settings = editor / f"editor_settings-{minor}.tres"
    # Preserve wrapper editor preferences on subsequent invocations.
    if not settings.exists():
        settings.write_text(
            '[gd_resource type="EditorSettings" format=3]\n\n[resource]\n'
            f'network/tls/editor_tls_certificates = {json.dumps(certificate.as_posix())}\n',
            encoding="utf-8",
        )
    return environment


def entrypoint(main) -> None:
    try:
        check_host()
        code = main()
    except (OSError, ValueError, RuntimeError, configparser.Error) as error:
        print(f"FAIL: {error}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        sys.exit(130)
    sys.exit(code or 0)
