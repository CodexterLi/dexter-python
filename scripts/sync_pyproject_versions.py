#!/usr/bin/env python3
"""Sync direct dependency lower bounds in pyproject.toml from uv.lock."""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

PYPROJECT_PATH = Path("pyproject.toml")
LOCK_PATH = Path("uv.lock")

PACKAGE_BLOCK_RE = re.compile(r"^\[\[package\]\]\n(.*?)(?=^\[\[package\]\]|\Z)", re.MULTILINE | re.DOTALL)
NAME_RE = re.compile(r'^name = "([^"]+)"$', re.MULTILINE)
VERSION_RE = re.compile(r'^version = "([^"]+)"$', re.MULTILINE)
DEP_NAME_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)")
QUOTE_RE = re.compile(r'"([^"]+)"')
SPEC_RE = re.compile(
    r"(?P<head>^[^<>=!~;\s]+(?:\[[^\]]+\])?)(?P<spec>\s*(?:>=|==|~=|<=|>|<|!=)[^;]*)?(?P<marker>;.*)?$"
)


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _read_locked_versions() -> dict[str, str]:
    text = LOCK_PATH.read_text(encoding="utf-8")
    versions: dict[str, str] = {}

    for block_match in PACKAGE_BLOCK_RE.finditer(text):
        block = block_match.group(1)
        name_match = NAME_RE.search(block)
        version_match = VERSION_RE.search(block)
        if not name_match or not version_match:
            continue
        versions[_normalize_name(name_match.group(1))] = version_match.group(1)

    return versions


def _direct_dependencies() -> set[str]:
    data = tomllib.loads(PYPROJECT_PATH.read_text(encoding="utf-8"))
    deps: set[str] = set(data.get("project", {}).get("dependencies", []))

    for group_deps in data.get("dependency-groups", {}).values():
        if isinstance(group_deps, list):
            deps.update(dep for dep in group_deps if isinstance(dep, str))

    return deps


def _dependency_name(requirement: str) -> str | None:
    match = DEP_NAME_RE.match(requirement)
    if not match:
        return None
    return _normalize_name(match.group(1))


def _updated_requirement(requirement: str, locked_versions: dict[str, str]) -> str:
    name = _dependency_name(requirement)
    if not name:
        return requirement

    locked_version = locked_versions.get(name)
    if not locked_version:
        return requirement

    match = SPEC_RE.match(requirement)
    if not match:
        return requirement

    marker = match.group("marker") or ""
    return f"{match.group('head')}>={locked_version}{marker}"


def main() -> None:
    locked_versions = _read_locked_versions()
    direct_deps = _direct_dependencies()
    replacements = {
        dep: updated for dep in direct_deps if (updated := _updated_requirement(dep, locked_versions)) != dep
    }

    if not replacements:
        print("pyproject.toml dependency lower bounds already match uv.lock")
        return

    text = PYPROJECT_PATH.read_text(encoding="utf-8")

    def replace_quoted(match: re.Match[str]) -> str:
        value = match.group(1)
        return f'"{replacements.get(value, value)}"'

    PYPROJECT_PATH.write_text(QUOTE_RE.sub(replace_quoted, text), encoding="utf-8")

    for old, new in sorted(replacements.items()):
        print(f"{old} -> {new}")


if __name__ == "__main__":
    main()
