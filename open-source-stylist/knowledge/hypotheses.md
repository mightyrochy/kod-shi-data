# Hypotheses & observations

Append-only, date-stamped. Rules: METHODOLOGY.md §1.
Nothing here is decision-grade. Each entry names the experiment that would verify it.

---

## 2026-06-10 — imported from the archived attempt (owner decision: none is hard proof)

Source: archive/FINDINGS.md and archived run records. All produced by single runs,
VLM judgments, or uninstrumented visual comparison.

- **H-COLOR** — Color words in prompts override visual references and degrade color
  fidelity (observed once: "pale ivory" text produced cream blouse vs lemon-green
  reference; removal improved color same-day). → Verify: E-007.
- **H-REF-CONTAMINATION** — Product reference photos containing model bodies or
  competing items contaminate conditioning: body proportions pulled toward reference
  models; black heels from a skirt photo appeared instead of the referenced green
  wedges (run 000003 observation). → Verify: E-008.
- **H-PROPORTIONS** — QIE-2511 reduces chest/waist when adding clothing (observed
  in runs 1–2, possibly a special case of H-REF-CONTAMINATION). → Verify: E-008 +
  proportion gate on E-005 baseline.
  **2026-06-12: measured support on this config.** E-005 (Lightning 4-step) shows
  systematic distortion on all 5 seeds: waist narrows (−4% to −11%), shoulders widen
  (+4% to +16%), hips widen (+5% to +9%). Owner confirmed visual distortion on seed_1337.
  Still a hypothesis — cause unknown (body-type mapping? reference contamination?
  Lightning-specific?). Remains open until E-008 or a dedicated ablation.
- **H-PROMPT-WEAK** — Prompt influence is weak; the model follows the reference panel.
  → Indirectly probed by E-007; full test deferred.
- **H-40STEPS** — "40 steps is worse than 4" was observed with Lightning LoRA likely
  still enabled (outside its regime) — confounded. → Verify: bench rows 1–3 (Stage 6).
- **H-LIGHTNING** — Lightning-4 trades detail for speed. Official sources claim
  otherwise; no rigorous same-seed comparison exists. → Verify: bench rows 1–3.
- **H-DUALVIEW** — Dual-view (front+side one canvas) breaks outfit coherence between
  views. → Deferred to post-V1 (design §9 sharpened hypothesis).
- **H-VLM-LOWRES** — Qwen3-VL-8B evaluation hallucinates at ~464×672 (called dark
  green shoes black; missed present earrings) and improves at higher resolution.
  → Verify: E-009 (calibration with resolution as a variable).
- **H-FLUX-LOCALITY** — FLUX Fill masked inpaint is local (0.048% change outside
  mask, archived single run) but text-only conditioning cannot do reference-faithful
  repair. → Locality re-verified implicitly in E-011 if FLUX Fill is used; the
  reference-repair claim is design-level (see SYSTEM_DESIGN §6 stage 7).
- **H-AI-UPSCALE-FACES** — AI upscalers (RealESRGAN x4plus, 4x-UltraSharp) distort
  faces on this person photo; plain LANCZOS does not (owner confirmed distortion
  visually, single image). Unknown whether upscaled-input artifacts actually harm
  generation: run 000003 used a distorted 4x input and produced the best result so far.
  → Verify: input-preprocessing comparison if input resolution becomes a decision
  point (fold into E-006).
- **H-ENV** — Environment facts observed 2026-06-10: ComfyUI on :8000 (not :8188),
  v0.24.1; LM Studio REST v1 with explicit unload (~1s); Qwen3-VL-8B cold load ~12s,
  warm call ~0.6s; QIE-2511 fp8 generation 4-step ~34s including load.
  → Re-verified automatically by `system/env_check.py` at Stage 0 (cheap,
  deterministic — promotes to Verified on reproduction).

---

## 2026-06-12 — E-006 observations (single experiment, K=5 per tier)

- **O-RES-001** — Color dE for top/bottom improves monotonically with resolution.
  High+ (1120x1600) achieved top=1.54, bottom=1.65 dE vs baseline 3.52/2.97.
  Gain is real but cannot be exploited without solving the identity failure at
  that resolution. → May revisit if identity at High+ is resolved through other means.

- **O-RES-002** — QIE-2511 Lightning generates head-cropped outputs (face
  undetectable) at Low (576x816) on 4/5 seeds and at High+ (1120x1600) on 5/5
  seeds. High (896x1280) avoids head cropping but identity is highly stochastic
  (1/5 PASS). Interpretation: Lightning LoRA is conditioned near 720-1024px; large
  deviations cause compositional failures. Single experiment; would require a wider
  resolution sweep or different LoRA to verify the mechanism.

- **O-RES-003** — High+ (1120x1600) shows consistent 346MB VRAM residual after
  each generation (vs ~10GB for Low). Possible: ComfyUI aggressively offloads to
  system RAM under VRAM pressure at this resolution, releasing GPU memory between
  seeds. Mechanism not confirmed.

- **O-SEG-GAP-001** — **RESOLVED 2026-06-13.** Pairwise garment overlap check
  implemented (`system/segmentation/sanity.py`, commit 5f8ceda). Check fires when
  overlap_pixels / min(area_a, area_b) > 20%. FAIL test added. First live
  detection: 3/5 seeds in E-008 (top absorbing bottom/belt on near-zero-identity
  outputs). No longer an open gap.

---

## 2026-06-13 — E-008 results (H-REF-CONTAMINATION verdict + new observations)

**H-REF-CONTAMINATION — verdict (see V-REF-002 + correction for numbers):**
- Proportions: **CONFIRMED** — raw panel adds ~10pp distortion vs cropped.
  Remaining baseline distortion (11.16% with cropped panel) is not from contamination.
- Identity: **CONFIRMED** (extended scope) — full product photos cause complete
  identity collapse (cosine ~0). Mechanism: model generates the product model's
  face/body instead of the input person's.
- Shoes (raw condition): **CONFIRMED** by owner visual review (2026-06-13). All 5
  raw-condition seeds produced black shoes; one became high heels — matching the
  black-heeled model in the uncropped skirt reference photo. Gate mean dE (13.82 vs
  14.03) was insensitive to this shift. See V-REF-002 correction.
- Shoes (cropped condition / E-005 baseline): contamination source removed; shoes
  still fail (14 dE, high variance). Cause unknown — different from contamination.

**H-PROPORTIONS — partially explained:**
- E-008 shows contamination accounts for ~10pp of the proportions distortion.
- Cropped-panel baseline (11.16%) is not explained by contamination.
- Remaining cause still open. Next candidate: Lightning-specific body-type mapping
  (bench rows 2-3 in Stage 6 will test this with same seeds, no-Lightning config).

**O-E008-001** — Bottom color is better in raw condition than cropped (0.89 vs
2.97 dE mean). On seeds with clean bottom masks (42/789/1337): 0.30/0.74/1.20 dE.
The full skirt reference photos give the model a stronger color signal for the skirt
region than garment-only crops. Effect is moot given identity failure. Cause
unknown — may relate to how QIE-2511 attends to large-area high-color-contrast
references. Not actionable in V1 given the rule from V-REF-001.

---
