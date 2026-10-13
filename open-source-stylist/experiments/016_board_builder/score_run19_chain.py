"""E-016 — measure identity + body proportions along the combined run-19 chain
(base -> padded canon -> skirt-FitDiT -> blouse-FitDiT final) vs the person, to quantify what each
FitDiT pass does to identity and body shape. No generation."""
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from system.gates import body_pose
from system.gates.identity import compare_faces

OUT = Path(r"C:/Users/Admin/ComfyUI/output")
ROOT = Path(__file__).resolve().parents[2]
PERSON = ROOT / "assets/person/person_front.png"

CHAIN = [
    ("base        qie_base_00024", OUT / "qie_base_00024_.png"),
    ("padded      canon34_00013", OUT / "canon34_00013_.png"),
    ("skirt-pass  qiefitdit_skirt_00019", OUT / "qiefitdit_skirt_00019_.png"),
    ("blouse-pass qiefitdit_norm_00019 (FINAL)", OUT / "qiefitdit_norm_00019_.png"),
]


def main():
    print(f"{'stage':42} {'ident':7} {'hip%':7} {'shldr%':8} {'ratio%':8} {'pose_mism':9}")
    print("-" * 90)
    for label, p in CHAIN:
        if not p.exists():
            print(f"{label:42} MISSING")
            continue
        idc = compare_faces(str(p), str(PERSON)).get("cosine", float("nan"))
        bp = body_pose.compare(str(PERSON), str(p))
        pc = bp.get("change_pct") or {}
        print(f"{label:42} {idc:<7.3f} "
              f"{pc.get('hip_width_norm', float('nan')):<7.1f} "
              f"{pc.get('shoulder_width_norm', float('nan')):<8.1f} "
              f"{pc.get('shoulder_hip_ratio', float('nan')):<8.1f} "
              f"{bp.get('pose_mismatch_deg', float('nan')):<9.2f}")


if __name__ == "__main__":
    main()
