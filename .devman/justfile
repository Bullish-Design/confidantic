set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

test:
    @python - <<'PY'
import tomllib
from pathlib import Path

required = ["pydantic", "typer", "rich"]
missing = []

for module in required:
    try:
        __import__(module)
    except ImportError:
        missing.append(module)

if missing:
    raise SystemExit(
        "Missing required dependencies: " + ", ".join(missing)
    )

pyproject = Path("pyproject.toml")
version = tomllib.loads(pyproject.read_text())["project"]["version"]
print(f"confidantic version: {version}")
PY

