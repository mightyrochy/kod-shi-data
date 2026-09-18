"""AI upscaling tool using spandrel (Real-ESRGAN / any ESRGAN-family model).

Requires: ComfyUI venv (spandrel, torch+cuda, PIL).

Model preference order (first found wins):
  1. 4x-UltraSharp.pth       — preferred for studio photos
  2. RealESRGAN_x4plus.pth   — fallback, auto-downloaded if missing

Models are read from / downloaded to ComfyUI's upscale_models folder.

Usage:
    python tools/upscale.py <input_image> [output_image] [--scale 4] [--model path]

    --scale     Only used for display; actual scale is determined by the model (4x).
    --model     Explicit .pth path, overrides auto-selection.
    --overwrite Replace input file in-place (output_image not needed).
    --download  Only download the fallback model, do not run inference.

Example:
    python tools/upscale.py runs/000001/input/person_front.png --overwrite
"""

import argparse
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore", category=UserWarning)

COMFY_ROOT = Path("C:/Users/Admin/ComfyUI")
UPSCALE_MODELS_DIR = COMFY_ROOT / "models" / "upscale_models"

PREFERRED_MODELS = [
    "4x-UltraSharp.pth",
    "RealESRGAN_x4plus.pth",
]

FALLBACK_MODEL_URL = (
    "https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth"
)
FALLBACK_MODEL_NAME = "RealESRGAN_x4plus.pth"


def _find_model(explicit: str | None = None) -> Path:
    if explicit:
        p = Path(explicit)
        if not p.exists():
            raise FileNotFoundError(f"Explicit model not found: {p}")
        return p
    for name in PREFERRED_MODELS:
        p = UPSCALE_MODELS_DIR / name
        if p.exists():
            return p
    raise FileNotFoundError(
        f"No upscale model found in {UPSCALE_MODELS_DIR}. "
        f"Run with --download to fetch the fallback, or place a .pth there manually."
    )


def _download_fallback(verbose: bool = True) -> Path:
    import requests

    dest = UPSCALE_MODELS_DIR / FALLBACK_MODEL_NAME
    if dest.exists():
        if verbose:
            print(f"Model already present: {dest}")
        return dest

    UPSCALE_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    if verbose:
        print(f"Downloading {FALLBACK_MODEL_NAME} (~64MB) ...")

    import requests

    with requests.get(FALLBACK_MODEL_URL, stream=True, timeout=120, verify=False) as r:
        r.raise_for_status()
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        with open(dest, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                downloaded += len(chunk)
                if verbose and total:
                    pct = downloaded * 100 // total
                    print(f"\r  {pct}% ({downloaded // 1024 // 1024}MB/{total // 1024 // 1024}MB)", end="", flush=True)
    if verbose:
        print(f"\nSaved: {dest}")
    return dest


def upscale(input_path: Path, output_path: Path, model_path: Path) -> None:
    import torch
    from PIL import Image
    import numpy as np
    from spandrel import ImageModelDescriptor, ModelLoader

    print(f"Model:  {model_path.name}")
    print(f"Input:  {input_path}  ({_img_size(input_path)})")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    model = ModelLoader().load_from_file(model_path)
    assert isinstance(model, ImageModelDescriptor), "Loaded model is not an image model"
    model = model.model.eval().to(device)

    img = Image.open(input_path).convert("RGB")
    tensor = _img_to_tensor(img, device)

    with torch.no_grad():
        out = model(tensor)

    result = _tensor_to_img(out)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    result.save(output_path, quality=95)
    print(f"Output: {output_path}  ({_img_size(output_path)})")


def _img_to_tensor(img: "Image.Image", device: "torch.device"):
    import torch
    import numpy as np
    arr = np.array(img).astype(np.float32) / 255.0
    t = torch.from_numpy(arr).permute(2, 0, 1).unsqueeze(0).to(device)
    return t


def _tensor_to_img(t) -> "Image.Image":
    import numpy as np
    from PIL import Image
    arr = t.squeeze(0).permute(1, 2, 0).clamp(0, 1).cpu().numpy()
    return Image.fromarray((arr * 255).round().astype(np.uint8))


def _img_size(path: Path) -> str:
    from PIL import Image
    with Image.open(path) as im:
        return f"{im.width}×{im.height}"


def main() -> int:
    parser = argparse.ArgumentParser(description="AI upscale a single image")
    parser.add_argument("input", nargs="?", help="Input image path")
    parser.add_argument("output", nargs="?", help="Output image path (omit with --overwrite)")
    parser.add_argument("--model", help="Explicit model .pth path")
    parser.add_argument("--overwrite", action="store_true", help="Replace input file in-place")
    parser.add_argument("--download", action="store_true", help="Only download fallback model")
    args = parser.parse_args()

    if args.download:
        _download_fallback(verbose=True)
        return 0

    if not args.input:
        parser.error("input image is required (or use --download to fetch the fallback model)")

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        print(f"ERROR: input not found: {input_path}")
        return 1

    if args.overwrite:
        output_path = input_path
    elif args.output:
        output_path = Path(args.output).resolve()
    else:
        output_path = input_path.with_stem(input_path.stem + "_4x")

    try:
        model_path = _find_model(args.model)
    except FileNotFoundError:
        print("No model found. Attempting to download fallback...")
        model_path = _download_fallback(verbose=True)

    upscale(input_path, output_path, model_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
