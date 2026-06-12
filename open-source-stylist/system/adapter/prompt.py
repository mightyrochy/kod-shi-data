"""Structural prompt builder for the outfit adapter.

Rule: no color words in the generated prompt (adapter constraint, pending E-007).
Color and texture come exclusively from reference images.
"""

from __future__ import annotations

# Words explicitly forbidden in generated prompts.
# This is enforced at the adapter boundary, not at runtime — callers who
# bypass build_prompt and write their own prompts must follow the same rule.
_COLOR_WORDS = frozenset({
    "red", "blue", "green", "yellow", "orange", "purple", "pink", "brown",
    "black", "white", "gray", "grey", "navy", "beige", "cream", "tan", "olive",
    "maroon", "coral", "teal", "cyan", "magenta", "indigo", "violet", "lavender",
    "gold", "silver", "bronze", "copper", "turquoise", "crimson", "scarlet",
    "amber", "jade", "emerald", "sapphire", "ruby", "rose", "charcoal", "ivory",
    "champagne", "nude", "khaki", "camel", "burgundy", "mauve", "peach", "lilac",
    "mint", "sage", "mustard", "rust", "terracotta", "blush",
})

# SAM text prompt template per item type.
# Values are GroundingDINO multi-label queries (period-separated phrases).
_ITEM_TYPE_TO_SAM_PROMPT: dict[str, str] = {
    "top": "top",
    "bottom": "bottom",
    "dress": "dress",
    "jacket": "jacket",
    "shoes": "footwear",
    "accessory": "accessory",
    "bag": "bag",
    "hat": "hat",
    "other": "clothing",
}


def build_prompt(outfit_package: dict) -> str:
    """Build a structural generation prompt from an OutfitPackage.

    Describes outfit structure and layering only — no color words.
    Raises ValueError if any color word is detected in the result.
    """
    items = outfit_package["items"]
    layout = outfit_package["layout_logic"]

    item_phrases = [item["description"] for item in items]
    wearing_clause = ", ".join(item_phrases)
    visibility = layout.get("visibility_notes", "")

    prompt = f"A person wearing {wearing_clause}. {visibility} Full body, standing pose.".strip()

    _check_no_color(prompt)
    return prompt


def item_sam_prompt(item: dict) -> str:
    """Return a GroundingDINO text prompt appropriate for an item's type.

    Falls back to the item's own description if the type is not in the table.
    """
    return _ITEM_TYPE_TO_SAM_PROMPT.get(item["type"], item["description"])


def _check_no_color(text: str) -> None:
    found = _COLOR_WORDS.intersection(text.lower().split())
    if found:
        raise ValueError(
            f"Color words found in prompt (forbidden per adapter rule): {sorted(found)}. "
            "Remove them — color comes from reference images."
        )
