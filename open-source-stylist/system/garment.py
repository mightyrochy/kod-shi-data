"""General garment classification — behaviour is DERIVED from a free-text label, never a per-outfit table.

Any label ("blouse front", "green wedge sandals", "midi skirt", "trousers") is mapped to a broad CATEGORY
by keyword. Everything the rest of the system needs is derived from that category:

  - atr_region      which human-parsing region to TRY first (None -> open-vocabulary only)
  - seg_term        a short, general GroundingDINO term (kept minimal on purpose: less text -> the model
                    leans on the image, which segments more accurately)
  - fitdit_category FitDiT repair category (None -> a failing item is flagged, not auto-repaired)
  - holistic        True  -> goes through the board + QIE try-on pass
                    False -> an accessory, deferred to the OmniTry stage

Nothing is special-cased to a particular outfit. An unrecognised label falls back to a safe general
default: treated as a worn garment, isolated open-vocabulary, with no ATR/FitDiT assumptions.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GarmentSpec:
    label: str                    # raw input label, used verbatim for board captions
    category: str                 # UPPER | SKIRT | PANTS | DRESS | FOOTWEAR | ACCESSORY | OTHER
    atr_region: str | None        # ATR semantic region to try first
    seg_term: str                 # short open-vocabulary segmentation term
    fitdit_category: str | None   # FitDiT repair category
    holistic: bool                # board+QIE pass vs deferred-to-OmniTry accessory


# category -> the keywords that select it. Checked in this order; first group with a hit wins, so more
# specific garments (dress, skirt) are tested before the broad UPPER bucket.
_CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "DRESS":     ["dress", "gown", "frock", "robe"],
    "SKIRT":     ["skirt", "kilt"],
    "PANTS":     ["pant", "trouser", "jean", "legging", "short", "chino", "slack", "culotte"],
    "UPPER":     ["blouse", "shirt", "top", "tee", "t-shirt", "sweater", "jumper", "hoodie",
                  "cardigan", "jacket", "coat", "blazer", "vest", "tank", "pullover", "knit"],
    "FOOTWEAR":  ["shoe", "sandal", "heel", "boot", "sneaker", "loafer", "pump", "wedge", "flat",
                  "footwear", "mule", "espadrille"],
    "ACCESSORY": ["belt", "earring", "necklace", "bracelet", "ring", "glasses", "sunglass", "watch",
                  "bag", "purse", "clutch", "hat", "cap", "beanie", "scarf", "tie", "glove", "sock"],
}
_ATR_REGION = {"UPPER": "upper", "SKIRT": "skirt", "PANTS": "pants", "DRESS": "dress", "FOOTWEAR": "shoes"}
_FITDIT = {"UPPER": "Upper-body", "SKIRT": "Lower-body", "PANTS": "Lower-body", "DRESS": "Dresses"}
_SEG = {"UPPER": "top", "SKIRT": "skirt", "PANTS": "pants", "DRESS": "dress", "FOOTWEAR": "shoe"}


def classify(label: str) -> GarmentSpec:
    """Map any garment label to a GarmentSpec. Unknown -> OTHER (worn garment, open-vocabulary)."""
    low = label.lower()
    category = "OTHER"
    for cat, kws in _CATEGORY_KEYWORDS.items():
        if any(k in low for k in kws):
            category = cat
            break
    # OTHER: assume a worn garment we can still board; isolate by the first label word, no ATR/FitDiT.
    seg = _SEG.get(category) or (low.split()[0] if low.split() else "garment")
    return GarmentSpec(
        label=label,
        category=category,
        atr_region=_ATR_REGION.get(category),
        seg_term=seg,
        fitdit_category=_FITDIT.get(category),
        holistic=(category != "ACCESSORY"),
    )
