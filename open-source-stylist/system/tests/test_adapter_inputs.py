"""Tests for frozen boards and file-backed outfit layout."""

import copy
import json
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from system.adapter.adapter import build_generation_request
from system.adapter.panel import resolve_board
from system.adapter.prompt import build_prompt


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_PATH = ROOT / "assets/outfits/outfit_001/outfit_package.json"


def _package() -> dict:
    return json.loads(PACKAGE_PATH.read_text(encoding="utf-8"))


def test_all_frozen_boards_resolve_with_recorded_hashes():
    package = _package()
    paths = {
        resolve_board(package, variant, ROOT)
        for variant in package["reference_board"]["variants"]
    }

    assert len(paths) == len(package["reference_board"]["variants"])
    assert all(path.is_file() for path in paths)


def test_board_hash_mismatch_fails_loudly():
    package = copy.deepcopy(_package())
    package["reference_board"]["variants"]["masked_crops"]["sha256"] = "0" * 64

    with pytest.raises(RuntimeError, match="reference board changed"):
        resolve_board(package, "masked_crops", ROOT)


def test_prompt_contains_layout_file_verbatim():
    package = _package()
    layout = (ROOT / package["layout_path"]).read_text(encoding="utf-8").strip()
    prompt = build_prompt(package, ROOT, "rectangular_crops")

    assert layout in prompt
    assert "belt goes over blouse" in prompt
    assert "same earrings on both ears" in prompt
    assert "wedge sandals" in prompt


def test_hybrid_prompt_uses_variant_specific_labels():
    package = _package()
    prompt = build_prompt(package, ROOT, "hybrid_mask_crop")

    assert "blouse front mask" in prompt
    assert "blouse front crop" in prompt
    assert "shoes mask" in prompt
    assert "shoes crop" in prompt


def test_corrected_blouse_mask_restores_only_button_area():
    original_path = (
        ROOT / "experiments/001_segmentation_masks/results/"
        "outfit_001_blouse_front/blouse.png"
    )
    corrected_path = (
        ROOT / "assets/outfits/outfit_001/reference_masks/blouse_front_buttons.png"
    )
    with Image.open(original_path) as image:
        original = np.asarray(image.convert("L"))
    with Image.open(corrected_path) as image:
        corrected = np.asarray(image.convert("L"))

    recovered_y, recovered_x = np.where((corrected > 127) & (original <= 127))
    assert recovered_x.size >= 1000
    assert recovered_x.min() >= 396 and recovered_x.max() <= 439
    assert recovered_y.min() >= 588 and recovered_y.max() <= 796


def test_generation_request_reuses_selected_board():
    package = _package()
    request = build_generation_request(
        package,
        ROOT / "assets/person/person_front.png",
        reference_board_variant="rectangular_crops",
        seed=42,
        resolution=(720, 1024),
    )

    expected = resolve_board(package, "rectangular_crops", ROOT)
    assert Path(request["reference_panel_path"]) == expected
    assert request["reference_board_variant"] == "rectangular_crops"
    assert request["params"]["cfg"] == 1.0


def test_generation_request_rejects_invalid_resolution():
    package = _package()
    with pytest.raises(ValueError, match="divisible by 16"):
        build_generation_request(
            package,
            ROOT / "assets/person/person_front.png",
            reference_board_variant="masked_crops",
            seed=42,
            resolution=(721, 1024),
        )
