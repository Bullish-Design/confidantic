import json
import typer
from rich import print as rprint
from pathlib import Path

from confidantic import init_settings, PluginRegistry, find_project_root
from confidantic.versioning import VersionBase

app = typer.Typer(add_completion=False, help="Confidantic CLI utilities")


@app.command()
def env(
    export: bool = typer.Option(
        False,
        "--export",
        "-e",
        help="Print as shell-export lines instead of pretty JSON.",
    ),
) -> None:
    """Pretty-print the resolved environment."""
    settings = init_settings(PluginRegistry.build_class())
    if export:
        for k, v in settings.model_dump().items():
            print(f"export {k}={json.dumps(str(v))}")
    else:
        rprint(settings.pretty())


@app.command()
def info() -> None:
    """Show high-level library / repo metadata."""
    settings = init_settings()
    info_dict = {
        "project_root": str(settings.project_root),
        "package_version": settings.package_version,
        "git_commit": settings.git_commit,
        "git_branch": settings.git_branch,
    }
    rprint(info_dict)


@app.command("bump-version")
def bump_version_cli(
    part: str = typer.Argument(
        ...,
        help="Which segment to bump: 'major', 'minor', or 'patch'.",
    ),
    prerelease: str | None = typer.Option(
        None,
        "--pre",
        help="Optional prerelease identifier (e.g. 'alpha', 'beta.1').",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        "-n",
        help="Show what *would* change without writing.",
    ),
) -> None:
    """
    Bump the semantic version in both *pyproject.toml* **and**
    `<package>/__init__.py`.

    Examples
    --------
    • Patch bump → `confidantic bump-version patch`
    • Minor bump with pre-release → `confidantic bump-version minor --pre rc.1`
    • Dry-run major bump → `confidantic bump-version major -n`
    """
    project_root = Path(find_project_root())
    new_version = VersionBase.bump_at_project_root(
        project_root,
        part=part,
        prerelease=prerelease,
        dry_run=dry_run,
    )
    if dry_run:
        rprint(f"[bold yellow]DRY-RUN:[/] would set version → {new_version}")
    else:
        rprint(f"[green]Version bumped to[/] {new_version}")


def main() -> None:  # entry-point for `python -m confidantic.cli`
    app()


if __name__ == "__main__":
    main()
