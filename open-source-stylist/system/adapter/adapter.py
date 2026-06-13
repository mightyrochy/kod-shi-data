"""Outfit Adapter v0 — OutfitPackage → GenerationRequest.

Entry point for Stage 2.  Pure formatting: no styling decisions.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from PIL import Image

from ..clients.comfyui import ComfyUIClient
from .panel import build_panel
from .prompt import build_prompt

# Longest side of the person image is scaled to this value (multiples of 16).
_DEFAULT_MAX_SIDE = 1024
_RESOLUTION_STEP = 16


def build_generation_request(
    outfit_package: dict,
    person_image_path: str | Path,
    output_dir: str | Path,
    client: ComfyUIClient,
    seed: int,
    steps: int = 40,
    resolution: tuple[int, int] | None = None,
    engine: str = "qie-2511",
) -> dict:
    """Build a GenerationRequest from an OutfitPackage.

    Builds the reference panel (requires ComfyUI for segmentation), then
    assembles and validates a GenerationRequest dict.

    Args:
        outfit_package: validated OutfitPackage dict.
        person_image_path: path to the person photo.
        output_dir: directory for panel output and intermediate files.
        client: live ComfyUIClient (used for panel segmentation).
        seed: generation seed.
        steps: sampler steps (40 = full model, no Lightning).
        resolution: explicit (width, height) or None for auto from person image.
        engine: engine identifier matching GenerationRequest schema enum.

    Returns:
        A GenerationRequest dict ready for JSON serialisation.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    panels_dir = output_dir / "panels"
    panel_path = build_panel(outfit_package, panels_dir, client)

    prompt = build_prompt(outfit_package)

    if resolution is None:
        resolution = _auto_resolution(person_image_path)
    width, height = resolution

    return {
        "schema_version": "1.0",
        "request_id": uuid.uuid4().hex[:12],
        "outfit_id": outfit_package["outfit_id"],
        "person_image_path": str(Path(person_image_path).resolve()),
        "reference_panel_path": str(panel_path.resolve()),
        "prompt": prompt,
        # Empty per E-007 protocol — cfg=1.0 (Lightning) makes negatives inert.
        # Wire negative_constraints here when testing cfg>1 rows (E-014).
        "negative_prompt": "",
        "engine": engine,
        "params": {
            "steps": steps,
            "seed": seed,
            "width": width,
            "height": height,
            "cfg": 1.0,
            "sampler": "euler",
            "scheduler": "simple",
        },
    }


def _auto_resolution(person_image_path: str | Path, max_side: int = _DEFAULT_MAX_SIDE) -> tuple[int, int]:
    img = Image.open(person_image_path)
    w, h = img.size
    scale = max_side / max(w, h)
    w2 = round(w * scale / _RESOLUTION_STEP) * _RESOLUTION_STEP
    h2 = round(h * scale / _RESOLUTION_STEP) * _RESOLUTION_STEP
    return w2, h2
