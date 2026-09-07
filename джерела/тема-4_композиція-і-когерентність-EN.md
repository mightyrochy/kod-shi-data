# Composition and Coherence

**Theme 4 of 9. Complete, self-contained.** Replaces `тема-4_композиція-і-когерентність.md` (1543 lines, 14 ancestor files) and the corrections pass `composition-knowledge-EN.md`.

Written in English because every primary source located for this domain is English; translating them into Ukrainian and back was where the corpus lost its numbers.

---

## How to read this file

Every rule *should* carry four fields:

- **WHEN** — the conditions under which it fires.
- **FORCE** — `hard` (reject) · `strong` (large penalty) · `default` (small penalty, overridable) · `hint` (prior only). **Force never exceeds verification.**
- **BREAKS** — the conditions under which it is known or suspected to fail.
- **CHANGES** — the concrete decision over a real garment that differs with the rule versus without it. A rule with no answer here is not a rule; it is explanation vocabulary.

**Most do not.** Audited count over the 71 rule blocks in this file:

| Field | Present | Absent |
|---|---|---|
| CHANGES | 30 | **41** |
| BREAKS | 19 | **52** |
| WHEN | 5 | **66** |

So **41 of 71 rules here are conclusions without conditions** — the form this project bans, carried over from the corpus and not repaired. They are readable and probably correct; they are not yet rules, because nobody can tell from them what decision would differ.

**Do not read the presence of a K-ID as verification.** A rule block with a FORCE tag and nothing else is a compressed practitioner convention. The rules that survive the four-field test are concentrated in Parts II, VII.3, VII.4, VIII, X.1, XI and XII — roughly, wherever a primary source or a real failure case exists behind the claim.

The missing fields cannot be written by reasoning. CHANGES has to come from a real decision over a real garment or a real failure prevented; inventing it would be the same fabrication this file exists to correct. They get filled by feed runs, not by another editing pass.

**Filled by a feed run, 2026-08-24:** CHANGES for K-COMP-01 and K-COL-01 (winner changed on `ager_brief.xml`), WHEN for K-COL-01 and K-SIL-09 (`stolyarchuk_com_ua.xml`), layer semantics for K-WEA-01, first executable instance of K-IO-05. Active by the three-tier test (executes · leaves a trace · changes the composer's winner) on real feeds, after the second pass of 2026-08-24: **4** (K-COL-01, K-COL-06, K-COMP-01, K-MAT-03); 3 more change rank but not the winner (K-BOD-02, K-KOH-05, K-KOH-06); K-VAR-01, K-COMP-02, K-SYS-08/09, K-IO-03/04, K-LNG-04, K-SIL-09, K-CUT-00 execute and leave a trace but change the *output text or portfolio*, not the winner; the rest have no input in these feeds — no shoes, no third piece, no lengths, no metal, no fabric labels. Gate: `check_edits.py` §25.

Evidence tiers: **T1** measured empirics · **T2** engineering standards · **T3** practitioner consensus · **T4** aesthetic/cultural systems.

**Three honest labels used throughout:**
- `[sourced]` — traced to a named primary source, numbers verified against it.
- `[convention]` — convergent practitioner practice, no traceable origin, no measurement. Not false; unverified.
- `[folkloric constant]` — a specific number we invented or inherited without calibration. Usable as a default, never as a threshold.

---

## Scope boundary

This theme owns: **how independently chosen garments become one intentional whole**, and whether that whole fits its occasion.

It does not own, and does not re-derive:
- body geometry, fit and silhouette diagnosis → theme 1
- colour on the person (undertone, contrast level, near-face rules) → theme 2
- fabric hand, materials science, craft signals → theme 3

Where this theme needs those layers it names the interface and moves on. The compact maps that physically lived in the theme-4 source file are preserved in Appendix A and B so this file remains usable alone.

The distinction that defines the theme: **a designer composes elements inside one garment they control entirely. A stylist coordinates independently chosen objects — top, bottom, shoes, bag — from different brands, fabrics and colours, which nobody designed together.** That is a coordination problem, harder than the design problem, with its own methodology. This is where a pile of clothes becomes either an outfit or a heap.

---

# PART I — What makes an outfit successful

## I.1 Two canonical answers, each incomplete

**The designer frame** (academic, T2): design elements + design principles → harmony/unity. Describes the outfit as a *visual object*. Convergent across textbooks and curricula.

**The practitioner triad** (T3): fit + appropriateness to occasion + expression of personal style. Describes the outfit *on a specific person in a context*. Near-unanimous among working stylists.

The designer frame says whether an outfit is good *in itself*. The stylist frame says whether it works *on this person, for this situation*. A successful outfit needs both.

Both frames explicitly concede that the final judgement of "good" is subjective and cultural. This is not a weakness of the frames — it is a built-in limit, and it is the direct argument for why the system needs **user goal + context**, and why there is **no universal numeric style score**.

## I.2 The nested levels

Ordered as preconditions: a lower level must hold for higher ones to mean anything.

| Level | Name | Content |
|---|---|---|
| **0** | Fit | The garment physically sits on the body. Nothing above works if this fails. |
| **1** | Internal composition | Balance, proportion, one focus, rhythm, enough contrast inside unity. |
| **2** | Suitability to the person | Complements this body's proportions and this person's colouring; expresses their identity. |
| **3** | Context appropriateness | Suits the occasion, environment, dress code. |
| **4** | Signal | What the outfit communicates to observers — and whether that matches intent. |
| **5** | Wearer experience | Comfort, movement, practicality; the person can actually live in it. |

The practitioner triad maps onto this: *fits well* = L0, *suits the occasion* = L3, *reflects personal style* = L2+L5. Practitioners treat L1 as assumed craft and do not name it — but L1 is what makes the triad executable. L4 they fold into "appropriate" plus "style."

**For the system, both are useful:** the full level set is the critic's definition of done; the triad is the human-facing goal structure at onboarding.

**Objectivity is not uniform across levels.** L1–L2 have a more perceptual core (balance, focus, fit). L3–L4 are culturally contingent and drift. L5 is purely individual. Therefore the weighting of levels is set by *the person's goal + context + culture*, not by a constant.

## I.3 The central tension

**Unity versus variety.** Too much repetition → dull. Too much variety → chaotic. A successful outfit sits between: enough unity to read as one thing, enough contrast not to be boring.

This is the whole definition of "put together but not bland," and it is the reason the system's quality model is **two-sided**: a ceiling on excess *and* a floor on interest. A system built only from constraints converges on a local optimum — neutral base plus one accent plus a third piece — which is the generic-safe uniform. Both checks are enforced.

**FORCE:** `strong`, architectural.
**Status:** the shape of the claim is `[sourced]` (§II); the specific floor and ceiling thresholds are `[folkloric constant]`.

## I.4 The wellbeing reframe

Older design texts state Level 2 as "emphasise assets, conceal flaws." Current practitioner consensus reformulates: not *change or hide the body* but **distribute visual weight**, *express*, *suit*.

This is not an ethical add-on to the professional standard — it **is** the current professional standard. The positive frame is adopted; flaw language is rejected outright.

**Consequence, `hard`:** every explanation is gated. A body zone may be discussed only when the person initiated that goal. Otherwise the explanation stays on composition, colour, occasion, comfort. The softened form ("delicate correction" without goal-initiation) is banned too.

---

# PART II — The coordination optimum: the one measured claim

This is the only quantitative empirical result in the composition domain, and it is smaller than the corpus claimed.

## II.1 The source

**Gray K, Schmitt P, Strohminger N, Kassam KS (2014). *The Science of Style: In Fashion, Colors Should Match Only Moderately.* PLoS ONE 9(7): e102772.** Open access.

**Prior corpus error, corrected:** the corpus cited "the Goldilocks principle (PLOS ONE, Duke + Carnegie Mellon)", "Gray et al. 2014" and "CIEDE2000" as *three independent converging sources*. The first two are the same paper — Gray was at UNC Chapel Hill, Strohminger at Duke, Kassam at Carnegie Mellon. The third is a colour-difference formula: a ruler, not a measurement. **One voice, counted three times.**

## II.2 What was measured

239 mTurk participants (69% women, mean age 35.4, SD 12.9). Each saw 30 colour combinations from one of four palettes. Palettes 1–2 were women's clothing, 3–4 men's. Each palette contained exactly four colours assigned across four garment slots — 256 possible combinations per palette, sampled quasi-randomly to span the range from fully matching to fully different.

**Coordination was not rated globally.** Participants rated **every pair of colour swatches** within a palette on three items (coordinated / matching / similar; α > .81). Those pairwise judgements were aggregated per outfit and **z-scored within palette**. Fashionableness came from fashionable / good / liked on 5-point scales (α > .95), also z-scored within palette.

## II.3 Results

| | Linear | Quadratic |
|---|---|---|
| Women's clothing | R² = .18, F(1,58) = 13.04, p = .001 | R² = .44, F(2,57) = 22.23, p < .001 |
| Men's clothing | F < 1, **not significant** | R² = .28, F(2,57) = 11.18, p < .001 |

The quadratic term explained roughly twice the variance of the linear term in womenswear. In menswear there was **no linear trend at all** — more matching was not on its own better.

**Unit of analysis:** the degrees of freedom (58, 57) show the curve was fitted over **60 outfit combinations per gender**, not over 239 people.

## II.4 The rule

> **K-COMP-01. Target the middle of the coordination range, not the maximum.**

**WHEN:** scoring any assembled outfit's colour relationships across its slots.
**FORCE:** `default`. One study, no located replication, illustrated stimuli, n = 60 at the level of the fitted curve.
**BREAKS:**
- **There is no ΔE target in the paper.** Coordination was z-scored *within* a four-colour palette, so the optimum is a **rank position inside the candidate set**, not an absolute colour distance. The corpus claim that this gives "a specific, measurable target (ΔE range, chroma spread)" is unsupported. Any absolute ΔE band is our invention.
- The optimum is relative to the sampled range. A palette of four near-neutrals has a different absolute midpoint than one containing a saturated colour.
- Menswear showed no linear component; the "more coordination is better up to a point" prior is not licensed symmetrically across categories.
- The study contains no texture, fabric, silhouette, fit, body, or occasion. It licenses **nothing** about coherence on those axes.
- The authors flag external validity as untested and call for work on real photographs.
- **The authors explicitly do not claim moderate matching is the dominant factor.** All other variables were held constant by design, and the paper states matching is not the only key to a fashionable outfit. Our file treats this curve as the objective function — more weight than the source gives it.

**CHANGES:** without it the composer maximises palette agreement and converges on tonal, matchy output; with it the composer targets a **middle rank** of mean pairwise colour similarity and penalises both extremes. This is the objective function, and it is the reason "matchy-matchy" is a failure rather than a safe default — it sits past the optimum on the over-coordination side.

**CHANGES — measured on a real feed (2026-08-24, `ager_brief.xml`, 124 designs, colours from the title word, `measure_theme4.py`):** warm-light profile, office +18 °C — without the coordination term the composer's top outfit is *beige printed tee + grey trousers* (the most distant pair in the pool); with it, *khaki printed top + brown eco-leather skirt*. Rank shifted in 16/20 combinations (warm-light) and 20/25 (cool-dark); before the model-key fix (R-FEED-01 branch 3) the pool was five sizes of one tee and the rule reported itself *withheld — candidate set colour-homogeneous* in 8/8 runs. Ablating the term changes the winner in both profiles. This is the first run on which the rule changed a decision over catalogue items; whether the change is *right* is untested (no wear verdict).

**Implementable form.** For an outfit with *k* colour-bearing slots, compute all *k(k−1)/2* pairwise perceptual colour similarities, take the mean, rank that mean within the candidate set. Score peaks at mid-rank. **Do not hardcode an absolute distance until calibrated on the Ukrainian feed.**

## II.5 The parent theory, and its contested status

The two-sided model has a theoretical parent: **Berlyne's inverted-U** between stimulus complexity and preference (Berlyne 1971; earlier Birkhoff 1933 defined beauty as a ratio of order to complexity). Gray et al. situate their finding in that tradition alongside infant attention to sequences of intermediate complexity (Kidd, Piantadosi & Aslin 2012) and optimal distinctiveness in social identity (Brewer 1991).

**But the parent is not settled.** Reviews of complexity and aesthetic preference describe the literature as diffuse and contradictory; some studies find images with *more* elements preferred over fewer, arguing against the inverted-U. Complexity also cannot be reduced to element count — breaking symmetry raises perceived complexity independently.

**Consequence:** the two-sided architecture is **theory-motivated, not empirically established**. It stays, because it is the right shape and it solves an observed failure mode. But it is an architectural bet, and every specific threshold inside it is `[folkloric constant]`.

**Closest adjacent primary source, absent from the corpus:** Hur Y-J, Etcoff NL & Silva ES (2023), *Can Fashion Aesthetics be Studied Empirically? The Preference Structure of Everyday Clothing Choices*, Clothing and Textiles Research Journal. Builds a factor structure for everyday clothing preference from cut-based style and colour across three judgement types (own and like / like but do not own / own but dislike). The nearest thing in the literature to an empirical preference model for ordinary dressing.

---

# PART III — Mechanism: how the eye reads separate garments as one thing

Three perceptual mechanisms, derived from Gestalt grouping. Status: **T3/T4 as applied to outfits.** The Gestalt principles themselves are old and robust; their application to garment coordination is analogy, not measurement. No study located that tests grouping-by-repetition on assembled outfits.

**1. Grouping by repetition (similarity).** A colour, metal or texture repeated at separated points causes the eye to bind those points into a group, which reads as *intentional*. This is the physical basis of cohesion.

**2. The eye travels (continuity).** Repetition gives the eye a route through the outfit — shoes → belt → earring in one colour. The outfit reads as a single movement rather than a set of islands.

**3. One resting point (figure–ground).** One focus holds the eye; everything else recedes as ground. Without a resting point — when everything shouts — the eye cannot resolve the whole, and the result reads as chaos.

So cohesion is not "everything abstractly goes together." It is **controlled repetition + a route for the eye + one pause.**

**CHANGES:** this converts "does it go together?" from a taste judgement into three checkable questions — is there a repeated element at ≥2 separated points? is there exactly one focus? does everything else sit below it in contrast? Those three are what the critic actually asks.

---

# PART IV — The composition toolkit

Convergent practitioner methodology. `[convention]` throughout unless marked.

> **K-COMP-02. Anchor first (hero piece).**
> Choose one expressive item first, then resolve volumes, value and formality around it. Two heroes compete and cancel.
> **WHEN:** at assembly start, before slot filling. **FORCE:** `default` — **lowered from `strong`, verification run 2, 2026-09-05:** no named primary source was found for *two heroes cancel each other* (○ after two passes). The mechanism agrees with K-CRA-02 (exactly one focus), so the rule is not deleted, but its own force cannot exceed convention. The executable form (the O2 pole of the portfolio) is unchanged — it was always ours, T3. **BREAKS:** in strict-uniform contexts (formal dress codes) the anchor may be the dress code itself, not a garment. **CHANGES:** assembly order — the anchor is chosen before the palette, so the palette serves the anchor rather than the reverse.
> **Executable form (code, 2026-08-24):** as the O2 pole of the portfolio (K-VAR-01) — anchor = the most expressive candidate (print > chroma > shine texture), slots filled by the existing ranking around it. It is one pole, not the default order: the default composer still fills from windows first. `strong` is the practitioner claim; the expressiveness score is ours (T3).

> **K-COMP-03. Limited palette with assigned roles.**
> 2–3 base neutrals from the right family + 1–2 accents, with explicit dominant / secondary / accent roles.
> **Source (run 2, 2026-09-05).** Anuschka Rees, "Developing a Colour Palette for your Wardrobe" (anuschkarees.com, 2013-05-23) `[✓]`: assign each item category at least one neutral; accents about 25 % of the capsule (accessories excluded). Named practitioner, mechanism stated (mixability), worked example (a summer capsule). **Re-tier: T4 → T3 `[sourced]`.** Force unchanged. The base's own *≤3 colour families* is **not** Rees's number and stays `[folkloric constant]`. Worked decision: Р-12 in the practitioner-decision register.
> **FORCE:** `default`. **BREAKS:** colour-dominant people go flat in neutrals regardless of value spread — they need actual hues at close values (see theme 2). **CHANGES:** guarantees default combinatorics — any top × any bottom has high prior probability of passing colour rules.
> **Executable form (code, 2026-08-24):** the check side is *≤3 colour families in the assembled outfit, neutrals counted softly* (`outfit` — formerly cited as `K-COL-04`, an ID no theme defines; renamed to this rule). Force in code `soft`: the family count is a T3 convention. The generative side (assign dominant / secondary / accent before filling slots) is **not** implemented — the composer fills slots from windows and checks afterwards.

> **K-COMP-04. Match intensity, not only hue — the hidden key.**
> Compatibility is governed by closeness in **chroma and value**, not primarily by hue relationship. A muted sage and a muted rust coordinate; a muted sage and a neon rust do not, despite the same hue relationship.
> **FORCE:** `strong` for the mechanism; **`hint` for the two numbers the code tests it with** (chroma-gap thresholds 0.044 / 0.163 in OKLab, read off one worked example — T3, `coordination.py`). Force ≤ verification: the code issues the finding as `hint`, and this file said `strong` without a calibrated threshold until 2026-08-24. **Input:** an intensity gap inside the outfit — on both real feeds the candidate pools are all-neutral because the `нейтрали+акцент` scheme assigns the accent role to slots far from the face (shoes, bag), which the feeds lack; the rule has fired only on the synthetic battery. **BREAKS:** deliberate high-low intensity contrast as a fashion signal (spends risk budget). **CHANGES:** this rewrites the default matching logic. Naive systems match by hue wheel relationships; this says sort candidates by chroma/value proximity **first**, then apply hue scheme. Direct change to the retrieval ranking in `outfit.py`.

> **K-COMP-05. Echo for cohesion.**
> An accent is either repeated at ≥2 separated points, or it is the single deliberate focus in the focal zone. A random orphan accent reads as noise.
> **Mechanism (run 2).** Gestalt similarity/repetition and Rubin figure–ground — academically real. But *≥2 separated points* is an aesthetic convention, not a consequence of Gestalt.
> **FORCE:** `default` — **lowered from `strong`, run 2, 2026-09-05:** the threshold "≥2" has no source. **BREAKS:** a single statement piece in the focal zone is the licensed exception, not a violation. **CHANGES:** a cobalt bag with nothing cobalt anywhere else fails unless the bag is the declared focus. Machine-checkable on extracted colours.

> **K-COMP-06. Texture as variety inside unity.**
> Texture contrast adds interest **without** adding a second colour or pattern focus. This is what resolves the core tension of Part I.3 — it is the cheapest way to raise interest without raising noise.
> **FORCE:** `strong`. **BREAKS:** texture contrast is invisible at distance and in photographs (see K-CRA-10). **CHANGES:** when the interest floor is unmet in a conservative context, the system reaches for texture first, not colour.

> **K-COMP-07. Formulas are cached solutions, not truths.**
> Standard combinations (monochrome column + texture contrast; neutral base + one accent) are pre-solved starting points. The wildcard operator is a controlled deviation from them.
> **FORCE:** `hint`. **CHANGES:** formulas seed generation; they never validate output. A formula-shaped outfit still has to pass the blandness checklist.

**Cultural shift of the optimum.** The moderate-coordination target has a culturally located midpoint. The Ukrainian market tolerates — and rewards — more "dressed-up" quality and more shine than the Western samples the research used. The optimum shifts; the shape of the curve does not. `[convention]`, and one of the highest-value things to measure on the local golden set.

---

# PART V — Silhouette and proportion as composition

The body plus clothing is read as one geometric figure. The brain does not evaluate garments; it evaluates **division lines** and **distribution of visual mass**.

**All maps in this part are conditional on intent.** The default described is `conventional-flattering` (moving toward visual balance and elongation). Under `fashion-forward` the same levers are deliberately inverted — controlled hypertrophy. Under `comfort-first`, sensory constraints are hard. Under `context-optimal`, appropriateness dominates.

> **K-SIL-01. One silhouette per outfit.**
> The outfit must resolve to one readable letter: A (narrow top widening down), H/I (straight column), X (marked waist), V/Y (wide top, narrow bottom), O (cocoon). Two competing silhouettes = visual noise.
> **FORCE:** `strong`. `[convention]`. **BREAKS:** deliberate deconstruction under `fashion-forward`. **CHANGES:** rejects candidate sets whose volume distribution is ambiguous — e.g. a full-volume top with a full-volume bottom and no anchor resolves to no letter.

> **K-SIL-02. The rule of thirds.**
> A horizontal division at 1:2 or 2:1 is more dynamic than 1:1. Division at the midpoint is static and shortens.
> **Source (run 2, 2026-09-05).** Imogen Lamport, Inside Out Style (2011) `[✓]`: a 1:1 ratio reads blocky and boxy; a 1:2 ratio elongates. **Re-tier: T3 `[sourced]` for the *shape* of the claim**; the number 1:2 remains a `[folkloric constant]` (it derives from the golden mean, which this base bans as a number). Force unchanged. Worked decision: Р-11.
> **FORCE:** `default`. **BREAKS:** the **golden ratio is explicitly banned as a number** — Φ = 1.618 is a `[folkloric constant]` with no perceptual anchor for garment division. The *shape* of the claim (avoid 50/50, prefer asymmetric) survives; the *number* does not. **CHANGES:** where the belt, hem or colour break is placed — machine-checkable against the body map.

> **K-SIL-03. Volume calculus.**
> Volume × closeness. Full volume both above and below requires an anchor — a defined waist, or exposed narrow points (wrist, ankle, neck). Full closeness everywhere is a separate deliberate silhouette, not a default.
> **FORCE:** `strong`. `[convention]`. **CHANGES:** the licensing condition for wide-leg + oversized top. Without the rule the pair passes; with it, it passes only with a tuck, belt, or exposed ankle/wrist.

> **K-SIL-04. Verticals reliably elongate; "horizontals widen" does not hold.**
> Plackets, creases, open long layers and colour columns elongate. See Part VII.3 for the full stripe evidence — the folk rule is refuted in the mid-body-size regime and reverses at larger sizes.
> **FORCE:** `default` for verticals, `hint` for stripe orientation.

> **K-SIL-05. Visual weight and foundation.**
> Dark / dense / textured / wide = heavier. A massive bottom needs shoes with mass. Hair volume counts as upper mass.
> **FORCE:** `default` — **lowered from `strong` on 2026-08-24**, because the only named source, DeLong, *The Way We Look* (ABC framework), has not been obtained or read by anyone on this project; Part XVI called this *an unchecked rule wearing a checked rule's tag*, and force ≤ verification does not allow the tag to stay. `[convention]` until the book is read.
> **Run 3 (2026-09-06) — closed for research.** DeLong contains the apparel-body-construct frame, figure–ground, closed/open form, part-to-whole and priority of viewing — and **no** rule of the form *dark / dense / wide = heavier*. The term *visual weight* comes from design theory (Arnheim), not from DeLong; *hair volume as upper mass* has no source at all. **The DeLong citation is therefore moved out of this rule** to K-SIL-01 / K-CRA-02 (garment-body wholeness as "the whole"), with provenance `[—]` (pages not opened) and `[✓]` for the existence of the frame (Roach-Higgins & Eicher 1992). Direction of weight can now come only from measurement (a K-COMP-01-style experiment), not from reading.
> **WHEN:** any outfit where bottom mass and shoe mass can be compared — no feed carries either, so the rule has no input today. **BREAKS:** unknown, because the source is unread; the sub-claim *hair volume counts as upper mass* has no source at all.

> **K-SIL-06. Scale matching.** Print size, accessory mass and texture coarseness scale with the person's overall scale (height × bone × features). **FORCE:** `strong`. `[convention]`.

> **K-SIL-07. Leg-line lengthening.**
> High rise; shoes toned to the bottom; nude to bare leg; no break; vertical crease; slit at the narrowest point. **One mechanism: remove horizontal breaks.** An internal colour column (top and bottom at one value under an open layer) is the same mechanism. Practitioners note it is especially effective for H, V and O.
> **FORCE:** `default`. **BREAKS:** the perceptual effect size of leg-lengthening tricks translates to roughly 0.7–1.2 cm — below phone-camera measurement resolution. The rule is real perceptually and **unmeasurable** by our capture pipeline. Do not attach a numeric threshold to it.

> **K-SIL-09. Dresses and jumpsuits are silhouette mono-objects.**
> A dress fixes top, bottom and silhouette simultaneously. The problem reduces to shoes + layer + accessories, and the third piece becomes near-obligatory, because a dress alone reads as *dressed*, not *styled*.
> Type semantics: wrap (X-maker, friendly to full bust and changing bodies) · sheath (formal H/X, fit-demanding) · shift (H, petite-friendly) · slip/bias (fluid, evening and layering; watch cling at the hip) · shirt (casual→smart, belt as the H strategy) · empire (O-friendly, with the caveat in Appendix A).
> **FORCE:** `strong`. `[convention]` — tier T3, so it is issued as `soft`, a remark, never a gate.
> **WHEN:** the outfit's only major surface is a dress (or a single garment). **CHANGES (2026-08-24, `stolyarchuk_com_ua.xml`):** the composer's output on a dress-only feed used to be a dress *blocked by K-COL-01*; now it is a clean dress carrying this remark and a catalogue request for the third piece (shoes toned to the hem, open layer, structural accessory). It changes the text and the request, not the rank — on a feed without shoes it is identical on every dress, and it says so.

> **K-SIL-10. Skirt map.** Pencil (structure, formality, X/H) · A-line (universal, balances A) · pleated (volume and movement, V-friendly) · bias (fluidity) · mini (legs become the focus → interacts with the one-zone rule) · **midi is the riskiest length: the termination point is critical (narrowest point of the calf) and the shoe decides the proportion** · maxi (needs height, lift, or deliberate volume).
> **FORCE:** `default`. `[convention]`.

> **K-FIT-03. Termination points.** Every edge — hem, cuff, waistband — is a horizontal line, and the eye reads body width exactly there. Under a flattering intent, do not terminate a garment at the widest point of a zone (bust, hip, calf). This single mechanism generates the length rules for jackets, skirts, crops and boots.
> **Source (run 2, 2026-09-05).** Imogen Lamport, "Imogen's Three Rules of Horizontal Lines" (2016) `[✓]`, with a client account that states the value of the mechanism: she was given a reason, not just a prohibition on ending jackets at the widest part of the hips. **Re-tier: T3 `[sourced]`.** Worked decision: Р-10.
> **Premise narrowed — the main substantive edit of run 2.** The base, and the whole popular literature, rests on *horizontal widens*. The opposite is measured for **fields of stripes**: Thompson & Mikellidou, *i-Perception* 2011, 2(1):69–76 `[✓]` — to match a vertically striped square in perceived width, a horizontally striped rectangle must be made about 4.5 % wider; horizontal stripes therefore **slim**. Koutsoumpis, Economou & van der Burg, *Perception* 2021 `[✓]`: horizontal stripes and lower luminance each give a small-to-moderate slimming effect, larger together. Two objects the corpus had merged must be separated:
> (a) **a single edge** (hem, cuff, waistband, boot shaft) — a horizontal line that points at body width *at that point*. K-FIT-03 holds, `strong`, now sourced.
> (b) **a field of stripes** across the plane of a garment — not the same object: measurement gives the opposite sign. The claim *horizontal stripes make you look wider* is **deleted as refuted**; K-SIL-04 and K-PRN-01 already stood on this literature and were right.
> **CHANGES:** *before* — a horizontally striped garment takes a penalty as "widening". *after* — that penalty is removed; the penalty remains only for an edge falling on the widest point of a zone.
> **FORCE:** `strong`. `[sourced]` for the edge mechanism, machine-checkable against the zone map.

> **K-FIT-04. Rise is the primary leg/torso proportion lever.** The waistband defines where the eye starts the legs. **FORCE:** `strong`.

> **K-FIT-06. Oversized ≠ ill-fitting.** Deliberate volume requires three markers: (a) a clean or constructively dropped shoulder, (b) balance against one close-fitting element, (c) exposed narrow points. Without all three it reads as clothes that are too big.
> **Voice (run 2, 2026-09-05).** Derek Guy `[✓]`: in oversize what matters is the silhouette as a whole, not volume by itself. This supports the *direction* of the rule; the three-marker test (shoulder / counter-element / narrow point) remains our synthesis.
> **FORCE:** `strong`. `[convention]`. **CHANGES:** this is the discriminator that lets the system offer oversized items at all rather than filtering them out as fit failures.

---

# PART VI — Colour structure in the outfit

Colour *on the person* is theme 2. This part covers colour *among the garments*.

**The paradigm shift, stated plainly:** outfits succeed or fail on **value structure and chroma discipline**, not on hue choice. "Busy" is almost always a conflict of several saturated chromas, not "too many colours."

> **K-COL-01. Value structure first.** 2–3 distinct steps of lightness. Equal value everywhere = flatness (rescuable by texture). Chaotic value = noise. Resolve lightness before hue.
> **FORCE:** `strong`. Supported indirectly by the stripe/luminance evidence in Part VII.3, where luminance was the reliable lever and pattern the weak one. **Issued as a full-force penalty, never a veto** (code register `репліка`, 2026-08-24): the Munsell step is a measured perceptual unit (T2), but *flat outfit = not wearable* is uncalibrated on verdicts, and `hard` requires calibration on a real test set. The same holds for K-COL-06.
> **WHEN:** ≥2 major colour surfaces in the outfit. **A single garment is one lightness level by definition and is not an input** — measured 2026-08-24 on `stolyarchuk_com_ua.xml` (24 dresses, no shoes in the feed): the gate blocked 5/5 candidates for both profiles because a lone dress always reads as *one level*. Now withheld on one surface; K-SIL-09 speaks instead.
> **CHANGES (measured, `ager_brief.xml`, warm-light):** before the R-FEED-01 fix every one of 25 combinations was *khaki top + grey trousers* at one lightness and the gate rejected all of them (0 clean); with a pool of distinct designs the gate is the term that separates the winner (*khaki printed top + brown eco-leather skirt*, ΔL ≈ 17) from the flat pairs — 12/20 clean, and ablating the rule changes the winner in the cool-dark evening run.

> **K-COL-02. Chroma budget.** ≤1–2 highly saturated elements per outfit — **counting hair** (dyed unnatural colours are a permanent near-face accent) and **counting eyewear frames**. Everything else neutral or muted.
> **FORCE:** `strong`. **Not `hard`, and this is the strength invariant biting.** The *mechanism* — chroma conflict rather than colour count drives "busy" — is sound and would justify a hard gate. The *threshold of 1–2* is a `[folkloric constant]`, and a gate can be no stronger than the number it tests. It was `hard` in the corpus; that was a violation. It returns to `hard` only after calibration on the feed.

> **K-COL-03. Schemes in descending reliability.**
> 1. Neutral base + accent — the reliable default **and the primary generator of blandness**, therefore subject to the interest floor.
> 2. Tonal/monochrome — one hue, 2–3 value steps, **texture variation obligatory**.
> 3. Analogous.
> 4. Muted complementary (burgundy + pine, camel + navy, teal + copper).
> 5. Triad — advanced.
> **FORCE:** `default`. **BREAKS:** classical colour-harmony schemes are near-chance predictors of real garment judgement (see theme 2/3 findings). This ordering is practitioner reliability, **not** a claim that the schemes predict perception.

> **K-COL-05. The echo rule.** See K-COMP-05.

> **K-COL-06. Neutrals have families.** Cool family (black, white, greys, navy) and warm (camel, beige, brown, cream, olive, khaki). Cross-combinations need a clear value step. The temperature of white (optic vs cream) follows the outfit's temperature and the person's undertone.
> **FORCE:** `default` — **lowered from `strong`, verification run 2, 2026-09-05.** The warm/cool split of neutrals descends from seasonal colour analysis (the Color Me Beautiful line); under the genealogy rule of theme 6 that is **one voice, not a consensus**. An independent named practitioner (Anuschka Rees) does not divide neutrals by temperature at all. `[convention]`.
> **BREAKS:** practitioners do not divide neutrals the same way; for a person with a measured neutral b\* the split makes no difference. Do not use family as a filter — only as a prior in the explanation.
> **Note.** The mechanism *cross-family combination needs a clear value step* is unaffected: it rests on K-COL-01 (T2, Munsell value step), not on the families.

> **K-COL-07. Area split ≈ 60-30-10** (dominant / secondary / accent).
> **FORCE:** `hint`. `[folkloric constant]` — borrowed from interior design. **No primary source was located in this pass.** It is a default proportion, never a threshold.

> **K-COL-08. Placement is attention control.** Light / bright / shiny / warm advances and enlarges; dark / muted / matte / cool recedes. Put advancing properties where the focus should be.
> **Mechanism split in two, verification run 2 (2026-09-05), because the halves carry different evidential weight:**
> (a) **advancing / receding in depth** (warm forward, cool back) = chromatic stereopsis. The effect is real but strongly individual and conditional on a dark surround and bright light — **`hint`**, not the load-bearing part of the rule.
> (b) **dark / matte reduces perceived size** = irradiation (Helmholtz), measured (Koutsoumpis, Economou & van der Burg, *Perception* 2021) — **T1**, and this is the load-bearing part.
> **Consequence for wording:** "enlarges" is correctly attributed to **value**, not to warmth.
> **FORCE:** `strong` for part (b); `hint` for part (a). **CHANGES:** this is how the focus is *placed* rather than merely counted — it connects K-CRA-02 to actual colour assignment per slot.

> **K-COL-10. Print mixing.** A shared colour thread + different scales + one print dominant. Without a shared colour the mix falls apart. Classic pairs: stripe + floral, dot + check.
> **FORCE:** `strong`. `[convention]`.

**Pattern scale matters and is distance-dependent.** A small print merges into a solid tone at distance; large blocks stay in contrast. Judge by how it reads at conversational distance, not by the colours in the swatch. **CHANGES:** print scale must be extracted as a feature, not just print presence.

---

# PART VII — Material, texture and the fabric↔silhouette contract

## VII.1 The contract, and how to measure it

> **K-MAT-02. Fabric–silhouette contract.** Structured fabrics hold a shape (A, V, sharp X); fluid fabrics fall (column, soft X, bias). Do not ask a fabric to do another fabric's job.
> **FORCE:** split. `hard` where the assignment is **physically impossible** (a fluid jersey cannot hold a structured A-line; a stiff taffeta cannot fall as a bias column) — that is mechanics, not taste. `strong` for the aesthetic cases in between, which are `[convention]`.
> **CHANGES:** rejects a structured A-line intent assigned to a fluid jersey, and vice versa — before any colour scoring runs.

This was `[convention]` in the corpus. It has a measurement standard.

**Cusick GE (1965), *The dependence of fabric drape on bending and shear stiffness*, Journal of the Textile Institute 56: T596–T606. Cusick GE (1968), *The measurement of fabric drape*, J. Text. Inst. 59: 253–260.** Standardised as **BS 5058** (1973) and **ISO 9073-9:2008**.

**Method.** A circular specimen of about 0.30 m diameter rests on a supporting disk of 0.18 m. The overhang folds under its own weight. A light source casts a shadow whose area is measured.

> Drape coefficient = (shadow area − disk area) / (specimen area − disk area)

**Direction, which the corpus never stated: DC runs 0 to 1 (or 0–100%). High DC = stiff. Low DC = limp.** Getting this backwards inverts the entire contract.

**The second descriptor the corpus dropped entirely: node count.** BS 5058 also uses the **number of folds (nodes)** in the draped specimen as a direct measure of drapability — **more nodes = softer fabric**. This is the more useful of the two for us, because node count is readable by a VLM from a try-on render or a product photograph, whereas DC requires a drapemeter.

**Cusick's 1965 finding:** bending and shear stiffness correlate most strongly with drape ratio. These are the same quantities used to parameterise fabrics in 3D garment simulation — the virtual-clothing industry already stands on them.

**BREAKS:** the textile literature is explicit that **drape ratio alone is inadequate to explain drape shape**. A single scalar does not capture how a fabric falls; two fabrics with equal DC can fold differently. Node count is the cheap second axis.

**CHANGES:** "structured vs fluid" stops being a hand-assigned vocabulary label and becomes a two-number axis with a published protocol. The try-on self-check gets a falsifiable claim: *if the rendered garment shows a node count inconsistent with its fabric class, the render is wrong.*

## VII.2 The rest of the material layer

> **K-MAT-01. Fabric formality must match cut formality.** Smooth-matte-fine reads formal; textured-coarse-heavy reads casual. **FORCE:** `strong`.
> **Source (run 2, 2026-09-05).** Flusser, *Dressing the Man* `[⚠]` (relayed, not read in the original): smoother and glossier materials read dressier; the proportion of white in the ground of a cloth adds formality. **Re-tier: T4 → T3**, provenance `[⚠]`. Force unchanged.

> **K-MAT-03. Seasonal fabric semantics.** Linen and seersucker read summer; flannel, tweed, velvet and chunky knit read cold. A violation reads as an error **even at thermal comfort**. **FORCE:** `strong`. `[convention]`. **BREAKS:** climate-controlled interiors and cross-hemisphere contexts.

> **K-MAT-04. Texture mix is the engine of monochrome.** Contrast along the smooth↔textured axis. **Shine budget ≤1–2 surfaces.** Counted as shine: metal, sequins, patent, satin, lurex. Soft lustre (silk crepe, washed sateen) is a background property — it does not spend the budget, but there should be only one such background.
> **FORCE:** `strong`. Threshold `[folkloric constant]`.

> **K-MAT-05. Quality and condition signals.** Cloth density, pattern match at seams, behaviour in movement, hardware weight. Pilling, stretching, worn-down heels fail the craft level regardless of composition. **FORCE:** `strong`.
> **Source (run 2, 2026-09-05).** Anuschka Rees `[✓]` on judging garment quality (cloth density, pattern match at seams, behaviour in movement, hardware weight); Flusser `[⚠]` (material / workmanship / fit as three axes). **Re-tier: T3.** Force unchanged.

> **K-MAT-06. Body interaction: cling / skim / stand-away.**
> - **Cling** (thin jersey, slinky knit): shows relief and underwear → only deliberately, with the right foundation.
> - **Skim** (crepe, ponte, dense drapey weaves): follows without adhering — **the default flattering behaviour**.
> - **Stand-away** (structured cotton, taffeta, dense twill): holds its own shape — conceals or builds.
> Map: to de-emphasise a zone → skim or stand-away, never cling. To show → cling deliberately.
> **FORCE:** `strong`. **CHANGES:** this is the largest quiet lever behind "the same garment sits differently," and it interacts hard with coverage vetoes — cling on a zone the person conceals is an automatic reject.

## VII.3 Tone versus pattern — the best-evidenced result in this theme

This is composer instruction #7 ("tone does more than pattern"), one of the six lines identified as actually changing LLM default behaviour. It has real sources, real effect sizes, and a documented sign reversal.

**Source A. Thompson P & Mikellidou K (2011), *Applying the Helmholtz illusion to fashion: horizontal stripes won't make you look fatter*, i-Perception 2: 69–76.**

| Stimulus | Magnitude |
|---|---|
| Abstract squares, height | vertical-striped must be **7.1%** taller to match horizontal-striped |
| Abstract squares, width | horizontal-striped must be **4.5%** wider to match vertical-striped |
| 2D female figure | horizontal-striped had to be **5.8%** broader to match |
| 3D mannequin photographs (stereoscopic) | horizontal-striped had to be **10.7%** wider to match |

**This corrects the restored R-HELM-02 block**, which asserted the effect is "of order ~4–7%" and rated T1 for abstract figures with T2 for transfer to real bodies. The paper itself carried the effect onto 2D figures and 3D mannequins, and the magnitude **grew** on 3D bodies (10.7%) — it did not shrink. Experiment 1 ran on six observers.

**Source B. Koutsoumpis A, Economou E & van der Burg E (2021), *Helmholtz Versus Haute Couture: How Horizontal Stripes and Dark Clothes Make You Look Thinner*, Perception 50(9): 741–756.**

The methodologically cleanest test: horizontal stripes against **no stripes** (rather than against vertical, which confounds which orientation causes the effect), on photographs of a real female model, with average stripe luminance controlled.

| Comparison | PSE | t | p | d |
|---|---|---|---|---|
| Striped vs light-green dress | 0.09° | t(42) = 3.98 | < .001 | **0.61** |
| Striped vs **black** dress | 0.03° | t(42) = 1.13 | **.26** | — |

Orientation and luminance each produce a small-to-moderate thinning effect independently; combined, the effect is larger. **But against a black garment, stripes added nothing detectable.** Experiment 3: the thinning effect of garment luminance **grows as the background darkens**.

**Source C — the sign flip.** Ashida et al. (2013): for **larger body sizes** horizontal stripes have a **widening** effect, the opposite of Helmholtz. Thompson & Mikellidou's own Experiment 3 found the effect fading on cylinders as they became fatter. Imai (1982), on figures of heavy men, found the vertically striped figure judged thinner by 15.37% (137 participants, SD 9.24%) — supporting the folk belief in that regime.

> **K-PRN-01. Value is the proportion lever; stripe orientation is a weak conditional modifier.**
> **WHEN:** always for value; for stripes only on mid-range bodies against a non-dark garment.
> **FORCE:** value `strong`; stripe orientation `hint`.
> **BREAKS:**
> - Against a dark garment, orientation contributes nothing measurable (p = .26). The two levers are **substitutes at the dark end**, not additive.
> - The effect **weakens** as body size increases, **with possible reversal** at larger sizes — Ashida, Kuraguchi & Miyoshi (2013), i-Perception 4(5):347–351. Their word is *possible*; the reversal is not established. The 15.37% reversal figure circulating in this literature comes from **Imai (1982), a Japanese-language popular psychology piece** (*Tateshima yokoshima no miekata no nazo*, Psychology 29:12, Tokyo: Saiensusya), reported second-hand through Ashida and never seen by us. **The crossover point is unknown and must not be invented.**
> - **Large variability across observers** (Ashida 2013), attributed to which features an observer attends to. The effect is unreliable at the individual level — the strongest independent reason to cap it at `hint`.
> - **Hysteresis by recent exposure** (Ashida 2013): judgements shifted with the order in which fat and thin figures were tested, which the authors read as an effect of the bodies one has been surrounded by. The same outfit reads differently depending on what the observer just looked at. We model nothing like this.
> - **The literature conflicts — and the conflict has a condition (read 2026-08-24: publisher abstract; the d values via Koutsoumpis et al. 2021, who re-report them; full text paywalled).** Swami V & Harris AS (2012), *The effects of striped clothing on perceptions of body size*, Social Behavior and Personality 40(8): 1239–1244. 120 naive participants had a brief **live interaction** with a female confederate wearing a dress with vertical stripes, horizontal stripes or no stripes, and **afterwards rated her body size from memory** on the Photographic Figure Rating Scale. Horizontal stripes → significantly larger body size than vertical (Cohen's d = 0.63) and than no stripes (d = 0.61); vertical = no stripes. Swami & Harris's own argument against Thompson: in the Helmholtz studies vertical and horizontal stimuli were shown **concurrently**, a perceptual anchor that does not exist when one person is seen alone. Koutsoumpis et al.'s argument back: the judgement was made from memory, participants were never told to attend to the dress, and the paradigm mixes perception with impression. **Reading both together, the sign is not a contradiction but a condition: side-by-side perceptual comparison → horizontal stripes read thinner; a single person seen once in life and judged afterwards → horizontal stripes read wider.** The second regime is how outfits are actually seen. Two consequences for this system: (a) K-PRN-01 stays `hint`, and its direction must be stated **per regime**, never as one sign; (b) **the A/B/C stand compares looks side by side — the comparative regime — so whatever it measures about stripes is not what an observer on the street sees; the stand cannot settle the sign.** The belief the person holds (K-LNG-04) matches the memory regime, which is one more reason not to argue with it.
> - Background luminance moderates the effect, and we model no background. In a try-on render, the background we choose changes the perceived slimming. **This is an uncontrolled variable inside our own pipeline.**
> - Thompson & Mikellidou report dependence on duty cycle (stripe width to spacing ratio). This is **in tension** with the theme-2/3 finding that absolute stripe period in centimetres governs perception. **Unresolved — encode neither as settled.**
> **CHANGES:** without it the composer treats stripes as a proportion tool and value as a colour choice; with it, value structure *is* the proportion tool, stripes are a weak modifier switched off for dark garments and flagged sign-uncertain above an unset body-size threshold.

## VII.4 Belief moderates perception — a gate on the explanation layer

**Koutsoumpis A, Economou E, Yao Z-F & Van der Burg E (2026), *When stripes in clothes deceive: Cross-cultural examination of perceptual and belief discrepancies about horizontal stripes in clothes*, PLoS ONE 21(4): e0347495.** Published 30 April 2026 — after the corpus was assembled; absent from it entirely.

Experiment 1 (n = 316; Greece, Netherlands) confirmed the folk belief that horizontal stripes widen is widespread in every country tested. Experiment 2 (n = 419; Greece, Netherlands, Taiwan) added a behavioural width-comparison task. The striped dress was again perceived as thinner. The belief–perception link was **asymmetric**: participants who believed stripes are slimming perceived the striped dress as correspondingly thinner, but for those who believed stripes widen, the belief–perception relation was **not significant**. No cross-cultural difference in this asymmetry.

> **K-LNG-04. Do not argue with the person's pattern beliefs.**
> **WHEN:** the person states a belief about stripes (or, provisionally, any folk shape rule).
> **FORCE:** `default`, language layer.
> **Additional support:** Miyazaki & Ishibashi (2022), i-Perception, document the same belief about striped clothing and body shape in an **1813 Japanese beauty handbook**. The belief is at least two centuries old and predates Western fashion advice entirely — it is not a misconception an app corrects in one sentence.
> **BREAKS:** tested on stripes only; generalisation to other folk rules is untested.
> **Executable form (code, 2026-08-24):** `profile.переконання_принт` routes a stated belief (stripes, checks) into the veto channel — on `ager_brief.xml` the 4 striped items leave the pool, the 58 printed ones stay; an attribute the feed cannot read ("large print") becomes a *preference* for the brief, not a filter, so the system does not widen the person's own limit. `language_gate` bans the correcting sentence itself («насправді … не повнить»).
> **CHANGES:** the natural move is to correct — *"actually, horizontal stripes don't widen."* The evidence says a stripe-sceptic's belief was never tracking their perception, so correcting them changes nothing they see and costs trust. Route the belief into the **preference/veto channel** instead. This is a concrete edit to explanation templates and to how the brief records pattern preferences.

---

# PART VIII — Shoes and the lower boundary

Shoes are resolved **together with hem length**, not last. Lower-body proportion cannot be solved without them.

> **K-SHO-01. Shoes and hem are one decision.**
> **FORCE:** `hard` (procedural). **CHANGES:** assembly order. A midi skirt scored without its shoe has no determinate proportion — the same skirt reads long-and-heavy with a flat and balanced with a heel. Scoring them separately produces incoherent output.

> **K-SHO-02. Shoe mass scales with bottom volume, and the ankle gap is controlled.**
> Heavy bottoms need shoes with visual mass; delicate bottoms need delicate shoes. The gap between hem and shoe at the ankle/calf is a proportion decision, not a residue.
> **FORCE:** `strong`. `[convention]`.

> **K-SHO-03. Shoes carry a formality level of their own.** A shoe can lift or sink an outfit by a full step. The most common single-item coherence failure is a shoe one register below everything else — which is also, deliberately deployed, the "wrong shoe" move (Part X).
> **Source (run 2, 2026-09-05).** Allison Bornstein, "Wrong Shoe Theory" `[✓]`: against something sweet, go a little tougher, edgier or sportier. A named practitioner with a stated mechanism (register contrast as a source of interest) and a worked decision (Р-14). **Re-tier: T3 `[sourced]`.** Force unchanged.
> **BREAKS (added run 2).** Bornstein states the rule *in the opposite direction* — not "the shoe must not fall a step below" but "the shoe is deliberately taken from another register". Both halves are compatible: the failure is an **unintended** drop, the move is a **deliberate** one. Only the unintended case is a finding.
> **FORCE:** `strong`.
> **Executable form (code, 2026-08-24):** when the formality outlier of the outfit is the shoe, a finding of its own (*shoe one register below/above the rest*) is issued beside K-KOH-02, force `soft` (T3 convention caps it); the ID was previously only quoted inside K-KOH-02's text as `K-SHO-06`, which no theme defines. **Input:** a shoe slot — absent from both real feeds; fires on the stub-shoe run of `measure_theme4.py --взуття-заглушка`.

> **K-SHO-04. Leg-line continuity.** A shoe toned to the leg or to the bottom continues the line; a contrasting shoe cuts it. Toe shape matters: a pointed toe extends the line, a rounded toe truncates it, an ankle strap cuts it at the narrowest point and shortens the leg.
> **FORCE:** `default`. `[convention]`. **BREAKS:** the measured magnitude of these effects is small (see K-SIL-07) — below our capture resolution. Use as ordering preference, never as a numeric claim to the user.

> **K-SHO-05. Boot shaft is a termination point.** A shaft ending at the widest part of the calf is the classic failure. Over-the-knee and ankle boots interact differently with every hem length.
> **FORCE:** `strong`. Machine-checkable against the zone map.

**Hosiery.** Sheer nude continues the leg; opaque black creates a column with a dark shoe and a hard break with a light one; textured tights are an interest source and spend from the pattern budget.

---

# PART IX — Coherence: context, formality, occasion

Level 3. This is the layer where an internally perfect outfit still fails.

## IX.1 The formality scale

> **K-KOH-01. Formality is a property of garments, not of events.** Every garment type carries an interval on the scale below (`outfit.ФОРМАЛЬНІСТЬ_ЯКОРІ`, `інтервал_формальності`); an event is derived into a *range* on the same scale by K-KOH-09. **FORCE:** `default` (architectural). The code has cited this ID since the first formality layer; the theme carried the table without the ID until 2026-08-24.

A 1–10 working scale. **`[folkloric constant]` — the granularity is ours; no source defines ten levels.** It is useful because it makes "one step" a computable quantity, not because it is true.

| Level | Register |
|---|---|
| 1–2 | Athletic, loungewear, beach |
| 3–4 | Casual (denim, tee, sneakers) |
| 5–6 | Smart casual (structured knit, tailored bottom, refined shoe) |
| 7 | Business casual |
| 8 | Business formal / cocktail |
| 9 | Black tie |
| 10 | White tie |

> **K-KOH-02. Formality spread ≤2 steps** across the assembled outfit, unless a high-low move is declared and anchored.
> **FORCE:** `strong`. `[folkloric constant]` — the number 2 is uncalibrated.
> **CHANGES:** this is the single most productive coherence filter in practice. It rejects the most common real failure: a good top, a good bottom, and shoes from another life.

## IX.2 Dress codes → concrete

> **K-KOH-05.**
> - **White tie** — floor-length gown.
> - **Black tie** — evening dress, floor-length or an impeccable midi.
> - **Cocktail** — knee-to-midi dress, heels or elegant footwear.
> - **Business formal** — suit, restrained colours, closed shoes.
> - **Business casual** — blazer or structured knit + trousers or skirt; no denim in conservative environments.
> - **Smart casual** (the most ambiguous) — formula: *tailored bottom OR structured top* + footwear at level 5–6; no athletic items.
> - **Casual** — anything except levels 1–2 in public contexts.
> **FORCE:** `hard` where a code is stated. `[convention]`.

> **K-KOH-06. Modifiers.** Evening +1 · summer/daytime −1 · region and venue shift the base range. Ukrainian market: the baseline sits **higher** than Western sources assume — defined waist and "dressed-up" quality are valued more, casual/oversize less.
> **FORCE:** `default`. `[convention]`, and a priority item for local calibration.

> **K-KOH-07. Risk asymmetry.** With a host or at stakes, err **slightly overdressed**. In creative environments, half a step **under** with one piece of visible quality. Never more than one step off in the direction that reads as disrespect.
> **Second voice (run 2, 2026-09-05).** To Debrett's (run 1, `[✓]`) is added Flusser `[⚠]`: when the formality of an event is unknown, it is safer to overshoot than to undershoot. Two independent voices (an etiquette authority and a tailoring author) — **T3 `[sourced]`**.
> **FORCE:** `strong`. `[sourced]`.

> **K-KOH-08. Guest taboos.** White at a wedding (unless the couple asked); black at a celebration in cultures that read it as mourning; outshining the host. These are hard vetoes, not preferences.
> **Source (run 2, 2026-09-05).** Emily Post Institute `[⚠ relayed]` — white at a wedding as one of the coarsest guest errors; the history of black mourning in the Western tradition (a mass norm from 1861) explains the *mechanism* of the second taboo. Provenance is stated honestly: the wording reached us through wedding material, not from emilypost.com directly.
> **FORCE:** `hard` — unchanged; this is a veto, not an assessment.

> **K-OCC-01. Mourning is a state with a duration, not a date.** Dark and quiet: no bright or light large surfaces, no shine near the face. Black is traditional; other dark shades are accepted. Head covering and the black kerchief are a separate norm of respect, not palette.
> **WHEN:** the person declares mourning (occasion `траур`, with closeness and months elapsed as inputs). **FORCE:** `hard` on the person's declaration, **decaying with time** — a year for parents, spouse, children; half a year for grandparents; three months for distant kin; again on the anniversary. The decay is the rule, not a switch. **Tier:** T4 — cultural convention; six independent Ukrainian sources agree on direction and on the durations (clergy stress it is a norm of respect, not dogma). **BREAKS:** durations are customary, vary by family and region, and are never a number to argue with the person; the rule takes the person's own timing. **CHANGES:** at `нагода="траур"` bright and light large surfaces are vetoed (`outfit.нагода_палітра`), and the veto weakens as months pass instead of vanishing. Born in code (2026), added here because the gate battery showed it changes the candidate set on the mourning scenario; it was cited as a corpus rule while absent from every theme.

> **K-KOH-09. Scenario → parameters before anything else.** Occasion, venue, role (guest / host / speaker), weather, walking distance, transport, duration, children in arms. These produce `formality_range`, `vetoes`, `weather_layer`, `risk_posture` — and they run **first**, before silhouette or colour.
> **FORCE:** `hard` (procedural). **CHANGES:** an outfit assembled before the scenario is read is not a candidate; it is a guess.

> **K-KOH-10. One exposed zone.** In daytime and business contexts at most one body zone is exposed — legs *or* décolleté *or* shoulders/back; evening contexts admit two. The unit is the **zone**, not the garment: a mini and a deep neckline are two zones even on one dress.
> **FORCE:** `strong` as stated by practitioners, issued as `soft` — the 1/2 limit is `[convention]`, T3, uncalibrated. **BREAKS:** beach, sport, stated dress codes that expose more by design; cultural settings that allow none. **CHANGES:** a mini skirt with an open-shoulder top is demoted in an office scenario and passes at an evening one; the repair names which zone to close. Input: `відкрита_зона` per garment — readable from names only for a few words («міні», «декольте»); absent from both real feeds. Code has emitted this ID since the first formality layer (`outfit.формальність_образу`); the theme lacked the block until 2026-08-24.

## IX.3 High-low as a controlled exception

> **K-KOH-03.** One deliberate break of register works under three conditions: **the break is single**; **it is anchored** (repeated, or supported by the focus); **everything fits impeccably**. Two or more accidental breaks are chaos. High-low is a *technique* that requires the rest of the outfit to be disciplined.
> **FORCE:** `strong`.
> **BREAKS — checked against the source, and our earlier count was wrong.** Bellezza, Gino & Keinan (2014), *The Red Sneakers Effect*, Journal of Consumer Research 41(1):35–54, report **three** boundary conditions under which the positive status inference **disappears**: (1) the observer is unfamiliar with the environment; (2) the nonconformity is depicted as **unintentional**; (3) there are no expected norms or shared standards of formal conduct in the setting. We previously claimed four.
> **Mediator we did not have:** the effect runs through **perceived autonomy** — the observer infers the person could have conformed and chose not to. This tells us *how* to execute the move, not only when: it must read as chosen. **That is the same mechanism as K-CRA-03 (sprezzatura)** — the two rules are one mechanism stated twice, and the deliberateness gesture is what satisfies boundary condition 2.
> **Moderator we cannot fill:** the effect is moderated by the **observer's individual need for uniqueness** — a per-person audience trait we cannot know, ask for, or infer from a scenario. Even with all three boundary conditions met, the move carries irreducible per-observer variance. **A term in this rule's equation is structurally unavailable to the system.**
> **CHANGES:** high-low is not offered by default. It is offered only when the scenario carries a legible prestige/creative marker, and it is never offered to a person whose stated goal is "look appropriate."

## IX.4 Weather and genre

> **K-WEA-01.** The weather layer is a **hard** input, not a garnish. Outerwear is part of the outfit and is scored as a slot. Rain and wind constrain fabric, hem and footwear absolutely. Above ~26 °C the third piece migrates to accessories or, per Part X, to an in-garment attribute.
> **FORCE:** `hard`.
> **Layer count = torso layers.** The bottom is worn always and is not a layer. Found 2026-08-24 on `ager_brief.xml`: the code counted the bottom, so *tee + trousers at +18 °C* produced *too many layers* (0.5) in every one of 50 combinations across both profiles — a false sentence in every output and zero difference between candidates; and at +12 °C a tee without a jacket passed silently. **CHANGES:** at 18–26 °C top + bottom is silent; at 10–18 °C a top without an outer layer gets *too few layers*. The 1/2/2.5/3.5/4 map itself is `[convention]`, uncalibrated.
> **The map, so it exists somewhere other than code** (torso layers per temperature band; the numbers are `[convention]`, inherited from an earlier corpus version and never calibrated): ≥26 °C → 1 (third piece = accessory, not a layer) · 18–26 → 1 · 10–18 → 2 · 2–10 → 2.5 · −8–2 → 3.5 (K-WEA-02: the coat is the outfit) · <−8 → 4 (hat-scarf-gloves carry the colour).

> **K-WEA-03. Dark + direct sun + cling.** A dark close-fitting garment in direct sun heats the skin; the same colour with an air gap does not.
> **WHEN:** scenario flags direct sun, outdoors; garment L* below ~55 **and** fit class `cling`. **FORCE:** `hint`, rising to `soft` with darkness × area; never a gate. **Source:** Shkolnik, Taylor, Finch & Borut (1980), *Why do Bedouins wear black robes in hot deserts?*, Nature 283: 373–375 — black absorbs about 2.5× the solar radiation of white, but with a loose robe the extra heat is lost by convection before it reaches the skin; the effect on the wearer appears only when the gap is gone. T1 for the mechanism, **T4 for every number in the rule** (the L* 55 threshold and the 10–28 mm gap are ours). **BREAKS:** shade, indoors, wind — the difference disappears; we have no measurement of garment surface temperature on a body, so the force is capped at `soft`. **CHANGES:** on a sunny outdoor scenario a black clinging top is demoted below the same top in a loose cut, with the repair *same colour, looser cut* offered first and *lighter colour, same cut* second. Born in code; added here because it was cited as a corpus rule while absent from every theme.

> **K-KOH-04. Genre grammar.** Minimal · classic · romantic · sporty · dramatic · bohemian. Mixing genres is allowed; mixing them **without dominance** is not. One genre leads; a second appears as citation.
> **FORCE:** `default`. `[convention]` — genre taxonomies are unstable between schools.

---

# PART X — Craft: from dressed to styled

The hardest layer for people and for models alike: the difference between correct and alive.

## X.1 The third piece

> **K-CRA-01. Third piece.** Top + bottom + a third element is the minimum unit of "put together."
> **Run 3 (2026-09-06) — closed for research.** Three passes found no named author either for the third piece or for the elimination doctrine ("take one thing off"); the candidates (Kelly & London 2005, Gunn 2007/2012, Garcia 2007/2008, Farr 2004, Mizrahi 2008, Zoe 2007) were not confirmed as the origin of the formulation. Both remain `[convention]` without an author. Force `strong` stays as a P-class convention, but the rule is marked closed: it can be raised only by two independent practitioner decisions over real garments (the decision register) or by a measurement on the stand.

**Provenance, corrected.** The corpus attributes this to a "retail canon (Nordstrom/J.Crew)." A provenance search returns **no originating retailer, no originating author, and no study**. It is convergent practitioner convention, widely stated, nowhere sourced. Re-tagged `[convention]`.

**Two operational criteria the corpus lost, recovered from the practitioner layer:**

1. **Visibility, not count.** The rule requires that an element of **all three** garments remain visible in the assembled look. A blazer worn fully closed over a top that then cannot be seen satisfies a count-based check and fails the rule.
2. **In-garment detail substitutes for a layer.** An unusual construction element (cutout, ruffle, sleeve treatment) or embellishment (beading, lace, embroidery) built into a two-piece outfit satisfies the rule without adding a layer — which is what makes it survivable in heat.

**Live disagreement, not a resolved hierarchy.** The third-piece rule and the elimination doctrine ("remove one thing before leaving") are stated by practitioners as **opposed positions**, not as a rule plus its guard. Our resolution (K-CRA-04 below: substitute a quieter interest source rather than delete) is ours, and it is untested.

> **FORCE:** `strong`. **BREAKS:** heat; strict uniform codes; deliberate minimalism where the garment itself carries the interest.
> **CHANGES:** `third_piece_present` changes from `count(garments) ≥ 3` to a two-branch predicate — *(three garments, all three visible in the assembled look)* **or** *(two garments where one carries a codable interest attribute)*. Direct edit to `outfit.py`; it changes which real catalogue items pass.

## X.2 Focus, layering, editing

> **K-CRA-02. Exactly one focus.** Zero focus → bland. Two or more → busy. The focus is chosen deliberately and placed where the eye should go on **this** body.
> **Run 2 (2026-09-05).** The mechanism is Gestalt (figure–ground after Rubin) and is academically real; *exactly one focus* is an aesthetic convention, not a consequence of it. Force `strong` stays (P-class convention), the label is sharpened to `[convention]` with the mechanism named. The DeLong frame reference moved here from K-SIL-05 belongs to the "whole" claim, provenance `[—]`.

> **K-CRA-06. Layering has depth rules.** Length gradation (a visible step between layers), thickness gradation (thin under thick), and a functional relationship between layers. Three visible layers is a practical ceiling — `[folkloric constant]`.

> **K-CRA-04. The editing step.** After assembly, remove any element whose removal does not reduce any metric.
> **FORCE:** `strong`. **Floored:** the edit may not cut below the interest floor. When editing and floor conflict, the resolution is **replacing a loud interest source with a quieter one**, not deletion.
> **CHANGES:** this is the anti-clutter pass, and the floor is what stops it from converging on the generic-safe uniform.

> **K-CRA-03. Sprezzatura — at most one.** Studied carelessness: a rolled cuff, a half-tuck, an undone button, pushed sleeves. Source: Castiglione, *Il Libro del Cortegiano* (1528) — mastery that conceals effort. **One gesture per outfit.** Two read as sloppiness.
> **Source discipline:** Castiglione supports the *concept* and nothing else — he says nothing about garments, rolled cuffs, or a ceiling of one. **The one-gesture limit is ours** and belongs in the invented-number list, not attached to a 1528 citation.
> **Mechanism link:** same mechanism as K-KOH-03's deliberateness condition. Sprezzatura is how a register break is made to read as chosen rather than accidental, which is what Bellezza's perceived-autonomy mediator requires.
> **FORCE:** `strong` for the concept, `hint` for the ceiling. `[convention]`, oldest working rule in the corpus.

> **K-CRA-05. Layout commands shift formality ~0.5 step.** Tucks, half-tucks, French tuck, rolls, cuffs, buttoning state, collar over lapel. These are **first-class citizens of the schema** — most craft moves are layout commands — and they interact directly with the try-on rendering contour.
> **FORCE:** `default`. `[folkloric constant]` (the 0.5 figure).

## X.3 Accessories, trend, authenticity

> **K-ACC-01. Accessories are structure, not decoration.** A belt makes an X. A bag's mass balances the lower body. Earrings are near-face colour and spend from the chroma budget. Frames are permanent near-face colour.
> **FORCE:** `strong`.

> **K-CRA-07. Metal consistency** is the default; deliberate mixing is a declared move requiring repetition.
> **FORCE:** `default`.
> **Executable form (code, 2026-08-24):** *mix without repetition* — a second metal tone that appears once is the orphan (`outfit`, formerly `K-COL-04-M`); a count of distinct metal tones is a separate `hint` (`K-CRA-07-N`, formerly `K-COL-04-M2`). Both were cited under an ID no theme defines and are now traced to this rule. Input: the `метал` field, absent from every feed — the rule has input only on the synthetic battery.

> **K-CRA-08. Trend dosing.** One current element in a durable base. The whole outfit in this season's silhouette dates instantly and reads as costume.
> **FORCE:** `default`. `[convention]`. Explicitly volatile — see K-SYS-07.

> **K-CRA-09. Anti-costume.** The failure mode where every element declares the same reference (all-Western, all-nautical, all-Parisian) — technically correct and *not her*. Genre citation, not genre uniform.
> **FORCE:** `strong`.

> **K-CRA-10. Camera ≠ life.** Photographs need more contrast, more structure and a sharper silhouette; in person, subtler works. Texture contrast in particular largely disappears in a photograph.
> **FORCE:** `hint`. **CHANGES:** if the system generates looks for content rather than for wearing, it needs a separate scoring mode — and our own try-on render **is** a photograph, so what the person sees in the render systematically understates texture-based interest. This is a known bias in our own output channel.

---

# PART XI — The signal layer: what the outfit says

Level 4. Three real studies, all narrower than the corpus implied.

## XI.1 The published structure

**Hester N & Hehman E (2023), *Dress is a Fundamental Component of Person Perception*, Personality and Social Psychology Review 27(4): 414–433.**

Impressions form from target face/body + target **dress** + context, filtered through **perceiver** beliefs, stereotypes and cultural knowledge. Four inference channels run off dress: **social categories, cognitive states, status, and aesthetics.**

Two things this gives us that the corpus's Level 4 lacked:

1. **The perceiver is a term in the model, not noise.** The `scenario` input should carry an audience descriptor, and currently does not. Concrete gap in the profile/scenario derivation.
2. **Aesthetics is a channel separate from status.** Our composer conflates them — "reads expensive" and "reads well put together" are treated as one axis. The review separates them, which supports keeping the goals explicit and non-blended: *expensive*, *on-trend* and *timeless* are different, conflicting targets.

The authors also note that because people choose their dress more than their face or body, dress-based inferences are plausibly **more accurate** than face-based ones.

**FORCE:** `default`, architectural. It is a review, not a measurement.

## XI.2 Fit is read fast — and the effect is small

**Howlett N, Pine K, Orakçıoğlu I, Fletcher B (2013), *The influence of clothing on first impressions: Rapid and positive responses to minor changes in male attire*, Journal of Fashion Marketing and Management 17(1): 38–48.**

308 recruited, 274 analysed (240 women, 68 men; mean age 29.42, SD 11.98). Repeated measures over four images — bespoke/off-the-peg × static/dynamic posture — in random order. Exposure capped at five seconds, floored at three. Suits matched on colour (dark blue) and cloth (herringbone); same shoes, tie and shirt; **face pixellated**; model white, tall, slim, BMI 21. The stated difference: cut and minor tailoring details. 7-point scales.

| Dimension | F | p | e² |
|---|---|---|---|
| Confidence | F(1,271) = 10.36 | < .01 | .04 |
| Salary | F(1,270) = 14.00 | < .01 | .05 |
| Composite | F(1,272) = 11.49 | < .01 | .04 |
| Success | F(1,270) = 3.49 | **.06** | .01 |
| Flexibility | F(1,271) = 3.00 | **.09** | .01 |
| Trustworthiness | F(1,270) = 0.21 | **.65** | .00 |

**Corrections to the corpus.** The corpus reports that fit improved confidence, **success** and salary. Success did not reach significance (p = .06); neither did flexibility (p = .09). The corpus omits that **trustworthiness did not move at all**, and omits the effect sizes entirely: e² ≈ .04–.05 — four to five percent of rating variance.

**Perceiver moderation.** Respondent earnings had a main effect across most dimensions, and **higher earners rated both suits less favourably**. Who is looking changes the reading — the same point as Hester & Hehman.

> **K-P0-01. Fit is a gate, not a weighted criterion.**
> **WHEN:** always, before composition scoring.
> **FORCE:** `strong` on the architecture (fit is read in seconds, without a face, so it precedes everything). The *number* behind it is small.
> **BREAKS — posture factor retrieved 2026-08-24 (full text, University of Hertfordshire repository).** The four images were bespoke/off-the-peg × **static (standing, facing the camera) / dynamic (walking towards the camera)**. Result, verbatim in substance: *there were no differences in ratings between the static and dynamic images for each suit, so the two ratings were collapsed into one*. **The fit effect did not depend on static versus moving presentation. On this evidence a static try-on render does not misrepresent the fit signal.** What the 2013 study did *not* test is posture *strength*; the authors raise it as the open question — answered by the follow-up: **Gurney DJ, Howlett N, Pine KJ, Tracey M & Moggridge R (2017), *Dressing up posture: the interactive effects of posture and clothing on competency judgements*, British Journal of Psychology 108(2): 436–451** (manuscript read in full). 86 raters, 4 models (2 m, 2 f, aged 19–22), faces blurred, no time limit; postures strong / neutral / weak (Carney et al. 2010 poses) × casual / smart (women: trouser suit / skirt suit); measures confidence, professionalism, approachability, high salary. **Clothing outweighed posture**: men, suit vs casual η² = .84; posture η² = .42; interaction η² = .08. **The neutral, natural pose was rated highest**, not the expansive *power pose*; a strong pose helped only men in casual clothes; for women the neutral pose won in every clothing condition, most of all in the skirt suit (women in a trouser suit were rated *below* the men on confidence and salary; in a skirt suit *above* them on professionalism, approachability and salary). The authors' conclusion: high-power poses cannot offset casual clothes; dressing smartly is the more reliable lever. **CHANGES for this system:** (1) the try-on render must show a **neutral, natural standing pose** — an expansive pose adds nothing over smart clothes and lowers the reading of a woman in every condition; (2) the register of the clothing (smart vs casual, K-KOH-*) is a larger term than anything the pose contributes, which supports scenario/formality running before composition (K-KOH-09). **Limits:** four models only, all young; competency measures, not attractiveness or *put-together*; still no womenswear fit manipulation. Male formal tailoring only. Womenswear is untested here — the same authors' companion work on female attire concerns provocativeness and found *negative* perceptions for senior women; the direction does not transfer. The manipulation is bespoke vs off-the-peg — cut plus tailoring details, not ease in isolation. Trustworthiness is untouched.
> **CHANGES:** keeps fit's position at the top of the priority stack; removes our licence to tell the user that better fit transforms how they are seen. Honest phrasing: *reads quickly, without your face.*

## XI.3 Status register — coarse grain only

**Kraus MW & Mendes WB (2014), *Sartorial symbols of social class elicit class-consistent behavioral and physiological responses: A dyadic approach*, Journal of Experimental Psychology: General 143(6): 2330–2340.**

Male participants wore upper-class (business suit), lower-class (sweatpants) or neutral clothing before a modified negotiation with a partner blind to the manipulation. Upper-class clothing raised negotiation profits, lowered concessions, and raised testosterone in the wearer. In perceivers it produced increased vagal withdrawal, physiological contagion, and — counter-intuitively — **reduced perceptions of social power**.

**FORCE:** `hint`. **BREAKS:** male-only; suit vs sweatpants is roughly formality 8 vs 2 on our own scale — far coarser than any decision the composer makes. One perceiver effect runs opposite to the naive reading. **It cannot license a "look more capable" promise.**

## XI.4 Enclothed cognition — direction only

Chain: **Adam H & Galinsky AD (2012)**, *Enclothed cognition*, JESP 48: 918–925 (Exp. 1, N = 74) → **Burns et al. (2019)**, preregistered high-powered direct replication, **failed** → **Adam & Galinsky (2019)**, JESP 83: 157–159, conceding the replication was competently run → **Horton CB, Adam H & Galinsky AD (2025)**, *Evaluating the Evidence for Enclothed Cognition: Z-Curve and Meta-Analyses*, Personality and Social Psychology Bulletin 51(2): 203–221.

The meta-analysis covers 105 effects from 40 studies across 24 articles (N = 3,789). Conclusion: concerns about the replicability of pre-2015 studies; evidential value affirmed for effects published after 2015.

**A note the corpus does not make:** the meta-analysis is co-authored by two of the three parties to the original dispute. That does not invalidate it, but it caps the independent weight it can carry.

**FORCE:** `hint`, direction only. Magnitudes do not survive. **BREAKS:** it concerns the wearer's own cognition, not outfit quality or observer judgement. **It licenses no composition rule at all** — only the comfort veto and the wellbeing framing.

> **K-PER-05. Comfort veto.** Fabrics and silhouettes in which the person is physically or psychologically constrained fail the wearer level even with perfect composition. Constraint is visible from outside. Sensory constraints (will not wear wool against skin, will not wear heels) are **hard and permanent** in the profile.
> **FORCE:** `hard`, **on the person's authority alone.** The enclothed-cognition literature does not carry this rule and is not cited in support of it: it concerns the wearer's own cognition, not outfit quality or observer judgement, and its meta-analysis is co-authored by two parties to the original dispute. The rule would stand unchanged if that literature vanished.

---

# PART XII — The two-sided quality model

An outfit must pass **both** checklists, item by item, before it is issued. This is the operational form of Part I.3.

## XII.1 The excess ceiling (16 points) — **K-SYS-08**

Fires when the outfit is overloaded. Any failure is repaired **before** output; a failed item may not appear in a delivered answer.

1. Chroma budget respected (≤1–2 saturated elements, hair and frames counted).
2. Exactly one focus.
3. Value structure resolves to 2–3 steps, not chaos.
4. One readable silhouette letter.
5. Formality spread ≤2 steps, or a declared and anchored high-low.
6. Shine budget respected (≤1–2 surfaces).
7. Pattern budget respected; print mix has a shared colour thread and differing scales.
8. Visible layers ≤3.
9. Every accent is echoed at ≥2 points, or is the single focus.
10. At most one sprezzatura gesture.
11. No termination point on the widest point of a zone (under a flattering intent).
12. Metal consistency, or deliberate mixing with repetition.
13. Genre has a dominant; no leaderless mix.
14. One trend element, not a full seasonal uniform.
15. Fabric–silhouette contract holds in every slot.
16. Scale (print, accessory mass, texture coarseness) matches the person's scale.

**Status:** thresholds in items 1, 6, 7, 8, 10 are `[folkloric constant]`. The *structure* is sound; the numbers are conventions awaiting calibration.

## XII.2 The blandness floor (6 points) — **K-SYS-09**

The mirror checklist. Its existence is the system's main defence against convergence on the generic-safe uniform.

- **B1.** Interest sources counted ≥ the minimum for the declared intent.
- **B2.** At least one element is not the median choice for this scenario.
- **B3.** The outfit is distinguishable from the neutral-base-plus-one-accent default.
- **B4.** Texture or material carries something the colour does not.
- **B5.** The silhouette makes a decision (a letter is chosen, not defaulted).
- **B6.** The result is not the same answer this system would give any other person with this scenario.

## XII.3 Interest sources

The countable menu, `{i1…i7}`:

| | Source |
|---|---|
| i1 | Texture contrast |
| i2 | Silhouette decision (deliberate volume, unexpected proportion) |
| i3 | Colour (accent, unusual neutral pairing, tonal depth) |
| i4 | Craft detail (construction, hardware, finish) |
| i5 | Register move (high-low, wrong shoe, gender borrowing) |
| i6 | Accessory as structure |
| i7 | Layout gesture (tuck, roll, buttoning state) |

**Minimums by intent:** `comfort` / `conventional` / `context` ≥1; `fashion_forward` ≥2, of which at least one from {i2, i5}.
**Risk budgets:** `conventional` = 1 (mandatory) · `context` = 0–1 · `comfort` = 0–1 · `fashion_forward` = 2–3.

**Status:** the menu is a genuine taxonomy of levers. Every threshold is `[folkloric constant]`. **Nothing here has been measured.**

## XII.4 Intent is a parameter, not an assumption

> **K-PER-00. "Flattering" is a function of goal, not an absolute.**
> Minimum enum: `conventional-flattering` (approach conventional proportion — elongate, balance, define) · `fashion-forward` (silhouette expression outranks convention) · `comfort-first` (sensory and movement freedom as hard constraints) · `context-optimal` (maximise appropriateness/status in the environment).
> The same wardrobe yields different correct answers under different intents. Without this parameter the stylist — human or machine — imposes their own default.
> **FORCE:** `hard`, conceptual core. **CHANGES:** it is the switch that inverts Part V. Without it, every body map is a prescription; with it, they are options.

---

# PART XIII — Generative operators and anti-medianness

> **K-VAR-01. Offer 2–3 looks from different poles, not one safe median.**
> A single stereotype per request is a failure; the value is in the range.
> **FORCE:** `strong`. **CHANGES:** the portfolio, not the individual look — candidates must differ in silhouette letter or composition strategy, not be five variations of one answer.
> **Executable form (code, 2026-08-24, `composer._портфель`):** the composer returns a *portfolio* — O1 the ranking winner; O2 anchor-first (K-COMP-02: the most expressive garment absent from O1, best combination around it); O3 palette-first (the most colour-coherent clean combination — the tonal pole opposite to K-COMP-01's middle). A pole that does not differ from O1 in at least one slot is not issued. Measured on `ager_brief.xml`, warm-light: before — the three *alternatives* were the same printed tee with different trousers; after — O1 khaki print top + brown eco-leather skirt, O2 beige print tee + grey trousers, O3 a grey tonal column carrying its own K-COL-01 penalty. Poles across *colour schemes* (K-COL-03) are not yet generated — the composer runs one scheme per call.

**Composition operators O1–O6** (alternatives to the silhouette-first default, used to force portfolio diversity):

| | Operator |
|---|---|
| O1 | Silhouette-first (default) |
| O2 | Hero-first — pick the expressive item, solve around it |
| O3 | Palette-first — fix the colour structure, fill slots to it |
| O4 | Register-first — fix the formality target, work down |
| O5 | Texture-first — build the interest from material, keep colour quiet |
| O6 | Wildcard — apply a named designer move as a constraint |

**Designer moves as reusable instructions** (T4 → generation vocabulary, never a decision mechanism): elimination (subtract, don't add) · silhouette as construction · volume held away from the body · gender borrowing · softness without structure · deliberate asymmetry · exposed construction · one deliberately discordant element · perfect cut with zero ornament.

This is the answer to "the output is plain and basic" — it gives generation a second-order language of *moves*, not just of *items*.

**Named aesthetics** (quiet luxury, old money, coquette, gorpcore, balletcore, dark academia, Y2K…) are the user's vocabulary for vibe requests. They are **not rules**. They belong in the data layer as embedding anchors — a curated image set per aesthetic, a centroid, a mapping from vibe request to centroid. Updating means replacing images, not changing code. Volatility: months.

---

# PART XIV — Assembly procedure and execution contract

## XIV.1 Order of operations

0. **Input check.** Confidence on critical profile attributes. Missing critical field → ask (one message, only about what is missing) or enter robust fallback. **Attributes are never invented or silently assumed.**
1. **Scenario → parameters.** Host/stakes → risk asymmetry; base range from dress code; modifiers; practical vetoes; weather layer. Output: `formality_range, vetoes, weather_layer, risk_posture`.
2. **Intent + risk budget.** From profile or request; adjusted by `risk_posture`.
3. **Composition strategy.** Default or operator O1–O6; hold portfolio quotas.
4. **Silhouette.** One readable letter for this body and intent; moves resolved **by zone, not by label**.
5. **Anchor item.** Hero or the structural element fixing the silhouette. A dress is its own anchor — and then the third piece is near-obligatory.
6. **Volumes around the anchor.** Full volume only with an anchor (waist or an exposed narrow point); no edge terminates at the widest point of a zone; rise set by vertical balance.
7. **Value structure → palette.** Lightness steps first, hues second. Chroma budget including hair and frames. Near-face colours by the face map, asymmetric: **exceeding the person's contrast is worse than under-shooting it**.
8. **Shoes together with hem length.** Not last.
9. **Third piece + focus.** Exactly one focus; count interest sources; meet the floor for the declared intent; in conservative contexts prefer quiet sources (i1/i2/i4).
10. **Gestures.** At most one sprezzatura; layout commands shift formality ~0.5 step.
11. **Editing step.** Remove anything whose removal costs nothing — floored, never cutting below the interest minimum.
12. **Run both checklists item by item**, then rule-trace, then output.

Each step is self-sufficient: the substance of the rule is inline, the ID is for tracing.

## XIV.2 Execution contract

> **K-IO-01. Required inputs:** person profile and scenario. No outfit is assembled without both.
> **FORCE:** `hard`.

> **K-IO-02. Missing-data protocol.** Never invent, never silently assume. Ask once, only about what is missing, covering: height and a front photo in close-fitting clothes (or, in words: shoulders vs hips, waist definition, legs vs torso); hair, skin, eyes — asked **indirectly** ("gold or silver?", "pure white or off-white?"), never by asking for an undertone; vetoes (zones not exposed, sensory prohibitions, cultural or religious requirements); scenario; weather; practical load; and the mood of the look (usual · a little bolder · maximally expressive → `intent` and `risk_budget`).
> **FORCE:** `hard`.

> **K-CUT-00. Cut is never guessed from the name.** When a garment carries no cut field, the silhouette layer computes on the default *regular* and says so as a **question**, never as a finding.
> **WHEN:** any garment without an explicit `крій` (the feeds carry none unless the title says «свободного кроя» or similar). **FORCE:** `hard` (procedural — an instance of K-IO-02). **BREAKS:** the question repeats on every outfit of a feed without cut data, so it moves no rank; its value is that the silhouette numbers are labelled as defaulted rather than measured. **CHANGES:** K-SIL-01/03 and K-BOD-02 issue their findings with the note that the wrap is the body +12 % by default — the reader can tell a measured volume verdict from a defaulted one. Born in code (`silhouette.крої_відомі`); added here because it was cited as a corpus rule while absent from every theme.

> **K-IO-03. Robust fallback.** Without a reliable profile, only reliable channels operate: silhouette, lengths, fit, value, texture. Fabrics default to skim; palettes stay neutral-safe with no bet on undertone; boldness moves into silhouette and texture, **not** colour. Every assumption goes explicitly into an `assumptions` block.
> **FORCE:** `hard`.

> **K-IO-04. Output schema.** Slots (each = a concrete item + 3–7 words of reasoning + rule IDs) → parameters → excess checklist item by item → blandness checklist item by item → assumptions → 2–4 sentences of plain-language explanation with no rule IDs.
> **FORCE:** `hard`.
> **Executable form (code, 2026-08-24, `pipeline.перевірити_образ`):** the output now carries `чеклісти` — the 16-point ceiling (K-SYS-08) and 6-point floor (K-SYS-09) item by item with one of three states, *failed / passed / no input* — and `припущення`, the K-IO-03 assumptions block (every *question* or *withheld* finding, every defaulted hem). *No input* is reported as such and never counted as *passed*. On `ager_brief.xml` a typical outfit shows ceiling 0 failed / 5–7 passed / 9–11 without input: that is the honest resolution of the feed, not a score.

> **K-IO-05. Rule-trace discipline.** A rule is cited only together with the concrete attribute it tested. Format: *rule ID: person's facial contrast is low → black-and-white near the face removed.* Citing an ID without binding it to data is a **decorative trace and counts as an error.**
> **FORCE:** `hard`. **CHANGES:** this is what makes rule-trace auditable rather than ornamental, and it is the mechanism by which the A/B/C test stand can tell whether a rule fired.
> **First executable instance (2026-08-24):** K-FIT-03 measured *hem ends on the hip bulge* at force 1.0 for every top on `ager_brief.xml` — over a hem that the composer had *defaulted* from the slot, because no feed carries garment length. That is a decorative trace by this rule's definition. Now a defaulted edge yields a *question* (length unknown) and K-IO-05 records the downgrade; K-SIL-02 (division line) is withheld on the same input.

> **K-IO-06. Worked examples are reasoning formats, not answer catalogues.** No item, colour or combination is transferred from an example unless it passed the full assembly pass independently for the current profile.
> **FORCE:** `hard`.

## XIV.3 What is deliberately not encoded

> **K-SYS-07.** (a) Which silhouettes are current — drifts over years, needs a maintained trend source. (b) Taste tie-breaks. (c) The cultural meaning of specific items in a specific environment right now.
> In these zones: lowered confidence and explicit caveats. **Not invented rules.**

**And the standing veto:** no numeric style score in v1. Evaluation is a composer judgement with an explanation, because Part I.2 establishes there is no universal "good" number.

---

# PART XV — Evidence register

Every constant that a decision depends on, with its actual standing. This is the table the strength invariant is enforced against.

## The split: which rules can be checked against a source at all

All 71 rule blocks in this file, classified by whether a primary source exists to run them against.

| Code | Meaning | Count |
|---|---|---|
| **S** | Primary source exists; traced and checked | 13 |
| **P** | Practitioner convention; **no origin exists**. Only checkable against worked stylist decisions, which we do not have | 34 |
| **I** | Invented number. Nothing to check against; only feed calibration resolves it | 14 |
| **X** | Source lives in theme 1/2/3; audited there | 4 |
| **A** | Architectural/procedural, ours by construction. No source is possible or needed | 6 |

**S (13):** K-COMP-01 · K-COMP-04 · K-P0-01 · K-PRN-01 · K-LNG-04 · K-KOH-03 · K-MAT-02 · K-PER-05 · K-SIL-04 · K-SIL-05 · K-SIL-07 · K-CRA-03 · K-COL-03.

**Of those 13, eight were found misstated** on the source pass: K-COMP-01 (three sources collapsed to one; no ΔE in the paper; authors' own limitation dropped), K-P0-01 (two non-significant results reported as findings; effect sizes omitted; posture factor never extracted), K-PRN-01 (reversal overstated; variability and hysteresis missing; Imai miscited in kind), K-KOH-03 (four conditions claimed, three exist; mediator and moderator missing), K-MAT-02 (formula direction unstated; node count dropped), K-PER-05 (rule stands, cited literature does not carry it), K-CRA-03 (ceiling attributed to a 1528 source that does not contain it), K-LNG-04 (support understated).

**P (34):** K-COMP-02, 03, 05, 06, 07 · K-SIL-01, 02, 03, 06, 09, 10 · K-FIT-03, 04, 06 · K-COL-05, 06, 08, 10 · K-MAT-01, 03, 05, 06 · K-SHO-02, 03, 04, 05 · K-KOH-04, 05, 07, 08 · K-CRA-02, 07, 08, 09 · K-ACC-01.

For every one of these, a search for an originating source returns nothing. **This is not a defect in the rules** — by this project's ordering, live practitioner decisions outrank cited theory. The defect is that we hold the *conclusions* of that practice and not the *decisions*. K-CRA-01 (third piece) is the proof: the practitioner formulation carried two operational criteria — all three garments visible, and in-garment detail substituting for a layer — that the compressed corpus version had thrown away. **Every rule in this class is likely carrying the same kind of loss, and source-chasing cannot find it, because the precision lives in worked examples rather than citations.**

**I (14):** the folkloric-constant list below. Running these against a source is not a task that can succeed.

**A (6):** K-PER-00 · K-VAR-01 · K-IO-01…06 · K-SYS-07 (counted as the architectural set).

**Do not read the presence of a K-ID as verification.** Force tags in classes P and I express judgement, not measurement.

## Sourced — traced to a primary source, numbers verified

| Claim | Source | Tier | Max force |
|---|---|---|---|
| Coordination optimum is mid-range, quadratic | Gray et al. 2014, PLoS ONE 9(7):e102772 | T1 (n=60 stimuli) | `default` |
| Fit read in ≤5 s without a face; e²≈.04–.05 | Howlett et al. 2013, JFMM 17(1):38–48 | T1 | `strong` (architecture only) |
| Horizontal stripes thin: 7.1% / 4.5% abstract, 5.8% 2D, 10.7% 3D | Thompson & Mikellidou 2011, i-Perception 2:69–76 | T1 | `hint` |
| Stripes add nothing over a black garment (p=.26); luminance is the reliable lever; d=0.61 | Koutsoumpis et al. 2021, Perception 50(9):741–756 | T1 | `strong` (value) / `hint` (stripes) |
| Stripe effect reverses at larger body sizes | Ashida et al. 2013; Imai 1982 | T1 (second-hand) | `hint` |
| Belief–perception asymmetry on stripes | Koutsoumpis et al. 2026, PLoS ONE 21(4):e0347495 | T1 | `default` (language layer) |
| Horizontal stripes read *wider* when one person is seen live and judged from memory (d = 0.63 vs vertical, 0.61 vs none) | Swami & Harris 2012, Soc Behav Pers 40(8):1239–1244 | T1 (abstract + secondary report) | `hint` — sign is regime-dependent |
| Fit effect unchanged between static and walking images | Howlett et al. 2013 (full text) | T1 | `default` (render channel) |
| Neutral pose rated above power pose; clothing register outweighs posture (η² .84 vs .42) | Gurney et al. 2017, Br J Psychol 108(2):436–451 | T1 (4 models, 86 raters) | `default` (render pose) |
| Four dress-inference channels; perceiver is a model term | Hester & Hehman 2023, PSPR 27(4):414–433 | T2 (review) | `default` |
| Coarse formality shifts wearer behaviour and perceiver physiology | Kraus & Mendes 2014, JEP:Gen 143(6):2330–2340 | T1 | `hint` |
| Clothing affects the wearer — direction only, post-2015 evidence | Horton, Adam & Galinsky 2025, PSPB 51(2):203–221 | T1 (author-conflicted) | `hint` |
| Drape is measurable: DC + node count; bending and shear dominate | Cusick 1965/1968; BS 5058; ISO 9073-9:2008 | T2 | `strong` |
| Complexity–preference inverted U (the parent of the two-sided model) | Berlyne 1971; Birkhoff 1933 | T3 (contested) | `hint` |

## Convention — convergent practice, no traceable origin

Third piece · one focus · one silhouette letter · anchor first · echo · intensity matching · texture as variety · metal consistency · genre dominance · trend dosing · anti-costume · sprezzatura (attributable to Castiglione 1528 as a concept, not as a styling rule) · dress-code contents · risk asymmetry · guest taboos · cling/skim/stand-away mapping · termination points · scale matching · shoe mass matching · boot-shaft rule · wardrobe architecture.

These are not false. They are the practitioner ground truth, and per the project's own ordering they outrank cited theory. They are simply **unmeasured**, and no rule built on them may carry `hard` on evidentiary grounds alone (procedural `hard` — e.g. "shoes and hem together" — is a different thing and is permitted).

## Folkloric constants — invented numbers, uncalibrated

`chroma budget 1–2` · `shine budget 1–2` · `visible layers ≤3` · `formality spread ≤2 steps` · `formality scale granularity 1–10` · `layout gesture ≈0.5 step` · `60-30-10 area split` · `interest floor ≥1 / ≥2` · `risk budgets 1 / 0–1 / 0–1 / 2–3` · `third piece migrates to accessories above ~26 °C` · `rule of thirds 1:2 / 2:1`.

**Every one of these is a threshold a real garment is judged against, and none has been measured.** Until calibrated they are defaults, and the system must not present them to the user as facts.

## Banned outright

- **Golden ratio Φ = 1.618** as a garment division target — no perceptual anchor. The asymmetric-division claim survives; the number does not.
- **Numeric style score** in v1.
- **Seasonal colour typing as a hard filter** — soft prior only, over the continuous axes (theme 2).
- **Body-shape labels as the decision unit** — zones and measured ratios decide; labels are routing only, and where label and zones conflict, zones win.
- **Flaw language** in any explanation.
- **Stripe orientation as a primary proportion tool.**

---

# PART XVI — What is not verified, and what is missing

Stated as prominently as what is verified.

**Nothing in this file is calibrated.** No threshold has been tested against a golden set of real outfits with human verdicts. Reading the sources moved nothing into `hard` on evidentiary grounds.

**Sources located but not read in full:** Ashida et al. 2013 (now read via abstract and citing papers — the three factors are secure, the underlying data are not); **Imai 1982 — a Japanese-language popular psychology piece, never seen, reported only through Ashida**; **Swami & Harris 2012 — abstract read, effect sizes taken from Koutsoumpis et al. 2021; full text paywalled; conditions recorded in VII.3**; Burns et al. 2019 (abstract and the authors' concession only); Hur, Etcoff & Silva 2023 (abstract and reference list only, and integrated nowhere); Hester & Hehman 2023 (abstract plus excerpts, paywalled); Miyazaki & Ishibashi 2022 (reference list only).

**Read in full on 2026-08-24:** Howlett et al. 2013 (repository PDF) — the posture factor is resolved, see XI.2; Gurney et al. 2017 (author manuscript) — posture × clothing interaction, see XI.2.

**Was carrying `strong` on a source never read: K-SIL-05** (visual weight) rests on DeLong's ABC framework, which was not obtained. Lowered to `default` on 2026-08-24; the book remains unread and the rule remains unchecked.

**Retrieved 2026-08-24: the static/dynamic posture factor in Howlett et al. 2013** — no difference between static and walking images; static renders do not misrepresent the fit signal on this evidence (XI.2).

**Never sourced, and load-bearing:** every item in the folkloric-constant list above.

**Practitioner layer, sourcing pass of 2026-08-24 — four searches (two English, two Ukrainian), text only, no video.** Found two named practitioners making a real decision with a stated mechanism; everything else returned was anonymous SEO copy and is not a source.

- **Angie Cox, YouLookFab, *How to Wear a Leather Skirt* (2011), a working stylist writing from client sessions.** Decision: *keep the support act soft and texture-rich — a drapey silk or polyester-rich blouse, cashmere or angora knits, sequined tops; creating this contrast against the severity of the leather makes it wearable for work and play. Tees and knit tops can work, although I find them a harder combination to pull off with sass. Denim and button-down shirts look okay, but provide a more hard-edged look.* Mechanism: texture contrast against leather's severity (K-COMP-06, K-MAT-01). **WHEN:** leather or faux-leather skirt as the anchor. **HOW MUCH:** preference, not veto — the tee *can* work. **BREAKS:** a 2011 lens; her examples lean office-to-evening, not weekend. T3, `hint`. **It bears on a live decision:** the composer's current winner for the warm-light profile on `ager_brief.xml` is exactly *printed tee + eco-leather skirt* — the pairing she calls the harder one. The wear verdict on row 4 of `вердикти.tsv` will say who is right.
- **Галина Денисюк, stylist, interview in Табло ID / Українська правда (28.04.2025).** Decision: *контраст кольорів між верхом і низом або «кольоровий блок» на талії — дуже добре малює силует.* Mechanism: a value/colour break at the waist draws the division line (K-COL-01 value step; K-SIL-02). **WHEN:** the person wants the waist read. **BREAKS:** she gives no counter-case; a break at the widest point would contradict K-FIT-03. T3, `hint`. Her working method — start from the question *«Чому я вірю, що мені це не можна?»* and move in small steps (a length slightly above the knee before a mini) — is the same posture as K-LNG-04 and the wellbeing frame of I.4, stated by a Ukrainian practitioner.

**Not found, after four searches:** a single text-form before/after by a named stylist over a named garment. The worked decisions this theme needs live in video breakdowns and paid consultations, as Part XVI predicted; text search surfaces conclusions, not decisions.

**The practitioner layer is still thin, and this is a standing failure.** This theme now rests on nine peer-reviewed papers, one textile standard and a scattering of practitioner blog posts. **Zero worked before/after decisions by a working stylist over a named garment have been collected.** By the project's own ordering — live practitioner decisions outrank cited theory — this is the wrong balance, and it is the largest gap in the file. The next sourcing pass must go to video breakdowns and worked examples, not to more journals.

**Open, unresolved:**
- Duty cycle (Thompson & Mikellidou) versus absolute stripe period in centimetres (theme 2/3) as the governing stripe variable.
- The body-size crossover at which the stripe effect changes sign.
- Where the Ukrainian market's coordination optimum sits relative to the Western samples.
- Background luminance in our own try-on render is uncontrolled and demonstrably affects perceived width.
- Our try-on render is a photograph, so it systematically understates texture-based interest — the channel we use to show the person their outfit is biased against the lever we most rely on for the interest floor.

---

# PART XVII — The falsifiable next step

One, over real things, with the outcome predicted in advance.

**Test.** Take 20 real garment sets assembled from the Ukrainian catalogue feed. For each, compute the mean pairwise colour similarity across colour-bearing slots and rank it within the candidate set. Then measure the discriminating power: **what fraction of the 20 falls in the middle third?**

**Prediction, stated before the run:** more than 70% will land mid-rank, because catalogue items within a single retailer's season are already palette-constrained.

**If the prediction holds:** the coordination target is not a filter — it passes almost everything — and it must be reported as such rather than shipped as a rule. The composer would need a within-outfit dispersion term instead of a mean.

**If it fails and the set splits:** keep it at `default` and record the split.

**Run, 2026-08-24 (`measure_theme4.py`, `ager_brief.xml`, colours from title words, two opposite profiles).** Share of assembled combinations whose mean pairwise similarity falls in the *middle third of the pool's range*: **warm-light 10/20 = 50 %; cool-dark 0/25 = 0 %.** The prediction (>70 %) **fails** — and it fails for a reason the prediction did not anticipate: with word-derived colours every garment of one colour word has the same Lab, so pairwise similarity is quantised (identical-word pairs at distance 0, the rest far), and the cool-dark pool is bimodal. Per the protocol above: K-COMP-01 stays `default`, the split is recorded here, and the number must be re-taken once colours come from photographs. Discriminating power on this input: rank shifted in 16/20 and 20/25 combinations, winner changed in both profiles.

**Second finding from the same run, on the coherence layer.** `feed.прогін` computed the garment type for fabric genus only and never wrote it into the catalogue record — so on every real feed the formality intervals were `None` and K-KOH-02/03/05, K-SHO-03 and K-MAT-01 were silent by construction (0 firings in 100 combinations of a feed tee against a stub court shoe). With the field written, K-KOH-02 fires in 16/100 and 21/125 combinations of `ager_brief` plus five *stub* shoes spanning the scale, moves ranks (83, 101) and does not move the winner in either profile — the shoes are not real garments, so this says the rule has an input, not that it is right. The formality layer is no longer unreachable; it is untested.

Either way the output is a number from real feed data, not another document. And the second half of the same run is the one that actually matters: **assemble one outfit and get a "would wear / would not" verdict from a person.** That is still missing, and it is still the only end-to-end validation that counts.

---

# APPENDIX A — Body zone maps

Preserved from the source file for self-containedness. **Owned by theme 1** — diagnosis, measurement and the zone architecture live there. Reproduced here because the composition rules reference them.

> **K-BOD-02. Zones, not labels.** Rules bind to zones and measured ratios: shoulders, bust, waist, high hip, low hip, mid-torso. A "type" is a routing label only. Most people are hybrids and are resolved zone by zone — **the top follows one type's rules, the bottom another**. Labels are unstable between schools (the same label means opposite advice about the lower body in different systems), so the decision is always derived from the ratio vector. **Where label and zones conflict, zones win.** FORCE: `strong`.

**A — balance the top to the bottom.** Structured or detailed shoulders; boat neck; double-breasting and wide lapels as upper volume; lighter or brighter top; darker, cleaner bottom; A-line skirts that skim; flare and bootcut; full-length straights falling from the widest hip point; high rise; jackets ending at the top of the hip bone or below the widest point. Conditional: **wide-leg only with a fitted or tucked top.** Anti (`strong`): accent pockets, whiskering or draping at the hip; a hem exactly at the widest point; a short fitted top with skinny bottoms simultaneously.

**V — soften the top, build the bottom.** Deep narrow V and U necklines; raglan, kimono, dolman; soft dropped shoulder; a clean darker top ending past the hip line; volume, detail, print or lightness below (pleats, wide trousers, cargo); A and H silhouettes. Conditional: halter only deliberately — with a small bust, narrow halter lines can lengthen; the canon disagrees. Anti (`strong`): shoulder pads, epaulettes; wide low necklines (boat, off-shoulder, square); puff sleeves; large collars.

**X — follow the line.** Wrap; fitted knit; high or mid rise (low rise visually widens the hips); a belt at the waist, dark reinforcing the cinch; pencil; soft fluid-structural fabrics; bootcut and flare work (the curve sits low). Anti (`strong`): boxy cuts that hide the waist; volume at bust and hips simultaneously; dropped waist.

**H — create a waist OR commit to a column; one strategy is mandatory.** Waist moves: wrap, belt, peplum, curved or princess seams, fitted jackets, layering with depth. Column moves: shift, longline layers, an unbuttoned coat past the knee. Anti (`strong`): the "no strategy" outfit — shapeless cling, or a sack with no choice made between waist and column; a cropped box with no waist strategy reads as a square.

**O — target the vertical; attention up (face, décolleté) and down (legs); detail in the upper and lower thirds, the centre quiet.** Open V necklines; vertical plackets; long open layers (duster); an under-bust line with a **clean fall** of fabric; skim fabrics; straight or tapered bottoms; a monochrome column. Hybrid: a top-heavy cluster resolves as V×O — volume moves downward. Anti (`strong`): cling at the mid-torso; a belt at the natural waist; a tight full tuck; small decoration on the stomach; **empire lines with gathers or pleats** falling over the widest point, which produce a pregnancy reading.

**8 (defined waist, high-hip shelf) — waist plus a clean straight line through the high hip.** Defined waist; straight bottom (straight skirt or trousers, straight or bootcut); flare only from the knee; peplum and belted styles are built for this; cropped jackets. Conditional: **if the shoulders are narrower than the hips, the top follows the A rules** — zone-by-zone resolution. Anti (`strong`): A-line or flare from the hip; wide-leg; pleats and gathers from the waistband (they open over the shelf); double-breasted jackets; anything boxy pressing on the high hip.

**A known structural defect, carried from the theme-1 audit:** the high hip is currently *derived* as hip × 0.92 rather than measured, which collapses the independent Spoon / Bottom-Hourglass axis and makes the 8 label structurally impossible below roughly a 77 cm waist. Until high hip is measured, all 8-specific routing above is unreliable. **This is an open code defect, not a knowledge gap.**

---

# APPENDIX B — Person-colouring interface

**Owned by theme 2.** Only the interface used by composition rules is stated here.

- **Derived, not asked.** Value contrast and colour contrast come from the spread of lightness and colourfulness across hair / skin / eyes. Clarity comes from the cleanliness of boundaries and the saturation of the person's own colours. Confidence: self-report ≈ 0.5; photo assessment ≈ 0.8; photo plus measurements ≈ 0.9. **Visual assessment of silhouette outranks tape measurements.**
- **Contrast matching is the main axis.** The outfit's value contrast is set to the person's contrast level. High contrast (dark hair, light skin) carries black-and-white; low contrast is erased by it and needs mid-value tonal ranges.
- **Asymmetry:** exceeding the person's contrast is worse than under-shooting it.
- **Undertone is the secondary axis**, strongest on metals, whites, and colours near the face. The near-face zone carries the majority of the "suits her" effect; the lower body is close to free. The 30 cm figure attached to this in the corpus is a `[folkloric constant]`.
- **Seasonal 12-type systems: soft prior only, never a hard filter.** Reliability is low, inter-expert agreement is poor, and state-of-the-art vision classifiers reach only ~55% on the four-season task.
- **Classical colour-harmony schemes are near-chance predictors of real garment judgement.** They remain useful as generation vocabulary and as explanation language. They are not a decision mechanism.

---

# APPENDIX C — The composer payload

The distillation of this theme into instructions an LLM stylist actually executes. Imperative, no IDs, no evidence markers — this is prompt text.

**Frame**
1. Judge the whole outfit on this specific body as one thing, not item by item. The goal is a coherent look, not a set of objects.
2. What the outfit says depends on audience and occasion. Establish *for whom / for what* first, then decide the rest.
3. Keep the goal explicit. *Look expensive*, *look current* and *look timeless* are different, conflicting goals. Build for the one requested, not a blend.

**Composition**
4. Give the outfit one readable silhouette and one focal point. Zero focus reads bland; two compete.
5. Repeated elements group perceptually — repeat a colour, metal or texture at two separated points and the outfit reads as intentional. This is also how you control where the eye divides the body.
6. Match intensity before matching hue. Closeness in chroma and lightness governs whether two garments agree; the hue relationship is secondary.
7. **Lightness structure does the proportion work, not pattern.** Stripe direction is a weak effect and disappears entirely against a dark garment. Do not use stripes as a shaping tool.
8. Pattern scale matters: small prints merge into a solid tone at distance, large blocks stay in contrast. Judge how it reads across a room.
9. Texture contrast adds interest without adding another colour or pattern focus. Reach for it first when the outfit is too quiet.

**Colour**
10. Colour near the face pushes the skin the other way. Use it toward the person's stated goal, never as a fixed verdict about their "season."
11. **Match colours moderately.** Neither everything in one tone nor maximum contrast — the middle reads best.
12. Loudness is a choice: complementary and high-contrast pairings read loud, adjacent and tonal read quiet. Pick the loudness the occasion wants.

**Status and register**
13. Perceived quality is read fast and involuntarily. If the goal is to look capable, raise the quality signals — fit, material, upkeep, craft detail — and remove anything reading as cheap imitation.
14. Status has two registers: loud (logos, bold) and quiet (restrained, unbranded). Choose one for the audience. Do not blend them without intent.

**Variability**
15. Offer two or three looks from different poles rather than one safe median. One stereotype per request is a failure; the value is in the range.

**Limits**
16. Frame everything as *emphasising or expressing what the person wants*, never as *hiding a flaw*. Do not impose a norm; help signal what they chose.
17. Signal meanings differ in the Ukrainian market from the Western research this is drawn from. Do not transfer directly: a defined waist and dressed-up quality rate higher here, casual and oversize lower.

**Honest verdict on the payload.** Roughly six of these seventeen genuinely change an LLM's default behaviour: #5 (grouping → proportion), #7 (tone over pattern), #10 (near-face colour as a direction), #11 (moderate matching), #14 (loud/quiet register), #15 (range over median). The rest is hygiene — useful because it makes the implicit explicit, not because it adds knowledge. **Which of the seventeen actually work is still unproven.** The only test is a run on real input from the feed, showing which lines changed the output and which stayed silent.
