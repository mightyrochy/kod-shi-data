# E-010 — Reconciliation & cleanup (2026-06-19)

**Purpose.** Bring the E-010 record back under METHODOLOGY after a 2026-06-18 session that
violated the rules: a long chain of single Leffa/FitDiT/warping runs, each read by the
AI assistant's eye, was committed as if it produced *findings*. Under METHODOLOGY §1 those
are **Observations** ("single run, or subjective judgment … points where to look; decides
nothing"), never Verified. This document reclassifies them, states the honest position, and
records what to clean. It does not delete experiment records (METHODOLOGY §2: raw results,
including failures, are preserved) and does not rewrite git history.

---

## 1. Process failures that produced the mess (so they are not repeated)

- **Observations committed as findings.** 9 commits (077412c → b697351) phrase single-run,
  eye-judged results as verified outcomes ("chain verified", "warping closed", "Leffa can't
  do skirts", later "it can"). METHODOLOGY §1/§5: AI-assistant visual comparison is an
  Observation source, *never* a verdict source.
- **Fishing / tweak-until-it-looks-better.** ~15 Leffa runs varying person, garment, mask,
  diffusers version, length — exactly the "re-run with tweaked settings until something
  passes" banned by METHODOLOGY §2. No protocol, no pre-stated acceptance criteria.
- **Theory from images, not sources.** A new mechanism was asserted after each run
  (densepose-enforces-legs → no-inter-leg-gap → bare-legs-missing → mask-over-calves-morph)
  without reading the Leffa paper or the `get_agnostic_mask_dc` code that *define* the
  mechanism. Corrected behaviour saved as memory `feedback-research-before-theorizing`.
- **Premature success declarations** reversed by the owner repeatedly (thumbnail-level reads;
  "no distortion" on an image where the skirt visibly melted into the legs).
- **Design divergence not flagged.** E-010 chased dedicated VTON (FitDiT, Leffa) while the
  canonical SYSTEM_DESIGN (§3 item 2, §7) holds that *editing models beat dedicated VTON on
  layered outfits* and sets QIE-2511 holistic + shell as the default. The VTON detour was
  never reconciled with the design.

## 2. Reclassification of 2026-06-18 E-010 claims → Observations

None of the following is decision-grade. Each is a single-run, eye-judged Observation.
They may inform where to look; they decide nothing until verified under METHODOLOGY §2
(protocol + acceptance criteria + ≥2 runs or owner direct evidence) — and most should be
re-grounded against primary sources first (deep-research dossier, §below).

| # | 2026-06-18 claim (as committed) | Honest status |
|---|---|---|
| O-L01 | "Chained FitDiT on source verified (blouse over skirt)" | Observation — 1 run, eye-judged. Identity cosine 0.929/0.976 are instrument numbers but on a single uncontrolled run. |
| O-L02 | "Garment-fidelity instrument: skirt 0.319 / blouse 0.211 DISTS, rank 1/5" | Instrument numbers, but ADVISORY/uncalibrated (no labelled set) and on 1 image. Not decision-grade by its own note. |
| O-L03 | "Warping arm B (geometric) loses; arm C (Leffa) disqualified; warping closed" | Observation — single runs, eye-judged. The "closed/disqualified" verdicts are withdrawn. |
| O-L04 | "Leffa can't do skirts (densepose enforces legs)" then "it can" | Both Observations; the strong capability claims are withdrawn. |
| O-L05 | "Root cause = missing bare legs; expose-legs is the standard fix" | Observation/hypothesis — plausible and partly source-aligned, but asserted from images; to be tested against the DressCode agnostic spec + a protocolled run. |
| O-L06 | "Skirt morphs into legs because the mask covers the calves" | Observation/hypothesis — single comparison, eye-judged. |
| O-L07 | drape.py `measure_on_model` / `agnostic_mask` "validated" | The CODE runs and computes sane numbers (component-level OK); "validated on outfit_001" as a placement method is an Observation, not stage-accepted. |

**What is genuinely established (stands):** only the environment/install facts — Leffa runs
locally (recipe in §protocol addendum: py3.10 venv, torch 2.6.0+cu124, prebuilt detectron2,
densepose-from-source, truststore SSL, trimmed DressCode ckpts, FLUX-Fill present in ComfyUI).
These are reproducible setup facts, not quality findings.

## 3. Authoritative mechanism note (replaces my image-derived theories)

From the actual source `leffa_utils/utils.py::get_agnostic_mask_dc` (read 2026-06-19): for
`lower_body`, the DressCode agnostic mask = `pants(6) + left-leg(12) + right-leg(13)`, dilated,
with upper-clothes + arms fixed. The pipeline (`leffa/pipeline.py:64`) zeroes that region
(`masked_image = src_image*(mask<0.5)`) and the UNet regenerates **legs + lower garment
together**, conditioned on densepose-IUV (concatenated) + the garment via reference attention.
So: the agnostic is meant to contain the legs; on a person wearing opaque full-length trousers
the parser labels the lower body as `pants` with no leg labels, changing the agnostic shape —
this is the correct place to ground the "bare legs" observation, in source, not in image-staring.
Full treatment in the deep-research dossier.

## 4. Cleanup actions

- **Docs:** this file is the honest E-010 status as of 2026-06-19. The 2026-06-18 addenda in
  `protocol.md` and the bullets in `CURRENT_STATE.md` remain as a dated historical record but
  are superseded by this reconciliation for "what is true"; CURRENT_STATE updated to point here.
- **Artifacts:** 90 files (~21 MB) in `results/proto_chain/` are preserved as Observation
  records (METHODOLOGY §2). No deletion without owner permission. If the owner wants them
  pruned, the keep-set is: the FitDiT chain result, the Leffa diagnostic series (SANITY/T1–T5/
  barelegs/maxi), `person_dcstyle`/`person_barelegs`, and the masks — the rest are intermediates.
- **External Leffa install** (`C:\Users\Admin\Leffa`, ~11 GB incl. ckpts) is outside the repo;
  kept as a working VTON toolchain. Runner copies live in this folder for provenance.

## 5. Forward

The next step is NOT another generation run. It is the **deep-research dossier** the owner
requested: read the primary sources (Leffa/DressCode/VTON/editing-model literature) end to
end and write an expert-level account of how garment generation works and which architecture
is right for this project, holding all problems found so far. See
`research/DEEP_RESEARCH_2026-06-19.md`.
