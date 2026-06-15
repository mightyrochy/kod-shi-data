# E-010 — Protect-by-construction try-on (inpaint): preserve the person, edit only the clothing

**Status:** APPROVED 2026-06-15 (owner-signed direction). To be EXECUTED IN A SEPARATE
SESSION — see `STARTER.md` in this folder. Not yet executed.
**Created:** 2026-06-15
**Governed by:** METHODOLOGY.md §2; design §7 (protect-by-construction); follows E-009.

---

## 1. Question

Does editing **only the clothing region** of the source photo — keeping the person's actual
pixels (face, skin, hands, body outside the clothing, background) by construction — reduce
the systematic body slimming below the ~9% full-regeneration floor (E-009), **without
regressing garment fidelity or face identity**?

Root cause this attacks (E-009): the current pipeline re-draws the whole person from an empty
latent (`EmptyQwenImageLayeredLatentImage`, denoise 1.0), so the body is re-synthesised and
drifts. Inpaint anchors everything outside the clothing mask to source pixels.

---

## 2. Decision informed

Whether protect-by-construction (inpaint) becomes the V1 try-on architecture (replacing
full re-generation), or whether residual under-clothing body drift still needs a body/pose
shape control on top (the next lever if E-010 is insufficient).

---

## 3. Prerequisites (Phase 0 — build, before any comparison)

This experiment requires components that do not exist yet:

1. **Inpaint engine — verify availability in the local ComfyUI** (env-check, no assumption):
   - preferred: **FLUX Fill** (named in the stack) — confirm model + nodes are installed;
   - fallback: **QIE-Edit in masked / img2img mode** (source image VAE-encoded as base latent,
     denoise < 1 inside a mask) if FLUX Fill is not present.
   - If neither is available locally, this is a **blocker** — surface the exact missing
     model/node to the owner (download is a GUI step the agent cannot do).
2. **Clothing-region mask on the source person.** Segment `person_front.png` for the
   body area that garments occupy (torso + legs), as the union of the person's current
   clothing and the target garment extent, dilated for seams. Outside this mask = source
   pixels, untouched.
3. **Inpaint workflow template** (`system/workflows/`), content-addressed and hashed like the
   existing ones, with cfg/sampler/scheduler/negative/denoise all threaded (no baked params).
   `run_slice` gains the params it lacks (sampler/scheduler/negative/denoise/mask).

Phase 0 is real engineering and may surface blockers; it ends at an owner checkpoint
(one inpaint output reviewed) before the A/B in Phase 1.

---

## 4. Method

### 4.1 Arms

| Arm | Engine | Latent | What it preserves |
|-----|--------|--------|-------------------|
| A — full regen (baseline) | QIE Lightning 4-step (E-009 R1) | empty latent, denoise 1.0 | nothing by construction — data exists |
| B — inpaint | FLUX Fill or QIE masked | source image, denoise<1 inside clothing mask | face/skin/hands/body-outside-mask/background = source pixels |

### 4.2 Fixed

Person `person_front.png`; outfit `outfit_001`; board `hybrid_mask_crop` (frozen, SHA-verified);
720×1024; seeds [42, 123]; task-correct prompt. Only the generation path (full-regen vs
masked inpaint) varies.

### 4.3 Axes — body AND garment are CO-PRIMARY (owner reminder, 2026-06-15)

| Axis | Metric | Role |
|------|--------|------|
| **Body** | `body_pose`: hip/shoulder Δ% vs source, pose_mismatch, visibility | the question |
| **Face** | ArcFace cosine vs source | must not regress (≥ 0.57, and not below arm A) |
| **Garment colour** | per item: ΔE + hue/chroma split + presence (segmentation/sanity) | **co-primary — must not regress** |
| **Garment detail** | owner verdict per item: cut, closure/buttons, straps, texture, layering | **co-primary**; machine item-identity/detail is a known gap (audit) → owner eye is primary here |
| Seam / mask quality | owner check for halo/seam at the mask boundary | inpaint-specific risk |

### 4.4 Phases

- **Phase 0:** build (engine check, mask, workflow); owner reviews one inpaint output.
- **Phase 1:** generate arm B for seeds [42, 123] with the full gate suite; arm A from E-009.
- **Checkpoint (owner):** per seed, judge the four criteria on B vs A side by side.
- **Phase 2:** per-axis comparison table; apply §5; `conclusion.md`.

---

## 5. Acceptance criteria (fixed before results)

Inpaint **wins only if it improves body WITHOUT regressing the outfit or the face** — both
halves matter:

- **Body better:** mean |hip change| materially below A's ~8.85% (target: ≤ ~4.5%), shoulders
  not worse, owner "same body".
- **Face not worse:** cosine ≥ 0.57 and not below arm A.
- **Garment not worse (hard gate):** for every required item, B's colour verdict (per the
  hue/chroma-aware gate) is **at least as good** as A's, all items present, layering correct,
  and the **owner's per-item detail verdict is not worse** than A. A body win bought by a
  blurrier / wrong-detail garment does **not** pass.
- **No seam/halo** the owner rejects at the mask boundary.

If body improves but garment regresses → inpaint is not adopted as-is; iterate the mask /
conditioning before concluding. If body still drifts inside the mask with garment intact →
escalate to a body/pose shape control (next lever).

---

## 6. Risks / unknowns (stated up front)

- FLUX Fill availability is unverified; QIE masked mode is the fallback.
- Mask boundary seams / halos (the `background_restore` audit finding applies — need
  feathering, not a hard binary edge).
- The under-clothing torso width is still drawn by the model **inside** the mask, so inpaint
  may not fully remove body drift — that residual is exactly what a later body-control lever
  would address.
- Inpaint is less "holistic" than a full pass — large-garment layering across the whole torso
  may compose less coherently; this is why garment fidelity is a hard gate here.

---

## 7. Cost estimate

| Step | Est. |
|------|------|
| Phase 0 build (engine check, mask, workflow, 1 test output) | 1–2 sessions |
| Phase 1 generate B ×2 seeds + gates | ~10–15 min GPU |
| Phase 2 collation + conclusion | < 1 session |

---

*Protocol written 2026-06-15. One person, one outfit, controlled frontal pose — generalisation
NOT claimed. Garment accuracy is a co-primary acceptance axis, not traded for body fidelity.*

---

## Owner sign-off

- [x] Direction approved: inpaint-first protect-by-construction (build Phase 0, then A/B).
- [x] Co-primary axes incl. garment fidelity as a hard gate, and the per-axis decision rule.
- [x] Accept that Phase 0 is a build that may surface an engine/download blocker.

**Signed:** owner, 2026-06-15 (approved in session). Execution delegated to a separate session.
