# E-001 — Segmentation mask quality on our images

**Date written:** 2026-06-11
**Status:** ready to run

---

## 1. Question

Does GroundingDINO + SAM1 (the deployed fallback) produce usable masks for the
region types required by the pipeline — both large regions and small/thin ones?

*(The original BUILD_PLAN question named SAM3. SAM3 is blocked; the actual tool
under test is GDINO+SAM1 via `comfyui_segment_anything`. The decision this
experiment informs is the same: tool choice for `system/segmentation/`.*

---

## 2. Decision informed

- **Primary:** whether GDINO+SAM1 is adequate for V1, or whether SAM3 must be
  unblocked despite the ComfyUI-venv risk.
- **Secondary:** if GDINO+SAM1 fails, the failure type determines the response:
  - Fails on **large regions** (person, top, bottom) → SAM3 needed, or different
    GDINO threshold; investigate before proceeding.
  - Fails on **small/thin regions only** (belt, earrings, face/hair boundary) →
    SAM3 in isolated venv (standalone Python, not ComfyUI). ArcFace face-crop and
    ΔE on accessories are the downstream consumers; they must still get a usable mask.

**SAM3 return trigger** (to be written in `conclusion.md` only if triggered):
Specific region type that failed E-001 acceptance + evidence that SAM3 fixes it
(small comparative test on the failing cases). This trigger, not installation
convenience, is the condition for installing SAM3 deps.

---

## 3. Method

**Inputs:**
- `assets/` person photos (all available frontal photos)
- 2 archived generated images from `archive/` (as stand-ins for pipeline output)

**Region labels per run:**
```
person, face, hair, background, top, bottom, shoes
```
Plus any accessories present in the photo:
```
belt, earrings, necklace, bag
```
(only if visible — document which labels were attempted on which photo)

**Tool configuration (frozen for this experiment):**
- `system/segmentation/grounded_sam.py`
- SAM model: `sam_vit_h (2.56GB)`
- GDINO model: `GroundingDINO_SwinT_OGC (694MB)`
- threshold: 0.3 (default; single value — no sweep in this experiment)

**Prompt mapping:**
```
person      → "person"
face        → "face"
hair        → "hair"
background  → "background"
top         → "shirt . top . blouse . sweater"
bottom      → "pants . trousers . skirt . jeans"
shoes       → "shoes . boots . sneakers"
belt        → "belt"
earrings    → "earrings . earring"
necklace    → "necklace"
bag         → "bag . handbag . purse"
```

**Output per image:** one mask PNG per label in `results/NNN_imagename/`.

**Overlay step:** for each mask, produce a coloured overlay on the source image
(mask region tinted, alpha ~0.5) for visual review. Save to same results dir.

**Owner review:** inspect every overlay. Annotate each mask as:
- `ok` — mask covers the intended region adequately
- `partial` — mask covers most of the region but has visible gaps or bleeds
- `fail` — mask is wrong or missing entirely

Document all `partial` and `fail` results with a one-line description
("bleeds into background", "missed left shoe", etc.).

---

## 4. Acceptance criteria

Defined before running. Evaluated after owner review.

**Pass (GDINO+SAM1 adequate for V1):**
- All six core regions (`person`, `face`, `background`, `top`, `bottom`, `shoes`)
  rated `ok` or `partial` on ≥ 80% of test images.
- `partial` ratings do not propagate to gate failures — verify by running the
  identity gate and ΔE gate on one image with the actual masks; if the gates give
  plausible numbers, `partial` is acceptable.

**Conditional pass with documentation (proceed, document gaps):**
- Core regions pass as above.
- Small/thin regions (`belt`, `earrings`, `necklace`) rate `fail` on some images.
- Document the failing region types. They are excluded from V1 evaluation scope
  pending a targeted fix. SAM3 return trigger is noted but not acted on yet.

**Fail (GDINO+SAM1 not adequate):**
- Any core region (`person`, `face`, `top`, `bottom`, `shoes`) rates `fail` on
  ≥ 50% of test images, OR `background` is unusable (no valid person isolation).
- Action: investigate threshold variation first (rerun with threshold 0.2 and 0.4
  on failing images; document results). If still failing → SAM3 trigger activated.

---

## 3b. Amendment (2026-06-11) — garment reference images

E-001 covers **two image types**, not one:

**Type A — person photo** (`assets/person/person_front.png`):
Segment body + worn-garment regions. Prompts as in §3 above.

**Type B — garment reference images** (`assets/outfits/outfit_001/`):
Segment the garment itself from the product-photo background. One label per image:
```
belt.jpg          → "belt"
blouse_front.webp → "blouse . shirt . top"
blouse_back.webp  → "blouse . shirt . top"
earrings_disc.webp → "earrings"
shoes_wedge.webp  → "shoes . heels . wedge"
skirt_front.webp  → "skirt"
skirt_back.webp   → "skirt"
```
Acceptance for Type B: mask isolates the garment from the white/neutral background.
Used by the color gate — contamination from background pixels inflates ΔE.

*(Asset structure note: `assets/person/` = photos of the person to re-dress;
`assets/outfits/outfit_NNN/` = garment reference images for outfit NNN;
`assets/outfits/pool/` = loose garment pool not yet assigned to an outfit.)*

---

## 5. Cost estimate

- ComfyUI segmentation runs: ~N_images × 7–11 regions × ~10–15s each ≈ 10–20 min
- VRAM: SAM-H (2.56GB) + GDINO (~1GB) concurrent; should fit in 16GB
- Owner review time: ~30 min
- Sessions: 1
