# Instrument calibration on the skirt triplet (2026-06-21)

Owner plan step 2: use the triplet — **reference** (textured `skirt_front crop.png`), **flat** (E-012 QIE
holistic skirt), **good** (e013hi FitDiT-repaired skirt, owner-accepted) — to calibrate the gates. Measured
on the **interior fabric only** (skirt mask eroded 35 px → no edges/slit), each interior crop resized to
256² for the texture energy; DISTS + FashionSigLIP sim vs the reference's interior patch.

## Measurements
| anchor | interior HF | HF ratio vs ref | DISTS | FashionSigLIP sim |
|--------|-------------|------------------|-------|-------------------|
| FLAT (E-012 QIE) | 48.7 | 0.29 | 0.409 | 0.845 |
| GOOD (e013hi FitDiT) | 50.3 | 0.30 | 0.408 | **0.922** |
| REFERENCE | 167.6 | 1.00 | — | — |

## What the triplet revealed (honest, and a correction)
1. **Interior fabric texture is the SAME in flat and good** (HF 48.7 vs 50.3; ratio 0.29 vs 0.30; DISTS
   equal). Neither QIE nor FitDiT reproduces the fabric weave — both reach ≈ **0.3 of the reference**. This
   is a **shared generator ceiling** at full-frame resolution, not something the FitDiT repair fixed.
2. **Correction of an earlier claim.** The "texture 2.1 → 2.8" gain reported before was measured on rough
   crops contaminated by the **slit and edges**, not interior fabric. On clean interior fabric there is no
   texture gain. Recorded so the record is accurate.
3. **The real flat→good discriminator is FashionSigLIP sim (0.845 → 0.922)** — i.e. garment
   STRUCTURE/identity (the slit, drape, silhouette). The "flat" the owner saw in the QIE skirt was the
   **absence of structure** (a smooth featureless block), not missing micro-weave; FitDiT restored the
   structure, lifting sim.

## Provisional calibrated thresholds (1 garment, 3 anchors — NOT the full set)
- **Garment-correspondence (the useful discriminator): FashionSigLIP `sim ≥ 0.90` = strong "same good
  item"** (good 0.922 passes; flat 0.845 = "same item, weaker render"). Update the correspondence roll-up:
  `sim < 0.85` = IDENTITY_LOW (was 0.80); `0.85–0.90` = acceptable-but-imperfect; `≥0.90` = strong.
- **Texture interior-ratio ≈ 0.30 = the achievable full-frame ceiling** — both generators hit it, so it
  does NOT separate flat/good here. Role: a **regression guard** (flag a future result that drops well
  below 0.30), and an absolute "weave not reproduced" indicator — NOT a flat-vs-good discriminator for
  full-frame skirts. Measure it on **interior fabric** (eroded mask), never on a bbox with edges/slit.
- DISTS (0.408 both) does not discriminate this pair.

## Caveats
- **1 garment, 3 anchors → provisional**, not decision-grade. The full set (~150–200 labelled crops across
  garments, EVAL_INSTRUMENTS) is still needed to harden these into thresholds that generalise.
- The thresholds are scale-dependent: the texture ceiling 0.30 is for a garment at full-body frame; a
  per-item repair CROP (garment filling the frame) can and should reach higher — calibrate that separately.

## Implication
If real fabric **weave** is wanted (beyond the 0.30 ceiling), neither QIE nor FitDiT delivers it at
full-frame; the lever is a per-item repair where the garment fills the frame (more pixels-on-weave), or a
dedicated texture-transfer step — a separate experiment, not the current spine.
