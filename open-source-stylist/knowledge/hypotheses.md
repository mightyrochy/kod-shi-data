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

**O-E008-002** — Raw condition produces a generic-fashion-model effect (2026-06-13,
owner visual review of all 5 seeds). Full-body product photos in the reference
panel cause the model to output "a standard fashion photo with a generic model in
generic clothes" rather than "the input person in the specific outfit." Per-item:
blouse → white in 4/5 seeds (generic shirt default); earrings → grey/silver disc
with arbitrary pattern (disc shape preserved, but color and texture default to
generic jewelry); shoes → all black, one high-heeled (contamination from skirt
reference model's heels). This is a unified mechanism, not independent per-item
hits. The garment-only crop rule (V-REF-001) is the direct fix.

**O-E008-001** — Bottom color is better in raw condition than cropped (0.89 vs
2.97 dE mean). On seeds with clean bottom masks (42/789/1337): 0.30/0.74/1.20 dE.
The full skirt reference photos give the model a stronger color signal for the skirt
region than garment-only crops. Effect is moot given identity failure. Cause
unknown — may relate to how QIE-2511 attends to large-area high-color-contrast
references. Not actionable in V1 given the rule from V-REF-001.

---

## 2026-06-13 — E-007 board-contamination forensics (owner-directed re-verification)

Context: an E-007 session report claimed a "mask regression" and diagnosed it as
"GroundingDINO non-determinism, raise threshold to 0.5". The owner distrusted the
report. Ground-truth re-verification from disk (and from VIEWING the images, which
neither the session nor the first review did) established the following.

**Verified facts (disk + measurement + visual):**
- **O-BOARD-001** — The E-007 reference panel is contaminated: blouse front/back and
  skirt front crops include the product model's head, face, and trousers. Face
  detector (insightface) confirms it deterministically: E-005 panel = **0 faces**,
  E-007 panel = **3 faces** (det scores 0.73, 0.73, 0.87). The clean/contaminated
  split is cleanly separable by a no-face check.
- **O-BOARD-002** — Panel garment-mask coverage doubled in E-007 vs E-005 for the
  full-body model photos: blouse_front 19.9→39.5%, blouse_back 19.4→39.8%,
  skirt_front 9.0→16.4%; stable for clean product shots (belt 13.3%, earrings 1.9%,
  shoes 10.5%, skirt_back ~11%). The doubled masks are the model's body+head pulled
  into the crop.
- **O-BOARD-003** — Same prompt ("top"/"bottom"), same threshold (0.3), same image,
  byte-identical segmentation code (git diff E-005↔E-007 = only the dead, uncalled
  `_largest_area_mask`); yet masks differ. So the board build is a **run-to-run
  lottery**: E-005 happened clean, E-006 reused it (skip-if-exists), E-007 rebuilt
  and lost. Not "fine until now" by design — fine by luck.
- **O-BOARD-004** — The board NEVER used the prompts the owner validated in E-001.
  E-001 (V-SEG-002, owner-approved) segmented garments with `"blouse . shirt . top"`
  and `"skirt"`. The panel builder uses the adapter's generic `"top"`/`"bottom"` —
  exactly the words V-SEG-004 found grab the full silhouette. The validated masks and
  the board masks are different code paths.

**Corrections to the session report (it was wrong):**
- "belt/earrings/shoes masks byte-identical E-005↔E-007" — FALSE. All masks differ by
  bytes; only coverage% matched on the stable items.
- "framing regression in E-007" — NOT supported. Person-mask framing is identical
  E-005↔E-007 seed_42 (coverage 1.0, top_frac 0.0, bottom_frac 0.999 both). Any head
  crop is not new to E-007.
- "GroundingDINO non-determinism → raise threshold to 0.5" — a band-aid that never
  looked at the board. The root is the wrong tool (general detection+union for a
  parsing job) with no validation, run in the loop.

**O-BOARD-005 (root cause, decision-grade direction not yet a Verified rule):**
garment isolation for the board is a parsing problem, done with the wrong tool
(generic GroundingDINO+SAM+union) in the wrong place (the generation loop) with no
validation. Fix = consistency by construction (design §6a): V1 frozen clean refs;
production clothes-parsing. → No experiment verifies the *production* parser yet;
the V1 stand-in is a build decision, not an experiment.

**E-007 attempt 1 STATUS: INVALID.** Its protocol and results are preserved under
dated `*_invalid_2026-06-13` paths. E-007 v2 (prepared 2026-06-14) is the controlled
comparison that was actually needed: frozen masked-crop board versus frozen simple
rectangular-crop board.

**E-007 v2 result (2026-06-14): MIXED A/B; HYBRID SUPPLEMENT MEASURED.** The owner
found advantages and disadvantages in both original arms and a visibly incorrect
blouse shade in both. The masked blouse-front input omitted its buttons, and that
defect propagated into the outputs. The corrected nine-cell hybrid produces visible
buttons, V necklines, and wedge sandals in 5/5 outputs with 5/5 usable measurement
mask sets. Identity remains stable (mean 0.787), but blouse shade still looks wrong
and the silhouette diagnostic remains poor (12.644%). Because the edited layout and
board changed together, the supplement ranks the complete input candidate rather
than proving which individual change caused the improvement.

---

## H-REPAIR-GEN — repair generalisation & the cuff lever (2026-06-20)

E-011 (V-REPAIR-001) is owner-accepted for ONE garment/person/seed. Open, unverified:
- **Cross-garment / cross-person:** whether QIE-2511 crop-and-stitch stays reference-faithful + local on
  other items (skirt, structured garments) and other people. → needs more cases, single-variable.
- **Peripheral fine detail (cuffs):** soft on v5; NOT fixed by steps or global resolution. Hypothesis: a
  **tighter per-detail crop** (cuff occupies ~6× more of the frame) sharpens it. Untested — the next
  single-variable move if a cuff-grade result is required.
- **Holistic try-on workflows — bug CONFIRMED and FIXED (2026-06-20), test PENDING.** Both
  `system/workflows/qie2511_vton.json` and `qie2511_vton_lightning.json` carried the SAME bug as the old
  edit graph: `EmptyQwenImageLayeredLatentImage` (a node misappropriated from the SEPARATE "Qwen Image
  Layered" feature — different model `qwen_image_layered_bf16` + VAE + plain `CLIPTextEncode`) instead of
  `VAEEncode`-of-input; AND no `ModelSamplingAuraFlow`/`CFGNorm` (the AuraFlow patch is in BOTH official
  templates). Origin: introduced 2026-06-10 (V1-alpha 7fe3dbf); `V-QIE-001` "Verified" only the output
  FRAME FORMAT of that latent, not its correctness, which froze the wrong choice into E-005/007/009;
  E-009 even named it "the root cause of the drift" but mis-prescribed the fix (→ E-010 VTON detour).
  Both files are now rebuilt on the corrected edit graph (V-QIE-EDIT-001), structurally validated. **Still
  a hypothesis until a protocolled whole-outfit run shows the holistic softness is gone** —
  fixed-but-untested, not Verified. Re-opens whether the E-009/E-010 conclusions stood on this bug rather
  than a model limit.

## H-PIPELINE-2026-06-21 — universal pipeline state, open items
(`system/pipeline.py`, research/QUALITY_CHECK_SURVEY_2026-06-21.md, experiments/015_isolation_compare/.)
- **Identity collapse in the universal pipeline (BLOCKING, not fully isolated).** The single-tile board
  gave identity 0.40 vs the combined (mask+crop) board 0.945 — same QIE workflow. The combined board is
  proven (QIE context/logic + good identity); single tiles were the regression. Likely cause = board
  structure (single-tile vs combined), but prompt was not separately isolated. Fix direction: combined board.
- **Checking instruments are provisional.** AnomalyDINO structure gate (`structure.py`) + VLM-judge
  (Qwen3-VL) catch the missing slit on the 2 owner-labelled anchors, but thresholds are 2-anchor provisional
  and need a labelled set. VLM-judge MISSES the half-tuck and CONFABULATES (reports absent items) → flagger
  + owner backstop, not decision-grade.
- **No instrument catches the layering/half-tuck defect** — between-garment problem; needs a layering
  detector or stays owner-eye.
- **Board isolation (single outfit, owner-shown — not generalised).** ATR human-parsing isolates on-model
  garments cleanest (buttons preserved, model excluded); grounded_sam better for shoes (ATR fragments them);
  matting (rembg/BiRefNet) keeps the MODEL on on-model photos → wrong tool there. Owner-shown on outfit_001
  only.
- **Proposed (not built): "intelligent board analyzer"** — per element run multiple isolators, auto-select
  the best (signals: face/skin leak, completeness/connectedness, garment-identity, optional VLM), and that
  selection IS the board verification. Must itself be validated against owner judgment.
- **OmniTry accessory stage** not stood up (16 GB-via-fp8 test pending).
