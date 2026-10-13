"""Prepare the two frozen reference boards used by E-007.

This is an offline asset-preparation command. Generation code never calls it.
Both boards use the same sources, order, cell geometry, and labels. The only
experimental variable is how each source is isolated:

* masked_crops: original product photo plus the frozen E-001 garment mask;
* rectangular_crops: owner-prepared rectangular crops from ``crops/``;
* hybrid_mask_crop: paired mask/crop references selected after E-007 v2, including
  a source-specific repair that restores the blouse-front buttons.

Run from the repository root only when source assets intentionally change:

    python assets/outfits/outfit_001/prepare_reference_boards.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[3]
OUTFIT_DIR = Path(__file__).resolve().parent
BOARDS_DIR = OUTFIT_DIR / "reference_boards"
REFERENCE_MASKS_DIR = OUTFIT_DIR / "reference_masks"
E001 = ROOT / "experiments/001_segmentation_masks/results"

CELL_SIZE = 256
MAX_COLS = 3
LABEL_BAND_HEIGHT = 22

try:
    LABEL_FONT = ImageFont.load_default(size=14)
except TypeError:
    LABEL_FONT = ImageFont.load_default()


CELLS = [
    ("blouse front", "blouse_front.webp", "outfit_001_blouse_front/blouse.png", "blouse front crop.png"),
    ("blouse back", "blouse_back.webp", "outfit_001_blouse_back/blouse.png", "blouse back crop.png"),
    ("skirt front", "skirt_front.webp", "outfit_001_skirt_front/skirt.png", "skirt_front crop.png"),
    ("skirt back", "skirt_back.webp", "outfit_001_skirt_back/skirt.png", "skirt_back crop.png"),
    ("belt", "belt.jpg", "outfit_001_belt/belt.png", "belt crop.png"),
    ("shoes", "shoes_wedge.webp", "outfit_001_shoes_wedge/shoes.png", "shoes crop.png"),
    ("earrings", "earrings_disc.webp", "outfit_001_earrings_disc/earrings.png", "earings crop.png"),
]

HYBRID_CELLS = [
    ("blouse front mask", "masked", CELLS[0], "corrected_blouse_front"),
    ("blouse front crop", "rectangular", CELLS[0], None),
    ("skirt front mask", "masked", CELLS[2], None),
    ("skirt front crop", "rectangular", CELLS[2], None),
    ("belt mask", "masked", CELLS[4], None),
    ("earrings mask", "masked", CELLS[6], None),
    ("earrings crop", "rectangular", CELLS[6], None),
    ("shoes mask", "masked", CELLS[5], None),
    ("shoes crop", "rectangular", CELLS[5], None),
]

# Source-specific manual repair: recover the pale front buttons excluded by the
# original GroundingDINO+SAM mask without filling the V neckline or blouse opening.
BUTTON_REPAIR_ROI = (398, 590, 438, 795)  # x1, y1, x2, y2 in blouse_front.webp
BUTTON_MIN_GRAY = 185


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _paths(cell: tuple[str, str, str, str]) -> tuple[str, Path, Path, Path]:
    label, source_name, mask_rel, crop_name = cell
    return label, OUTFIT_DIR / source_name, E001 / mask_rel, OUTFIT_DIR / "crops" / crop_name


def _prepare_corrected_blouse_front_mask() -> Path:
    _, source, original_mask, _ = _paths(CELLS[0])
    source_bgr = cv2.imread(str(source), cv2.IMREAD_COLOR)
    mask = cv2.imread(str(original_mask), cv2.IMREAD_GRAYSCALE)
    if source_bgr is None or mask is None:
        raise FileNotFoundError("Cannot load blouse-front source or original mask")
    if source_bgr.shape[:2] != mask.shape:
        raise ValueError("Blouse-front source and mask dimensions do not match")

    gray = cv2.cvtColor(source_bgr, cv2.COLOR_BGR2GRAY)
    x1, y1, x2, y2 = BUTTON_REPAIR_ROI
    roi = np.zeros_like(mask, dtype=np.uint8)
    roi[y1:y2, x1:x2] = 255
    recovered = ((mask <= 127) & (gray >= BUTTON_MIN_GRAY) & (roi > 0)).astype(np.uint8) * 255
    recovered = cv2.dilate(
        recovered,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        iterations=1,
    )
    corrected = np.maximum(mask, recovered)
    added_pixels = int(np.count_nonzero((corrected > 127) & (mask <= 127)))
    if added_pixels < 1000:
        raise RuntimeError(f"Button repair recovered too few pixels: {added_pixels}")

    REFERENCE_MASKS_DIR.mkdir(parents=True, exist_ok=True)
    output = REFERENCE_MASKS_DIR / "blouse_front_buttons.png"
    if not cv2.imwrite(str(output), corrected, [cv2.IMWRITE_PNG_COMPRESSION, 9]):
        raise RuntimeError(f"Could not write corrected blouse mask: {output}")
    return output


def _masked_image(source: Path, mask_path: Path) -> Image.Image:
    with Image.open(source) as source_image:
        image = source_image.convert("RGBA")
    with Image.open(mask_path) as mask_image:
        mask = mask_image.convert("L")
    if mask.size != image.size:
        raise ValueError(f"Mask size {mask.size} does not match {source}: {image.size}")
    bbox = mask.getbbox()
    if bbox is None:
        raise ValueError(f"Empty frozen mask: {mask_path}")

    data = np.array(image)
    data[:, :, 3] = np.array(mask)
    return Image.fromarray(data).crop(bbox)


def _render_cell(image: Image.Image, label: str) -> Image.Image:
    image = image.copy()
    image.thumbnail((CELL_SIZE, CELL_SIZE - LABEL_BAND_HEIGHT), Image.LANCZOS)

    cell = Image.new("RGBA", (CELL_SIZE, CELL_SIZE), (255, 255, 255, 255))
    x = (CELL_SIZE - image.width) // 2
    y = (CELL_SIZE - LABEL_BAND_HEIGHT - image.height) // 2
    cell.paste(image, (x, y), mask=image.getchannel("A") if image.mode == "RGBA" else None)

    draw = ImageDraw.Draw(cell)
    draw.rectangle((0, CELL_SIZE - LABEL_BAND_HEIGHT, CELL_SIZE, CELL_SIZE), fill=(255, 255, 255, 255))
    bbox = draw.textbbox((0, 0), label, font=LABEL_FONT)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    draw.text(
        ((CELL_SIZE - text_width) // 2, CELL_SIZE - LABEL_BAND_HEIGHT + (LABEL_BAND_HEIGHT - text_height) // 2),
        label,
        fill=(0, 0, 0, 255),
        font=LABEL_FONT,
    )
    return cell


def _build_board(kind: str, corrected_blouse_mask: Path) -> tuple[Path, list[str]]:
    if kind not in {"masked_crops", "rectangular_crops", "hybrid_mask_crop"}:
        raise ValueError(f"Unknown board kind: {kind}")

    rendered = []
    labels = []
    if kind == "hybrid_mask_crop":
        for label, mode, raw_cell, mask_override in HYBRID_CELLS:
            _, source, mask, crop = _paths(raw_cell)
            if mask_override == "corrected_blouse_front":
                mask = corrected_blouse_mask
            for path in (source, mask, crop):
                if not path.is_file():
                    raise FileNotFoundError(path)
            if mode == "masked":
                image = _masked_image(source, mask)
            else:
                with Image.open(crop) as crop_image:
                    image = crop_image.convert("RGBA")
            rendered.append(_render_cell(image, label))
            labels.append(label)
    else:
        for raw_cell in CELLS:
            label, source, mask, crop = _paths(raw_cell)
            for path in (source, mask, crop):
                if not path.is_file():
                    raise FileNotFoundError(path)
            if kind == "masked_crops":
                image = _masked_image(source, mask)
            else:
                with Image.open(crop) as crop_image:
                    image = crop_image.convert("RGBA")
            rendered.append(_render_cell(image, label))
            labels.append(label)

    cols = min(len(rendered), MAX_COLS)
    rows = (len(rendered) + cols - 1) // cols
    board = Image.new("RGB", (cols * CELL_SIZE, rows * CELL_SIZE), (255, 255, 255))
    for index, cell in enumerate(rendered):
        row, col = divmod(index, cols)
        board.paste(cell.convert("RGB"), (col * CELL_SIZE, row * CELL_SIZE))

    BOARDS_DIR.mkdir(parents=True, exist_ok=True)
    output = BOARDS_DIR / f"{kind}.png"
    board.save(output, format="PNG", optimize=False, compress_level=9)
    return output, labels


def main() -> None:
    corrected_blouse_mask = _prepare_corrected_blouse_front_mask()
    built = {
        kind: _build_board(kind, corrected_blouse_mask)
        for kind in ("masked_crops", "rectangular_crops", "hybrid_mask_crop")
    }
    manifest = {
        "schema_version": "1.0",
        "frozen": True,
        "cell_size": CELL_SIZE,
        "columns": MAX_COLS,
        "labels": [cell[0] for cell in CELLS],
        "boards": {
            kind: {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": _sha256(path),
                "labels": labels,
            }
            for kind, (path, labels) in built.items()
        },
        "corrected_masks": {
            "blouse_front_buttons": {
                "path": corrected_blouse_mask.relative_to(ROOT).as_posix(),
                "sha256": _sha256(corrected_blouse_mask),
                "base_mask": _paths(CELLS[0])[2].relative_to(ROOT).as_posix(),
                "repair_roi": list(BUTTON_REPAIR_ROI),
                "minimum_gray": BUTTON_MIN_GRAY,
            }
        },
        "inputs": [
            {
                "label": label,
                "source": source.relative_to(ROOT).as_posix(),
                "mask": mask.relative_to(ROOT).as_posix(),
                "rectangular_crop": crop.relative_to(ROOT).as_posix(),
            }
            for label, source, mask, crop in map(_paths, CELLS)
        ],
    }
    manifest_path = BOARDS_DIR / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    for kind, (path, _) in built.items():
        print(f"{kind}: {path.relative_to(ROOT)} sha256={_sha256(path)}")
    print(
        "corrected blouse mask: "
        f"{corrected_blouse_mask.relative_to(ROOT)} sha256={_sha256(corrected_blouse_mask)}"
    )
    print(f"manifest: {manifest_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
