# E-010 — Garment-faithful try-on (garment fidelity is axis #1)

**Status:** UPDATED 2026-06-16 (owner-directed reprioritisation: garment accuracy > body). Approved
direction; generation engine selected in Phase 0. Execute in a separate session — see `STARTER.md`.
Not yet run.
**Supersedes** the earlier body-first / inpaint+body-control framing of this protocol.
**Companion docs:** `ENGINE_LANDSCAPE.md` (engine survey), `GEN_INSTRUMENTS.md` (generation tools),
`EVAL_INSTRUMENTS.md` (measurement). **Governed by:** METHODOLOGY.md §2; design §5/§7; follows E-009.

---

## 1. Decision history that produced this protocol

1. The earlier FLUX-Fill Phase-0 build (`system/workflows/flux_fill_inpaint.json`) is **text-only**
   (person + mask + text, **no board image**). With our colour-less prompt it invents generic clothes →
   **fails garment fidelity by construction**. **Disqualified** (kept only as a body-only control).
   The engine MUST condition the garment on an **image**, never text.
2. We first reframed toward inpaint + body-control. Then the owner corrected the **priority**:
   **garment accuracy is the product** (showing the SPECIFIC item). Body morphology (the E-009 ~9 %
   hip slim) matters but is **secondary** — a recognisable person in the EXACT outfit beats a perfect
   body in an approximate one.
3. Garment exact-reproduction from a reference is the genuine product frontier: generic VTON
   re-synthesises → detail drift. The fidelity tools **keep the real garment pixels** (warping /
   high-res feature injection).

## 2. Axes, in priority order

1. **Garment fidelity (axis #1, HARD gate).** Per item: "is this the same item?" — measured by the
   `EVAL_INSTRUMENTS` stack (retrieval-rank vs decoys via FashionSigLIP; DISTS; colour hue/chroma +
   palette; silhouette descriptors; OCR for logo/print; Qwen-VL detail checklist; owner per-item verdict).
2. **Identity (axis #2).** ArcFace face cosine ≥ 0.57 and not below baseline; (hair/skin owner-checked).
3. **Body morphology (axis #3, secondary).** `body_pose` skeletal hip/shoulder; protect-by-construction
   (source pixels outside the clothing) + optional DensePose/SMPL-shape. Measured and reported, but it
   does **not** block acceptance unless the body is grossly wrong — the ~9 % slim is polish.

## 3. Generation instruments (see GEN_INSTRUMENTS.md)

Core garment-transfer chosen for detail: **FitDiT** (DiT, high-res garment feature injection, ComfyUI)
primary; **DiffFit / GP-VTON** warping fallback. Plus **per-item high-res reference conditioning** (the
hybrid board's per-item crops, not the 768 tiled board), **high-res single-item local repair** per
garment (design §5), and **OmniTry** for accessories (belt/earrings/shoes). Identity (PuLID/InstantID)
and body (DensePose/SMPL) ride along as secondary.

## 4. Engine selection — Phase 0 (garment-first; see ENGINE_LANDSCAPE.md)

Pick the stack by, in order: (a) **garment exact-fidelity** on our specific items; (b) coverage of
**multi-item + accessories**; (c) 16 GB local feasibility; (d) license (Leffa MIT / OmniTry CC-BY-SA
commercial-OK; CatVTON/IDM-VTON NC = prototype only); identity/body secondary.

Candidate cores: **FitDiT** (detail), **DiffFit/GP-VTON** (warping), **IDM-VTON** (best texture, NC),
**Leffa** (MIT, light) — single-garment, applied **per garment** (blouse → skirt); **OmniTry** for
accessories. **Cloud (FASHN/Kling/GPT-4o)** is the detail ceiling and a legitimate V1 fallback.

Phase 0 procedure: query the live ComfyUI `/object_info`; for the top garment-fidelity candidate
produce ONE output and review at an **owner checkpoint** against the EVAL stack. If no local stack
reproduces our items acceptably → escalate to cloud or a Garments2Look-style fine-tune (rented GPU),
do not force a weak local engine.

## 5. Method (A/B)

| Arm | Path |
|-----|------|
| A — baseline | current full-regen (QIE Lightning, E-009 R1) — approximate garment, ~9 % body slim |
| B — garment-first | FitDiT/warping core (per garment) + per-item high-res refs + single-item local repair + OmniTry accessories |

Fixed: `person_front.png`; `outfit_001`; per-item references from `hybrid_mask_crop` crops (SHA-verified);
seeds [42, 123].

## 6. Acceptance (fixed before results)

- **Garment (axis #1, HARD gate):** for every required item, target ranks top-K in retrieval (vs decoys),
  DISTS/colour/silhouette/detail not worse than A, owner per-item detail verdict **not worse**. This is
  the PASS axis. Calibration set required (see EVAL_INSTRUMENTS).
- **Identity:** face cosine ≥ 0.57 and not below A.
- **Body (secondary):** measured + reported; blocks only if grossly wrong; the ~9 % slim is acceptable
  for V1 unless owner says otherwise. Body refinement is a later lever (DensePose/SMPL or fine-tune).
- No aggregate score; owner verdict per axis is the acceptance.

## 7. Honest unknowns

- Exact-item reproduction (buttons / exact shade / wedge geometry) is the real frontier; even SOTA
  approximates; cloud is the ceiling.
- No single LOCAL open model cleanly covers {multi-item + accessories + exact detail + non-idealised
  body} — likely a small pipeline (FitDiT + local repair + OmniTry) or cloud. This is a kill-criterion check.
- FitDiT/OmniTry exact VRAM + license + whether they handle OUR multi-item outfit must be verified in Phase 0.
- The garment-fidelity instrument itself needs a labelled calibration set before its numbers are trusted.

## 8. Cost

Phase 0 engine selection + 1 test output per candidate: 1–2 sessions. Build EVAL stack (FashionSigLIP +
DISTS + calibration): ~1 session. Phase 1 A/B + measurement: GPU batches. Local repair / OmniTry: +1–2 sessions.

---

## Owner sign-off

- [x] Garment fidelity is axis #1 (HARD gate); identity #2; body #3 (secondary, non-blocking unless gross).
- [x] Generation core = detail-preserving (FitDiT/warping) + per-item high-res + local repair + OmniTry;
      text-only / generic re-synthesis disqualified for garment.
- [x] Engine selected in Phase 0 from ENGINE_LANDSCAPE (garment-first); cloud is a legitimate fallback.
- [x] Garment-fidelity instrument (EVAL_INSTRUMENTS) must be built + calibrated to make axis #1 measurable.

**Signed:** owner, 2026-06-16 (directed this reprioritisation). Execution delegated to a separate session.
