"""Mask sanity guard — plausibility checks before any consumer reads a mask.

Three checks (METHODOLOGY §2 p.6 — deterministic gate path):
  1. Area fraction: foreground pixels / total pixels within expected bounds per region.
  2. Position prior: centroid y-fraction within expected vertical band per region.
  3. Containment: garment mask pixels ≥ threshold% within the person mask.

Violations are advisory FLAGS, not verdicts. Flagged masks are surfaced for owner
review; the pipeline does not auto-fail on them.

Motivation: two silent mask-corruption incidents in E-005 (shoes ΔE exploded;
top mask silently empty) were caught late. Early detection keeps every downstream
measurement trustworthy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Public data types
# ---------------------------------------------------------------------------

@dataclass
class SanityFlag:
    region: str
    check: str    # "area_fraction" | "position_prior" | "containment" | "empty"
    detail: str   # human-readable, owner-facing


@dataclass
class SanityResult:
    region: str
    flags: list[SanityFlag] = field(default_factory=list)

    @property
    def clean(self) -> bool:
        return len(self.flags) == 0


# ---------------------------------------------------------------------------
# Per-region configuration
# ---------------------------------------------------------------------------

# Area fraction bounds (foreground_pixels / total_pixels), closed interval.
# Grounded from E-005 observations:
#   shoes → 0.4% of image; top → 11.5%; person → large fraction.
_AREA_BOUNDS: dict[str, tuple[float, float]] = {
    "person":     (0.05, 0.95),
    "face":       (0.002, 0.15),
    "hair":       (0.002, 0.20),
    "background": (0.05, 0.95),
    "top":        (0.02, 0.50),
    "bottom":     (0.02, 0.50),
    "shoes":      (0.001, 0.15),
    "footwear":   (0.001, 0.15),
    "belt":       (0.001, 0.10),
    "earrings":   (0.0001, 0.05),
    "glasses":    (0.001, 0.05),
}

# Positional priors: (min_centroid_y_frac, max_centroid_y_frac), 0=top, 1=bottom.
# Grounded from E-005: shoes centroid ~97.5% (rows 95–100%), top centroid ~36%
# (rows 17–56%), face in upper quarter.
_POSITION_PRIOR: dict[str, tuple[float, float]] = {
    "shoes":    (0.55, 1.00),   # footwear lives in the lower 45%
    "footwear": (0.55, 1.00),
    "face":     (0.00, 0.45),   # face in upper 45%
    "hair":     (0.00, 0.45),
    "top":      (0.05, 0.70),   # torso region spans upper 65%
}

# Labels whose pixels should be mostly inside the person mask.
_GARMENT_LABELS: frozenset[str] = frozenset(
    {"top", "bottom", "shoes", "footwear", "belt", "earrings", "glasses"}
)

_DEFAULT_CONTAINMENT_THRESHOLD = 0.70  # 70% of garment pixels must fall inside person


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check(
    mask: Union[np.ndarray, str, Path],
    region: str,
    *,
    person_mask: Union[np.ndarray, str, Path, None] = None,
    containment_threshold: float = _DEFAULT_CONTAINMENT_THRESHOLD,
) -> SanityResult:
    """Run all plausibility checks on a single mask.

    Args:
        mask: grayscale array (255=fg, 0=bg) or path to mask PNG.
        region: label name, e.g. "shoes", "top", "person".
        person_mask: optional person silhouette for containment check.
                     Required for meaningful containment results on garment labels.
        containment_threshold: minimum fraction of garment pixels inside person mask.

    Returns:
        SanityResult — .clean is True when no flags were raised.
    """
    m = _load(mask)
    # Foreground threshold matches the color and proportion gates (>127), so
    # anti-aliased mask edges are counted identically across all consumers.
    fgmask = m > 127
    result = SanityResult(region=region)
    label = region.lower()

    total = fgmask.size
    fg = int(np.count_nonzero(fgmask))

    if fg == 0:
        result.flags.append(SanityFlag(
            region=region,
            check="empty",
            detail="mask is entirely empty (zero foreground pixels)",
        ))
        return result  # remaining checks are meaningless on an empty mask

    area_frac = fg / total

    # 1. Area fraction bounds
    if label in _AREA_BOUNDS:
        lo, hi = _AREA_BOUNDS[label]
        if not (lo <= area_frac <= hi):
            result.flags.append(SanityFlag(
                region=region,
                check="area_fraction",
                detail=(
                    f"area fraction {area_frac:.4f} outside expected "
                    f"[{lo:.4f}, {hi:.4f}] for '{region}'"
                ),
            ))

    # 2. Positional prior (mask centroid y-fraction)
    if label in _POSITION_PRIOR:
        ys, _ = np.where(fgmask)
        centroid_y = float(ys.mean()) / fgmask.shape[0]
        min_y, max_y = _POSITION_PRIOR[label]
        if not (min_y <= centroid_y <= max_y):
            result.flags.append(SanityFlag(
                region=region,
                check="position_prior",
                detail=(
                    f"centroid y={centroid_y:.3f} outside expected "
                    f"[{min_y:.3f}, {max_y:.3f}] for '{region}'"
                ),
            ))

    # 3. Garment containment within person mask
    if label in _GARMENT_LABELS and person_mask is not None:
        pm = _load(person_mask) > 127
        if pm.shape != fgmask.shape:
            result.flags.append(SanityFlag(
                region=region,
                check="containment",
                detail=(
                    f"person mask shape {pm.shape} != garment mask shape {fgmask.shape}; "
                    "cannot check containment"
                ),
            ))
        else:
            overlap = int(np.count_nonzero(fgmask & pm))
            frac = overlap / fg
            if frac < containment_threshold:
                result.flags.append(SanityFlag(
                    region=region,
                    check="containment",
                    detail=(
                        f"{frac:.1%} of '{region}' pixels inside person mask "
                        f"(threshold {containment_threshold:.0%})"
                    ),
                ))

    return result


def check_all(
    masks: dict[str, Union[np.ndarray, str, Path]],
    *,
    person_mask: Union[np.ndarray, str, Path, None] = None,
    containment_threshold: float = _DEFAULT_CONTAINMENT_THRESHOLD,
) -> dict[str, SanityResult]:
    """Run check() on every mask in the dict.

    If "person" is in masks and person_mask is not supplied, the person mask is
    extracted automatically for containment checks.

    Args:
        masks: {label: mask_array_or_path}
        person_mask: explicit person silhouette; auto-extracted from masks if absent.
        containment_threshold: passed through to check().

    Returns:
        {label: SanityResult}
    """
    effective_person = person_mask
    if effective_person is None and "person" in masks:
        effective_person = masks["person"]

    return {
        label: check(
            m, label,
            person_mask=effective_person,
            containment_threshold=containment_threshold,
        )
        for label, m in masks.items()
    }


def format_report(results: dict[str, SanityResult]) -> str:
    """Return a human-readable summary of check_all() output."""
    lines: list[str] = []
    flagged = {k: v for k, v in results.items() if not v.clean}
    clean = [k for k, v in results.items() if v.clean]

    if flagged:
        lines.append(f"SANITY FLAGS ({len(flagged)} region(s)):")
        for label, r in flagged.items():
            for f in r.flags:
                lines.append(f"  [{label}] {f.check}: {f.detail}")
    if clean:
        lines.append(f"clean: {', '.join(sorted(clean))}")
    return "\n".join(lines) if lines else "all masks clean"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load(mask: Union[np.ndarray, str, Path]) -> np.ndarray:
    if isinstance(mask, np.ndarray):
        return mask
    path = Path(mask)
    m = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    if m is None:
        raise FileNotFoundError(f"Cannot load mask: {path}")
    return m
