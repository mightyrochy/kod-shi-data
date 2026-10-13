# FINDINGS — empirical ground truth

Facts verified against the live local environment. Append-only, date-stamped.

---

## 2026-06-10 — environment verification (plumbing smoke test)

**ComfyUI**
- Runs on port **8000**, NOT 8188 as CLAUDE.md states. Version 0.24.1.
- 16GB VRAM total, ~14.7GB free at idle.
- `POST /free` returns 200 (unload/free levers available for VRAM sequencing).
- Image upload via `POST /upload/image` works.

**LM Studio**
- Native REST API v1 (`/api/v1/models`) available alongside OpenAI-compatible API.
- Loaded state lives in `loaded_instances` (list), not a `loaded` boolean.
- Default JIT TTL observed: 60 min.
- Explicit unload via `POST /api/v1/models/unload` works; call takes ~1.1s.

**VLM: qwen3-vl-8b-instruct** (Q4_K_M, 6.2GB, vision-capable, 262k max context)
- Already downloaded — the Qwen3-VL upgrade recommended in SYSTEM_DESIGN_R4 is in place.
- Cold vision call (incl. JIT model load): **11.8s**. Warm call: **0.6s**.
- Schema-enforced structured output (`response_format: json_schema`) works —
  returned valid JSON matching the schema on first try.

**Python**
- System Python 3.10.11; `requests` installed 2026-06-10; PIL 12.2.0, numpy 2.2.6 present.

**Implication for the orchestrator:** VLM load cost is ~12s, unload ~1s. Sequencing
VLM ↔ generation model swaps will cost roughly 15-60s per swap depending on the
generation model's load time (not yet measured — needs a real generation run).

---

## 2026-06-10 — V1-alpha first automated run (run_000001)

**Pipeline:** `python -m pipeline.run_v1alpha 000001`
**Model:** QIE-2511 fp8mixed + Lightning LoRA, 4 steps, euler/simple, cfg=1.0
**Input:** person_front.png (464×672) + qwen/reference_board_clean.png
**Generation time:** 34.3s on RTX 4090 (16GB)
**Evaluation model:** qwen3-vl-8b-instruct (Q4_K_M)

**Automated evaluation result:**
| Criterion | Result | Notes |
|-----------|--------|-------|
| Identity preserved | PASS | Face, hair, body shape, pose, background correct |
| Outfit items present | FAIL | Sandals: black heels instead of dark green wedge; earrings not visible |
| Outfit logic | FAIL | Skirt mid-calf not ankle-length; belt not visible |
| Colors/textures match | FAIL | Sandals wrong color/type; belt absent |
| Overall | FAIL | |

**Pattern confirmed:** Identity is reliably preserved. Accessories (belt, earrings)
and footwear details (color, type, texture) are the primary failure points.
Skirt length tends to be shorter than specified.

**Matches prior manual evaluations** from runs/000001/evaluation/ — automated
evaluator surfaces the same failure modes human review found.

**Generation model load time:** QIE-2511 fp8mixed loads in ~30s (inferred from
34.3s total for 4-step inference; prior smoke test showed idle load = near-instant,
so most of that 34s is model load + 4 inference steps).

**Implication:** Evaluation pipeline is working correctly. Generation quality is
the variable to improve — bench-off (§7 R4) is the next step.

## 2026-06-10 — V1-alpha run 2: color-free prompts (run_000001, second generation)

**Change from run 1:** All color adjectives removed from outfit_package.json and
prompt.txt. Added explicit instruction: "Use reference images for exact colors,
textures, and material finish. Do not use text descriptions for color."

**Automated evaluation:**
| Criterion | Result | Change vs run 1 |
|-----------|--------|-----------------|
| Identity preserved | PASS | same |
| Outfit items present | FAIL | similar (earrings/belt still missing per VLM) |
| Outfit logic | PASS | improved (was FAIL run 1) |
| Colors/textures | FAIL | VLM now correctly says blouse "light yellow" — improved |
| Overall | FAIL | |

**Visual assessment (human):**
- Body proportions: significantly improved vs run 1 — closer to original natural figure
- Blouse color: more yellow-tinted than run 1 (cream → pale yellow), moving toward reference lemon-green
- Skirt: length correct, front slit visible, color matches
- Shoes: very dark, hard to confirm color at this resolution
- Earrings: present but small
- Skirt pockets: still not visible

**Confirmed finding:** Removing color text from prompts improved both color accuracy
AND body proportion preservation in the same run. Hypothesis: text color labels caused
the model to "rebuild" the garments conceptually rather than transfer from reference,
which also affected body shape in the process.

**VLM evaluator accuracy improving:** Now correctly identifies blouse as "light yellow"
(was "cream/ivory" and called shoes "black" in run 1). Still struggles with small
texture details (earring spiral, shoe croco) at 464×672 resolution.

### Human correction of automated evaluation (same run)

Manual review of runs/000001/v1alpha/output.png against the same criteria:

**Person/identity:**
- Face: PASS (borderline — slight color cooling)
- Body proportions: FAIL — chest and waist visibly reduced; chest is the worse
  failure zone. NOT captured by the evaluator (no criterion for this).

**Earrings:** PASS (present, slightly simplified; resolution prevents detail
  assessment of texture/hang logic — minor logic issue with hang angle)

**Blouse:**
- Shape/form: PASS; sleeve volume slightly off, not critical
- Color: FAIL (definitive) — VLM missed this entirely
- Buttons: inconclusive (resolution too low), generally PASS
- Hem/peplum: PASS

**Skirt:**
- Length: PASS
- Front slit: FAIL — VLM caught this
- Pockets: FAIL — VLM caught this
- Color + texture: FAIL — VLM caught this
- Belt: absent; user verdict = NOT a fail (outfit logic allows partially hidden
  belt; model chose to hide it completely which is within the spec)

**Shoes:** Color BARELY PASS (dark green present, slightly darker than ref);
  texture inconclusive (resolution); shape PASS.
  VLM incorrectly called this "black heels" — a hallucination.

**Overall impression:** person looks "polished/smoothed"; outfit noticeably
  simplified vs reference.

**VLM evaluator verdict from human: FAIL**
- False positives: shoes called black (actually dark green), earrings called
  missing (they are present)
- False negatives: missed blouse color fail, missed body proportion reduction
- VLM struggles with low-resolution detail assessment

**Blouse color clarification:** The reference image (blouse_ivory_front.webp) is
actually a pale lime/chartreuse green, NOT ivory as described in outfit_package.
The generated blouse is white/cream — a color fail, confirmed visually.
The package description "pale ivory" does not match the actual reference image color.

**Root cause of body proportion failure — confirmed mechanism:**
Product reference images (blouse, skirt) feature visibly slimmer models.
QIE-2511 learns body shape from BOTH input images — person AND garment references.
Result: model partially transfers the reference model's silhouette onto the
input person. This is not random drift — it is systematic behavior. The more
reference images feature slim models, the stronger the pull toward their proportions.
This will occur on any run using standard product photography as references.
Mitigation options: (a) crop references to garment-only (no body visible),
(b) add explicit body preservation prompting, (c) use a dedicated body-lock
mechanism (pose/silhouette conditioning).

**Action items logged:**
1. Resolution too low (464×672) — limits both generation quality AND evaluation
   accuracy. Next run should use higher resolution.
2. Body proportion criterion missing from eval schema — add as 5th criterion
   or expand identity criterion to cover it explicitly.
3. VLM evaluator calibration is unreliable at current image size — evaluation
   results must be treated as advisory until resolution is increased.
4. Crop reference images to garment-only before feeding to QIE-2511 — removes
   reference model body from conditioning and reduces proportion transfer.
5. outfit_package visual_description for blouse says "pale ivory" but actual
   reference is pale lime/chartreuse green — package description needs correction.

---

## 2026-06-10 — Phase A1: resolution experiment (run_000003, 928×1344)

**Hypothesis:** generation at 928×1344 (2x baseline) improves garment detail and VLM accuracy.
**Source:** runs/000001 (same inputs as runs 1–2)
**Input:** person_front.png **4x AI-upscaled** (469×672 → 1876×2688, RealESRGAN_x4plus, 1.1s GPU)
**Generation:** QIE-2511 fp8mixed + Lightning LoRA, 4 steps, 928×1344
**Generation time:** 60.7s (vs 34.3s baseline — +77%, expected for ~4x pixel area)
**Evaluation model:** qwen3-vl-8b-instruct, resized to 672px long-edge (new: fixed VLM input size)

**Automated evaluation:**
| Criterion | Result | Change vs run 2 (464×672) |
|-----------|--------|---------------------------|
| Identity preserved | PASS | same |
| Outfit items present | FAIL | similar (shoes type wrong, earring texture) |
| Outfit logic | FAIL | similar (blouse hem, shoes) |
| Colors/textures | FAIL* | VLM now reports blouse as "light green" — correct color |
| Overall | FAIL | |

*Color FAIL is now partly a **VLM evaluation gap**: colors were removed from outfit_package
(color-free principle), so VLM cannot compare against a known reference — it can only
report what it sees, not whether it matches. Color appears correct to the VLM but the
eval logic marks it FAIL by default when no reference exists.

**Key finding — blouse color improved at 2x resolution:**
Run 2 (464×672): generated blouse was white/cream (wrong).
Run 000003 (928×1344): VLM reports "light green" — consistent with the lemon-green reference.
Hypothesis: higher resolution allows the model to read the reference image color more accurately.
**Human validation required** to confirm (output: runs/experiments/v1alpha/000003/output/output.png).

**Infrastructure fixes discovered during this run:**
1. VLM context overflow at 928×1344: images sent at full resolution exceeded LM Studio's
   default 4096-token context. Fixed: evaluator now resizes images to 672px long-edge
   before VLM (generation resolution decoupled from eval resolution).
2. _find_source matched empty folder: v1alpha/000001 existed but was empty; matched
   before legacy runs/000001 which had the actual files. Fixed: validate input presence.

**Evaluation gap identified:**
Color criterion is VLM-only and can't compare to reference without color in the package.
This reinforces Phase C priority: deterministic delta-E color check against reference images
is needed. VLM color verdict is advisory only.

**Action items:**
1. Human visual validation of 000003 output (identity, proportions, blouse color vs reference).
2. If blouse color confirms, log resolution effect in DECISIONS.md and proceed A2 (K=5 seeds).
3. Consider one more run at 1392x2016 (3x) or at native 1876x2688 to find the ceiling.

---
