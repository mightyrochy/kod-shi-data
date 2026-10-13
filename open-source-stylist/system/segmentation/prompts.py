"""Segmentation prompt knowledge — single source of truth.

Two prompt domains, deliberately separate because they were validated on
different image types:

1. REGION_PROMPTS — GroundingDINO prompts for AI-GENERATED full-body images.
   Verified by V-SEG-004 (knowledge/verified.md): single general nouns work;
   compound/specific queries ("top", "shoes . sandals . wedge") return the full
   silhouette on synthetic textures. Future experiment runners that segment
   generated outputs MUST import this dict instead of redefining it. (The closed
   E-005/E-006 runners hold frozen copies — historical records, not edited.)

2. sam_prompt_for_item() — GroundingDINO prompt for a single garment's REFERENCE
   PRODUCT PHOTO, keyed by the item's type. Product photos are clean single-object
   images, a different domain from generated outputs, so the values differ from
   REGION_PROMPTS by design.

Keeping both here means the verified prompt knowledge has exactly one home and
cannot drift between consumers.
"""

from __future__ import annotations

# --- Domain 1: generated-image region prompts (V-SEG-004) -------------------

REGION_PROMPTS: dict[str, str] = {
    "person":     "person",
    "face":       "face",
    "hair":       "hair",
    "background": "background",
    "top":        "shirt",
    "bottom":     "skirt",
    "shoes":      "footwear",
    "belt":       "belt",
    "earrings":   "earrings",
    "glasses":    "glasses",
}


def generated_prompts(*regions: str) -> dict[str, str]:
    """Return a {region: prompt} subset of REGION_PROMPTS for the given regions.

    Future runners call e.g. generated_prompts("person","face","top","bottom",
    "shoes","belt","earrings") instead of hand-copying the literals.
    """
    return {r: REGION_PROMPTS[r] for r in regions}


# --- Domain 2: reference-product-photo prompts, keyed by item type ----------

# Item type -> GroundingDINO prompt for segmenting that item's product photo.
_TYPE_TO_PROMPT: dict[str, str] = {
    "top":    "top",
    "bottom": "bottom",
    "shoes":  "footwear",
    "dress":  "dress",
    "jacket": "jacket",
    "bag":    "bag",
    "hat":    "hat",
}


def sam_prompt_for_item(item: dict) -> str:
    """GroundingDINO prompt for segmenting one item's reference product photo.

    For unambiguous types, use the type map. For 'accessory'/'other' the type is
    ambiguous (a belt and earrings are both 'accessory'), so use the item_id —
    in practice a specific noun ("belt", "earrings") — falling back to the
    free-text description only if no item_id is present.
    """
    t = item.get("type")
    if t in _TYPE_TO_PROMPT:
        return _TYPE_TO_PROMPT[t]
    return item.get("item_id") or item["description"]
