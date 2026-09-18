"""E-016 — numeric comparison of 4 results vs the originals, with all our instruments.
2 mine (union pose-control LoRA) + 2 owner (Lightning LoRA). Identity + body-proportions at image level;
colour / structure / FashionSigLIP-sim per garment region (ATR-parsed on the result)."""
import json
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

from system.gates import body_pose
from system.gates.garment_fidelity import _region_to_temp, siglip_similarity
from system.gates.identity import compare_faces
from system.pipeline import check_garment
from system.segmentation.parsing import garment_masks

ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "assets/outfits/outfit_001"
RES = Path(__file__).resolve().parent / "results"
ISO = RES / "isolate"
OUT_DIR = ComfyOUT = Path(r"C:/Users/Admin/ComfyUI/output")
PERSON = ROOT / "assets/person/person_front.png"
TMP = RES / "_cmp_tmp"; TMP.mkdir(exist_ok=True)

RESULTS = {
    "mine_pose_s42 (union)": RES / "qie_pose.png",
    "mine_pose_s20240613 (union)": RES / "qie_seedC.png",
    "owner_s42 (lightning)": ComfyOUT / "gui_pose_00001_.png",
    "owner_s2 (lightning)": ComfyOUT / "gui_pose_00002_.png",
}
GARMENTS = [("blouse", "upper", ISO / "blouse_front_mask.png"),
            ("skirt", "skirt", ISO / "skirt_front_mask.png"),
            ("shoes", "shoes", ISO / "shoes_mask.png")]


def evaluate(img: Path) -> dict:
    rep = {"identity_cosine": round(compare_faces(str(img), str(PERSON)).get("cosine", float("nan")), 4)}
    bp = body_pose.compare(str(PERSON), str(img))
    rep["proportions_change_pct"] = bp.get("change_pct")
    rep["pose_mismatch_deg"] = bp.get("pose_mismatch_deg")
    masks = garment_masks(str(img), [g[1] for g in GARMENTS])
    for name, region, ref in GARMENTS:
        m = masks[region]
        cg = check_garment(img, name, ref, m)
        try:
            crop = _region_to_temp(str(img), m, TMP / f"{img.stem}_{name}.png")
            sim = siglip_similarity(str(crop), str(ref))
        except Exception:
            sim = None
        rep[name] = {"dE": cg.get("dE"), "colour": cg.get("colour_verdict"),
                     "structure": cg.get("structure", {}).get("verdict"),
                     "anomaly": cg.get("structure", {}).get("anomaly"),
                     "sim": round(sim, 4) if sim is not None else None,
                     "texture": cg.get("texture_recorded")}
    return rep


if __name__ == "__main__":
    report = {}
    for label, path in RESULTS.items():
        print(f"... {label}  ({path.name})")
        report[label] = evaluate(path)
    (RES / "comparison.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    print("\n" + json.dumps(report, indent=2, default=str))
