# E-010 — Edit-the-photo try-on: preserve the person, change only the garments (reference-conditioned inpaint)

**Status:** UPDATED 2026-06-15 (owner-directed re-architecture after the FLUX-Fill Phase-0 build
exposed a text-only conditioning gap). Approved direction; the **engine is selected in Phase 0**.
Execute in a separate session — see `STARTER.md`. Not yet run (no generation done).
**Supersedes** the FLUX-Fill-text framing of the previous draft.
**Governed by:** METHODOLOGY.md §2; design §7 (protect-by-construction); follows E-009.

---

## 1. Question and frame

The current pipeline re-draws the whole person from an empty latent
(`EmptyQwenImageLayeredLatentImage`, denoise 1.0) → body slims ~9% (E-009, owner-rejected).
The fix is to **edit the source photo** instead of regenerating the person: keep the person's
pixels, change only the garments, and take the new garments from the **reference board image**.

**Hard requirement that disqualified the first build:** the engine MUST take the garment as an
**image**. The colour-less, task-correct prompt ("appearance from board only", no colour words)
means a **text-only** inpaint (`system/workflows/flux_fill_inpaint.json`, person+mask+text, no
board) invents generic clothes and **fails garment fidelity by construction**. That build is kept
ONLY as a possible body-only control; it is NOT the product path.

## 2. Honest decomposition of "preserve the body" — do NOT oversell inpaint

Editing only the clothing protects, **by construction**, everything OUTSIDE the clothing mask:
face, hair, neck, hands/forearms, visible skin, lower legs below the skirt, background. That is
most of "same person", and it removes the gross "different person" failure (E-009 R2 cosine 0.35).

It does **not**, by itself, pin the body width UNDER the clothing. Two facts force honesty:
- The model still draws inside the mask, so the clothed torso/hips are model-decided.
- The E-009 hip −9% is measured at hip joints that sit **under the skirt** — `body_pose` infers
  clothed-region joints from the image, so that number is **part real body slimming, part
  slim-skirt-vs-jeans silhouette**. The cleaner body signal is the near-zero **shoulder** change
  (shoulders are higher, less skirt-influenced).

Therefore E-010 is expected to fix identity/face/skin/limbs/background. If the **clothed-torso
width** still drifts and the owner rejects it, the next lever is a **body-shape / pose control**
on the clothing region — scoped as **E-011**, not claimed here. This protocol does not pretend
inpaint alone closes the body gap.

## 3. Engine selection — Phase 0 is a feasibility gate (pick the mechanism, don't assume)

Requirement: (a) source pixels preserved outside a clothing mask; (b) garment appearance
conditioned on the board **image**; (c) runs locally on 16 GB.

Candidates, in priority order, each feasibility-tested before committing:

| # | Mechanism | Garment from image? | Feasibility risk to resolve in Phase 0 |
|---|-----------|---------------------|----------------------------------------|
| C1 | QIE-Edit native masked: VAEEncode(source) + clothing mask + denoise<1, **image2=board kept** | yes | QIE-2511 uses a special 5-D *layered* latent; a standard masked latent may not slot in. Test live in ComfyUI; if it errors, drop. |
| C2 | QIE-Edit full-regen (as now) + **composite source back outside the clothing mask** (feathered) | yes (board conditions the full pass) | no new model, but the clothing was drawn on a *slimmed* body → boundary misalignment with the fuller source at the waist/edges. |
| C3 | FLUX Fill + a **reference-image** conditioner (FLUX Redux / IP-Adapter on the board or per-garment crops) | yes | availability of Redux/IP-Adapter nodes + weights locally (download = owner GUI step). |
| C4 | Garment-image VTON model (IDM-VTON / CatVTON / FLUX-VTON) | yes | install/availability + license + VRAM. |

**Phase 0 procedure:**
1. Query the live ComfyUI `/object_info`: which of C1–C4 are actually available?
2. Take the highest-priority AVAILABLE candidate; produce ONE output on one seed.
3. **Owner checkpoint (single output):** does the garment match the board? are face/skin/background
   source-clean? any seam/halo? Pick the engine the owner accepts here.
4. If none qualifies (e.g. only text-only is available) → surface the exact missing model/node to
   the owner. **Do not fall back to text-only conditioning.**

Phase-0 deliverables: the chosen engine, the clothing mask
(`experiments/010_protect_by_construction/masks/clothing_region.png` already built — re-review it),
and a content-addressed, hashed inpaint workflow with cfg/sampler/scheduler/negative/denoise/mask
all threaded. Reuse the mask/param plumbing the FLUX-Fill build already added; verify it reaches
the selected engine.

## 4. Method (A/B)

| Arm | Path | Data |
|-----|------|------|
| A — full regen (baseline) | QIE Lightning, empty latent (E-009 R1) | exists; NOT regenerated |
| B — edit-the-photo | the Phase-0-selected reference-conditioned inpaint | new |

Fixed: `person_front.png`; `outfit_001`; board `hybrid_mask_crop` (frozen, SHA-verified);
720×1024; seeds [42, 123]; task-correct colour-less prompt. Only the generation path varies.

## 5. Axes — body AND garment co-primary; garment is a HARD gate

| Axis | Metric | Notes |
|------|--------|-------|
| Body | `body_pose`: hip/shoulder/ratio Δ%, pose_mismatch, visibility | report **shoulder** (cleaner) prominently; the clothed-hip number carries the §2 caveat |
| Face | ArcFace cosine vs source | must be ≥0.57 and not below A |
| Garment colour | per item: ΔE + hue/chroma split + presence (segmentation/sanity) | **hard gate** |
| Garment detail | owner per-item verdict: cut, closure/buttons, straps, texture, layering | **hard gate**; machine item-identity is a known gap (audit) → owner eye primary |
| Seam / mask | owner check for halo at the mask boundary | inpaint-specific; needs feathering |

## 6. Acceptance criteria (fixed before results)

Inpaint is adopted only if it preserves the person **without** regressing the outfit:
- **Garment (hard gate):** every required item's colour/presence/layering **not worse** than A,
  and the owner's per-item detail verdict **not worse**. A body win bought by a worse garment fails.
- **Face:** cosine ≥ 0.57 and not below A.
- **Body:** the gross different-person/body failure removed and outside-clothing source-clean
  (owner). If the clothed-torso width still drifts beyond owner tolerance → **trigger E-011
  (body-shape control)**; do NOT record "inpaint failed" — it did its job for the unclothed person.
- **Seam:** no halo the owner rejects.

Owner verdict per axis is the acceptance; gates advisory; no aggregate score.

## 7. Risks / unknowns (stated up front)

- QIE layered-latent may not accept masking (C1) — the central Phase-0 unknown.
- C2 composite: clothing drawn on a slimmed body vs fuller source → boundary mismatch; needs
  feathering (the `background_restore` audit finding: no hard binary edge).
- C3/C4: local availability of reference/VTON models is unverified (possible download blocker).
- The clothed-torso body width is still model-drawn inside the mask → residual drift is expected
  and is exactly what E-011 (body control) would address.
- Holistic composition is lost in region editing → large-garment layering may compose less
  coherently; this is why garment is a hard gate.

## 8. Cost estimate

| Step | Est. |
|------|------|
| Phase 0: engine check + 1 test output (per candidate tried) | 1–2 sessions |
| Phase 1: arm B ×2 seeds + gates | ~10–20 min GPU |
| Phase 2: collation + conclusion | < 1 session |

---

*Updated 2026-06-15. One person, one outfit, controlled frontal pose; generalisation NOT claimed.
Garment accuracy is a co-primary hard gate; the engine must condition garments on the board image,
never text. Inpaint protects the unclothed person; the clothed-torso body width is a separate
lever (E-011) if it persists.*

---

## Owner sign-off

- [x] Re-architecture approved (owner-directed 2026-06-15): edit-the-photo, reference-conditioned
      inpaint; text-only engines disqualified for garment fidelity.
- [x] Engine chosen in Phase 0 at the single-output owner checkpoint (not pre-committed).
- [x] Honest body decomposition accepted: inpaint protects the unclothed person; clothed-torso
      width may need E-011 (body control).

**Signed:** owner, 2026-06-15 (directed this update). Execution delegated to a separate session.
