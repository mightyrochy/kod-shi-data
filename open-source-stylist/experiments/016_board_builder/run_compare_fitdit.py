"""Score the chained-FitDiT finals (skirt+blouse) vs originals + aggregate."""
import importlib, json, statistics as st
from pathlib import Path
_rc = importlib.import_module("experiments.016_board_builder.run_compare")
OUT = Path(r"C:/Users/Admin/ComfyUI/output")
RES = Path(__file__).resolve().parent / "results"
if __name__ == "__main__":
    rows = {}
    for f in sorted(OUT.glob("fitdit_0*.png")):
        ev = _rc.evaluate(f); pc = ev.get("proportions_change_pct") or {}
        sims = [ev[g]["sim"] for g in ("blouse","skirt","shoes") if ev[g]["sim"] is not None]
        rows[f.name[7:12]] = {"identity": ev["identity_cosine"], "hip": pc.get("hip_width_norm"),
            "ratio": pc.get("shoulder_hip_ratio"), "mism": ev["pose_mismatch_deg"],
            "bl": ev["blouse"]["sim"], "sk": ev["skirt"]["sim"], "sh": ev["shoes"]["sim"],
            "garm_sim": round(st.mean(sims),3) if sims else None}
        print("  done", f.name[7:12])
    (RES/"comparison_fitdit.json").write_text(json.dumps(rows,indent=2,default=str)+"\n",encoding="utf-8")
    good=[r for r in rows.values() if r["mism"] is not None and r["mism"]<10 and r["hip"] is not None]
    print("\nidx   id     hip    ratio  mism  garmSim")
    for idx,r in rows.items():
        print(f"{idx} {r['identity']!s:6} {r['hip']!s:6} {r['ratio']!s:6} {r['mism']!s:5} {r['garm_sim']}")
    if good:
        print(f"\nclean (mism<10): n={len(good)} id_mean={round(st.mean([r['identity'] for r in good]),3)} "
              f"|hip|_mean={round(st.mean([abs(r['hip']) for r in good]),2)} "
              f"hip_rng={min(abs(r['hip']) for r in good):.1f}-{max(abs(r['hip']) for r in good):.1f} "
              f"garmSim_mean={round(st.mean([r['garm_sim'] for r in good if r['garm_sim']]),3)}")
