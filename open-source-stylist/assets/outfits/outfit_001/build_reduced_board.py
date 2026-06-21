"""Build the reduced 3-item board (blouse + skirt + wedge sandals) for the scoped QIE pass.

Same cell geometry / labels / hybrid mask+crop approach as prepare_reference_boards.py, but only the
three items that go through the holistic QIE pass (belt + earrings are added later by OmniTry).

    python assets/outfits/outfit_001/build_reduced_board.py
"""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUTFIT_DIR = Path(__file__).resolve().parent
ROOT = OUTFIT_DIR.parents[2]
E001 = ROOT / "experiments/001_segmentation_masks/results"
BOARDS_DIR = OUTFIT_DIR / "reference_boards"
CELL_SIZE, MAX_COLS, LABEL_BAND = 256, 3, 22
try:
    FONT = ImageFont.load_default(size=14)
except TypeError:
    FONT = ImageFont.load_default()

# (label, source webp, mask png, crop png) — hybrid mask+crop, 3 items only.
CELLS = [
    ("blouse front mask", "blouse_front.webp", OUTFIT_DIR / "reference_masks/blouse_front_buttons.png",
     "crops/blouse front crop.png", "mask"),
    ("blouse front crop", None, None, "crops/blouse front crop.png", "crop"),
    ("skirt front mask", "skirt_front.webp", E001 / "outfit_001_skirt_front/skirt.png",
     "crops/skirt_front crop.png", "mask"),
    ("skirt front crop", None, None, "crops/skirt_front crop.png", "crop"),
    ("shoes mask", "shoes_wedge.webp", E001 / "outfit_001_shoes_wedge/shoes.png",
     "crops/shoes crop.png", "mask"),
    ("shoes crop", None, None, "crops/shoes crop.png", "crop"),
]


def _masked(source: Path, mask_path: Path) -> Image.Image:
    img = Image.open(source).convert("RGBA")
    mask = Image.open(mask_path).convert("L")
    if mask.size != img.size:
        raise ValueError(f"mask {mask.size} != source {img.size} for {source}")
    bbox = mask.getbbox()
    data = np.array(img)
    data[:, :, 3] = np.array(mask)
    return Image.fromarray(data).crop(bbox)


def _cell(image: Image.Image, label: str) -> Image.Image:
    image = image.copy()
    image.thumbnail((CELL_SIZE, CELL_SIZE - LABEL_BAND), Image.LANCZOS)
    cell = Image.new("RGBA", (CELL_SIZE, CELL_SIZE), (255, 255, 255, 255))
    cell.paste(image, ((CELL_SIZE - image.width) // 2, (CELL_SIZE - LABEL_BAND - image.height) // 2),
               mask=image.getchannel("A") if image.mode == "RGBA" else None)
    draw = ImageDraw.Draw(cell)
    draw.rectangle((0, CELL_SIZE - LABEL_BAND, CELL_SIZE, CELL_SIZE), fill=(255, 255, 255, 255))
    b = draw.textbbox((0, 0), label, font=FONT)
    draw.text(((CELL_SIZE - (b[2] - b[0])) // 2, CELL_SIZE - LABEL_BAND + (LABEL_BAND - (b[3] - b[1])) // 2),
              label, fill=(0, 0, 0, 255), font=FONT)
    return cell


def main() -> None:
    rendered = []
    for label, src, mask, crop, mode in CELLS:
        if mode == "mask":
            image = _masked(OUTFIT_DIR / src, Path(mask))
        else:
            image = Image.open(OUTFIT_DIR / crop).convert("RGBA")
        rendered.append(_cell(image, label))
    cols = min(len(rendered), MAX_COLS)
    rows = (len(rendered) + cols - 1) // cols
    board = Image.new("RGB", (cols * CELL_SIZE, rows * CELL_SIZE), (255, 255, 255))
    for i, c in enumerate(rendered):
        r, col = divmod(i, cols)
        board.paste(c.convert("RGB"), (col * CELL_SIZE, r * CELL_SIZE))
    BOARDS_DIR.mkdir(parents=True, exist_ok=True)
    out = BOARDS_DIR / "garments3_hybrid.png"
    board.save(out, format="PNG", compress_level=9)
    sha = hashlib.sha256(out.read_bytes()).hexdigest()
    print(f"built {out.relative_to(ROOT)}  {board.size}  sha256={sha[:16]}")
    print("labels:", [c[0] for c in CELLS])


if __name__ == "__main__":
    main()
