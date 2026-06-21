# FitDiT audit — "for real, like QIE" (2026-06-21)

Owner-directed audit: read FitDiT against its canonical source and our wiring, find+fix any bug like the
QIE wrong-workflow bug. Method: read the node source + our E-010 invocation + **verify against ground
truth** (look at the actual results), not trust the project's own docs.

## Finding: FitDiT is SOUND — no QIE-style wiring bug
1. **The node is canonical.** `custom_nodes/FitDiT-ComfyUI/src/utils_mask.py::get_mask_location` is the
   official FitDiT agnostic-mask logic. Lower-body = a rectangle from the hip line (`body[8/11]`) down to
   the ankles/feet (`body[10/13]`, foot keypoints), full width across both legs — the standard VTON
   lower-body agnostic. Upper/Dresses likewise. We did not hand-build this (unlike the QIE workflow).
2. **Our invocation is canonical.** E-010 (`proto_chain.py`, `proto_filled_skirt.py`) called
   `FitDiTMaskGenerator(category="Lower-body")` + `FitDiTTryOn(resolution="768x1024", n_steps=20,
   image_scale=2.0)` — FitDiT's own defaults. No wrong-latent / missing-patch class of bug exists here.
3. **The skirt→pants FAIL was an INPUT-topology bug on OUR side, not FitDiT.** The garment crop
   `skirt_front_fitdit.png` is a flat-lay with the front slit **cut through to background** → a bifurcated
   (two-column) silhouette → FitDiT reads two legs → renders pants/culottes. E-010 diagnosed this
   correctly (STATUS_2026-06-16: "the slit-skirt failure is masking/category, NOT model choice").

## Ground-truth verification (the QIE lesson: verify, don't trust the doc)
- `results/proto_chain/skirt_result.png` — through-slit input → central through-gap showing the legs/jeans
  ("схожа на штани"). The FAIL.
- `results/proto_chain/skirt_filled_result.png` — after `proto_filled_skirt.fill_slit_gap` makes the
  silhouette **continuous** (slit kept as an internal dark line) + native FitDiT auto mask → **a proper
  brown maxi skirt with a slit, not pants.** The fix WORKS. Confirmed by looking, not by the doc.

## Conclusion — distinct from QIE
- **QIE (E-009):** a real hidden wiring bug (wrong latent + missing model patches); the E-009 "drift/model
  limit" conclusion was bug-contaminated. Fixed in commit a3a896c.
- **FitDiT (E-010):** NO hidden wiring bug. The node is faithful, our call was canonical, and the
  skirt→pants was correctly understood as a garment-silhouette-topology INPUT problem — verified here by
  ground truth. **E-010's FitDiT conclusion stands.** The earlier worry ("did E-009/E-010 stand on a bug?")
  resolves YES for E-009, NO for FitDiT.

## What is actually open (build items, not bug fixes)
- **Garment representation.** The fix is to feed FitDiT an "as-worn" continuous silhouette (slit as an
  internal feature, not a through-gap) — already spec'd in `DRAPE_SYNTHESIS.md`. The crude `fill_slit_gap`
  works but removes the *real* slit (axis-1 detail loss); a proper continuous-silhouette builder keeps it.
- **Resolution lever untested.** E-010 used FitDiT's lowest option `768x1024`; `1152x1536` / `1536x2048`
  are untested and may matter for fabric texture (cf. the E-012 flat-skirt / texture-gate finding).
- **Strategic:** the QIE holistic+repair spine now works (E-012), so FitDiT is a per-garment *alternative*,
  not on the critical path. Investing in the FitDiT garment-rep pipeline is optional, owner's call.
