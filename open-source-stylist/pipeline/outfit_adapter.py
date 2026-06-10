"""Outfit adapter: reference panel assembly + QIE-2511 workflow preparation.

Responsibilities:
- Build a reference panel image (PIL composite) from individual garment images.
- Upload person + reference images to ComfyUI.
- Fill the workflow template with actual image names, prompt, dimensions, seed.
- Return a ready-to-submit workflow dict.

Keeps no state between calls; each prepare() is a self-contained operation.
"""

import json
import random
import tempfile
from pathlib import Path

from PIL import Image

from pipeline.comfyui_client import ComfyUIClient

WORKFLOW_TEMPLATE = Path(__file__).parent / "workflows" / "qie2511_vton.json"

# tile size for each garment in the reference panel
TILE_W, TILE_H = 512, 512


def build_reference_panel(image_paths: list[Path], tile_w: int = TILE_W, tile_h: int = TILE_H) -> Image.Image:
    """Lay images side-by-side, each scaled to (tile_w, tile_h), white background."""
    if not image_paths:
        raise ValueError("need at least one image for the reference panel")
    tiles = []
    for p in image_paths:
        img = Image.open(p).convert("RGBA")
        img.thumbnail((tile_w, tile_h), Image.LANCZOS)
        canvas = Image.new("RGBA", (tile_w, tile_h), (255, 255, 255, 255))
        offset = ((tile_w - img.width) // 2, (tile_h - img.height) // 2)
        canvas.paste(img, offset, img if img.mode == "RGBA" else None)
        tiles.append(canvas.convert("RGB"))
    total_w = tile_w * len(tiles)
    panel = Image.new("RGB", (total_w, tile_h), (255, 255, 255))
    for i, tile in enumerate(tiles):
        panel.paste(tile, (i * tile_w, 0))
    return panel


def _fill_workflow(template: dict, replacements: dict) -> dict:
    """Replace __KEY__ placeholders (including their surrounding quotes) in the template.

    Integer and float replacements strip the surrounding quotes so the JSON type
    is preserved.  String replacements keep the quotes.
    """
    text = json.dumps(template)
    for key, value in replacements.items():
        placeholder = f'"__{key}__"'
        if isinstance(value, str):
            text = text.replace(placeholder, json.dumps(value))
        else:
            text = text.replace(placeholder, json.dumps(value))
    return json.loads(text)


def _detect_image_size(path: Path) -> tuple[int, int]:
    """Return (width, height) rounded to the nearest multiple of 16."""
    with Image.open(path) as img:
        w, h = img.size
    return (w // 16) * 16, (h // 16) * 16


def _select_reference_images(outfit_package: dict, max_images: int = 4) -> list[Path]:
    """Pick the most visually important garment images from the outfit package.

    Sorts by visibility_priority descending, takes the first reference image of
    each item, up to max_images.  Paths are resolved relative to the package file
    location (outfit_package must include a _base_dir key, set by the caller).
    """
    base = Path(outfit_package.get("_base_dir", "."))
    items = sorted(
        outfit_package.get("items", []),
        key=lambda x: x.get("visibility_priority", 0),
        reverse=True,
    )
    paths: list[Path] = []
    for item in items:
        refs = item.get("reference_images", [])
        if not refs:
            continue
        p = (base / refs[0]).resolve()
        if p.exists():
            paths.append(p)
        if len(paths) >= max_images:
            break
    return paths


class OutfitAdapter:
    def __init__(self, comfy: ComfyUIClient, workflow_path: Path = WORKFLOW_TEMPLATE):
        self.comfy = comfy
        with open(workflow_path, encoding="utf-8") as f:
            self._template = json.load(f)

    def prepare(
        self,
        person_image: Path,
        reference_image: Path,
        prompt: str,
        *,
        seed: int | None = None,
        output_prefix: str = "qie_vton",
    ) -> dict:
        """Upload images and return a filled, ready-to-submit workflow dict.

        Args:
            person_image: path to the person's frontal photo.
            reference_image: path to a pre-assembled reference panel or single
                             reference image already on disk.
            prompt: the text prompt describing the desired outfit transfer.
            seed: random seed (None = random).
            output_prefix: ComfyUI SaveImage filename prefix.

        Returns:
            A dict in ComfyUI API format, ready for ComfyUIClient.run().
        """
        person_image = Path(person_image)
        reference_image = Path(reference_image)

        w, h = _detect_image_size(person_image)

        person_server = self.comfy.upload_image(person_image)
        ref_server = self.comfy.upload_image(reference_image)

        if seed is None:
            seed = random.randint(0, 2**32 - 1)

        return _fill_workflow(
            self._template,
            {
                "PERSON_IMAGE": person_server,
                "REF_IMAGE": ref_server,
                "POSITIVE_PROMPT": prompt,
                "WIDTH": w,
                "HEIGHT": h,
                "SEED": seed,
                "OUTPUT_PREFIX": output_prefix,
            },
        )

    def prepare_from_package(
        self,
        outfit_package_path: Path,
        person_image: Path,
        *,
        reference_board: Path | None = None,
        seed: int | None = None,
        output_prefix: str = "qie_vton",
        prompt_path: Path | None = None,
    ) -> dict:
        """High-level entry point for automated use.

        If reference_board is provided, uses it directly.
        Otherwise assembles a panel from the outfit package's reference images.
        If prompt_path is provided, reads the prompt from that file.
        Otherwise builds the prompt automatically from the outfit package.
        """
        outfit_package_path = Path(outfit_package_path)
        with open(outfit_package_path, encoding="utf-8") as f:
            pkg = json.load(f)
        pkg["_base_dir"] = str(outfit_package_path.parent)

        if prompt_path and Path(prompt_path).exists():
            prompt = Path(prompt_path).read_text(encoding="utf-8").strip()
        else:
            prompt = _build_prompt_from_package(pkg)

        if reference_board and Path(reference_board).exists():
            ref_path = Path(reference_board)
        else:
            ref_images = _select_reference_images(pkg)
            if not ref_images:
                raise RuntimeError("no reference images found in outfit package")
            panel = build_reference_panel(ref_images)
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            panel.save(tmp.name)
            ref_path = Path(tmp.name)

        return self.prepare(
            person_image,
            ref_path,
            prompt,
            seed=seed,
            output_prefix=output_prefix,
        )


def _build_prompt_from_package(pkg: dict) -> str:
    """Generate a concise outfit transfer prompt from the outfit_package dict.

    Colors are intentionally excluded from the prompt — the model must read
    colors, textures, and material finish directly from the reference images.
    """
    items = pkg.get("items", [])
    person_inputs = pkg.get("person_inputs", {})
    preserve = person_inputs.get("preserve", [])
    replace = person_inputs.get("replace_current_clothing", [])
    logic = pkg.get("outfit_logic", [])
    negatives = pkg.get("negative_constraints", [])

    # Filter out "same person" duplication from preserve list
    preserve_filtered = [p for p in preserve if p.lower() != "same person"]

    lines = [
        "Edit image 1 using image 2 as the garment reference. "
        "Keep the same person — " + ", ".join(preserve_filtered[:6]) + ".",
        "",
    ]
    if replace:
        lines.append("Replace completely: " + ", ".join(replace) + ".")
        lines.append("")

    lines.append("Outfit to create:")
    for item in sorted(items, key=lambda x: x.get("visibility_priority", 0), reverse=True):
        desc = item.get("visual_description", item.get("name", ""))
        lines.append(f"- {desc}.")

    if logic:
        lines.append("")
        lines.append("Outfit layout:")
        for rule in logic:
            lines.append(f"- {rule}")

    lines.append("")
    lines.append(
        "Use the reference images for exact colors, textures, and material finish "
        "of every garment. Do not use text descriptions for color."
    )

    if negatives:
        lines.append("")
        lines.append("Do not: " + " ".join(negatives[:6]) + ".")

    return "\n".join(lines)
