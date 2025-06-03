#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from functools import reduce
from itertools import chain
from logging import getLogger
from typing import TYPE_CHECKING

from utilities.git import get_repo_name, get_repo_root
from utilities.logging import basic_config

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator
    from pathlib import Path

basic_config()
_LOGGER = getLogger()


@dataclass(frozen=True, kw_only=True)
class _Replacement:
    from_: str
    to: str


def main() -> None:
    root = get_repo_root()
    _LOGGER.info(root)

    template_dashed = "dycw-template"
    template_underscore = template_dashed.replace("-", "_")

    name = get_repo_name()
    template_replacements = [
        _Replacement(from_=template_dashed, to=name.replace("_", "-")),
        _Replacement(from_=template_underscore, to=name.replace("-", "_")),
    ]

    pre_commit_replacements = [
        _Replacement(
            from_="# - id: run-bump-my-version", to="- id: run-bump-my-version"
        )
    ]
    replacements = list(chain(template_replacements, pre_commit_replacements))
    _process_file_contents(root, replacements)

    _process_file_names(root, template_replacements)


def _process_file_contents(root: Path, replacements: Iterable[_Replacement], /) -> None:
    replacements = list(replacements)
    _LOGGER.info(
        "Processing file contents: %s (%s)", root, _desc_replacements(replacements)
    )
    for path in _yield_paths(root):
        if path.is_file():
            try:
                with path.open() as fh:
                    old_contents = fh.read()
            except UnicodeDecodeError:
                _LOGGER.exception("Failed to read %s", path)
            else:
                new_contents = _apply_replacements(old_contents, replacements)
                if old_contents != new_contents:
                    _LOGGER.info("Re-writing %s...", path)
                    with path.open(mode="w") as fh:
                        _ = fh.write(new_contents)


def _desc_replacements(replacements: Iterable[_Replacement], /) -> str:
    return ", ".join(f"{r.from_}->{r.to}" for r in replacements)


def _yield_paths(root: Path, /) -> Iterator[Path]:
    skips = {root.joinpath(".direnv"), root.joinpath(".git")}
    for path in root.rglob("**/*"):
        if not any(path.is_relative_to(skip) for skip in skips):
            yield path


def _apply_replacements(text: str, replacements: Iterable[_Replacement], /) -> str:
    def inner(text: str, replacement: _Replacement, /) -> str:
        return text.replace(replacement.from_, replacement.to)

    return reduce(inner, replacements, text)


def _process_file_names(root: Path, replacements: Iterable[_Replacement], /) -> None:
    replacements = list(replacements)
    _LOGGER.info(
        "Processing file names: %s (%s)", root, _desc_replacements(replacements)
    )
    for path in list(_yield_paths(root)):
        old_stem = path.stem
        new_stem = _apply_replacements(old_stem, replacements)
        new_path = path.with_stem(new_stem)
        if path != new_path:
            _LOGGER.info("Renaming %s -> %s...", path, new_path)
            _ = path.rename(new_path)


if __name__ == "__main__":
    main()
