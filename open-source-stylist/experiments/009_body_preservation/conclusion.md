# E-009 — Conclusion: QIE config comparison (body · face · item colour)

**Closed:** 2026-06-15 (partial — the no-Lightning arm is an invalid config; see below)
**Data:** `results/comparison.md`, `results/{R1_lightning,R2_full_cfg5}/seed_*/`
**Owner checkpoint:** done (4 generated.png reviewed; verdict recorded below)

---

## Answer to the question

**The Lightning-vs-full-model body question is NOT answered — the fair no-Lightning arm
came out invalid.** What is settled:

1. **Lightning body slimming is confirmed systematic and owner-rejected.** Hips narrow
   ~9% with shoulders held, across all four Lightning seeds measured (today s42 −8.8% /
   s123 −9.0%; earlier s42 −8.8% / s123 −8.9%), pose match ≤3°, face identity preserved
   (cosine 0.76–0.81). **Owner verdict: ~9% is noticeable and unacceptable** — and this is
   the easiest possible case (plain background, simple outfit, frontal pose); harder cases
   are expected to drift more.

2. **The fair no-Lightning arm (R2: full model, 20 steps, cfg 5.0, euler/simple, empty
   negative) is INVALID per the pre-registered §4 validity guard:**
   - Face identity collapsed: cosine **0.348 / 0.373** (both ≪ 0.57) — a visibly different,
     generic person (the "generic-fashion-model effect", cf. V-REF-002 / E-008).
   - Output is **under-converged / raw**: marbled satin, blotchy skin — the non-distilled
     base model run with Lightning-tuned sampler settings (euler/simple, only 20 steps).
     BUILD_PLAN row 3b specifies no-Lightning at **40 steps**; the full model also needs a
     **real negative** (BUILD_PLAN:171), held empty here.
   - seed 42 additionally had pose drift 10.7° (>10° = comparison invalid) and hip −28.7%.

   Per the guard, this is **not** evidence that "the full model is worse" — it is a wrong
   config. Removing Lightning is not a toggle: it requires 40 steps + cfg 4–7 + real
   negative + a full-model-appropriate sampler/scheduler, run together.

---

## Per-axis data (advisory gates; owner verdict is acceptance)

See `results/comparison.md`. Summary:

| arm | hipΔ% (s42/s123) | face cosine | item colour |
|-----|------------------|-------------|-------------|
| R1 Lightning | −8.8 / −9.0 | 0.806 / 0.760 | blouse PASS, skirt WARN, belt/shoes mixed |
| R2 full cfg5 | −28.7 / −8.3 | **0.348 / 0.373** | wrecked (sanity skips s42; green skirt FAIL 18.7 s123) |

---

## Decisions

1. **Body preservation by config is not the path.** Lightning systematically slims
   (~9%, rejected); the full model at the tested config collapses identity and
   under-converges. → Pivot to **protect-by-construction** (E-010, inpaint-first): keep the
   source person's pixels (face/skin/body-outside-clothing/background) and edit only the
   clothing region, instead of re-generating the whole person from an empty latent
   (the current `EmptyQwenImageLayeredLatentImage`, denoise 1.0 — the root cause of the drift).

2. **Tooling gap found.** The adapter hardcodes `euler`/`simple` (adapter.py:62-63) and
   `run_slice` does not expose sampler/scheduler/negative. A *fair* no-Lightning bench
   cannot be run until these reach the engine (as cfg now does). Deferred unless the
   full-model route is revisited.

3. **No-Lightning question stays OPEN, deprioritised** — not refuted, just not yet fairly
   tested.

---

## Knowledge status changes

Write to `knowledge/` (hypotheses, with this date):
- Lightning 4-step systematically slims hips ~9% (shoulders held) on outfit_001 — measured
  at the skeleton (`body_pose`), owner-rejected. Root cause: full re-generation from an
  empty latent (body not pixel-anchored), not a colour/seed issue.
- "Full model preserves the body better" — **untested** (the only no-Lightning run was an
  invalid config). Do not record it either way.
- Generic-fashion-model collapse reconfirmed when conditioning is under-constrained.

---

*Closed 2026-06-15. Next: E-010 — protect-by-construction try-on (inpaint), measured on
body AND item fidelity. Owner reminder recorded: garment accuracy is a co-primary axis,
not to be traded for body preservation.*
