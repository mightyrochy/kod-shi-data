"""Reference panel builder.

Crops each garment reference image to the garment region (via segmentation),
composites a text label into each cell (adapter_redesign_2026-06-13 §9 decision 1),
then tiles everything into a single panel image for use as the reference
conditioning input to QIE-2511.

Label per cell = Path(ref_path).stem with underscores replaced by spaces,
e.g. "blouse_front.webp" → "blouse front". QIE reads in-image text; the labels
align the board with the transfer prompt's garment references.

Segmentation requires a live ComfyUI instance.  VRAM note: call this before
loading QIE-2511 — SAM/GroundingDINO and QIE-2511 fp8 together exceed 16GB.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..clients.comfyui import ComfyUIClient
from ..segmentation.grounded_sam import segment
from ..segmentation.prompts import sam_prompt_for_item

# Bitmap font — loaded once at import time.
# Pillow 10.1+ supports load_default(size=N); older versions ignore the arg.
try:
    _LABEL_FONT = ImageFont.load_default(size=14)
except TypeError:
    _LABEL_FONT = ImageFont.load_default()

# Height of the white label band at the bottom of each cell (pixels).
_LABEL_BAND_H = 22


def build_panel(
    outfit_package: dict,
    output_dir: str | Path,
    client: ComfyUIClient,
    cell_size: int = 256,
    max_cols: int = 3,
) -> Path:
    """Build a labeled, tiled reference panel from all garment reference images.

    For each item in the outfit, each reference image is segmented to isolate
    the garment region. A text label (derived from the reference file name) is
    rendered at the bottom of each cell so the transfer prompt can reference
    garments by their board label.  The resulting crops are tiled into a grid
    and saved as ``reference_panel.png`` in output_dir.

    Returns the path to the saved panel PNG.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    masks_dir = output_dir / "seg_masks"
    masks_dir.mkdir(parents=True, exist_ok=True)

    crops: list[Image.Image] = []
    for item in outfit_package["items"]:
        sam_prompt = sam_prompt_for_item(item)
        for ref_path in item["reference_image_paths"]:
            crop = _crop_garment(ref_path, sam_prompt, item["item_id"], masks_dir, client, cell_size)
            label = _cell_label(ref_path)
            crops.append(_render_label(crop, label))

    panel_path = output_dir / "reference_panel.png"
    _tile_panel(crops, panel_path, cell_size, max_cols)
    return panel_path


def _crop_garment(
    ref_path: str,
    sam_prompt: str,
    label: str,
    masks_dir: Path,
    client: ComfyUIClient,
    cell_size: int,
) -> Image.Image:
    """Segment one reference image and return a cell_size×cell_size crop."""
    ref_path = Path(ref_path)
    label_safe = f"{label}_{ref_path.stem}"

    mask_results = segment(
        image_path=ref_path,
        prompts={label_safe: sam_prompt},
        client=client,
        output_dir=masks_dir,
    )
    mask_path = Path(mask_results[label_safe])

    img = Image.open(ref_path).convert("RGBA")
    mask = Image.open(mask_path).convert("L")

    bbox = mask.getbbox()
    if bbox is None:
        # Segmentation produced no foreground. Fall back to the full, OPAQUE
        # product image — a single-garment product photo is mostly the garment.
        # (Do NOT apply the empty mask as alpha: that yields a blank cell, which
        # silently drops the garment from the panel.)
        return _fit_to_cell(img, cell_size)

    mask_arr = np.array(mask)
    img_arr = np.array(img)
    img_arr[:, :, 3] = mask_arr
    masked = Image.fromarray(img_arr).crop(bbox)

    return _fit_to_cell(masked, cell_size)


def _cell_label(ref_path: str | Path) -> str:
    """Derive cell label from the reference file name stem.

    "blouse_front.webp" → "blouse front", "belt.jpg" → "belt".
    Must match the label list emitted by prompt.py's build_prompt so the
    transfer prompt and the board are consistent.
    """
    return Path(ref_path).stem.replace("_", " ")


def _render_label(cell: Image.Image, label: str) -> Image.Image:
    """Draw a white label band at the bottom of a cell image.

    Returns a copy of the cell with a _LABEL_BAND_H-pixel white strip at the
    bottom containing the label text centered in black.
    """
    cell = cell.copy()
    draw = ImageDraw.Draw(cell)
    w, h = cell.size
    # White background band
    draw.rectangle([0, h - _LABEL_BAND_H, w, h], fill=(255, 255, 255, 255))
    # Centered label text
    bbox = draw.textbbox((0, 0), label, font=_LABEL_FONT)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = max(0, (w - text_w) // 2)
    y = h - _LABEL_BAND_H + max(0, (_LABEL_BAND_H - text_h) // 2)
    draw.text((x, y), label, fill=(0, 0, 0), font=_LABEL_FONT)
    return cell


def _fit_to_cell(img: Image.Image, cell_size: int) -> Image.Image:
    """Resize img (keeping aspect ratio) into a cell_size×cell_size square with white padding."""
    img.thumbnail((cell_size, cell_size), Image.LANCZOS)
    cell = Image.new("RGBA", (cell_size, cell_size), (255, 255, 255, 255))
    x = (cell_size - img.width) // 2
    y = (cell_size - img.height) // 2
    cell.paste(img, (x, y), mask=img.split()[3] if img.mode == "RGBA" else None)
    return cell


def _tile_panel(crops: list[Image.Image], out_path: Path, cell_size: int, max_cols: int):
    n = len(crops)
    if n == 0:
        raise ValueError("No crops to tile — outfit_package has no reference images.")
    cols = min(n, max_cols)
    rows = math.ceil(n / cols)
    panel = Image.new("RGB", (cols * cell_size, rows * cell_size), (255, 255, 255))
    for i, crop in enumerate(crops):
        row, col = divmod(i, cols)
        # Flatten RGBA → RGB over white background
        bg = Image.new("RGB", (cell_size, cell_size), (255, 255, 255))
        if crop.mode == "RGBA":
            bg.paste(crop, mask=crop.split()[3])
        else:
            bg.paste(crop)
        panel.paste(bg, (col * cell_size, row * cell_size))
    panel.save(out_path)
