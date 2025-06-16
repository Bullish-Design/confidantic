# Confidantic
Magical one stop settings shop. Kinda like Wonka, but these settings factories have less oompa loopas. And a better OSHA record.

---

Confidantic is a lightweight, Pydantic‑v2‑powered toolkit that centralises **all** the knobs your Python project needs – environment variables, version info, feature flags and whatever new tricks tomorrow brings – behind one pleasant `Settings` import.

## Why Confidantic?

* **Recursive `.env` discovery** – walks from the current working directory up to the project root, merging every `*.env` it finds (deepest path wins).
* **Typed & validated** – built on Pydantic v2 so every value arrives clean and IDE‑hinted.
* **Single source of truth** – `from confidantic import settings` gives the same singleton everywhere.
* **Smart metadata** – auto‑detects package version and Git branch/commit when available.
* **Tiny plugin system** – drop‑in mix‑ins can extend the settings model at runtime (e.g. generate a Markdown change‑log from commit messages).
* **Rich CLI** – `confidantic env` pretty prints resolved settings or emits shell‑ready `export` lines.

## Installation

```bash
pip install confidantic           # base package
pip install confidantic[git]      # add Git metadata support
```

## Quick Start

```python
from confidantic import Settings, init_settings

class MySettings(Settings):
    debug: bool = False
    api_url: str
    timeout_secs: int = 15

settings = init_settings(MySettings)
print(settings.api_url, settings.git_commit)
```

## CLI Cheatsheet

```bash
# Pretty JSON of every resolved field
$ confidantic env

# POSIX export lines
$ confidantic env -e | source /dev/stdin

# Repo & package metadata
$ confidantic info
```

## Example Plugin

```python
from confidantic import PluginRegistry, Settings, init_settings
import subprocess

class Changelog(Settings):
    last_release_tag: str | None = None

    def changelog(self) -> str:
        tag = self.last_release_tag or "HEAD~20"
        return subprocess.check_output(
            ["git", "-C", str(self.project_root), "log", f"{tag}..HEAD", "--oneline"],
            text=True,
        )

PluginRegistry.register(Changelog)
settings = init_settings(PluginRegistry.build_class())
print(settings.changelog())
```

## Typical Layout

```
project-root/
├── .env                # global defaults
├── services/
│   └── worker/.env     # overrides for that folder
├── .config/
│   └── confidantic.yaml  # auto‑generated snapshot
└── my_package/
    └── …
```

## Contributing

1. Fork & clone `https://github.com/Bullish-Design/confidantic`.
2. `pip install -e '.[dev,git]'` – includes linting & test extras.
3. `pytest -q && ruff check . && mypy confidantic`.
4. Open a PR; GitHub Actions will run on Python 3.10‑3.13.

We follow **Semantic Versioning**; PRs should include tests and updated docs where relevant.

## License

Released under the MIT License.

---

Maintained with ❤️ by **[Bullish‑Design](https://github.com/Bullish-Design)**.

