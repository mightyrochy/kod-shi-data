"""Identity gate - ArcFace cosine similarity between two face images.

Uses insightface buffalo_l model (ArcFace R100).
Model weights are downloaded on first use to ~/.insightface/.

The CUDA provider is preferred. On Windows, NVIDIA wheel DLL directories and
cuDNN sub-libraries are loaded explicitly before InsightFace creates sessions.
CPU remains a functional fallback when CUDA is not installed.

Dependencies: insightface, onnxruntime-gpu (or onnxruntime for CPU-only use).
"""

import ctypes
import os
import site
import sys
from pathlib import Path

import cv2
import numpy as np

# ---------------------------------------------------------------------------
# Lazy-loaded analyser (initialised once per process)
# ---------------------------------------------------------------------------

_analyser = None
_cuda_dll_handles = []


def _preload_cuda_runtime() -> list[str]:
    """Return provider preference after making pip-installed CUDA DLLs visible."""
    try:
        import onnxruntime as ort
    except ImportError:
        return ["CPUExecutionProvider"]

    available = ort.get_available_providers()
    if "CUDAExecutionProvider" not in available:
        return ["CPUExecutionProvider"]

    if sys.platform == "win32":
        roots = [*site.getsitepackages(), site.getusersitepackages()]
        dll_dirs = []
        for root in dict.fromkeys(roots):
            nvidia_root = Path(root) / "nvidia"
            if not nvidia_root.is_dir():
                continue
            dll_dirs.extend(sorted(path for path in nvidia_root.glob("*/bin") if path.is_dir()))

        for dll_dir in dll_dirs:
            _cuda_dll_handles.append(os.add_dll_directory(str(dll_dir)))
        for dll_dir in dll_dirs:
            for dll_path in sorted(dll_dir.glob("*.dll")):
                _cuda_dll_handles.append(ctypes.WinDLL(str(dll_path)))

    preload = getattr(ort, "preload_dlls", None)
    if preload is not None:
        preload(directory="")
    return ["CUDAExecutionProvider", "CPUExecutionProvider"]


def _get_analyser():
    global _analyser
    if _analyser is not None:
        return _analyser
    try:
        from insightface.app import FaceAnalysis
    except ImportError:
        raise ImportError("insightface is required: pip install insightface")
    app = FaceAnalysis(
        name="buffalo_l",
        allowed_modules=["detection", "recognition"],
        providers=_preload_cuda_runtime(),
    )
    app.prepare(ctx_id=0, det_size=(640, 640))
    _analyser = app
    return _analyser


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_bgr(image) -> np.ndarray:
    if isinstance(image, (str, Path)):
        img = cv2.imread(str(image))
        if img is None:
            raise FileNotFoundError(f"Cannot read image: {image}")
        return img
    return np.asarray(image)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_embedding(image) -> np.ndarray | None:
    """Return normalised ArcFace embedding (512-d) for the largest face detected.

    Returns None if no face is found.
    """
    img = _load_bgr(image)
    app = _get_analyser()
    faces = app.get(img)
    if not faces:
        return None
    # pick the face with the largest bounding-box area
    face = max(faces, key=lambda f: (f.bbox[2] - f.bbox[0]) * (f.bbox[3] - f.bbox[1]))
    emb = face.embedding.astype(np.float32)
    return emb / (np.linalg.norm(emb) + 1e-8)


def cosine(emb_a: np.ndarray, emb_b: np.ndarray) -> float:
    """Cosine similarity between two normalised embeddings, in [-1, 1]."""
    a = emb_a / (np.linalg.norm(emb_a) + 1e-8)
    b = emb_b / (np.linalg.norm(emb_b) + 1e-8)
    return float(np.dot(a, b))


def compare_faces(image_a, image_b) -> dict:
    """Compare face identity between two images.

    Returns:
        cosine        similarity in [-1, 1]; same person typically > 0.3
        detected_a    whether a face was found in image_a
        detected_b    whether a face was found in image_b

    Threshold is NOT applied here — it is set by calibration in E-003
    and applied by the caller with knowledge/verified.md values.
    """
    emb_a = get_embedding(image_a)
    emb_b = get_embedding(image_b)

    result = {
        "cosine": None,
        "detected_a": emb_a is not None,
        "detected_b": emb_b is not None,
    }

    if emb_a is not None and emb_b is not None:
        result["cosine"] = round(cosine(emb_a, emb_b), 4)

    return result
