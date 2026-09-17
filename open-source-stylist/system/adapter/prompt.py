"""Build the task-correct transfer prompt from frozen outfit inputs."""

from __future__ import annotations

import re
from pathlib import Path

from .panel import PROJECT_ROOT, board_labels


_COLOR_WORDS = frozenset({
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
    "black", "white", "gray", "grey", "navy", "beige", "cream", "tan", "olive",
    "maroon", "coral", "teal", "cyan", "magenta", "indigo", "violet", "lavender",
    "gold", "silver", "bronze", "copper", "turquoise", "crimson", "scarlet",
    "amber", "jade", "emerald", "sapphire", "ruby", "rose", "charcoal", "ivory",
    "champagne", "nude", "khaki", "camel", "burgundy", "mauve", "peach", "lilac",
    "mint", "sage", "mustard", "rust", "terracotta", "blush",
})


def build_prompt(
    outfit_package: dict,
    project_root: str | Path = PROJECT_ROOT,
    reference_board_variant: str | None = None,
) -> str:
    """Build a transfer prompt using board labels and the outfit layout file."""
    labels = board_labels(outfit_package, reference_board_variant)
    layout_path = Path(outfit_package["layout_path"])
    if not layout_path.is_absolute():
        layout_path = Path(project_root) / layout_path
    if not layout_path.is_file():
        raise FileNotFoundError(f"Outfit layout file does not exist: {layout_path}")

    layout_text = layout_path.read_text(encoding="utf-8").strip()
    if not layout_text:
        raise ValueError(f"Outfit layout file is empty: {layout_path}")

    prompt = "\n".join([
        "Keep this exact person: face, hair, skin tone, body proportions, pose, and background unchanged.",
        "Using the reference board (image 2), re-dress them in the outfit shown.",
        f"The board contains labeled garments: {', '.join(labels)}.",
        layout_text,
        "Take all garment appearance from the board only.",
    ])
    _check_no_color(prompt)
    return prompt


def _check_no_color(text: str) -> None:
    found = _COLOR_WORDS.intersection(re.findall(r"[a-z]+", text.lower()))
    if found:
        raise ValueError(
            f"Color words found in prompt: {sorted(found)}. "
            "Color must come from the reference board."
        )
