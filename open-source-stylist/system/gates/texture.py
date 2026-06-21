"""Texture-fidelity gate — does an output garment region keep the reference's texture, or is it FLAT?

Deterministic, model-free (cv2 + numpy). Answers the axis the colour gate is blind to: a region can
match the reference HUE/CHROMA exactly yet look "flat" — the fine fabric texture (weave, twill, folds)
is gone. This happens when a garment occupies only a small share of a packed reference board, so QIE
sees it at a few hundred px (the board is VAE-referenced at ~1 MP total — see V-QIE-EDIT-001 / the
CONDITION_IMAGE_SIZE=384² vs VAE_IMAGE_SIZE=1024² split in the Qwen-Image-Edit-Plus pipeline).

The measure is COMPARATIVE and scale-normalised: the output region and the reference garment are each
resized to a common size, then we compare
  - texture = high-frequency luminance energy (difference-of-Gaussian) — `texture_ratio` = out / ref,
  - colour spread = chroma std (LAB a,b) and luminance std — `chroma_ratio`, `lum_ratio` = out / ref.
A ratio < 1 means the output is FLATTER than the reference on that axis. Thresholds are ADVISORY until
calibrated on owner-labelled flat/not-flat examples (METHODOLOGY §1) — the ratios themselves are the
owner-verifiable statement ("the output skirt has X% of the reference's texture energy").

    from system.gates.texture import compare_texture
    compare_texture(out_bgr_or_path, ref_bgr_or_path, out_mask=..., ref_mask=...)
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

# Advisory thresholds (uncalibrated — see module docstring). A ratio below this flags the axis.
TEXTURE_FLAT_RATIO = 0.6
COLOUR_FLAT_RATIO = 0.6
_WORK = 256  # common comparison size; both regions are resized here so texture energy is comparable


def _load(img) -> np.ndarray:
    if isinstance(img, (str, Path)):
        out = cv2.imread(str(img))
        if out is None:
            raise FileNotFoundError(img)
        return out
    return img


def _region(img: np.ndarray, mask: np.ndarray | None) -> np.ndarray:
    """Bounding-box crop of the masked garment (or the whole image if no mask), resized to _WORK²."""
    if mask is not None:
        if (mask.shape[1], mask.shape[0]) != (img.shape[1], img.shape[0]):
            mask = cv2.resize(mask, (img.shape[1], img.shape[0]), interpolation=cv2.INTER_NEAREST)
        ys, xs = np.where(mask > 127)
        if ys.size == 0:
            raise ValueError("empty region mask")
        img = img[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return cv2.resize(img, (_WORK, _WORK), interpolation=cv2.INTER_AREA)


def _texture_energy(region_bgr: np.ndarray) -> float:
    """High-frequency luminance energy via difference-of-Gaussian (fine + medium bands)."""
    g = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hp = (g - cv2.GaussianBlur(g, (0, 0), 1.0)) + (g - cv2.GaussianBlur(g, (0, 0), 2.0))
    return float(np.mean(hp * hp))


def _colour_spread(region_bgr: np.ndarray) -> tuple[float, float]:
    """(chroma_std, luminance_std) in LAB — how much the region varies in colour and lightness."""
    lab = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, a, b = lab[..., 0], lab[..., 1] - 128.0, lab[..., 2] - 128.0
    chroma = np.sqrt(a * a + b * b)
    return float(chroma.std()), float(L.std())


def _ratio(out: float, ref: float) -> float | None:
    return None if ref <= 1e-6 else round(out / ref, 3)


def compare_texture(out_image, ref_image, out_mask=None, ref_mask=None) -> dict:
    """Compare an output garment region's texture/colour spread against its reference.

    Returns the raw measures, out/ref ratios, and an ADVISORY verdict. A ratio < ~0.6 means the output
    is flatter than the reference on that axis. `texture_ref_energy` near 0 means the reference itself is
    flat (so output flatness is not a fidelity loss) — guard with that before trusting `texture_ratio`.
    """
    out_r = _region(_load(out_image), out_mask)
    ref_r = _region(_load(ref_image), ref_mask)

    out_t, ref_t = _texture_energy(out_r), _texture_energy(ref_r)
    out_c, out_l = _colour_spread(out_r)
    ref_c, ref_l = _colour_spread(ref_r)

    texture_ratio = _ratio(out_t, ref_t)
    chroma_ratio = _ratio(out_c, ref_c)
    lum_ratio = _ratio(out_l, ref_l)

    flags = []
    if texture_ratio is not None and texture_ratio < TEXTURE_FLAT_RATIO:
        flags.append("LOW_TEXTURE")
    if (chroma_ratio is not None and chroma_ratio < COLOUR_FLAT_RATIO) or \
       (lum_ratio is not None and lum_ratio < COLOUR_FLAT_RATIO):
        flags.append("FLAT_COLOUR")

    return {
        "texture_ratio": texture_ratio, "chroma_ratio": chroma_ratio, "lum_ratio": lum_ratio,
        "texture_out_energy": round(out_t, 2), "texture_ref_energy": round(ref_t, 2),
        "chroma_std_out": round(out_c, 2), "chroma_std_ref": round(ref_c, 2),
        "lum_std_out": round(out_l, 2), "lum_std_ref": round(ref_l, 2),
        "verdict": "FLAT" if flags else "OK",
        "flags": flags,
        "note": "ADVISORY — thresholds uncalibrated; ratios are the owner-verifiable signal. "
                "Check texture_ref_energy is not near 0 before trusting texture_ratio.",
    }
