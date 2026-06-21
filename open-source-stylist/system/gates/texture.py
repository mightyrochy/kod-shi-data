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


def _finedetail_energy(region_bgr: np.ndarray) -> float:
    """Finest-band energy via difference-of-Gaussian (sigma 1-2). Captures the pixel-scale band where
    photographic NOISE / JPEG grain lives as well as the finest detail — kept as a diagnostic, NOT the
    weave measure (a noisy reference inflates it; see CALIBRATION/owner_crops _hp_check)."""
    g = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    hp = (g - cv2.GaussianBlur(g, (0, 0), 1.0)) + (g - cv2.GaussianBlur(g, (0, 0), 2.0))
    return float(np.mean(hp * hp))


_GABOR_BANK: list[np.ndarray] | None = None


def _gabor_bank() -> list[np.ndarray]:
    """Zero-mean Gabor kernels at 4 orientations x weave-scale wavelengths (4,6,8 px) x 2 phases.
    Wavelengths >=4 deliberately SKIP the lambda<=2 band where pixel noise dominates."""
    global _GABOR_BANK
    if _GABOR_BANK is None:
        bank = []
        for theta in (0.0, np.pi / 4, np.pi / 2, 3 * np.pi / 4):
            for lam in (4.0, 6.0, 8.0):
                ks = int(3 * lam) | 1
                for psi in (0.0, np.pi / 2):
                    k = cv2.getGaborKernel((ks, ks), lam * 0.56, theta, lam, 0.5, psi, ktype=cv2.CV_32F)
                    bank.append(k - k.mean())
        _GABOR_BANK = bank
    return _GABOR_BANK


def _weave_energy(region_bgr: np.ndarray) -> float:
    """Oriented mid-frequency (weave-scale) texture energy via the Gabor bank. Reflects STRUCTURED weave
    rather than photographic noise — the fix for the difference-of-Gaussian measure, which conflated weave
    with the reference photo's pixel grain (verified on owner_crops/_hp_check.png)."""
    g = cv2.cvtColor(region_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    return float(np.mean([np.mean(cv2.filter2D(g, cv2.CV_32F, k) ** 2) for k in _gabor_bank()]))


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

    out_t, ref_t = _weave_energy(out_r), _weave_energy(ref_r)          # PRIMARY: weave (Gabor)
    out_fd, ref_fd = _finedetail_energy(out_r), _finedetail_energy(ref_r)  # diagnostic: finest band (noise)
    out_c, out_l = _colour_spread(out_r)
    ref_c, ref_l = _colour_spread(ref_r)

    texture_ratio = _ratio(out_t, ref_t)            # weave-structure ratio (noise-robust)
    finedetail_ratio = _ratio(out_fd, ref_fd)       # finest-band ratio (noise-inflated; diagnostic only)
    chroma_ratio = _ratio(out_c, ref_c)
    lum_ratio = _ratio(out_l, ref_l)

    flags = []
    if texture_ratio is not None and texture_ratio < TEXTURE_FLAT_RATIO:
        flags.append("LOW_TEXTURE")
    if (chroma_ratio is not None and chroma_ratio < COLOUR_FLAT_RATIO) or \
       (lum_ratio is not None and lum_ratio < COLOUR_FLAT_RATIO):
        flags.append("FLAT_COLOUR")

    return {
        "texture_ratio": texture_ratio, "finedetail_ratio": finedetail_ratio,
        "chroma_ratio": chroma_ratio, "lum_ratio": lum_ratio,
        "texture_out_energy": round(out_t, 4), "texture_ref_energy": round(ref_t, 4),
        "finedetail_out": round(out_fd, 2), "finedetail_ref": round(ref_fd, 2),
        "chroma_std_out": round(out_c, 2), "chroma_std_ref": round(ref_c, 2),
        "lum_std_out": round(out_l, 2), "lum_std_ref": round(ref_l, 2),
        "verdict": "FLAT" if flags else "OK",
        "flags": flags,
        "note": "ADVISORY. texture_ratio = WEAVE structure (Gabor, noise-robust); finedetail_ratio = "
                "finest band (noise-inflated, diagnostic). Check texture_ref_energy is not ~0 first.",
    }
