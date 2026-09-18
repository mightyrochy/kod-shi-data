# FLUX Fill audit — "for real, like QIE" (2026-06-21)

Owner-directed. Method: diff `system/workflows/flux_fill_inpaint.json` against the official ComfyUI
template `flux_fill_inpaint_example.json` (its "Flux.1 Fill Dev Image Inpainting" subgraph), node + link
level. **Unlike FitDiT/Leffa, this one HAD real deviations — like QIE.** Fixed.

## Deviations found (our old workflow vs canonical)
| | Canonical (official subgraph) | Our old workflow | Impact |
|---|---|---|---|
| **Guidance** | `FluxGuidance = 30` (fixed) | `FluxGuidance(__CFG__)` ← pipeline cfg, default **1.0** | severely UNDER-guided if run with defaults |
| **Model patch** | `UNETLoader → DifferentialDiffusion → KSampler` | `UNETLoader → ModelSamplingFlux → KSampler` | wrong patch; no differential-diffusion mask blending |
| **Positive encode** | plain `CLIPTextEncode` + one `FluxGuidance` | `CLIPTextEncodeFlux` (own guidance) + `FluxGuidance` | redundant double-guidance |
| **Negative** | `ConditioningZeroOut` of the positive | a 2nd `CLIPTextEncodeFlux(__NEGATIVE_PROMPT__)` | non-canonical (inert at cfg 1, but not the pattern) |
| KSampler | 20 steps, cfg 1, euler, **normal**, denoise 1 | params; adapter default scheduler **simple** | minor (caller default) |

`InpaintModelConditioning` (the key fill node: positive/negative/latent with `noise_mask=true`) was already
present and correctly feeding the KSampler latent — that part was right.

## Fix applied
Rebuilt `flux_fill_inpaint.json` to the canonical graph (validated: refs resolve, classes known,
`KSampler.model ← DifferentialDiffusion`, latent/neg ← `InpaintModelConditioning`, `FluxGuidance = 30`):
- `UNETLoader → DifferentialDiffusion → KSampler`;
- plain `CLIPTextEncode → FluxGuidance(30) → InpaintModelConditioning.positive`;
- `CLIPTextEncode → ConditioningZeroOut → InpaintModelConditioning.negative`;
- kept our separate-mask-file adaptation (`LoadImage` mask → `ImageScale` → `ImageToMask`), which the
  canonical (alpha-mask) template does not need but is a legitimate adaptation.
Dropped the `__CFG__` / `__NEGATIVE_PROMPT__` placeholders for this engine (guidance is the fixed 30;
negative is zeroed).

## Functional caveat — the fix does NOT make FLUX Fill a try-on engine
`flux1-fill-dev` is a **text-prompted** inpaint model: it has **no garment-image input**. Even canonical,
it cannot reproduce a SPECIFIC garment from a reference — it invents clothing from the text prompt (the
project's earlier "invents generic clothes" disqualification stands). So the corrected workflow is a
correct utility for **text-driven inpaint / background-object cleanup**, NOT garment-faithful try-on. For
garment fidelity the engines are QIE (edit, image2=board) and FitDiT (garment encoder).

## Status
Structural-canonical fix + validated; **untested by a run** (no owner-reviewed FLUX Fill output exists).
Commit alongside this note.

## Four tools audited — summary
| Tool | Wiring bug like QIE? | Action |
|------|----------------------|--------|
| QIE (E-009) | **Yes** (latent + patches) | fixed (a3a896c), E-012 verified |
| FitDiT (E-010) | No (canonical) | none; works w/ continuous silhouette |
| Leffa (E-010) | No (canonical) | none; architectural densepose-hard limit on skirts |
| **FLUX Fill** | **Yes** (guidance, DifferentialDiffusion, encode/negative) | **fixed**; but text-only → not a try-on engine |
