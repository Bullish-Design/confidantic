#!/usr/bin/env python3
"""
demo_confidantic.py
~~~~~~~~~~~~~~~~~~~

Quick sanity-check for Confidantic.

What it shows
-------------
1. That simply importing  `from confidantic import Settings` gives you a
   fully-populated singleton.
2. Which *.env* files were discovered and merged (deepest path wins).
3. Accessing an arbitrary Settings field.
4. A dry-run semantic-version bump via VersionBase.

Run it from the project root:

    python examples/demo_confidantic.py
"""

from pathlib import Path

from confidantic import Settings  # ← auto-initialised instance
from confidantic.versioning import VersionBase


# --------------------------------------------------------------------------- #
def main() -> None:
    print("=== Confidantic Demo ===\n")

    # 1) show the auto-initialised settings object
    print("👉 Auto-initialised Settings:\n")
    # print(f"\n{Settings}\n\n")
    # pretty = Settings.pretty()
    print(f"\n{Settings.pretty()} \n\n")

    # 2) list every .env file that was merged (deepest paths first)
    print("👉 .env files detected (priority: deepest > shallowest):")
    for fp in Settings.env_files:
        print("  •", fp)
    print()

    # 3) access an arbitrary settings key (first key in the dict, if any)
    first_key = next(iter(Settings.model_dump()), None)
    if first_key:
        print(
            f"👉 Example access — Settings.{first_key} =", getattr(Settings, first_key)
        )
        print()

    # 4) dry-run a patch bump
    root = Path(Settings.project_root)
    current = VersionBase.parse(Settings.package_version or "0.0.0")
    bumped = VersionBase.bump_at_project_root(root, part="patch", dry_run=True)

    print("👉 Dry-run patch bump:")
    print("   Current version:", current)
    print("   Would become   :", bumped)
    print("\n✅ Confidantic appears to be functioning correctly!")


# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    main()
