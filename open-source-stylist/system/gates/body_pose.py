"""Body-shape gate — skeletal keypoints, NOT the clothed silhouette.

Why this exists: proportions.py measures the width of the *clothed* person mask, so
volume sleeves / peplum / a slim skirt move its number even when the body is unchanged
(and vice-versa: a real body slimming can hide behind loose clothing). This gate reads
MediaPipe Pose joint landmarks (shoulders, hips) — joint-to-joint distances are far
less sensitive to what the person is wearing — and normalises them by torso length so
the ratios are resolution- and scale-invariant. It compares the SOURCE person to the
generated one and reports how much the body proportions changed.

It is a measurement, not yet a verdict: no calibrated pass/fail threshold. Same-pose
(frontal standing) is assumed; tilt angles are reported so a pose mismatch is visible.

Dependency: mediapipe==0.10.35 (Tasks API) + models/pose_landmarker_full.task in this
module's directory, opencv-python, numpy.
"""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

# MediaPipe Pose landmark indices.
_L_SHOULDER, _R_SHOULDER = 11, 12
_L_HIP, _R_HIP = 23, 24
_POINTS = {
    "l_shoulder": _L_SHOULDER, "r_shoulder": _R_SHOULDER,
    "l_hip": _L_HIP, "r_hip": _R_HIP,
}


def _load_rgb(image):
    if isinstance(image, (str, Path)):
        bgr = cv2.imread(str(image))
        if bgr is None:
            raise FileNotFoundError(f"Cannot read image: {image}")
    else:
        bgr = np.asarray(image)
    h, w = bgr.shape[:2]
    return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB), (w, h)


_MODEL_PATH = Path(__file__).parent / "models" / "pose_landmarker_full.task"
_LANDMARKER = None


def _get_landmarker():
    """Lazily build a singleton PoseLandmarker (Tasks API, IMAGE mode)."""
    global _LANDMARKER
    if _LANDMARKER is None:
        from mediapipe.tasks import python as mp_tasks
        from mediapipe.tasks.python import vision

        if not _MODEL_PATH.is_file():
            raise FileNotFoundError(
                f"Pose model missing: {_MODEL_PATH}. Download pose_landmarker_full.task "
                "from Google's mediapipe-models bucket into that folder."
            )
        options = vision.PoseLandmarkerOptions(
            base_options=mp_tasks.BaseOptions(model_asset_path=str(_MODEL_PATH)),
            running_mode=vision.RunningMode.IMAGE,
            num_poses=1,
            min_pose_detection_confidence=0.5,
        )
        _LANDMARKER = vision.PoseLandmarker.create_from_options(options)
    return _LANDMARKER


def landmarks(image) -> dict | None:
    """Return pixel-space body landmarks + visibility, or None if no pose is found."""
    import mediapipe as mp

    rgb, (w, h) = _load_rgb(image)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
    result = _get_landmarker().detect(mp_image)
    if not result.pose_landmarks:
        return None
    lm = result.pose_landmarks[0]
    points = {name: (lm[i].x * w, lm[i].y * h) for name, i in _POINTS.items()}
    visibility = {name: float(lm[i].visibility) for name, i in _POINTS.items()}
    return {"points": points, "visibility": visibility, "image_size": (w, h)}


def _dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _mid(a, b):
    return ((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0)


def _tilt_deg(left, right):
    """Angle of the left-right line vs horizontal (0 = level)."""
    return math.degrees(math.atan2(right[1] - left[1], right[0] - left[0]))


def _profile(lms: dict) -> dict:
    p = lms["points"]
    shoulder_w = _dist(p["l_shoulder"], p["r_shoulder"])
    hip_w = _dist(p["l_hip"], p["r_hip"])
    torso = _dist(_mid(p["l_shoulder"], p["r_shoulder"]), _mid(p["l_hip"], p["r_hip"]))
    if torso <= 1e-6:
        return {"valid": False}
    return {
        "valid": True,
        "shoulder_width_norm": round(shoulder_w / torso, 4),
        "hip_width_norm": round(hip_w / torso, 4),
        "shoulder_hip_ratio": round(shoulder_w / hip_w, 4) if hip_w > 1e-6 else None,
        "shoulder_tilt_deg": round(_tilt_deg(p["l_shoulder"], p["r_shoulder"]), 1),
        "hip_tilt_deg": round(_tilt_deg(p["l_hip"], p["r_hip"]), 1),
        "min_visibility": round(min(lms["visibility"].values()), 3),
    }


def compare(source_image, generated_image) -> dict:
    """Compare body proportions (source -> generated) from skeletal landmarks.

    Returns per-metric % change (positive = wider/larger in the generated image).
    `pose_mismatch_deg` flags how differently the two bodies are posed; a large value
    means the comparison mixes pose with shape and must be read with care.
    """
    src = landmarks(source_image)
    gen = landmarks(generated_image)
    if src is None or gen is None:
        return {"verdict": "NO_POSE",
                "source_detected": src is not None,
                "generated_detected": gen is not None}

    a, b = _profile(src), _profile(gen)
    if not a["valid"] or not b["valid"]:
        return {"verdict": "DEGENERATE", "source": a, "generated": b}

    def pct(key):
        return round((b[key] - a[key]) / a[key] * 100.0, 2) if a[key] else None

    return {
        "verdict": "MEASURED",
        "source": a,
        "generated": b,
        "change_pct": {
            "shoulder_width_norm": pct("shoulder_width_norm"),
            "hip_width_norm": pct("hip_width_norm"),
            "shoulder_hip_ratio": pct("shoulder_hip_ratio"),
        },
        "pose_mismatch_deg": round(
            abs(a["shoulder_tilt_deg"] - b["shoulder_tilt_deg"])
            + abs(a["hip_tilt_deg"] - b["hip_tilt_deg"]), 1),
        "min_visibility": min(a["min_visibility"], b["min_visibility"]),
        "note": "skeletal joints, clothing-robust; no calibrated threshold yet — measurement only",
    }


if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Body-shape comparison from pose landmarks")
    parser.add_argument("source")
    parser.add_argument("generated")
    args = parser.parse_args()
    print(json.dumps(compare(args.source, args.generated), indent=2))
