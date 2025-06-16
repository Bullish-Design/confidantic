from __future__ import annotations

import re
import tomllib
from pathlib import Path
from typing import ClassVar, Literal

from pydantic import BaseModel, Field, model_validator

# --------------------------------------------------------------------------- #
#                              Version  Model                                 #
# --------------------------------------------------------------------------- #


class VersionBase(BaseModel):
    """Light-weight semantic-version model with bump helpers."""

    major: int = Field(..., ge=0)
    minor: int = Field(..., ge=0)
    patch: int = Field(..., ge=0)
    prerelease: str | None = Field(default=None)

    _SEMVER_RE: ClassVar[re.Pattern[str]] = re.compile(
        r"""
        ^
        (?P<major>0|[1-9]\d*)
        \.
        (?P<minor>0|[1-9]\d*)
        \.
        (?P<patch>0|[1-9]\d*)
        (?:-(?P<pre>[0-9A-Za-z.-]+))?
        $
        """,
        re.VERBOSE,
    )

    # ------------------------------------------------------------------ #
    #  Constructors / Validators                                         #
    # ------------------------------------------------------------------ #

    @model_validator(mode="before")
    @classmethod
    def _coerce_from_str(cls, v):  # noqa: ANN001 (pydantic hook)
        if isinstance(v, str):
            return cls.parse(v).model_dump()
        return v

    @classmethod
    def parse(cls, value: str) -> "VersionBase":
        match = cls._SEMVER_RE.match(value.strip())
        if not match:
            raise ValueError(f"'{value}' is not valid SemVer.")
        gd = match.groupdict()
        return cls(
            major=int(gd["major"]),
            minor=int(gd["minor"]),
            patch=int(gd["patch"]),
            prerelease=gd["pre"],
        )

    # ------------------------------------------------------------------ #
    #  Magic methods & helpers                                           #
    # ------------------------------------------------------------------ #

    def __str__(self) -> str:  # noqa: Dunder
        base = f"{self.major}.{self.minor}.{self.patch}"
        return f"{base}-{self.prerelease}" if self.prerelease else base

    def _bumped(
        self,
        part: Literal["major", "minor", "patch"],
        *,
        prerelease: str | None = None,
    ) -> "VersionBase":
        new = self.model_copy()
        if part == "major":
            new.major, new.minor, new.patch = self.major + 1, 0, 0
        elif part == "minor":
            new.minor, new.patch = self.minor + 1, 0
        else:  # patch
            new.patch += 1
        new.prerelease = prerelease
        return new

    # public bump helpers ------------------------------------------------

    def bump_major(self, pre: str | None = None) -> "VersionBase":
        return self._bumped("major", prerelease=pre)

    def bump_minor(self, pre: str | None = None) -> "VersionBase":
        return self._bumped("minor", prerelease=pre)

    def bump_patch(self, pre: str | None = None) -> "VersionBase":
        return self._bumped("patch", prerelease=pre)

    # ordering for “latest” checks --------------------------------------

    def _cmp_tuple(self) -> tuple[int, int, int, str]:
        pre = self.prerelease or ""
        return (self.major, self.minor, self.patch, pre)

    def __lt__(self, other: "VersionBase"):  # noqa: Dunder
        return self._cmp_tuple() < other._cmp_tuple()

    # ------------------------------------------------------------------ #
    #  Filesystem integration                                            #
    # ------------------------------------------------------------------ #

    # Regexes reused by CLI helper functions
    _PYPROJECT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r'^version\s*=\s*"(.*?)"', re.M
    )
    _INIT_RE: ClassVar[re.Pattern[str]] = re.compile(
        r'^__version__\s*=\s*"(.*?)"', re.M
    )

    # ------------------------------------------------------------------ #

    # TOP-LEVEL convenience -------------------------------------------------

    @classmethod
    def bump_at_project_root(  # noqa: C901 (clarity > line-count)
        cls,
        project_root: Path,
        part: Literal["major", "minor", "patch"],
        prerelease: str | None = None,
        dry_run: bool = False,
    ) -> "VersionBase":
        """
        Read version → bump → write pyproject & package __init__.

        Returns the **new** VersionBase.  If *dry_run* is true, nothing is
        written; you just get the calculated new version back.
        """
        pyproject_path = project_root / "pyproject.toml"
        if not pyproject_path.exists():
            raise FileNotFoundError("pyproject.toml not found at project root!")

        pkg_init = project_root / "src" / project_root.name / "__init__.py"
        if not pkg_init.exists():
            raise FileNotFoundError(f"Package __init__ not found at {pkg_init}")

        current = cls._read_version(pyproject_path)
        bumped = current._bumped(part, prerelease=prerelease)

        if not dry_run:
            cls._write_pyproject(pyproject_path, bumped)
            cls._write_init(pkg_init, bumped)

        return bumped

    # ------------------------------------------------------------------ #
    #  Private file helpers                                              #
    # ------------------------------------------------------------------ #

    @classmethod
    def _read_version(cls, pyproject: Path) -> "VersionBase":
        data = tomllib.loads(pyproject.read_text("utf8"))
        version_str: str | None = data.get("project", {}).get("version") or data.get(
            "tool", {}
        ).get("poetry", {}).get("version")
        if not version_str:
            raise ValueError("Could not find 'version' key in pyproject.toml")
        return cls.parse(version_str)

    @classmethod
    def _write_pyproject(cls, pyproject: Path, new: "VersionBase") -> None:
        txt = pyproject.read_text("utf8")
        new_txt, n = cls._PYPROJECT_RE.subn(f'version = "{new}"', txt, count=1)
        if n == 0:
            raise ValueError("Failed to update version in pyproject.toml")
        pyproject.write_text(new_txt, encoding="utf8")

    @classmethod
    def _write_init(cls, init_file: Path, new: "VersionBase") -> None:
        txt = init_file.read_text("utf8")
        if cls._INIT_RE.search(txt):
            txt, _ = cls._INIT_RE.subn(f'__version__ = "{new}"', txt, count=1)
        else:
            # Add at very top
            txt = f'__version__ = "{new}"\n' + txt
        init_file.write_text(txt, encoding="utf8")
