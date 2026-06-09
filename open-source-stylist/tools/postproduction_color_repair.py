import argparse
import colorsys
import json
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def parse_hex_color(value):
    value = value.strip().lstrip("#")
    if len(value) != 6:
        raise ValueError("target color must be a 6-digit hex value")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def make_mask(size, polygons, feather_px):
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    for polygon in polygons:
        points = [tuple(point) for point in polygon]
        draw.polygon(points, fill=255)
    if feather_px > 0:
        mask = mask.filter(ImageFilter.GaussianBlur(radius=feather_px))
    return mask


def rgb_to_hsv_array(rgb):
    flat = rgb.reshape(-1, 3) / 255.0
    hsv = np.array([colorsys.rgb_to_hsv(*pixel) for pixel in flat], dtype=np.float32)
    return hsv.reshape(rgb.shape)


def hsv_to_rgb_array(hsv):
    flat = hsv.reshape(-1, 3)
    rgb = np.array([colorsys.hsv_to_rgb(*pixel) for pixel in flat], dtype=np.float32)
    return np.clip(rgb.reshape(hsv.shape) * 255.0, 0, 255)


def repair_color(
    image,
    mask,
    target_rgb,
    hue_strength,
    sat_strength,
    value_strength,
    min_saturation,
    max_value,
):
    rgb = np.asarray(image.convert("RGB"), dtype=np.float32)
    alpha = np.asarray(mask, dtype=np.float32)[:, :, None] / 255.0

    target_hsv = colorsys.rgb_to_hsv(*(channel / 255.0 for channel in target_rgb))
    hsv = rgb_to_hsv_array(rgb)
    original_hsv = hsv.copy()
    selection = np.ones_like(alpha[:, :, 0], dtype=np.float32)
    if min_saturation is not None:
        selection *= hsv[:, :, 1] >= min_saturation
    if max_value is not None:
        selection *= hsv[:, :, 2] <= max_value
    alpha = alpha * selection[:, :, None]

    hue_delta = ((target_hsv[0] - hsv[:, :, 0] + 0.5) % 1.0) - 0.5
    hsv[:, :, 0] = (hsv[:, :, 0] + hue_delta * hue_strength * alpha[:, :, 0]) % 1.0
    hsv[:, :, 1] = hsv[:, :, 1] * (1.0 - sat_strength * alpha[:, :, 0]) + target_hsv[1] * sat_strength * alpha[:, :, 0]
    hsv[:, :, 2] = hsv[:, :, 2] * (1.0 - value_strength * alpha[:, :, 0]) + target_hsv[2] * value_strength * alpha[:, :, 0]

    repaired_rgb = hsv_to_rgb_array(hsv)
    blended = rgb * (1.0 - alpha) + repaired_rgb * alpha
    result = Image.fromarray(np.uint8(np.round(blended)))

    mask_pixels = alpha[:, :, 0] > 0.25
    metrics = {
        "masked_pixel_count": int(mask_pixels.sum()),
        "original_mean_rgb": [round(float(v), 2) for v in rgb[mask_pixels].mean(axis=0)],
        "repaired_mean_rgb": [round(float(v), 2) for v in np.asarray(result, dtype=np.float32)[mask_pixels].mean(axis=0)],
        "original_mean_hsv": [round(float(v), 4) for v in original_hsv[mask_pixels].mean(axis=0)],
        "repaired_mean_hsv": [round(float(v), 4) for v in rgb_to_hsv_array(np.asarray(result, dtype=np.float32))[mask_pixels].mean(axis=0)],
    }
    return result, metrics


def main():
    parser = argparse.ArgumentParser(description="Deterministic masked color repair.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--mask-output", required=True)
    parser.add_argument("--report-output", required=True)
    parser.add_argument("--target", required=True, help="Target RGB color as hex, for example #0f4035.")
    parser.add_argument("--polygons-json", required=True, help="JSON file containing a list of polygons.")
    parser.add_argument("--feather", type=float, default=8.0)
    parser.add_argument("--hue-strength", type=float, default=0.85)
    parser.add_argument("--sat-strength", type=float, default=0.45)
    parser.add_argument("--value-strength", type=float, default=0.08)
    parser.add_argument("--min-saturation", type=float, default=None)
    parser.add_argument("--max-value", type=float, default=None)
    args = parser.parse_args()

    started = time.perf_counter()
    image = Image.open(args.input).convert("RGB")
    polygons = json.loads(Path(args.polygons_json).read_text(encoding="utf-8"))
    mask = make_mask(image.size, polygons, args.feather)
    target_rgb = parse_hex_color(args.target)

    result, metrics = repair_color(
        image=image,
        mask=mask,
        target_rgb=target_rgb,
        hue_strength=args.hue_strength,
        sat_strength=args.sat_strength,
        value_strength=args.value_strength,
        min_saturation=args.min_saturation,
        max_value=args.max_value,
    )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.mask_output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.report_output).parent.mkdir(parents=True, exist_ok=True)
    result.save(args.output)
    mask.save(args.mask_output)

    report = {
        "executor": "deterministic_masked_color_repair",
        "input": args.input,
        "output": args.output,
        "mask_output": args.mask_output,
        "target_rgb": list(target_rgb),
        "target_hex": "#" + "".join(f"{channel:02x}" for channel in target_rgb),
        "settings": {
            "feather_px": args.feather,
            "hue_strength": args.hue_strength,
            "sat_strength": args.sat_strength,
            "value_strength": args.value_strength,
            "min_saturation": args.min_saturation,
            "max_value": args.max_value,
        },
        "metrics": metrics,
        "runtime_seconds": round(time.perf_counter() - started, 3),
    }
    Path(args.report_output).write_text(json.dumps(report, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
