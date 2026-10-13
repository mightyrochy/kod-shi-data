"""E-016 — score every not-yet-reviewed union gui_pose generation vs originals, with its params, so the
owner can untangle which settings were tried. Reuses run_compare.evaluate()."""
import importlib
import json
from pathlib import Path

from PIL import Image

_rc = importlib.import_module("experiments.016_board_builder.run_compare")
evaluate = _rc.evaluate

OUT = Path(r"C:/Users/Admin/ComfyUI/output")
RES = Path(__file__).resolve().parent / "results"
ALREADY = {"00017", "00018", "00022", "00023", "00025"}  # union ones already tabled


def gen_params(path: Path):
    d = json.loads(Image.open(path).info.get("prompt", "{}"))
    ks = lora = None
    for n in d.values():
        ct = n.get("class_type", "")
        if ct == "KSampler":
            ks = n["inputs"]
        if "LoraLoader" in ct:
            lora = n["inputs"]
    return ks, lora


if __name__ == "__main__":
    rows = {}
    for f in sorted(OUT.glob("gui_pose_*.png")):
        idx = f.name[9:14]
        ks, lora = gen_params(f)
        if not ks or not lora or "union" not in (lora.get("lora_name") or ""):
            continue
        if idx in ALREADY:
            continue
        print("...", idx, "str", lora.get("strength_model"), "steps", ks.get("steps"), "cfg", ks.get("cfg"))
        ev = evaluate(f)
        pc = ev.get("proportions_change_pct") or {}
        rows[idx] = {
            "strength": lora.get("strength_model"), "steps": ks.get("steps"), "cfg": ks.get("cfg"),
            "seed": str(ks.get("seed"))[:6],
            "identity": ev.get("identity_cosine"),
            "hip": pc.get("hip_width_norm"), "ratio": pc.get("shoulder_hip_ratio"),
            "mism": ev.get("pose_mismatch_deg"),
            "bl_sim": ev["blouse"]["sim"], "sk_sim": ev["skirt"]["sim"], "sh_sim": ev["shoes"]["sim"],
        }
    (RES / "comparison_all.json").write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
    hdr = f"{'idx':5} {'str':4} {'stp':3} {'cfg':4} {'seed':6} | {'ident':6} {'hip%':6} {'rat%':6} {'mism':5} | {'blsim':5} {'sksim':5} {'shsim':5}"
    print("\n" + hdr)
    print("-" * len(hdr))
    for idx, r in rows.items():
        print(f"{idx:5} {r['strength']!s:4} {r['steps']!s:3} {r['cfg']!s:4} {r['seed']:6} | "
              f"{r['identity']!s:6} {r['hip']!s:6} {r['ratio']!s:6} {r['mism']!s:5} | "
              f"{r['bl_sim']!s:5} {r['sk_sim']!s:5} {r['sh_sim']!s:5}")
