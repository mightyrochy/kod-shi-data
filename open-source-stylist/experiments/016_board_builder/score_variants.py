"""E-016 — measure identity + body proportions for every NEW final (A / B / F variants) vs the person,
plus each variant's tuning params pulled from the embedded graph, and base->final ratio delta where the
base index aligns. No generation."""
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from PIL import Image

from system.gates import body_pose
from system.gates.identity import compare_faces

OUT = Path(r"C:/Users/Admin/ComfyUI/output")
ROOT = Path(__file__).resolve().parents[2]
PERSON = ROOT / "assets/person/person_front.png"


def graph(p: Path):
    return json.loads(Image.open(p).info.get("prompt", "{}"))


def prop(p: Path):
    idc = compare_faces(str(p), str(PERSON)).get("cosine", float("nan"))
    bp = body_pose.compare(str(PERSON), str(p))
    pc = bp.get("change_pct") or {}
    return idc, pc.get("hip_width_norm"), pc.get("shoulder_width_norm"), \
        pc.get("shoulder_hip_ratio"), bp.get("pose_mismatch_deg")


def b_params(g):
    ero = feath = None
    for n in g.values():
        ct = n.get("class_type", "")
        if ct == "GrowMask" and n["inputs"].get("expand", 0) < 0:
            ero = n["inputs"]["expand"]
        if ct == "FeatherMask":
            feath = n["inputs"].get("left")
    return f"ero={ero} feath={feath}"


def f_params(g):
    steps = scale = None
    for n in g.values():
        if n.get("class_type") == "FitDiTTryOn":
            steps = n["inputs"].get("n_steps"); scale = n["inputs"].get("image_scale")
    return f"nstep={steps} iscale={scale}"


def base_ratio(base: Path):
    if not base.exists():
        return None
    _, _, _, r, _ = prop(base)
    return r


def block(title, finals, base_prefix, params_fn):
    print(f"\n=== {title} ===")
    print(f"{'final':28} {'params':22} {'ident':6} {'hip%':6} {'shldr%':7} {'ratio%':7} {'mism':5} {'base->fin ratio':18}")
    for f in finals:
        g = graph(f)
        idc, hip, sh, ratio, mism = prop(f)
        idx = f.stem.split("_")[-1]
        base = OUT / f"{base_prefix}_{idx}_.png" if base_prefix else None
        br = base_ratio(base) if base else None
        dr = (round(ratio - br, 1) if (ratio is not None and br is not None) else None)
        pr = params_fn(g) if params_fn else ""
        print(f"{f.name:28} {pr:22} {idc:<6.3f} {hip!s:6} {sh!s:7} {ratio!s:7} {mism!s:5} "
              f"{f'{br}->{ratio} ({dr:+})' if dr is not None else '-':18}")


if __name__ == "__main__":
    block("B  (our masks, eroded composite)", sorted(OUT.glob("qiefitdit_normB_*.png")), "qie_baseB", b_params)
    block("F  (native FitDiT masks, no composite)", sorted(OUT.glob("qiefitdit_normF_*.png")), "qie_baseF", f_params)
    A = [f for f in sorted(OUT.glob("qiefitdit_norm_*.png")) if int(f.stem.split("_")[-1]) >= 20]
    block("A  (our masks, grown composite) — new only (>=20)", A, None, None)
