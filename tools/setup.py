"""Install pinned Godot and GUT. This is the only tool that uses the network."""

from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import urllib.request
import zipfile

from common import ROOT, assert_hash, entrypoint, verify_godot, verify_gut, versions


def download_file(destination: Path, url: str, expected: str) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists():
        print(f"Downloading {destination.name}...", flush=True)
        # A partial download can never be mistaken for a verified cached archive.
        with tempfile.TemporaryDirectory(prefix="download-", dir=destination.parent) as staging:
            download = Path(staging) / "download"
            request = urllib.request.Request(url, headers={"User-Agent": "ServerFirst-setup"})
            with urllib.request.urlopen(request, timeout=120) as source, download.open("wb") as output:
                shutil.copyfileobj(source, output)
            assert_hash(download, expected)
            download.rename(destination)
    assert_hash(destination, expected)
    return destination


def archive(root: Path, name: str, pin: dict) -> Path:
    destination = root / "bin/cache" / f"{name}-{pin['archive_sha256']}.zip"
    return download_file(destination, pin["download_url"], pin["archive_sha256"])


def extract_gut(source: Path, destination: Path, prefix: str) -> None:
    with zipfile.ZipFile(source) as bundle:
        for member in bundle.infolist():
            if not member.filename.startswith(prefix) or member.is_dir():
                continue
            name = member.filename[len(prefix):]
            relative = Path(name)
            if relative.is_absolute() or relative.drive or ".." in relative.parts or "\\" in name:
                raise RuntimeError(f"Unsafe archive member: {member.filename}")
            target = destination.joinpath(*relative.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with bundle.open(member) as data, target.open("wb") as output:
                shutil.copyfileobj(data, output)


def install(root: Path = ROOT) -> None:
    pins = versions(root)
    engine_pin, gut_pin = pins["godot"], pins["gut"]
    engine = root / engine_pin["directory"]
    gut = root / gut_pin["directory"]

    # Check existing dependencies before downloading or publishing anything.
    if engine.exists():
        verify_godot(engine, engine_pin)
    if gut.exists():
        verify_gut(gut, gut_pin)
    certificate = pins["ca_bundle"]
    if (root / certificate["path"]).exists():
        assert_hash(root / certificate["path"], certificate["sha256"])

    engine.parent.mkdir(parents=True, exist_ok=True)
    if not engine.exists():
        source = archive(root, "godot", engine_pin)
        with tempfile.TemporaryDirectory(prefix="install-", dir=engine.parent) as staging:
            candidate = Path(staging) / "engine"
            candidate.mkdir()
            with zipfile.ZipFile(source) as bundle:
                for name in engine_pin["files"]:
                    with bundle.open(name) as data, (candidate / name).open("wb") as output:
                        shutil.copyfileobj(data, output)
            verify_godot(candidate, engine_pin)
            candidate.rename(engine)

    if not gut.exists():
        source = archive(root, "gut", gut_pin)
        gut.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="install-", dir=gut.parent) as staging:
            candidate = Path(staging) / "gut"
            candidate.mkdir()
            extract_gut(source, candidate, gut_pin["archive_member"])
            verify_gut(candidate, gut_pin)
            candidate.rename(gut)
    download_file(root / certificate["path"], certificate["download_url"], certificate["sha256"])
    print("Pinned Godot and GUT verified. Run tools/validate.py with the same Python interpreter.")


def main() -> None:
    try:
        install()
    except (zipfile.BadZipFile, KeyError) as error:
        raise RuntimeError(f"Pinned archive layout is invalid: {error}. Check tools/versions.json.") from error


if __name__ == "__main__":
    entrypoint(main)
