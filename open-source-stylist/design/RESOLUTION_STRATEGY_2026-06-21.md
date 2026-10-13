# Pipeline resolution strategy (2026-06-21)

Owner-directed: "resolution must not become a cause of quality degradation." This pins the canonical
working resolution and the rules that keep resampling from losing detail. Owner-chosen canonical: **1.77 MP**.

## Where resolution was degrading quality (measured 2026-06-21)
| Stage | Was | Problem |
|-------|-----|---------|
| source photo | 938×1344 (1.26 MP) | — |
| QIE holistic | 832×1248 (1.04 MP) | QIE caps at ~1 MP (FluxKontextImageScale) — base already below source |
| reference board (hybrid) | 768×768, 7 garments | each garment ≈ 0.08 MP → root of the flat skirt |
| FitDiT repair | output 832×1248 | **FitDiT resizes its output back to the INPUT size** → a 1152×1536 generation was downscaled to 832×1248, throwing away the detail |

Three independent losses: QIE's 1 MP cap, the shared low-res board, and FitDiT discarding its own hi-res output.

## The strategy (canonical resolution + 4 rules)
**Canonical working resolution = 1.77 MP, at the CONTENT's aspect ratio** (2:3 photo → ~1088×1632; do NOT
force FitDiT's 3:4 frame onto a 2:3 photo — that distorts the person). FitDiT's `resolution` param
(1152×1536) is the *generation budget*, separate from the output size.

1. **Canonical base, upscaled once.** The QIE holistic (~1 MP) is upscaled to 1.77 MP (Lanczos,
   aspect-preserved) a single time. Un-edited regions are resampled at most once.
2. **Repairs run at the canonical resolution.** Feed the repair engine a base ALREADY at canonical res, so
   its output stays hi-res. (FitDiT outputs at its input size — never feed it a low-res base and let it
   downscale. This was the E-013 bug.)
3. **Hi-res per-item references for repairs.** Use the dedicated garment reference (e.g. the 3.17 MP skirt
   crop), NOT the 768² shared board, when repairing a single item.
4. **Local mask-limited composite.** A repair is composited back into the base ONLY within the garment mask
   (minus protected neighbours, e.g. the belt). Everything else stays byte-identical from the base. This
   both preserves quality (no global re-encode) AND fixes non-local engines erasing neighbours (FitDiT
   regenerates the whole lower body → the belt vanished; the local composite of skirt-minus-belt restores it).

## Demonstrated (E-013 hi-res, run_e013_hires.py)
Base 832×1248 → canonical 1088×1632 (1.78 MP) → FitDiT skirt repair (gen 1152×1536, output stays 1088×1632)
→ segment skirt (result) + belt (base) → composite skirt-minus-belt into the base.
- **Belt restored**, blouse/face/background byte-preserved (local composite).
- **Skirt texture (clean-fabric HF), same patch:** QIE 1.3 → FitDiT@832 2.1 → FitDiT@1088 **2.8** — keeping
  the hi-res output is a real gain. Identity held (FashionSigLIP sim 0.86).

## Honest limits
- The QIE holistic base is fundamentally ~1 MP (model cap); the canonical upscale is interpolation — real
  detail comes from the per-item repairs, not the base. This is acceptable: holistic = coarse layout,
  repairs = detail.
- The 768² board still starves the holistic pass per-garment. Enlarging the board (or hi-res per-garment
  refs for the holistic too) is a separate open item.
- Texture in a full-body frame is bounded by the garment's pixel share even at 1.77 MP; per-item repair is
  the lever, not global resolution alone.
