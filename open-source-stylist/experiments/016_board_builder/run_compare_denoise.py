"""E-016 — score the denoise sweep (gui_pose 00040-00051, base 0.5/10/cfg5) and aggregate by denoise,
to see whether denoise<1.0 reduces the body-proportion drift and at what cost to garment fidelity."""
import importlib
import json
import statistics as st
from collections import defaultdict
from pathlib import Path

from PIL import Image

_rc = importlib.import_module("experiments.016_board_builder.run_compare")
evaluate = _rc.evaluate
OUT = Path(r"C:/Users/Admin/ComfyUI/output")
RES = Path(__file__).resolve().parent / "results"


def denoise_of(path: Path):
    d = json.loads(Image.open(path).info.get("prompt", "{}"))
    for n in d.values():
        if n.get("class_type") == "KSampler":
            return n["inputs"].get("denoise")
    return None


if __name__ == "__main__":
    rows, by_dn = {}, defaultdict(list)
    for f in sorted(OUT.glob("gui_pose_*.png")):
        idx = int(f.name[9:14])
        if not (40 <= idx <= 51):
            continue
        dn = denoise_of(f)
        ev = evaluate(f)
        pc = ev.get("proportions_change_pct") or {}
        sims = [ev[g]["sim"] for g in ("blouse", "skirt", "shoes") if ev[g]["sim"] is not None]
        row = {"denoise": dn, "identity": ev["identity_cosine"],
               "hip": pc.get("hip_width_norm"), "ratio": pc.get("shoulder_hip_ratio"),
               "mism": ev["pose_mismatch_deg"], "garm_sim_mean": round(st.mean(sims), 3) if sims else None,
               "bl": ev["blouse"]["sim"], "sk": ev["skirt"]["sim"], "sh": ev["shoes"]["sim"]}
        rows[f.name[9:14]] = row
        print(f"  {f.name[9:14]} dn={dn} id={row['identity']} hip={row['hip']} garm_sim={row['garm_sim_mean']}")
        if row["identity"] is not None and row["hip"] is not None:
            by_dn[dn].append(row)
    (RES / "comparison_denoise.json").write_text(json.dumps(rows, indent=2, default=str) + "\n", encoding="utf-8")
    print("\n=== aggregated by denoise ===")
    print(f"{'denoise':8}{'n':3}{'id_mean':9}{'|hip|mean':11}{'hip_rng':14}{'garm_sim_mean':14}")
    for dn in sorted(by_dn, reverse=True):
        v = by_dn[dn]
        ids = [x["identity"] for x in v]; hips = [abs(x["hip"]) for x in v]
        gs = [x["garm_sim_mean"] for x in v if x["garm_sim_mean"] is not None]
        print(f"{dn!s:8}{len(v):<3}{round(st.mean(ids),3)!s:9}{round(st.mean(hips),2)!s:11}"
              f"{f'{min(hips):.1f}-{max(hips):.1f}':14}{round(st.mean(gs),3)!s:14}")
