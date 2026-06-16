# E-010 — Reliable try-on = edit-the-photo (inpaint) + body-shape control

**Status:** UPDATED 2026-06-15 (owner-directed; corrected an internal inconsistency — body-control
was wrongly deferred). Approved direction; engine selected in Phase 0. Execute in a separate
session — see `STARTER.md`. Not yet run.
**Governed by:** METHODOLOGY.md §2; design §7 (protect-by-construction); follows E-009.

---

## 1. The reliable method is BOTH (this is the whole point)

The owner-rejected defect is **body proportions** (E-009: hips ~−9%, overall slimmer figure). Two
mechanisms are needed, because each fixes a different part and **neither alone is sufficient**:

- **Inpaint (edit only the clothing):** keeps the person's pixels OUTSIDE the clothing mask
  (face, hair, neck, hands, visible skin, lower legs, background) by construction, and takes the
  garments from the **board IMAGE** (not text). Fixes identity/face/skin/limbs/background and kills
  the gross "different person" failure. **Does NOT pin the body width under the clothing** — the
  model still draws there, and the rejected hip slim sits under the skirt.
- **Body-shape control:** gives the model an extra input — the source person's **pose/silhouette
  (skeleton or body outline)** — and forces the generated body to follow it ("draw what you like,
  but shoulders/waist/hips must match this shape"). This is the **only** mechanism that pins the
  proportions **under** the clothing — i.e. it fixes the actual rejected defect. It does not pin
  face/background pixels — that is inpaint's job.

So the target architecture is **inpaint + body-control together**. E-010 builds toward both;
inpaint alone is a measurement step, **not** the expected end state. (Earlier drafts deferred
body-control to a hypothetical E-011 — that was wrong: it deferred the one fix for the complaint.)

## 2. Engine selection — Phase 0 must pick a stack that supports ALL THREE

Requirements for the engine/stack: (a) condition garments on an **image** (board / per-garment
crops); (b) **masked / source-preserving** edit (keep pixels outside the clothing mask); (c) a
**body/pose-shape control** (pose, depth, or silhouette) to constrain proportions. Plus local 16 GB.

This criterion likely **reframes the engine choice**: QIE-2511's masking AND control support are
both uncertain (special layered latent; no known body ControlNet), whereas the **FLUX ecosystem**
has mature, composable pieces — FLUX Fill (inpaint) + FLUX Redux / IP-Adapter (garment image) +
FLUX ControlNet (pose/depth). The text-only FLUX-Fill build already present
(`flux_fill_inpaint.json`) is **disqualified** (no garment image) and kept only as a body-only control.

| Capability | QIE-2511 | FLUX ecosystem |
|---|---|---|
| garment from image | yes (image2=board) | via Redux / IP-Adapter (verify weights) |
| masked source-preserving edit | uncertain (layered latent) | FLUX Fill (designed for it) |
| body/pose-shape control | none known | FLUX ControlNet (pose/depth) |

**Phase 0 procedure:** query the live ComfyUI `/object_info` for what is actually installed across
both stacks; pick the one stack that can do all three (verify each missing weight is downloadable —
that is an owner GUI step, surface it). Produce ONE inpaint test output and review at an owner
checkpoint before committing. If no stack can do all three, surface the exact gap — do NOT proceed
with a half-method or text-only conditioning.

## 3. Method — staged, both committed

| Arm | Path | Fixes | Data |
|-----|------|-------|------|
| A — full regen (baseline) | QIE Lightning, empty latent (E-009 R1) | nothing by construction | exists; not regenerated |
| B1 — inpaint only | selected reference-conditioned inpaint | unclothed person + garment | new (measurement step) |
| B2 — inpaint + body-control | B1 + pose/shape control of the source body | adds: clothed-torso proportions | new (expected end state) |

Fixed: `person_front.png`; `outfit_001`; board `hybrid_mask_crop` (frozen, SHA-verified); 720×1024;
seeds [42, 123]; task-correct colour-less prompt. Phases:
- **Phase 0:** engine/stack selection (§2) + reuse the clothing mask
  (`masks/clothing_region.png`); owner checkpoint on one test output.
- **Phase 1 (B1):** inpaint only → measure how much body drift remains (it may help partially; do
  not assume). Owner checkpoint.
- **Phase 2 (B2):** add the body-shape control → re-measure. This is the committed completion.

## 4. Axes — body AND garment co-primary; garment is a HARD gate

| Axis | Metric | Notes |
|------|--------|-------|
| Body | `body_pose`: hip/shoulder/ratio Δ%, pose_mismatch, visibility | shoulder is the cleaner signal; clothed-hip carries the §1 caveat |
| Face | ArcFace cosine | ≥0.57 and not below A |
| Garment colour | per item: ΔE + hue/chroma + presence | **hard gate** |
| Garment detail | owner per-item verdict: cut/closure/straps/texture/layering | **hard gate**; machine item-identity is a known gap |
| Seam / mask | owner check for halo at the boundary | needs feathering |

## 5. Acceptance criteria (fixed before results)

- **Garment (hard gate):** every item's colour/presence/layering not worse than A AND owner per-item
  detail not worse. A body win bought by a worse garment fails.
- **Face:** cosine ≥ 0.57 and not below A.
- **Body (the rejected defect):** B1 is judged on whether it removes the gross failure and is
  source-clean outside the clothing; the **proportions verdict is expected to require B2**
  (inpaint + body-control). Pass = owner accepts "same body" on B2.
- **Seam:** no halo the owner rejects.

Owner verdict per axis is the acceptance; gates advisory; no aggregate score.

## 6. Risks / unknowns

- **Body-control feasibility is the central risk** — a pose/shape control compatible with the chosen
  garment-image + inpaint engine may not exist locally. If it does not, "reliable body off-the-shelf"
  is in doubt → either a warp-to-source-body composite, or this becomes a kill-criterion signal
  (off-the-shelf cannot preserve body morphology; revisit engine/product). Phase 0 must check this.
- QIE layered-latent may not accept masking; FLUX Redux/IP-Adapter/ControlNet weights may need
  download (owner GUI step).
- Mask-boundary seams (feathering required, per the `background_restore` audit finding).
- Holistic composition lost in region editing → garment layering may be less coherent (hence the
  hard gate).

## 7. Cost estimate

| Step | Est. |
|------|------|
| Phase 0: stack check + 1 test output | 1–2 sessions |
| Phase 1 (B1) ×2 seeds + gates | ~10–20 min GPU |
| Phase 2 (B2) ×2 seeds + gates | ~10–20 min GPU + control setup |
| Collation + conclusion | < 1 session |

---

*Updated 2026-06-15. One person, one outfit, controlled frontal pose; generalisation NOT claimed.
The reliable method is inpaint + body-control TOGETHER — inpaint protects the unclothed person and
the garment (from the board image, never text); body-control pins the clothed-torso proportions,
which is the owner-rejected defect. Neither half alone is the goal.*

---

## Owner sign-off

- [x] Reliable method = inpaint + body-control together (body-control NOT deferred — it fixes the
      rejected under-clothing proportions).
- [x] Engine selected in Phase 0 by support for all three (garment-image, masked edit, body control);
      text-only disqualified.
- [x] Body-control feasibility may be a blocker / kill-criterion signal; surface it honestly.

**Signed:** owner, 2026-06-15 (directed this correction). Execution delegated to a separate session.
