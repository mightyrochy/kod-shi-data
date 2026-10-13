# E-016 — combined QIE+FitDiT workflow debug status (2026-06-23)

Workflow: `experiments/016_board_builder/qie_fitdit_norm_GUI.json` (GUI). QIE half = `system/workflows/qie2511_vton_pose.json`.

## CONFIRMED problems (looked at the data, all runs)
1. **Blouse mask eats the skirt — CONFIRMED across all 18 FitDiT-chain runs.** `GroundingDinoSAMSegment("blouse")`
   on the skirt-intermediate produces a mask covering torso **+ the whole skirt down to the ankles** (blouse+skirt
   are one connected garment). The Upper-body FitDiT pass then regenerates that whole region → the brown skirt is
   destroyed → **final = pale baggy pants**, every run. (Skirt pass itself is fine: brown skirt.)
   - Fix options: bound the blouse mask to the upper body — semantic ATR upper-clothes / intersect with an upper
     region / use FitDiTMaskGenerator's own Upper-body agnostic mask for the blouse.
2. **QIE BASE degradation — RESOLVED 2026-06-25 (see RESOLUTION below). The combined graph does NOT degrade QIE.**

   *Original (now-falsified) framing kept for the record:*
   **QIE BASE is degraded since switching to the combined workflow — NOT yet isolated.** Owner: no good QIE base
   since combining. At denoise 1.0 the blouse is cream (ok) but the **skirt comes out olive/green** in several runs,
   and steps=5 → camo garbage. QIE wiring is byte-identical to the standalone `qie2511_vton_pose` and the board/person
   files are identical (md5 match). So the cause is NOT wiring/inputs. UNRESOLVED suspects: union pose-LoRA (0.5),
   DWPose image3, VRAM pressure from FitDiT+SAM+GroundingDINO co-loaded on 16 GB, or seed. **This breaks BEFORE the
   blouse mask** and is the more fundamental issue.
   - denoise 0.9 was a real mistake (kept the person's original jeans → pants bleed); 1.0 is better but olive persists.
   - Resolution: pad-to-3:4 once (ImageScale→1024×1536 + ImagePadForOutpaint→1152×1536) + crop-at-end FIXED the
     earlier ghost/misalignment from the stretch-back round-trip.

## RESOLUTION of problem 2 — QIE base (2026-06-25, from full data + full-res, no new generation)
Method: `diff_qie_graph.py` (diff the embedded execution graph of good-standalone `qie_pose.png` vs combined
`qie_base_00023`) + `scan_qie_base_params.py` (tabulate the sampler config of every `qie_base_*.png`) + eyeballing
the full-res images. Findings:
- The combined graph's QIE topology is identical to standalone; only the **sampler config differed**. The
  standalone-good config (union 1.0 / steps 20 / cfg 4.0 / denoise 1.0) was **NEVER run** in the combined graph —
  the whole sweep sat at union 0.5 / cfg 5.0 and varied only steps (5/10/20), denoise (0.9–1.0), seed.
- **A clean QIE base IS reachable in the combined graph** — proven by `qie_base_00001` (steps 20, cfg 4.0, denoise
  1.0, no LoRA), `qie_base_00010` and `qie_base_00018` (steps 20, cfg 5.0, union 0.5, denoise 1.0): all show the
  correct brown skirt + good proportions. So the combined graph does NOT degrade QIE. VRAM/seed/LoRA-pose are
  **ruled out** as the cause.
- (FIRST PASS — PARTLY FALSIFIED, see CORRECTION below) I claimed two undercooked knobs break the base:
  steps too low (20 clean; 10 pants `00023`; 5 garbage `00013`) and denoise<1.0 contamination (`00016`).

### CORRECTION (2026-06-25, later — full data on the steps-10 bucket)
The "steps 10 = pants" claim was an OUTLIER overgeneralization (I'd only looked at `00023`). Looking at ALL
steps-10 `qie_base` at denoise 1.0: `00008`, `00009`, `00015`, `00022` all show the CORRECT brown skirt (and
`00006` at dn0.9 too). Only `00023` is pants. So **steps 10 is NOT broken — ~4/5 clean**, and the owner's earlier
multi-run analysis shows steps 10 additionally WINS identity + hip-drift. steps is NOT the discriminator (10 and
20 both ~clean at dn1.0; `00019` foggy at steps 20 is the matching steps-20 outlier). Corrected picture:
  - **Keep the owner's config: union 0.5 / steps 10 / cfg 5 / denoise 1.0.** Base is clean ~75–80% of seeds.
  - denoise 1.0 is the safe choice (0.9 occasionally contaminates: `00016`), not a hard requirement.
  - Residual base failures (`00023` pants, `00019` foggy) are **seed variance**, low rate, present at both step
    counts — a variance/seed issue, not a config one.
  - **The systematic FINAL "pale pants" is NOT the base — it is problem 1 (blouse FitDiT mask eats the whole
    skirt), confirmed across all final runs.** The base mostly yields a correct skirt; FitDiT then destroys it.

## NEXT
1. The QIE base config stays as the owner set it (0.5 / 10 / cfg5 / denoise 1.0). No steps change.
2. Fix the blouse mask (problem 1) — the real systematic failure — bound it to the upper body.

## Mistakes made this session (so they are not repeated)
Theorized causes from downscaled thumbnails instead of gathering full data first; falsely claimed "all good
standalone runs were denoise 1.0" (owner swept 0.8–0.95); over-claimed board color-contamination. Gather full
data + look at full-res + isolate ONE variable before any cause claim.
- (2026-06-25) Theorized a VRAM / combined-graph cause for the QIE degradation BEFORE diffing the actual run
  configs. The data showed it was plain sampler-config drift (steps 10/5, denoise 0.9) — the working config was
  simply never tried in the combined graph. Diff the embedded run params FIRST.
