# System Design — AI Stylist Pipeline
**Revision 4** — 2026-06-10 — independent deep-research pass by Claude Code (Fable 5).

> Builds on Revision 3 (Fable 5 deep-research doc, currently outside the repo on the owner's
> desktop — recommend committing it as `docs/SYSTEM_DESIGN_R3.md` for lineage).
> R4 verifies R3's research claims against primary sources, corrects two of them,
> adds new findings (June 2026), and revises the architecture and build order accordingly.
> Not a fixed spec. FINDINGS.md and actual code override this document.

---

## 1. Research verification (R3 claims checked against primary sources)

| # | Claim from R3 | Verdict after checking |
|---|---|---|
| 1 | Garments2Look (CVPR 2026) — first outfit-level VTON benchmark; current methods fail at full outfits | **CONFIRMED.** arXiv 2603.14153. 80K outfit→look pairs, 3–12 refs/look (avg 4.48), 40 categories. Dataset is open on HuggingFace. **No fine-tuned checkpoint released** — the QIE fine-tune result (0.41→0.627) is reproducible only by training ourselves (cloud GPU, deferred). |
| 2 | FastFit scored lowest on layering in the user study; editing models handle layering better | **CONFIRMED** (benchmark paper). FastFit itself is open: ComfyUI workflow exists, 5 categories (tops/bottoms/dresses/shoes/bags), cacheable refs → fast. Worth one honest bench row despite the layering result. |
| 3 | Lightning LoRA trades detail for speed — "documented" | **OVERSTATED.** Official LightX2V claims quality is *preserved* at 4 steps. No rigorous public same-seed comparison found. What remains true: our "40 steps worse" test was likely run WITH Lightning enabled (outside its regime) — the confound hypothesis stands and the experiment (bench rows 1–3) is still the right test. Status: **open question, not documented fact.** |
| 4 | OmniTry — mask-free try-on of any wearable incl. jewelry | **CONFIRMED, with a catch.** Open weights (Kunbyte-AI/OmniTry). It is a **LoRA on FLUX.1-Fill-dev** — the exact model we already run locally. Official requirement: **28GB VRAM at bf16** — does NOT fit 16GB as-is; fp8/quantized + offload is plausible but unverified. NeurIPS 2025. |
| 5 | Deterministic face restore (landmarks → warp → Poisson) is established | CONFIRMED as a known pattern. Untested on our photos (unchanged from R3). |
| 6 | Grounded-SAM-2 for text-prompted garment masks | **SUPERSEDED.** Meta **SAM 3** (Nov 2025) does open-vocabulary text-prompted segmentation natively, has multiple maintained ComfyUI node packs including a low-VRAM variant with aggressive unload. Use SAM 3, keep Grounded-SAM-2 as fallback. |
| 7 | Qwen-with-mask repair is untested / an open blocker | **NO LONGER TRUE.** Community inpainting workflows for QIE-2511 exist and are mature: crop-and-stitch (`InpaintCropImproved`/`InpaintStitchImproved`) + `TextEncodeQwenImageEditPlus` + SAM3 mask sourcing. The repair executor doesn't need to be invented — it needs to be **imported and validated.** |

### New findings (not in R3)

| Finding | Implication |
|---|---|
| **Tstars-Tryon 1.0** (Alibaba/Taobao, arXiv 2604.19748, Apr 2026): industrial try-on at Taobao scale. Up to 6 reference images, 8 fashion categories, explicit identity + background control, near-real-time. **Weights closed**; benchmark released. | The industrial SOTA converged on exactly our direction: multi-reference *editing-model* architecture with engineered identity/background preservation. Validates the design; their benchmark is usable for comparison. |
| **Qwen-Image-2.0** (Feb 2026, tech report arXiv 2605.10730): 7B unified gen+edit, Qwen3-VL as condition encoder, #1 on AI Arena editing. **Weights NOT open** as of June 2026. | Watch item. If open-sourced: ~3x smaller than QIE-2511 (20B), likely better multi-reference grounding. Engine swappability (P-interface) is what makes this a free upgrade later. |
| **Qwen3-VL-8B** available as GGUF in LM Studio. | Direct upgrade over Qwen2.5-VL-7B for person analysis + evaluation. Same serving path. |
| **LM Studio REST API v1**: explicit `/api/v1/models/unload`, per-request TTL, auto-evict. | VRAM sequencing has concrete levers on the LLM side. ComfyUI side: `/free` endpoint (verify on our install). |
| Port discrepancy in our own docs: CLAUDE.md says ComfyUI `:8188`, docs/architecture says `:8000`. | Verify locally before writing the client. Trivial but blocking for plumbing. |

---

## 2. What R4 changes relative to R3

1. **The repair-executor blocker is dissolved by adoption, not research.** R3 treated "Qwen-with-mask" as an open question. Mature community workflows exist (crop-and-stitch + QIE-2511 + SAM3). First action: import one, run it on the documented run-000001 belt failure, measure. Principle: **adopt before building** (new P8).
2. **OmniTry is re-positioned: from "Architecture B candidate" to "accessory executor".** It's a FLUX.1-Fill LoRA — same base we already run — and it targets exactly our persistent failures (earrings, belt, shoes). It is not a competitor to Qwen for the whole outfit; it's a complement for the items Qwen simplifies. VRAM fit (16GB, fp8) is the gating test.
3. **Lightning-fidelity downgraded from fact to hypothesis.** The bench decides; no architecture decision should pre-assume the answer.
4. **P5 (cheap drafts → expensive final) gets a correctness caveat.** Same seed across different configs (Lightning on/off, different step counts) does NOT give "the same image at higher quality" — the sampling trajectory differs. Draft-ranking only works if draft quality *correlates* with full-quality output for the same seed/panel. That correlation is itself an unverified hypothesis — test it with 5 paired generations before relying on the two-tier strategy.
5. **Identity strategy split in two, by generation mode:**
   - *Holistic pass* (whole-person edit): restore-after — composite original face/background back (R3's shell). Add a deterministic gate: **ArcFace embedding cosine** between input and final face. Cheap, objective, catches both generator drift and bad blends (lighting/pose seam risk of Poisson compositing is real).
   - *Repair pass* (local edit): protect-by-construction — generation physically cannot touch face/background because the inpaint mask excludes them. No restore step needed.
6. **New deterministic gate: body-proportion check.** Known failure: waist/hip drift when adding clothing. From SAM3 person masks on input vs output: shoulder/waist/hip pixel widths normalized by person height; threshold on relative change. R3 had no measurable answer to this documented problem.
7. **Build order inverted: close the thinnest loop first.** R3 ordered plumbing → segmentation → shell → eval → bench → close loop. That defers integration risk to the end. V1's success bar is *closed*, so close a minimal loop immediately after plumbing, then upgrade it in place (see §6).
8. **Segmentation tool: SAM 3** (text-prompted, low-VRAM nodes, ComfyUI-native). VLM: **Qwen3-VL-8B**.

---

## 3. Operating principles (P1–P7 inherited from R3, amended)

- **P1 — Minimize the trusted-generation surface.** Unchanged, now with two modes (restore-after vs protect-by-construction, §2.5).
- **P2 — Reference panel > prompt.** Unchanged. Note: QIE-2511 multi-image input is officially 1–3 images; with person + 5 items, panel compositing (or item grouping) remains necessary.
- **P3 — Deterministic where possible.** Unchanged.
- **P4 — Per-region evaluation, hybrid methods.** Unchanged + body-proportion gate + ArcFace gate.
- **P5 — Cheap drafts, expensive finals.** Retained **as hypothesis** pending the correlation test (§2.4).
- **P6 — Everything inspectable/resumable.** Unchanged.
- **P7 — VRAM sequencing is the orchestrator's job.** Now with named levers: LM Studio `/api/v1/models/unload` + TTL; ComfyUI `/free`; SAM3 low-VRAM node unloads itself.
- **P8 (new) — Adopt before building.** For any capability, first look for a maintained community workflow/node; import, validate on our failure cases, only then build custom. The repair executor is the first application.

---

## 4. Pipeline stages (delta view — only changes vs R3 listed)

```
[1] Person Analysis      — Qwen3-VL-8B (upgraded from Qwen2.5-VL-7B)
[2] Stylist              — unchanged (manual in V1)
[3] Outfit Adapter       — unchanged (panel compositing is the lever)
[4] Try-On Engine        — QIE-2511 default; strategies in §5
[5] Segmentation         — SAM 3 (text-prompted), person+garment+face+background masks
                           on both input and output → RegionMap
[6] Evaluation           — per-region, hybrid:
                           • presence/layering: Qwen3-VL-8B, schema JSON
                           • color: ΔE (LAB) per garment region vs reference
                           • identity: ArcFace cosine (deterministic gate)
                           • proportions: mask-derived width ratios (deterministic gate)
                           • countable details (buttons/buckles): SAM3 instance counts — advisory in V1
[7] Restoration Shell    — order: face/background composite → per-region LAB color match →
                           targeted generative repair (LAST, only on evaluator flag)
```

**Repair executor (shell step 4) — resolved design:**
- Tool: QIE-2511 + crop-and-stitch inpaint (imported community workflow), mask from RegionMap,
  **single garment reference** for the failing item (fewer simultaneous refs = better control,
  per Garments2Look's reference-count degradation finding).
- FLUX Fill demoted: text-only conditioning makes it architecturally incapable of
  reference-faithful repair — explains the documented run-000001 failure (locality passed,
  semantics failed). Keep only for reference-free structural fixes.
- OmniTry (FLUX-Fill LoRA): candidate executor specifically for **accessories** — if it fits
  in 16GB quantized. One gating test.

---

## 5. Generation strategies for stage [4]

All share stages [1][2][3][5][6][7]. Decision by bench-off (§7).

- **A — Holistic QIE-2511 pass + shell** *(default favorite — current evidence + industrial precedent via Tstars)*. One edit generates the dressed person; shell restores/corrects; repair pass fixes flagged regions.
- **B — FastFit + shell.** Open, fast, multi-reference. Documented worst-in-class layering. One honest bench row to disprove or surprise.
- **C — Hybrid sequential: holistic clothing pass + per-item accessory passes.** Clothing layers (blouse/skirt) in one Qwen pass — layering is where editing models win. Accessories (belt, shoes, earrings) added by separate local passes (QIE inpaint repair executor, or OmniTry if it fits). Responds directly to reference-count degradation: each pass sees ≤2 references. Cost: +N generations, cumulative-drift risk outside masks is zero by construction (protect-by-construction passes).
- **D — Look compilation (pilot hypothesis).** Two-stage: (1) compile the outfit board into ONE coherent worn-look image (on a mannequin/neutral model); (2) transfer that single look-reference onto the person. Compresses 5 refs → 1 at the person step. Risk: detail loss compounds across two generations. Cheap pilot only if A/C underperform on layering coherence.

---

## 6. V1 build order (revised — every step keeps the system runnable end-to-end)

1. **Plumbing.** ComfyUI client (submit/poll/fetch; verify port 8188 vs 8000), LM Studio client (chat + vision + load/unload), run-folder I/O. Measure model load/unload timings → FINDINGS.md.
2. **Thin closed loop (V1-alpha).** Manual OutfitPackage → adapter (panel) → one QIE-2511 generation → Qwen3-VL-8B schema evaluation → report in run folder. No segmentation, no shell, no repair. **This is the "closed" milestone — everything after upgrades a running loop.**
3. **Segmentation stage + RegionMap (SAM 3).** Enables per-region ΔE color eval, proportion gate, and all shell steps.
4. **Restoration shell, deterministic part.** Face/background composite + ArcFace gate; per-region LAB color match. (The old `tools/postproduction_color_repair.py` is deprecated — do not build on it.)
5. **Repair executor.** Import community QIE-2511 crop-and-stitch workflow; validate on the archived run-000001 belt failure; wire to evaluator flags. Gating test for OmniTry-on-16GB alongside.
6. **Bench-off (§7)** — now runs with automated metrics instead of eyeballing.
7. **V1-final.** Winning config + repair loop + retry caps + final report.

---

## 7. Bench-off protocol v2

- **Fixed inputs:** run-000001 assets + one harder outfit (more layers, patterned fabric).
- **Matrix:**
  | Row | Config | Answers |
  |---|---|---|
  | 1 | QIE-2511 + Lightning, 4 steps | baseline |
  | 2 | QIE-2511, no Lightning, 20 steps | Lightning-fidelity question |
  | 3 | QIE-2511, no Lightning, 40 steps | (with row 2) |
  | 4 | FastFit | strategy B |
  | 5 | Strategy C (holistic + accessory passes) | hybrid sequential |
  | 6 | OmniTry, accessories only, fp8 | accessory executor + VRAM fit |
- **K=5 seeds per row, same seeds across rows.** Plus the P5 correlation test: rank 5 Lightning drafts, regenerate each seed at full steps, check rank stability.
- **Metrics:** per-garment ΔE; VLM presence/layering checklist; ArcFace cosine; proportion-gate deltas; SAM3 detail counts (advisory); wall-clock + VRAM peak.
- **Output:** FINDINGS.md entry + engine/strategy decision for V1-final.

---

## 8. Open questions (re-prioritized)

1. Repair executor validation — imported QIE-2511 inpaint workflow vs the run-000001 belt case. *(was R3's #3; now first because it's pure adoption, no research)*
2. Bench-off §7 — engine/strategy + Lightning question. *(needs build steps 1–3 first)*
3. OmniTry on 16GB (fp8/offload) — yes/no gating test.
4. Restoration-shell seams — Poisson blend quality on our photos; ArcFace gate thresholds.
5. P5 draft-rank correlation — does Lightning-draft ranking predict full-step quality?
6. Dual-view composite approach — deferred (unchanged from R3).
7. Qwen-Image-2.0 weights — watch monthly; if open, re-run bench with it as row 7.
8. V2 questions (stylist LLM quality, FashionCLIP vs SigLIP) — unchanged, deferred.

---

## 9. Verified-vs-hypothesis ledger (updated)

| Claim | Status |
|---|---|
| Outfit-level VTON is unsolved; editing models > dedicated VTON at layering | [R] verified (Garments2Look, CVPR 2026) |
| Industrial SOTA uses multi-ref editing + engineered identity/background control | [R] verified (Tstars-Tryon 1.0) |
| Lightning LoRA loses detail vs full steps | **hypothesis** — official sources claim otherwise; bench rows 1–3 decide |
| "40 steps worse" was confounded by Lightning left on | hypothesis, plausible, same bench decides |
| QIE-2511 masked repair is feasible | [R] community-validated workflows exist; unvalidated on our cases |
| OmniTry fits 16GB | hypothesis (official req: 28GB bf16); gating test |
| SAM3 gives usable garment/face masks on our images | [R] documented; untested locally |
| Deterministic face composite is seamless on our photos | hypothesis; ArcFace gate added as objective check |
| Draft-ranking predicts full-step quality (P5) | hypothesis; correlation test defined |
| color_repair.py | deprecated — do not use (owner verdict) |

---

## Sources

- Garments2Look: https://arxiv.org/abs/2603.14153 · https://github.com/ArtmeScienceLab/Garments2Look
- Tstars-Tryon 1.0: https://arxiv.org/abs/2604.19748
- OmniTry: https://arxiv.org/abs/2508.13632 · https://github.com/Kunbyte-AI/OmniTry
- FastFit: https://arxiv.org/abs/2508.20586 · https://github.com/Zheng-Chong/FastFit
- Voost: https://arxiv.org/abs/2508.04825 · https://github.com/nxnai/Voost
- Qwen-Image-2.0 tech report: https://huggingface.co/papers/2605.10730
- Qwen-Image-Edit-2511: https://qwen.ai/blog?id=qwen-image-edit-2511
- QIE-2511 Lightning: https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning
- QIE-2511 inpaint workflows: https://openart.ai/workflows/makisekurisu/inpainting-for-qwen-image-edit-2511/AYcG8mrxUuvwk1BUbEMT · https://github.com/axiomgraph/ComfyUIWorkflow
- SAM 3 ComfyUI: https://github.com/PozzettiAndrea/ComfyUI-SAM3 · https://github.com/yolain/ComfyUI-Easy-Sam3
- Qwen3-VL-8B in LM Studio: https://lmstudio.ai/models/qwen/qwen3-vl-8b
- LM Studio model mgmt API: https://lmstudio.ai/docs/developer/rest/unload · https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
- Awesome-Try-On-Models (tracking list): https://github.com/Zheng-Chong/Awesome-Try-On-Models
