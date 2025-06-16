# Confidantic
Magical one stop settings shop. Kinda like Wonka, but these settings factories have less oompa loopas. And a better OSHA record.

---

Confidantic is a lightweight, Pydantic‑v2‑powered toolkit that centralises **all** the knobs your Python project needs – environment variables, version info, feature flags and whatever new tricks tomorrow brings – behind one pleasant `Settings` import.

## Why Confidantic?

Stop writing the same brittle glue code to pull `.env` files into `pydantic` models, wire them into CLIs, and keep project metadata in sync. **Confidantic gives you a single import**:

```python
from confidantic import Settings
```

…and you instantly get a fully populated, type‑safe configuration object:

* Recursive load of every `*.env` file from the repo root down (deepest wins).
* OS environment variables layered on top.
* Git branch/commit metadata.
* Project version (kept in sync between `pyproject.toml` and `__init__.py`).
* Your own fields—via plug‑in mix‑ins—auto‑merged at import time.

No init calls, no singleton ceremony. Just **import & go**.

## Features

| Feature                    | Description                                               |       |                                                                        |
| -------------------------- | --------------------------------------------------------- | ----- | ---------------------------------------------------------------------- |
| Zero‑boilerplate settings  | `Settings` instance auto‑initialised on import            |       |                                                                        |
| Recursive `.env` discovery | Deepest path wins; OS env overrides `.env` values         |       |                                                                        |
| Semantic version model     | `VersionBase` (`major.minor.patch-pre`) with bump helpers |       |                                                                        |
| Version CLI                | \`confidantic bump-version {major                         | minor | patch} \[--pre rc.1]`keeps`pyproject.toml`&`**init**.py\` in lock‑step |
| Rich pretty‑printing       | `Settings.pretty()` via Rich                              |       |                                                                        |
| Plug‑in registry           | Third‑party packages can extend Settings via mix‑ins      |       |                                                                        |
| Type‑safe core             | Built on Pydantic v2                                      |       |                                                                        |

## Installation

```bash
pip install confidantic
# Optional Git integration (for commit/branch metadata)
pip install confidantic[git]
```

## Quickstart

```python
from confidantic import Settings

print(Settings.project_root)   # Path to repo root
print(Settings.package_version) # e.g. '0.7.0'
print(Settings.MY_API_KEY)      # Pulled from any .env or OS environment
```

### Adding your own fields

```python
from pydantic import Field
from confidantic import PluginRegistry, SettingsType

class MyCloudMixin(SettingsType):
    cloud_token: str = Field(env="CLOUD_TOKEN")

PluginRegistry.register(MyCloudMixin)

from confidantic import Settings  # re-import picks up new mix‑in
print(Settings.cloud_token)
```

## CLI

| Command                               | Purpose                                       |
| ------------------------------------- | --------------------------------------------- |
| `confidantic env`                     | Pretty‑prints the resolved settings           |
| `confidantic env --export`            | Emits `export KEY=VAL` lines for shells       |
| `confidantic info`                    | Shows project root, version, Git info         |
| `confidantic bump-version patch [-n]` | Bump & sync semantic version; `-n` is dry‑run |

All commands are also invokable as `python -m confidantic.cli …`.

## Demo

A ready‑to‑run sanity check lives at **`examples/demo_confidantic.py`**:

```bash
python examples/demo_confidantic.py
```

It prints your merged settings and performs a dry‑run version bump.

## How version bump works

1. Read current version from `pyproject.toml`.
2. Compute next semantic version via `VersionBase`.
3. Update both `pyproject.toml` **and** `package/__init__.py` atomically.

Use `--pre alpha.1` to add prerelease tags.

## Project structure assumptions

* Repo root contains a `pyproject.toml`.
* Your package lives directly under the root folder (`/confidantic`, `/my_pkg`, …).
* Git info is optional; if `gitpython` isn’t installed or you're outside a repo, the fields are simply `None`.

## Contributing

Issues & PRs welcome on GitHub ([@Bullish-Design](https://github.com/Bullish-Design)).

```bash
pip install -e ".[dev]" && pytest
```

---

MIT © 2025 Bullish‑Design

