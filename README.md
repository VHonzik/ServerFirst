# Server First demo

Guild management simulator game demo set in fictional western MMORPG. Written in GDScript in Godot 4.7.2.

## Development setup

Use native Windows x64 with Python 3.10 or newer. From the repository root:

```text
python tools/setup.py
python tools/validate.py
```

Setup downloads pinned Godot and GUT releases. Validation runs headlessly and needs no network or export templates. The project currently contains infrastructure smoke tests; there is no gameplay or main scene yet.

See [the setup guide](docs/setup.md) for tool commands, pinned dependencies and Windows certificate handling.
