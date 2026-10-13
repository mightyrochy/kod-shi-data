# E-007 Protocol — Task-correct adapter re-baseline

Date: 2026-06-13. Status: **owner signed 2026-06-13 — running.**
Spec: design/adapter_redesign_2026-06-13.md §3, §5, §6, §9.

---

## 1. Question

Does the task-correct adapter — labeled crop board + board/layout/label-referencing
transfer prompt — produce the intended transfer task (preserve the input person,
re-dress from the board) measurably better than the confounded pre-2026-06-13 baseline?

---

## 2. Decision informed

Adapter conditioning design for ALL future experiments. This is the re-baseline:
the first generation under a conditioning stack that actually expresses the task.
E-005/E-006/E-008 generation conclusions are confounded by the old conditioning
(see design/adapter_redesign_2026-06-13.md §1) and must not be used for decisions
until this re-baseline exists.

Secondary: H-COLOR (do color words in prompts degrade color fidelity?) rides along
at no extra cost — the new transfer prompt is still color-word-free, so the rule
is tested implicitly.

---

## 3. Method

### What the new adapter does (implemented before this protocol — pending sign-off)

**Board (`system/adapter/panel.py`):**
Each garment crop cell carries a rendered text label at its bottom, derived from
the reference file stem: `Path(ref_path).stem.replace("_", " ")`.
- "blouse_front.webp" → cell label "blouse front"
- "blouse_back.webp"  → cell label "blouse back"
- "skirt_front.webp"  → cell label "skirt front"
- "skirt_back.webp"   → cell label "skirt back"
- "belt.jpg"          → cell label "belt"
- "shoes_wedge.webp"  → cell label "shoes wedge"
- "earrings_disc.webp"→ cell label "earrings disc"

Garment crops are unchanged (garment-only, V-REF-001 still enforced).

**Prompt (`system/adapter/prompt.py`):**
Transfer instruction. Exact text for outfit_001 (see checkpoint §a below).
- States person preservation positively (face, hair, skin tone, body, pose, background).
- References image 2 (the board) and its cell labels by name.
- Wires layering_order: "blouse, belt, skirt, shoes, earrings".
- Includes visibility_notes verbatim from layout_logic.
- No color words.
- Negative prompt: empty (cfg=1.0 → inert; E-014 tests the negative channel later).

**Instance selection (`system/segmentation/grounded_sam.py`):**
After ImpactFlattenMask union is downloaded, `_largest_area_mask()` extracts only
the largest connected component. Eliminates the secondary-detection absorption
that corrupted belt/bottom masks.

### Conditions (arms)

| Arm | Description | Generations |
|-----|-------------|-------------|
| A (baseline, historical) | Confounded pre-2026-06-13 adapter. Data from E-005: K=5 seeds 42/137/256/512/1337, Lightning config (4 steps, cfg=1.0, 720×1024). | 0 — data exists |
| B (new adapter) | Same K=5 seeds, same Lightning config (4 steps, cfg=1.0, 720×1024), corrected adapter (labeled board + transfer prompt + instance selection). | 5 new |

### Fixed across arms (no variation)

- Outfit: outfit_001 (blouse, skirt, belt, shoes, earrings)
- Person photo: same as E-005
- Seed set: 42, 137, 256, 512, 1337
- Config: Lightning (4 steps, cfg=1.0, 720×1024, sampler=euler, scheduler=simple)
- References: garment-only crops (V-REF-001)
- Negative prompt: empty (cfg=1.0)
- Segmentation threshold: 0.3

### Measurements per generation (arm B)

1. Mask sanity guard (`system/segmentation/sanity.py`) — run on all region masks.
   Any flag is surfaced to owner before gates are run.
2. ArcFace identity cosine (`system/gates/identity.py`) — generated vs person source.
3. CIEDE2000 ΔE per garment region (`system/gates/color.py`) — vs reference crops.
4. Proportion gate score (`system/gates/proportions.py`) — generated vs person source.
5. Owner visual review of all 5 arm-B outputs — mandatory; no conclusion without it.

---

## 4. Acceptance criteria

The re-baseline is accepted (new adapter becomes the standard) when ALL of:

**A. Identity (gate):**
Mean ArcFace cosine across 5 seeds ≥ 0.776 (arm-A floor from E-005).
Identity must appear to be expressed by the prompt (owner confirms), not merely
preserved by QIE's structural bias.

**B. No color regression (gate):**
For each garment region that was PASS (ΔE < 3.0) in arm-A E-005:
at least 3/5 arm-B seeds do not cross into FAIL (ΔE ≥ 5.0).
WARN range (ΔE 3–5) on a previously-PASS region is surfaced to owner, not auto-fail.

**C. Task expression (owner verdict — mandatory):**
Owner confirms that at least 3/5 arm-B outputs visually show garments taken from
the board (not hallucinated), stated explicitly. This criterion cannot be substituted
by gate numbers.

Failure outcome is also valid knowledge: if the re-baseline fails any criterion,
the failure mode is documented and the adapter design goes back to revision.

---

## 5. Cost estimate

- Arm B: 5 generations × ~30–60 s = ~5 minutes GPU time.
- Gate analysis + report: ~30 minutes.
- Owner review session: 1 session.

---

## 6. Integration FAIL tests (required before first run)

Per METHODOLOGY §2 p.6 — all must pass before any generation is run:

| Test | File | Status |
|------|------|--------|
| Instance selection: multi-component union → selects largest, not union | `system/tests/test_instance_selection_fail.py` | written (this commit) |
| Prompt: no color words in build_prompt output | `system/adapter/prompt.py` — `_check_no_color` fires at build time | enforced at build time |
| Panel: labeled board visual checkpoint | checkpoint §b (owner review before run) | pending owner sign-off |

Run before execution:
```
python -m pytest system/tests/test_instance_selection_fail.py -v
```

---

## 7. Pre-run checklist (owner sign-off items)

- [ ] (a) Exact prompt text for outfit_001 — reviewed and accepted
- [ ] (b) Labeled board cell layout — reviewed and accepted
- [ ] (c) This protocol — signed

Owner sign-off: confirmed verbally. Date: 2026-06-13

**Prompt revision (owner, 2026-06-13):** removed "Layer from inner to outer: ..." sentence (redundant with visibility_notes); simplified visibility_notes: "Blouse is the visible top; peplum hem..." → "Blouse hem sits over..."; removed "if ears are visible" conditional. Final prompt text in system/adapter/prompt.py build_prompt(), verified against outfit_package.json.
