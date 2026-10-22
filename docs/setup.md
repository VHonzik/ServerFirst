# Development setup

Requires Windows x64 and Python 3.10+. The scripts use only Python's standard library.

## Pinned dependencies

[tools/versions.json](../tools/versions.json) defines download URLs and SHA-256 hashes for:

- Godot 4.7.2 Standard.
- GUT 9.7.1.
- The CA bundle shipped with Godot 4.7.2.

## Tools

Run from the repository root:

| Command | Purpose |
| --- | --- |
| `python tools/setup.py` | Download and verify pinned dependencies. Reuses valid installations and rejects mismatches. |
| `python tools/godot.py --editor` | Launch the pinned editor. The wrapper forwards native Godot arguments. |
| `python tools/validate.py` | Run offline headless import and GUT tests; fail on errors, timeouts or incomplete results. |
| `python -m unittest discover -s tools -v` | Run the Python tooling tests. |

Downloaded tools and caches are stored in `bin/`, GUT in `addons/gut/`, and validation logs and JUnit reports in `reports/validation/`. These generated files are gitignored.

## Windows certificates

Codex's Windows sandbox blocks Godot's access to the system root certificate store, causing startup errors even in headless mode. Tool processes use the verified CA bundle through workspace-local editor and project settings, keeping TLS certificate verification enabled.
