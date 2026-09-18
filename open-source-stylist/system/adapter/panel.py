"""Resolve and verify frozen reference-board assets.

Board preparation is deliberately outside the generation path. A generation
selects one already-reviewed PNG from the OutfitPackage and verifies its SHA-256.
It never segments references or rebuilds a board.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def resolve_board(outfit_package: dict, variant: str, project_root: str | Path = PROJECT_ROOT) -> Path:
    """Return a frozen board path after checking its recorded SHA-256."""
    board = outfit_package.get("reference_board")
    if not isinstance(board, dict):
        raise ValueError("OutfitPackage is missing reference_board configuration")

    variants = board.get("variants", {})
    if variant not in variants:
        available = ", ".join(sorted(variants)) or "none"
        raise ValueError(f"Unknown reference-board variant {variant!r}; available: {available}")

    spec = variants[variant]
    path = Path(spec["path"])
    if not path.is_absolute():
        path = Path(project_root) / path
    path = path.resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Frozen reference board does not exist: {path}")

    expected = spec.get("sha256", "").lower()
    actual = file_sha256(path)
    if expected and actual != expected:
        raise RuntimeError(
            f"Frozen reference board changed: {path}\n"
            f"expected sha256={expected}\nactual   sha256={actual}"
        )
    return path


def board_labels(outfit_package: dict, variant: str | None = None) -> list[str]:
    """Return the labels rendered on the selected board variant."""
    board = outfit_package.get("reference_board", {})
    labels = board.get("labels")
    if variant is not None:
        spec = board.get("variants", {}).get(variant)
        if spec is None:
            available = ", ".join(sorted(board.get("variants", {}))) or "none"
            raise ValueError(f"Unknown reference-board variant {variant!r}; available: {available}")
        labels = spec.get("labels", labels)
    if not isinstance(labels, list) or not labels or not all(isinstance(x, str) and x.strip() for x in labels):
        raise ValueError("reference_board.labels must be a non-empty list of strings")
    return [label.strip() for label in labels]


def file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_panel(*args, **kwargs) -> Path:
    """Reject the removed in-loop board-building path.

    Kept only so closed historical runners fail with an explicit explanation
    instead of an import error.
    """
    raise RuntimeError(
        "In-loop reference-board building was removed. "
        "Use resolve_board(outfit_package, variant) with a frozen board asset."
    )
