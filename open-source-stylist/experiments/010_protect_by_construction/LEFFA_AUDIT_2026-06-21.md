# Leffa audit — "for real, like QIE" (2026-06-21)

Owner-directed. Method: read canonical Leffa (`C:\Users\Admin\Leffa\app.py` `leffa_predict`) against our
wiring (`leffa_skirt.py`), diff, and **verify against ground truth** (the actual E-010 Leffa results).

## Wiring diff: our Leffa call is canonical — no QIE-style bug
Our `leffa_skirt.py` (DressCode branch) vs canonical `app.py`:
- **densepose — IDENTICAL.** Canonical dress_code: `predict_iuv(src)[:, :, 0:1]` → `concat([·]*3)`. Ours:
  `predict_iuv(src_arr)[:, :, 0:1]` → `concat([·]*3)`. Byte-for-byte the same representation. (This
  debunks the standing suspicion that our densepose channel was wired wrong.)
- **model** `virtual_tryon_dc.pth` (DressCode) ✓ correct for lower_body; **mask**
  `get_agnostic_mask_dc(parse, kp, "lower_body")` ✓ canonical; **scale** 2.5 ✓; src/ref `resize_and_center
  (768,1024)` ✓.
- **Deviations (minor, NOT the cause):** (1) we skip `preprocess_garment_image` — it only square-centres
  the garment on a white 768×1024 canvas; it does NOT fix a through-slit silhouette. (2) `step=30` vs the
  app default 50 — fewer steps, not a topology driver.

## Ground truth: Leffa works, but CANNOT do free-hanging skirts
- **Sanity (`leffa_SANITY_tee.png`): PASS** — a tee renders as a clean, correct try-on. Leffa is functional.
- **`leffa_maxi_solid.png`** — a SOLID continuous maxi garment (no slit) → Leffa renders the lower body as
  **leg-conforming fabric clinging to both legs (leggings/pants), not a skirt.**
- **`leffa_T5_skirt_reframed_drapemask.png`** — the best setup: reframed person + a CONTINUOUS drape mask
  (overriding Leffa's leg-split auto mask) + continuous garment → **STILL leg-conforming pants.**
- So with a continuous garment AND a continuous mask, Leffa still produces legs. The mask override does not
  fix it.

## Mechanism (ground-truth elimination + sources) — architectural, not a bug
With garment and mask both continuous, the only remaining leg-shaped input is the **densepose IUV**, which
Leffa uses as a **HARD structural channel** (dual-UNet, 12-ch input). densepose maps the two legs, so the
generated lower garment conforms to leg geometry → pants. This is a Leffa **architectural limitation** for
free-hanging lower garments (skirts / volume dresses), consistent with DEEP_RESEARCH / PROMO (2603.11675):
"DensePose distorts on long skirts." It is NOT fixable by our wiring.

## Conclusion — three audited tools, three different outcomes
| Tool | Wiring bug (like QIE)? | Skirt verdict | Cause |
|------|------------------------|---------------|-------|
| QIE (E-009) | **YES** — wrong latent + missing patches | n/a | our hand-built workflow; fixed (a3a896c) |
| FitDiT (E-010) | No | **works** with a continuous silhouette (`skirt_filled_result.png`) | input topology (flat-lay slit) |
| Leffa (E-010) | No | **fails** even with continuous garment + mask | **densepose hard-channel** forces legs (architectural) |

So Leffa's E-010 skirt failure was NOT our wiring (canonical) and NOT only the input — it is a genuine
densepose-driven limitation. For free-hanging skirts: FitDiT (DWpose, softer) > Leffa (densepose, hard);
and the QIE editing spine (E-012) > both.

## Untested lever (NOT recommended)
One could blank/edit the densepose leg region to free the skirt from leg geometry — but given FitDiT renders
skirts correctly and the QIE holistic+repair spine works (E-012), pursuing Leffa-for-skirts is not worth it.
