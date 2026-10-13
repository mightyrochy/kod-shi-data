"""OutfitPackage to GenerationRequest formatting."""

from __future__ import annotations

import uuid
from pathlib import Path

from PIL import Image

from .panel import resolve_board
from .prompt import build_prompt


_DEFAULT_MAX_SIDE = 1024
_RESOLUTION_STEP = 16


def build_generation_request(
    outfit_package: dict,
    person_image_path: str | Path,
    reference_board_variant: str,
    seed: int,
    steps: int = 4,
    resolution: tuple[int, int] | None = None,
    engine: str = "qie-2511-lightning",
    cfg: float = 1.0,
    denoise: float = 1.0,
) -> dict:
    """Build a request that points to an existing, hash-verified board."""
    person_path = Path(person_image_path).resolve()
    if not person_path.is_file():
        raise FileNotFoundError(f"Person image does not exist: {person_path}")

    panel_path = resolve_board(outfit_package, reference_board_variant)
    prompt = build_prompt(outfit_package, reference_board_variant=reference_board_variant)

    if resolution is None:
        resolution = _auto_resolution(person_path)
    width, height = resolution
    if steps < 1:
        raise ValueError("steps must be at least 1")
    if cfg < 0:
        raise ValueError("cfg must be non-negative")
    if width < 64 or height < 64 or width % 16 or height % 16:
        raise ValueError("resolution must be at least 64x64 and divisible by 16")

    return {
        "schema_version": "1.0",
        "request_id": uuid.uuid4().hex[:12],
        "outfit_id": outfit_package["outfit_id"],
        "person_image_path": str(person_path),
        "reference_panel_path": str(panel_path),
        "reference_board_variant": reference_board_variant,
        "prompt": prompt,
        "negative_prompt": "",
        "engine": engine,
        "params": {
            "steps": steps,
            "seed": seed,
            "width": width,
            "height": height,
            "cfg": cfg,
            "sampler": "euler",
            "scheduler": "simple",
            "denoise": denoise,
        },
    }


def _auto_resolution(person_image_path: str | Path, max_side: int = _DEFAULT_MAX_SIDE) -> tuple[int, int]:
    with Image.open(person_image_path) as image:
        width, height = image.size
    scale = max_side / max(width, height)
    width_out = max(_RESOLUTION_STEP, round(width * scale / _RESOLUTION_STEP) * _RESOLUTION_STEP)
    height_out = max(_RESOLUTION_STEP, round(height * scale / _RESOLUTION_STEP) * _RESOLUTION_STEP)
    return width_out, height_out
