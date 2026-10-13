"""Deterministic contract for the garment-correspondence region cropper (no models, no GPU).

The heavy axes (FashionSigLIP, DISTS) are exercised by the E-012 demo; here we only pin the pure
region-extraction helper that all four axes share: a mask must crop to its tight bounding box.
"""

import numpy as np

from system.gates.garment_fidelity import _region_to_temp


def test_region_to_temp_crops_mask_bbox(tmp_path):
    img = np.zeros((100, 100, 3), np.uint8)
    img[30:70, 20:60] = (50, 120, 200)      # a coloured patch
    mask = np.zeros((100, 100), np.uint8)
    mask[30:70, 20:60] = 255                 # mask exactly over the patch
    dst = _region_to_temp(img, mask, tmp_path / "crop.png")

    import cv2
    out = cv2.imread(str(dst))
    assert out.shape[:2] == (40, 40)         # tight bbox of the mask (70-30, 60-20)
    assert (out == np.array([50, 120, 200])).all()


def test_region_to_temp_no_mask_keeps_image(tmp_path):
    img = np.full((20, 30, 3), 77, np.uint8)
    dst = _region_to_temp(img, None, tmp_path / "full.png")
    import cv2
    assert cv2.imread(str(dst)).shape[:2] == (20, 30)
