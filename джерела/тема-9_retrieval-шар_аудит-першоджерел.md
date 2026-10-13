# тема-9 → шар retrieval: знання після аудиту першоджерел

**Статус файлу.** Це заміна, не доповнення. З 1 641 рядка теми-9 аудит першоджерел витягнув один придатний блок знання — про вибір embedding-моделі й межі retrieval. Решта теми-9 не має першоджерел, бо це власні документи проєкту (індекс, дорожня карта, план верифікації, план жнив, мапа знань, шаблони промптів). Розділ 0 нижче пояснює, чому їх не треба аудитувати, а треба видалити.

**Головне, одним абзацом.** Твердження теми-9 «незалежний бенчмарк показав, що Marqo не б'є базовий SigLIP на image-to-image» стосується **іншої моделі**, ніж та, яку проєкт збирається ставити. Реальний фешн-специфічний бенчмарк (LookBench, січ. 2026) тестував саме Marqo-Fashion-моделі на image-to-image і показав протилежне: вони б'ють SigLIP2 на 3,3–3,8 пункти. Водночас той самий бенчмарк дає число, якого в корпусі не було й яке обмежує весь продукт: **ймовірність, що всі речі зібраного образу знайдені атрибутно-точно, ≈ 53 % у найкращої моделі 2026 року.**

> **Ревізія за станом лідерборду на 30.06.2026.** Перевірено на офіційній сторінці LookBench. Усі висновки нижче встояли; змінилися дві речі — рядок стеку (§1.7) і поява кривої recall@k (§1.4). Дві поправки до поширеного формулювання «новим лідером стала Tianmu-MERE»:
> 1. **Tianmu-MERE не обійшла GR-Pro на зваженому overall** — за числами з її ж картки виходить 66,20 проти 67,34 у GR-Pro. Вона програє **найважчий і найважливіший для нас сабсет RealStreetLook на 4,18 пункти**, а виграє синтетичні. Її реальне досягнення інше й теж важливе: це **найкраща модель з відкритими вагами**, бо GR-Pro пропрієтарна.
> 2. **ZooClaw-FashionSigLIP2 узагалі не на цьому лідерборді.** Сторінка ставить її в окрему секцію **text-image retrieval** на власних бенчмарках ZooClaw-Fashion і H&M. Це інше завдання, інший датасет, числа самозвітні, а сам оціночний датасет ще не опублікований. Як конкурента в image→image її порівнювати нема з чим.
>
> **Тестовий набір не оновився.** Сторінка досі каже «поточний реліз v2601, ~2 300 запитів». Стаття обіцяла піврічне оновлення до ~10K запитів і 200K корпусу — не сталося. Оновилися **подання моделей, не бенчмарк**. Обіцянка contamination-mitigation поки не виконана, і це знижує вагу LookBench як «живого» бенчмарку рівно настільки, наскільки він насправді статичний.

---

## 0. Що таке тема-9 насправді (правило 0)

Тема-9 склеєна з 10 документів. Розподіл:

| Документ | Тип | Чи є першоджерело |
|---|---|---|
| `00-індекс-логіка-і-вердикти.md` | власний індекс | ні |
| `05-архітектура-системи-і-даних.md` | власний дизайн-док | частково (§1.2 ландшафт) |
| `06-дорожня-карта-і-операції.md` | власний план | ні |
| `07-план-верифікації-і-валідації.md` | план перевірки | ні |
| `ai-stylist-architecture.md` | власний дизайн-док | частково (§2, §6) |
| `knowledge-system-map-v0.md` | мапа знань | ні |
| `knowledge-harvest-plan-v0.md` | план збору знань | ні |
| `layout-test-matrix.md` | власна тестова матриця | ні (тест не прогнано) |
| `конкурентна-карта_...md` | ринкова розвідка | так, але не змінює рішень про річ |
| `розбір-конкурента_alta-daily-2.md` | ринкова розвідка | так, але не змінює рішень про річ |

**Сім із десяти — це «про». `knowledge-harvest-plan` — це план збору знань; `07-план-верифікації` — план перевірки зібраного. Це буквально «план перевірки нотатки» і «нотатка про план», які заборонені правилом 0.** Шукати їм першоджерела неможливо й безглуздо: у них немає джерел, бо їх написав проєкт про самого себе.

Два конкурентні документи мають зовнішні джерела (TechCrunch, WWD, App Store), але провалюють тест before/after правила 3: знання, що Alta підняла $11M, не змінює жодного рішення про жодну річ. Тримати як ринковий контекст — так; називати знанням системи — ні.

**Придатний вихід аудиту сконцентрований у трьох абзацах теми-9** (рядки 799–801 і таблиця стеку, рядок 897–907). Вони й переписані нижче.

---

## 1. Corrected knowledge: embedding model selection for garment retrieval

*English, because every number below comes from an English-language primary source and must survive without the conversation.*

### 1.1 The corpus attributed a benchmark result to the wrong model

**What the corpus said.** Marqo-FashionCLIP / Marqo-FashionSigLIP, ~203M parameters; an independent benchmark (arXiv 2504.07567) found that on image-to-image retrieval "Marqo-B" did not beat baseline SigLIP.

**What the primary source says.** Czerwinska, Bircanoglu & Chamoux (Adevinta), *Benchmarking Image Embeddings for E-Commerce*, arXiv:2504.07567, submitted 10 Apr 2025, accepted at FTC 2025. §7.4 states that Marqo-B, which had been shown to beat its SigLIP baseline on zero-shot text-to-image retrieval over labels and categories, does not beat SigLIP on image-to-image retrieval on their benchmark. The citation behind "Marqo-B" is Sleightholm 2024, *Introducing Marqo Specialized Embedding Models for Ecommerce* — the **Marqo-Ecommerce** blog post.

**The conflation.** Marqo ships two unrelated model families:

| Family | Members | Params | Base | Released |
|---|---|---|---|---|
| Marqo-Ecommerce | Marqo-Ecommerce-B, Marqo-Ecommerce-L | 203M / 652M | — | Nov 2024 |
| Marqo-Fashion | Marqo-FashionCLIP, Marqo-FashionSigLIP | ~0.2B (HF card) | ViT-B-16-laion2b / ViT-B-16-SigLIP-webli | Aug 2024 |

"Marqo-B" = **Marqo-Ecommerce-B**, a general e-commerce model covering dining chairs and toothbrushes as much as garments. Its 203M parameter count is exactly the figure the corpus attached to the *Fashion* models. The Adevinta paper never evaluated Marqo-FashionCLIP or Marqo-FashionSigLIP.

**Consequence for the system.** The stated justification for benchmarking both retrieval modes locally — "an independent benchmark showed the fashion model loses on image→image" — is not supported by that paper. A different, better-targeted result exists and points the other way (§1.3).

### 1.2 The Adevinta benchmark cannot discriminate on fashion anyway

Two structural limits make arXiv:2504.07567 unusable as evidence about garment retrieval, independent of the model mix-up:

**Limit A — the Fashion split is saturated.** The paper designates Fashion (≈40k images, six classes) explicitly as a technical control, the simplest classification task in the set. Its mMP@5 results:

| Model type | Fashion mMP@5 |
|---|---|
| Pretrained supervised | 0.991 |
| Top-tuned supervised | 0.991 |
| Pretrained SSL | 0.994 |
| Top-tuned SSL | 0.994 |
| Pretrained text-image | 0.995 |
| Top-tuned text-image | 0.996 |

Spread across every model family and tuning strategy: **0.005**. A benchmark whose discriminating power on the target domain is half a percentage point cannot rank models for that domain. (This is the project's own "a filter that passes 85 % of the item space is not a filter" principle applied to a benchmark.)

**Limit B — relevance is defined at category level.** The retrieval protocol assumes images sharing a classification category are similar. With six categories on Fashion, a query for an olive midi A-line skirt scores a hit on any skirt. The task the system must perform — separating an A-line from a pencil skirt in the same colour — is invisible to this metric.

**Applies when / breaks where.** Cite 2504.07567 for its actual contribution: top-tuning (2–3 FC layers on frozen embeddings) lifts text-image embeddings by ~3.9 % and SSL embeddings by ~5.0 % mean mMP@5 at a fraction of full fine-tuning cost, and full fine-tuning on one dataset transfers badly to another (up to −0.5 mMP@5). Do **not** cite it for any fashion-domain model ranking.

### 1.3 The benchmark that does discriminate: LookBench

Gao, Xue, Peng, Fu, Gu, Li & Zhou (Gensmo.ai), *LookBench: A Live and Holistic Open Benchmark for Fashion Image Retrieval*, arXiv:2601.14706, 21 Jan 2026. CC BY 4.0. Purely **image-to-image**, fashion-only, contamination-aware.

**Design.** Four subsets, ~2,500 queries total, ~60k-image corpus each:

| Subset | Source | Items | Difficulty | Queries / corpus |
|---|---|---|---|---|
| RealStudioFlat | real studio flat-lay packshots | single | easy | 1,011 / 62,226 |
| AIGen-Studio | AI-generated lifestyle studio | single | medium | 192 / 59,254 |
| RealStreetLook | real street outfit photos | multi | hard | 1,000 / 61,553 |
| AIGen-StreetLook | AI-generated street outfits | multi | hard | 160 / 58,846 |

Distractors are drawn from Fashion200K and kept only if cosine similarity to an anchor falls in [0.25, 0.45] — near-duplicates and obvious non-matches are both excluded, leaving soft negatives. 58,275 distractors per task.

**Metric that matters.** *Fine* Recall@1 counts a query correct only if the top-ranked item matches the query's garment category **and all** annotated attributes. *Coarse* Recall@1 credits any category match. The fine/coarse split is precisely the distinction older fashion benchmarks collapse.

**Main result, fine Recall@1 (query-count-weighted overall):**

| Model | AIGen-Street | AIGen-Studio | RealStreet | RealStudio | Overall |
|---|---|---|---|---|---|
| GR-Pro (proprietary) | 77.50 | 75.13 | **62.39** | 69.14 | **67.38** |
| Tianmu-MERE *(added 2026-06-04)* | 78.75 | **79.27** | 58.21 | **69.63** | 66.20 † |
| GR-Lite (open) | 75.00 | 70.47 | 60.14 | 68.74 | 65.71 |
| Marqo-FashionCLIP | 71.88 | 72.02 | 56.88 | 66.37 | 63.24 |
| Marqo-FashionSigLIP | 74.38 | 74.09 | 55.15 | 66.17 | 62.77 |
| SigLIP2-B/16 | 69.38 | 72.02 | 51.89 | 62.81 | 59.44 |
| SigLIP2-L/16 | 60.00 | 65.80 | 48.22 | 58.36 | 54.84 |
| PP-ShiTuV2 | 38.12 | 44.04 | 43.12 | 57.86 | 49.21 |
| DINOv3-ViT-L | 22.50 | 38.86 | 37.41 | 54.70 | 43.97 |
| DINOv3-ViT-7B | 20.00 | 39.90 | 37.92 | 52.92 | 43.33 |
| DINOv2-ViT-G | 38.50 | 35.75 | 33.94 | 52.42 | 41.49 |
| DINOv2-ViT-L | 29.38 | 36.27 | 33.64 | 51.04 | 41.07 |
| CLIP-L/14 | 30.00 | 33.16 | 29.26 | 52.82 | 39.79 |
| DINOv3-ConvNext | 12.50 | 25.39 | 25.08 | 45.10 | 32.88 |
| CLIP-B/16 | 22.50 | 17.62 | 22.43 | 45.30 | 31.90 |
| InternViT-6B | 19.38 | 29.53 | 22.12 | 40.85 | 30.62 |

**Four findings, each with a decision attached:**

1. **Fashion fine-tuning wins on image-to-image.** Marqo-FashionSigLIP 62.77 vs SigLIP2-B/16 59.44 = +3.33 absolute (+5.6 % relative); Marqo-FashionCLIP 63.24 = +3.80 absolute (+6.4 %). This directly contradicts the corpus's stated worry. *Force: this is one benchmark, n=1 independent group, but it is the only one that tests the right models on the right task.*

2. **The two Marqo models swap order by domain.** On RealStudioFlat (catalogue packshots) FashionSigLIP 66.17 ≈ FashionCLIP 66.37. On RealStreetLook (a person photographed in the wild — i.e. a user selfie) FashionCLIP 56.88 clearly beats FashionSigLIP 55.15. *Decision: if the image→image path is ever fed a user photo rather than a packshot, FashionCLIP is the better default, not FashionSigLIP.*

3. **Bigger is worse, twice over.** SigLIP2-L (54.84) loses to SigLIP2-B (59.44). DINOv3-ViT-7B (43.33) loses to DINOv3-ViT-L (43.97). *Decision: do not spend VRAM on larger checkpoints in this domain without measuring.*

4. **Generic self-supervised vision encoders are unusable here.** DINOv2/v3 and CLIP land at 30–44 % overall — 20+ points below fashion-tuned models. *Decision: the "just use DINOv2" shortcut is closed.*

5. **Tianmu-MERE (Kuaishou, submitted 4 Jun 2026) wins the synthetic subsets and loses the real one.** † Overall is not published on its model card; 66.20 is computed here from the card's per-subset Fine@1 with LookBench's own query-count weights (1,011 / 192 / 1,000 / 160; n = 2,363). The same computation reproduces GR-Pro at 67.34 and GR-Lite at 65.67 against the paper's published 67.38 and 65.71, so the method is sound to ±0.05.

   Specification: dual-encoder, SigLIP2-based vision tower + **BGE-base-zh-v1.5** text tower, 1B params, Apache-2.0, trained on large-scale Chinese e-commerce data including **livestream video frames**. Its own model card states it is primarily optimised for Chinese e-commerce and that performance may degrade on distant domains.

   **Three consequences, in descending order of importance for код+ші:**
   - **Its text tower is Chinese-only.** The card's own usage example encodes `"V领无袖碎花连衣裙"`. There is no text→image path here for Ukrainian or English queries. Usable as an image→image encoder only.
   - **It loses RealStreetLook to GR-Lite (58.21 vs 60.14) and to GR-Pro (58.21 vs 62.39).** RealStreetLook is real people photographed in the wild — the closest proxy in existence for "user selfie → catalogue." It wins AIGen-Studio by 4.14, but that subset is Qwen-generated imagery, 192 queries, and models nothing the product does.
   - **It costs ~3× GR-Lite in parameters (1B vs ~0.3B) for +0.53 overall and −1.93 on the subset that matters.** The one genuine advantage is licence: Apache-2.0, clean, versus GR-Lite's unread DINOv3-derivative terms.

   *Force: `default`. Single self-reported table on a vendor model card, no independent re-run by the benchmark authors.*

### 1.4 The ceiling number: outfit-level retrieval ≈ 53 %

On RealStreetLook, LookBench also scores retrieval at outfit level: a query counts correct only if **every** garment in the outfit achieves fine Recall@1. Results: GR-Pro 53.2 %, GR-Lite 46.8 %, generic encoders at most low-to-mid 40 %.

**Why this is the single most important number in the file.** The pipeline of код+ші assembles a multi-slot outfit. If each slot's retrieval is independent and the state of the art puts the joint probability of all slots being attribute-faithful at roughly one in two, then:

- Any promise of the form "here is your outfit, assembled from real items matching your profile" is correct about half the time on the retrieval step alone, before composition or colour rules are applied.
- **The composer must not be handed a single candidate per slot.** It must receive a ranked shortlist and be able to reject, because rank-1 is wrong ~35–45 % of the time per item even in studio conditions.
- The A/B/C testing stand's arms are all downstream of this. If retrieval is the dominant error source, arm differences (rules vs no rules) may be swamped by retrieval noise. **The stand must log which slots came from which retrieval rank, or its verdicts are uninterpretable.**

#### 1.4a The recall@k curve — new as of June 2026, and it sizes the shortlist

The January paper reported only @1. The Tianmu-MERE submission is the first entry to publish the full curve on the same model, and it converts "hand the composer a shortlist" from a principle into a number.

| Subset | Fine@1 | Fine@5 | Fine@10 | Fine@20 | Coarse@1 |
|---|---|---|---|---|---|
| Real Studio | 69.63 | 87.24 | 90.60 | 93.77 | 91.99 |
| Real StreetLook | 58.21 | 75.13 | 79.10 | 82.57 | 77.78 |
| AI-Gen Studio | 79.27 | 93.26 | 96.37 | 98.45 | 93.78 |
| AI-Gen StreetLook | 78.75 | 92.50 | 95.62 | 96.25 | 88.75 |

**Marginal gain per step, real subsets:**

| Step | Studio | Street |
|---|---|---|
| 1 → 5 | +17.61 | +16.92 |
| 5 → 10 | +3.36 | +3.97 |
| 10 → 20 | +3.17 | +3.47 |

**The knee is at k = 5.** Widening the shortlist from 1 to 5 recovers ~17 points of attribute-faithful recall. Every subsequent doubling buys ~3.4. The architecture's stated "shortlist ≤ 30 candidates" is not wrong but is badly shaped: 25 of those 30 slots buy roughly 7 points between them, at 6× the composer's token cost and 6× the surface for the composer to pick something plausible-but-wrong.

*Decision: retrieve 20, pass 5–8 to the composer per slot. Not 1, and not 30.*

**Second reading of the same table — the coarse/fine gap.** Coarse@1 counts a hit on category match alone; Fine@1 requires every annotated attribute. The gap on real data:

- Real Studio: 91.99 − 69.63 = **22.4 points**
- Real StreetLook: 77.78 − 58.21 = **19.6 points**

So roughly one retrieval in five is **category-correct and attribute-wrong**: the right kind of garment, the wrong garment. This is precisely the failure a person notices immediately and a category-level metric cannot see — "це спідниця, але не та олива, не та довжина". It also means any evaluation of the pipeline that scores "did we return a skirt for the skirt slot" is measuring a task ~20 points easier than the one the product must pass.

*Note that Fine@5 on Real Studio (87.24) is now above Coarse@1 (91.99) minus five points — i.e. a shortlist of five items is roughly as likely to contain the attribute-correct item as a single item is to be merely the right category. This is the quantitative case for the deterministic-filter-then-LLM-rerank architecture (П2), stated in numbers rather than principle.*

### 1.5 Retrieval accuracy varies ~2× by garment category

GR-Pro (best model) fine Recall@1 broken down by category:

| Subset | Category | Fine R@1 |
|---|---|---|
| RealStudioFlat | blouse | 79.3 |
| RealStudioFlat | dress | 72.7 |
| RealStudioFlat | pants | 57.6 |
| RealStudioFlat | T-shirt | 45.2 |
| RealStudioFlat | sweatshirt | 39.7 |
| RealStreetLook | skirt | 78.4 |
| RealStreetLook | vest | 75.6 |
| RealStreetLook | pants | 52.6 |
| RealStreetLook | coat | 43.4 |

**Mechanism.** Categories with distinctive silhouettes (dress, skirt, blouse) separate well in embedding space. Categories with high intra-class similarity (T-shirt, sweatshirt, coat) do not — one grey crew-neck sweatshirt is near-indistinguishable from another at the embedding level, and the attributes that differ (weight, hand, exact neckline depth) are not visually recoverable from a packshot.

**Where it breaks / applies.** The spread is roughly 2× between best and worst category *within the same model, same subset, comparable query counts*. Domain shift adds on top: pants 57.6 in studio vs 52.6 in street.

**Decision for код+ші.** Retrieval confidence is **not** a single system constant. A candidate in a `светр`/`футболка` slot is roughly half as trustworthy as a candidate in a `сукня`/`спідниця` slot. This must be a per-category coefficient in the pipeline, and the composer's explanation ("чому це на тобі працює") must not be equally assertive across slots. Currently the code has no such coefficient — this is a concrete gap, not a refinement.

### 1.6 Vendor benchmark numbers are inflated by contamination

Marqo's own model card (huggingface.co/Marqo/marqo-fashionSigLIP, Apache-2.0, ~379k downloads/month) reports averages over six public fashion datasets — Atlas, DeepFashion In-shop, DeepFashion Multimodal, Fashion200k, KAGL, Polyvore:

**Text-to-Image, averaged over 6 datasets:**

| Model | AvgRecall | R@1 | R@10 | MRR |
|---|---|---|---|---|
| Marqo-FashionSigLIP | 0.231 | 0.121 | 0.340 | 0.239 |
| ViT-B-16-SigLIP-webli *(its own base)* | 0.212 | 0.111 | 0.314 | 0.214 |
| ViT-B-16-laion2b_s34b_b88k | 0.174 | 0.088 | 0.261 | 0.180 |
| FashionCLIP2.0 | 0.163 | 0.077 | 0.249 | 0.165 |
| OpenFashionCLIP | 0.132 | 0.060 | 0.204 | 0.135 |

**Category-to-Product (5 datasets):** Marqo-FashionSigLIP P@1 0.758 / MRR 0.812; base SigLIP-webli P@1 0.690 / MRR 0.751.
**Sub-Category-to-Product (4 datasets):** Marqo-FashionSigLIP P@1 0.767 / MRR 0.811; base SigLIP-webli P@1 0.643 / MRR 0.726.

**Three corrections this forces:**

1. **The "+57 %" headline is measured against FashionCLIP2.0, not against a general model.** 0.121 / 0.077 = +57 % on R@1 — correct, but the comparator is a weaker *fashion-specific* predecessor. Against **its own base model**, ViT-B-16-SigLIP-webli, the same table gives +9.0 % on R@1 (0.121 vs 0.111, one percentage point absolute) and +11.7 % on MRR. The corpus's phrasing "significantly better than general CLIP" reads the headline number as if it were the base-model comparison. It is not.

2. **Absolute text-to-image R@1 is 0.121.** The best fashion-specific open model retrieves the intended garment at rank 1 roughly **one time in eight** from a text query. This is not a fallback path — it is the weakest link in the whole architecture, and it makes principle П2 (deterministic SQL filter first, vector similarity only for ranking within an already-filtered set) load-bearing rather than stylistic.

3. **Item-level and category-level tasks differ by ~6×** in the same table: R@1 0.121 for text→item vs P@1 0.758 for text→category. The model knows what a skirt is; it does not reliably know *which* skirt. Any evaluation that reports category-level accuracy as evidence of retrieval quality is measuring the easy task.

**Contamination check.** LookBench evaluated the same Marqo models on legacy Fashion200K and on its own fresh, time-stamped data. Marqo models reach ~80 % Recall@1 on Fashion200K but 62.8–63.2 % overall on LookBench. Legacy fashion benchmarks are static and their images likely overlap with the web-scale pretraining corpora of the models being tested. **Treat every pre-2026 fashion benchmark number, including Marqo's own card, as an upper bound inflated by contamination.**

**Stronger finding, June 2026 — the ground truth itself is biased, not merely contaminated.** Xue & Xu, *ZooClaw-FashionSigLIP2: Distilled Fine-tuning for Robust Fashion Retrieval*, arXiv:2606.27708, 26 Jun 2026, report that Fashion200K's public ground truth is skewed toward caption-source instances, and re-evaluate it TREC-style with **102,494 pooled held-out judgments**. They release the analysis as a systematic quality audit of widely used fashion benchmarks.

The distinction matters operationally. *Contamination* means the model has seen the test images, so scores are too high but the ranking between models may still hold. *Biased ground truth* means the labels themselves favour a particular retrieval behaviour, so the **ranking between models can be wrong**, not just the absolute level. Six of the six datasets behind Marqo's headline table — Atlas, DeepFashion ×2, Fashion200k, KAGL, Polyvore — are pre-2024 static sets of exactly this family.

*Consequence: the §1.6 numbers stay in this file as the only published figures, but their force drops from `default` to `hint` for anything except order-of-magnitude. The absolute R@1 ≈ 0.121 remains directionally safe because a biased ground truth inflates rather than deflates.*

**Two further results from ZooClaw worth carrying, both independent of its own benchmark.** Its recipe — full fine-tuning with knowledge distillation on curated in-domain data, then WiSE-FT weight interpolation back toward the base checkpoint — reportedly beats (a) LoRA and other parameter-efficient methods, (b) **larger backbones up to 1B parameters**, and (c) augmenting with external data. Point (b) is a third independent observation of the same anti-scaling pattern already seen twice in §1.3 finding 3 (SigLIP2-L < SigLIP2-B; DINOv3-7B < DINOv3-L) and once in LookBench's own scaling study (0.8B adds 0.08 points over 0.3B). **In fashion retrieval, capacity past ~0.3B buys nothing; curation and training recipe buy everything.** 1B is exactly Tianmu-MERE's size.

**Genealogy warning — this is one group, not three.** Siqiao Xue is co-first author of LookBench *and* first author of ZooClaw-FashionSigLIP2. The ZooClaw model is hosted in the `srpone` namespace, the same org that hosts GR-Lite and the LookBench dataset. The ZooClaw-Fashion and H&M numbers on the leaderboard are, by the page's own footnote, taken from the ZooClaw paper rather than re-run by the benchmark maintainers, and the evaluation dataset is not yet released. So LookBench, GR-Pro, GR-Lite, ZooClaw-FashionSigLIP2 and the ZooClaw-Fashion benchmark are **one voice, not five** — the same failure mode recorded elsewhere in the corpus for Gray et al. 2014. Tianmu-MERE (Kuaishou) is the only genuinely external submission on the board, and it is self-reported too.

**On "FashionSigLIP-2, +78 % MRR, commercial."** Verified as stated in the corpus, with one qualification worth recording: the claim appears as a single line at the top of the public model card followed by a link to book a sales demo. There is no published benchmark, no model card, no paper. *Force: `hint`, vendor claim, unverifiable. Correctly excluded from the stack.*

### 1.7 GR-Lite: an open alternative the corpus does not know about

Released alongside LookBench at `huggingface.co/srpone/gr-lite`. Overall fine Recall@1 65.71 vs Marqo-FashionSigLIP 62.77 — **+2.94 absolute over the model currently in the stack table**, and it leads on every subset.

Specification, sufficient to reproduce the decision without the paper:

- Backbone: DINOv3 ViT-L/16 (`facebook/dinov3-vitl16-pretrain-lvd1689m`), 24 layers, 16×16 patches, ~300M params.
- Head: 1024-dim global representation → linear projection → 512-dim, ℓ2-normalised. The 512-d vector is the retrieval embedding.
- **Text-free.** Vision-only, no text tower. Motivation: text encoders in contrastive VLMs bottleneck compositional reasoning (Kamath, Hessel & Chang, arXiv:2305.14897), which is exactly what attribute-and-outfit search needs.
- Loss: ArcFace (m₁=1.0, m₂=0.25, m₃=0.0, s=32) over product identities, with Partial FC for the distributed classifier.
- Training: 1.3M open-source + 0.5M in-house images; AdamW, constant lr 1e-4 (10× for the classifier), global batch 2048, 224×224 inputs.
- Scaling knees, measured: data plateaus at 6.5M images (0.59M→1.82M gives +6.54 points; 11.62M and 21.83M give *slightly worse* results than 6.5M); model plateaus at 0.3B params (0.8B adds 0.08 points).

**Where it breaks.** Text-free means **no text→image path at all**. GR-Lite cannot answer "олива міді А-силует" as a query; it can only answer "find me items visually like this crop." Licence is a DINOv3 derivative and must be read before commercial use — the paper devotes an appendix to it.

**Decision.** The stack line "Embeddings: Marqo-FashionSigLIP ⟂ SigLIP-base" is wrong on both arms. The honest v1 configuration is two *different* models for two *different* jobs:

| Path | Model | Justification |
|---|---|---|
| text → item (compiler spec → candidates) | Marqo-FashionSigLIP | only path with a usable text tower; R@1 ≈ 0.12, so SQL filter must do the heavy lifting. **Not** Tianmu-MERE: its text tower is BGE-base-**zh**. |
| image → item (user photo → candidates) | **GR-Lite** | 60.14 on RealStreetLook vs Tianmu-MERE 58.21 and Marqo-FashionCLIP 56.88. Street photos are the user-selfie case and GR-Lite still leads the open field there. **Blocked pending licence read.** |
| image → item (catalogue packshot → catalogue, e.g. wildcard seed) | Tianmu-MERE *or* GR-Lite | 69.63 vs 68.74 on RealStudioFlat — inside noise. Choose on licence and cost, not score: Tianmu-MERE is Apache-2.0 but 1B params; GR-Lite is ~0.3B with unread terms. |
| control arm for own benchmark | SigLIP2-B/16 | 59.44 — the honest "did fashion tuning buy anything on *our* catalogue" baseline. Not SigLIP2-L (54.84). |

**Licence is now the deciding variable, not accuracy.** The image→image spread across every viable candidate is under two points on the subset that matters and under one point on packshots. That is smaller than the uncertainty of transferring any of these numbers to a Ukrainian feed. Spending further effort ranking them before running one is exactly the kind of reading-instead-of-measuring this file exists to stop. **If GR-Lite's DINOv3 terms turn out to block commercial use, take Tianmu-MERE and lose ~2 points on street; the decision is that cheap.**

### 1.8 VLM attribute extraction: the pattern is confirmed, with a measured accuracy

The corpus described the AutoPKG pattern (schema-constrained JSON, `null` when not confidently visible, no invention) without an accuracy figure. LookBench ran that exact pattern at scale and measured it:

- Model: Qwen2.5-VL-72B.
- Input per item: the garment crop + its category + the category-specific attribute vocabulary.
- Instruction: attend only to the target item; select only attributes clearly supported by visual evidence; return structured JSON with a single `main_attribute` and a list of `other_attributes`; never introduce an attribute outside the supplied vocabulary.
- Audit: GPT-5.1 as independent judge on 200 randomly sampled crops, marking each predicted attribute correct or incorrect from the image alone.
- **Result: ≈93 % per-attribute correctness.**

**Two things this changes.**

1. The corpus's plan — "sample human check of ~100 SKU on start, count per-attribute accuracy" — is right in shape but under-sampled and under-specified. 200 crops with an independent model-judge is the published protocol; ~93 % is the number to beat, not a number to hope for.
2. **Passing the vocabulary in with each call is load-bearing**, not decoration. It is what constrains the output space and makes 93 % achievable. The current VLM prompt spec lists attributes to extract but does not commit to passing a closed per-category vocabulary. That is a concrete change to the enrichment layer.

**Taxonomy scale for reference:** 100+ visually grounded properties, typically 10–25 per category, 27 garment categories. Example vocabularies from the paper — shirt: v-neck, crew neck, button-down, collared, long sleeve, short sleeve, slim/regular/loose fit, cotton, linen, denim, stripe, check, plain, oxford, pocket, formal, casual. Blouse: v-neck, sweetheart, round neck, off-the-shoulder, long/puff/bishop/flared sleeve, silk, chiffon, satin, floral, lace, ruffled, pleated, feminine, elegant. These are directly comparable in grain to the project's canonical dictionary and can be used to check its coverage.

### 1.9 The Qwen3-VL "industry standard" claim: true, but scoped wrongly

**Verified.** MLPerf Inference v6.0 debuts a VLM benchmark using Qwen3-VL-235B-A22B-Instruct (released 23 Sept 2025) with Shopify's Product Catalog dataset (released 12 Dec 2025), for product classification and understanding. Submission deadline 13 Feb 2026; results published 1 Apr 2026. It is the first Qwen-family model in the suite. Dataset: 48,289 multimodal samples of real e-commerce product images paired with text; the model must emit structured JSON; image resolution varies by up to 20×, which stresses the vision encoder and produces highly uneven request sizes.

**Two scope errors in the corpus's use of it.**

1. **The benchmarked model is a 235B mixture-of-experts with 22B active parameters, run on 8×B200 / 8×H200 datacenter GPUs** (Red Hat's submission: 79.04 samples/s offline on 8×B200; 18.22 on 8×H200). The stack table plans "Qwen3-VL локально" on consumer hardware. MLPerf says nothing about the 4B/8B/32B local variants. Using a datacenter benchmark to justify a consumer-GPU deployment is a category error.
2. **MLPerf Inference measures throughput, not extraction accuracy.** It establishes that catalogue→structured-metadata is industrially important enough to standardise, and that Qwen3-VL was chosen as the reference model for it. It does not establish that Qwen3-VL extracts garment attributes well. The 93 % figure in §1.8 is from Qwen2.5-VL-72B and is the only measured accuracy number available.

**Corrected statement.** *The task shape is validated as industry-standard; the specific local model is not. Force: `default` for "catalogue→JSON via VLM is the right architecture"; `hint` for "Qwen3-VL specifically, run locally, is the right model" — untested at that size.*

---

## 2. Що НЕ зроблено

- **Text2Outfit (Amazon) не перевірено.** Це єдина академічна підпора механізму wildcard-first, який стоїть у v1. Не знайдено й не прочитано. Поки що wildcard-first — конвенція проєкту без джерела.
- **arXiv 2409.12150 (DPO на outfit compatibility) не відкрито.** Стоїть у research-беклозі як стартова точка; не верифіковано, що це та стаття.
- **OutfitTransformer, LMLMO, «21–68k курованих сетів Polyvore» не перевірено.** Числа 21k/68k лишаються неперевіреними. Ліцензійний статус Polyvore для комерційного R&D не з'ясовано — а LookBench показує, що Marqo використовує Polyvore як eval-датасет, тож питання живе.
- **Ліцензія GR-Lite не прочитана.** Похідна від DINOv3. Рекомендувати в стек до прочитання не можна. Після ревізії 30.06.2026 це вже не формальність, а **єдина змінна, що вирішує вибір моделі** — див. §1.7.
- **ZooClaw-FashionSigLIP2 не оцінено на image→image.** Вона стоїть у text-image секції лідерборду на власних бенчмарках. Її сильні заяви («leads or ties on every metric of every benchmark in our suite») обмежені їхнім набором базових ліній — Marqo + zero-shot SigLIP2. Проти GR-Pro, GR-Lite чи Tianmu-MERE вона не порівнювалась ніде.
- **Бенчмарк ZooClaw-Fashion не опублікований.** Сторінка каже «буде released shortly» на `srpone/zooclaw-fashion-eval`. Числа text-image секції поки неперевірювані сторонньою особою.
- **Overall для Tianmu-MERE порахований мною, не опублікований.** Метод відтворює GR-Pro і GR-Lite з точністю ±0,05, але це реконструкція. Якщо Gensmo опублікує власний overall — вірити їхньому.
- **Розкид по категоріях для Tianmu-MERE невідомий.** Числа §1.5 (сукні 72,7 проти світшотів 39,7) — з GR-Pro, січень. Чи зберігається двократний розкид у нових моделей, не перевірено, а саме він іде в код як коефіцієнт.
- **Outfit-level для Tianmu-MERE і ZooClaw невідомий.** Стеля 53,2 % лишається з GR-Pro. Це число обмежує продукт сильніше за будь-яке інше у файлі й досі має n=1.
- **Qwen-Image-Edit-2511 не перевірено.** Layout-тестова матриця в темі-9 (розділ 6, ~90 рядків команд) не прогнана жодного разу — це план тесту, а не результат.
- **Alta / Stylitics / Cluise не переперевірено.** Свідомо: провалюють тест before/after.
- **Жодне з чисел вище не виміряно на українському каталозі.** Усі — з англомовних датасетів (студійні пекшоти + вуличні фото Google Images). Чи переносяться вони на Rozetka/Prom-фіди — невідомо.
- **Genealogy.** LookBench — n=1 незалежна група, і вона ж автор моделей-переможців (GR-Pro/GR-Lite). Це конфлікт інтересів того самого класу, що Menlo Ventures у розборі Alta. Числа Marqo-моделей у їхній таблиці — доказ проти власного інтересу (вони показують конкурента сильним), тому надійніші; числа GR-* — самозвіт.

---

## 3. Один фальсифікований наступний крок

**Не читати далі. Прогнати.**

Взяти будь-який один живий український фід (Rozetka або Prom, `feed.py` уже вміє), витягти 200 SKU з категорій, де LookBench дає протилежні прогнози — **сукні/спідниці (очікувано ~73–78 % fine R@1) проти футболок/світшотів (очікувано ~40–45 %)** — і зміряти fine Recall@1 обома моделями (Marqo-FashionSigLIP і SigLIP2-B/16) на завданні image→image: пекшот речі як запит, той самий фід як корпус.

**Прогноз, який можна спростувати:** розрив між «сукня/спідниця» і «футболка/світшот» на українському фіді буде ≥ 20 пунктів fine Recall@1, у той самий бік, що в LookBench.

- **Якщо справджується** — категорійний коефіцієнт довіри йде в `конвеєр.py` як число, і композитор перестає однаково впевнено пояснювати всі слоти.
- **Якщо не справджується** — LookBench не переноситься на UA-каталог, і всі числа цього файлу опускаються до `hint` до власного заміру.

**Той самий прогін, нуль додаткової роботи, дає другий вимір.** Рахуй не лише @1, а @1/@5/@10/@20 — це ті самі ембединги, той самий індекс, один додатковий рядок у скрипті.

**Другий прогноз:** приріст 1→5 буде ≈ +17 пунктів, 5→10 і 10→20 — по ≈ +3,5. Тобто коліно на k = 5.

- **Якщо справджується** — розмір shortlist у `конвеєр.py` фіксується числом (діставати 20, віддавати композитору 5–8), і рядок «≤30 кандидатів» в архітектурі замінюється на виміряний.
- **Якщо крива на UA-фіді плоскіша** — значить український каталог рідший за LookBench-корпус (60k позицій на завдання), і вузьке місце не в моделі, а в покритті асортименту. Це інший діагноз і інший фікс.

Це перший прогін на реальному фіді за весь час проєкту. Він же закриває пункт «end-to-end валідація на реальних речах», який висить у списку без руху. **Ревізія лідерборду за червень нічого в ньому не змінила — розкид між усіма кандидатами менший за невизначеність переносу на UA-каталог. Це і є аргумент, чому далі читати нема сенсу.**
