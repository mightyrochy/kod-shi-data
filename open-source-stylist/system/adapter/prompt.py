"""Transfer-task prompt builder for the outfit adapter.

Contract (adapter_redesign_2026-06-13 §3 + §9 decision 2):
  - Frame as an edit of image1 (person photo), not generation of a new person.
  - State preservation targets explicitly: face, hair, skin tone, body, pose, background.
  - Reference image2 (the board) by its cell labels — do NOT describe garments as free text.
  - Wire layering_order from layout_logic (was dead in the pre-2026-06-13 adapter).
  - No color words — appearance comes from the board references.
  - Negative prompt: empty (cfg=1.0 → inert under Lightning; channel tested by E-014).

Board labels in the prompt are derived the same way panel.py derives cell labels
(Path(ref_path).stem.replace("_", " ")), so the prompt and board are consistent.

Rules:
  - No color words in the generated prompt (enforced by _check_no_color).
  - No SAM/GroundingDINO prompt literals — those live in segmentation/prompts.py only.
"""

from __future__ import annotations

from pathlib import Path

# Words explicitly forbidden in generated prompts.
# Color comes from reference images, not from text — adapter rule, verified by E-007.
_COLOR_WORDS = frozenset({
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
    "black", "white", "gray", "grey", "navy", "beige", "cream", "tan", "olive",
    "maroon", "coral", "teal", "cyan", "magenta", "indigo", "violet", "lavender",
    "gold", "silver", "bronze", "copper", "turquoise", "crimson", "scarlet",
    "amber", "jade", "emerald", "sapphire", "ruby", "rose", "charcoal", "ivory",
    "champagne", "nude", "khaki", "camel", "burgundy", "mauve", "peach", "lilac",
    "mint", "sage", "mustard", "rust", "terracotta", "blush",
})


def build_prompt(outfit_package: dict) -> str:
    """Build a transfer-task generation prompt from an OutfitPackage.

    Instructs re-dressing the input person (image1) using the labeled reference
    board (image2). Preservation of person attributes is stated positively —
    cfg=1.0 makes the negative channel inert, so this is the only textual channel
    that can carry preservation under the Lightning config.

    Raises ValueError if any color word appears in the result.
    """
    items = outfit_package["items"]
    layout = outfit_package["layout_logic"]

    # Board labels: one per reference image, in outfit order.
    # Must match _cell_label() in panel.py — both use stem.replace("_", " ").
    board_labels = [
        Path(ref_path).stem.replace("_", " ")
        for item in items
        for ref_path in item["reference_image_paths"]
    ]

    # Visibility notes from layout_logic (structural, no color words expected here).
    visibility = layout.get("visibility_notes", "").strip()

    parts = [
        "Keep this exact person: face, hair, skin tone, body proportions, pose,"
        " and background — unchanged.",
        "Using the reference board (image 2), re-dress them in the outfit shown.",
        f"The board contains labeled garments: {', '.join(board_labels)}.",
    ]
    if visibility:
        parts.append(visibility)
    parts.append("Take all garment appearance from the board only.")

    prompt = " ".join(parts)
    _check_no_color(prompt)
    return prompt


def _check_no_color(text: str) -> None:
    found = _COLOR_WORDS.intersection(text.lower().split())
    if found:
        raise ValueError(
            f"Color words found in prompt (forbidden per adapter rule): {sorted(found)}. "
            "Remove them — color comes from reference images."
        )
