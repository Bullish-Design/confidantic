from __future__ import annotations

import sys
import importlib
from pathlib import Path


def find_repo_root() -> Path:
    # .devman/scripts/test.py -> scripts -> .devman -> repo root
    return Path(__file__).resolve().parents[2]


def load_toml(text: str) -> dict:
    try:
        import tomllib  # py3.11+

        return tomllib.loads(text)
    except ModuleNotFoundError:
        # Optional fallback for older Pythons
        try:
            import tomli  # type: ignore

            return tomli.loads(text)
        except ModuleNotFoundError as e:
            raise SystemExit(
                "TOML parser not available. Use Python 3.11+ (tomllib) or install tomli."
            ) from e


def main() -> int:
    required = ["pydantic", "typer", "rich"]
    missing: list[str] = []

    for module in required:
        try:
            importlib.import_module(module)
        except ImportError:
            missing.append(module)

    if missing:
        print("Missing required dependencies: " + ", ".join(missing), file=sys.stderr)
        return 1

    root = find_repo_root()
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        print(f"pyproject.toml not found at: {pyproject}", file=sys.stderr)
        return 1

    data = load_toml(pyproject.read_text(encoding="utf-8"))
    try:
        version = data["project"]["version"]
    except Exception:
        print("Could not find [project].version in pyproject.toml", file=sys.stderr)
        return 1

    print(f"confidantic version: {version}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
