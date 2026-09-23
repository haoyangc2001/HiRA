"""Root-bound, read-only file lookup helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .errors import not_found, ConsoleError


def contained_path(root: Path, relative: str | Path, *, allow_absolute: bool = False) -> Path:
    candidate_input = Path(relative)
    if candidate_input.is_absolute() and not allow_absolute:
        raise ConsoleError("PATH_ABSOLUTE_FORBIDDEN", "absolute paths are not accepted", "security", 400)
    root_resolved = root.resolve()
    candidate = (candidate_input if candidate_input.is_absolute() else root_resolved / candidate_input).resolve()
    if candidate != root_resolved and root_resolved not in candidate.parents:
        raise ConsoleError("PATH_OUTSIDE_ROOT", "requested path is outside the controlled root", "security", 400)
    return candidate


def list_files(roots: Iterable[Path], extensions: set[str]) -> list[Path]:
    result: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in extensions:
                try:
                    if path.resolve().is_relative_to(root.resolve()):
                        result.append(path)
                except (OSError, ValueError):
                    continue
    return sorted(set(result), key=lambda item: str(item).lower())


def require_file(path: Path) -> Path:
    if not path.is_file():
        raise not_found(f"resource not found: {path}", {"path": str(path)})
    return path

