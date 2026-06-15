# Open Source Stylist: Implementation Blueprint

Дата: 2026-06-15

Цей документ відповідає на практичне питання: які модулі, моделі, бібліотеки,
дані, алгоритми та етапи потрібні, щоб із поточного репозиторію побудувати
завершений локальний Open Source Stylist на RTX 4090 Laptop 16GB.

Він не замінює чинний `BUILD_PLAN.md`, доки власник не затвердить новий напрям.

## 1. Продуктова задача

Вхід:

- одне фото людини;
- короткий текстовий запит;
- опційні обмеження: сценарій, сезон, бюджет, кольори, небажані речі,
  ступінь відкритості, бренди та розміри.

Вихід:

1. Три конкретні outfit-кандидати з реальних речей.
2. Пояснення вибору та точні посилання на речі.
3. Після вибору outfit: візуалізація тієї самої людини.
4. `FidelityReport`, який показує, які речі відтворені точно, а які ні.

Критично зберегти: обличчя, identity, видиму морфологію тіла, тон шкіри,
колір і загальну форму волосся. Фон і поза не є product-critical.

Для речей критичні: category, крій, довжина, силует, колір, принт,
фурнітура, material cues, характерні деталі та layering.

## 2. Цільова архітектура

```text
Photo + UserRequest
        |
        v
PhotoQA + PersonEvidenceExtractor
        |
        +----> IdentityProfile
        +----> StyleEvidence
        |
        v
IntentParser -> StyleIntent
        |
        v
StylePlanner -> 3-5 OutfitBlueprint
        |
        v
CatalogRetrieval -> top-K GarmentItem per slot
        |
        v
OutfitAssembler + ConstraintSolver -> OutfitCandidate[]
        |
        v
User selects one candidate
        |
        v
TryOnPlanner -> board + layer graph + GarmentEvidencePack[]
        |
        v
Holistic Try-On -> base image
        |
        v
PersonFidelity + ItemFidelity + LayeringFidelity
        |
        +---- pass ---------------------> RecommendationBundle
        |
        +---- localized fail -> SingleItemRepair -> re-evaluate
        |
        +---- unrecoverable -> warning / alternate candidate
```

Три підсистеми мають незалежні acceptance tests:

1. `Stylist`: чи доречний і внутрішньо узгоджений outfit.
2. `Catalog`: чи вибрано конкретні валідні речі.
3. `Visualization`: чи збережена людина й точно показані речі.

## 3. Рекомендований стек

### 3.1 Application core

| Задача | Інструмент | Рішення |
|---|---|---|
| Runtime | Python 3.10.x | Залишити поточний runtime, але в окремій `.venv` |
| Environment | `uv` + `uv.lock` | Замість global pip setup |
| Domain models | Pydantic 2 | Типи й JSON Schema з одного джерела |
| CLI | Typer | Команди ingest/analyze/style/try-on/evaluate/run |
| Metadata DB | SQLite | Канонічні item/request/run records |
| Vector index | Qdrant local mode | Derived fashion index, який можна перебудувати |
| Images | Filesystem + SHA-256 manifest | Великі images не зберігати в SQLite |
| Logging | JSONL events + stdlib logging | Відтворюваний provenance |
| Tests | pytest markers | Unit, integration, live-gpu окремо |
| Local UI | Gradio | Alpha UI без окремого frontend |
| Generation | ComfyUI API | Залишити чинний сервер |
| LLM/VLM | LM Studio | Залишити lifecycle API |

Не потрібні Airflow, Celery, Kubernetes або microservices. На одній машині
orchestrator має бути Python state machine з durable run manifest.

### 3.2 Models by role

| Роль | Primary | Fallback/bench |
|---|---|---|
| Intent parsing | Qwen3.5-9B Q4 | поточний Qwen3-VL-8B |
| Person/style semantics | Qwen3.5-9B vision | Qwen3-VL-8B |
| Outfit planning/rerank | Qwen3.5-9B | Qwen3-14B Q4, якщо 9B слабкий |
| Fashion retrieval | Marqo FashionSigLIP | FashionCLIP |
| Generic visual structure | DINOv2 ViT-S/14 | FashionSigLIP features |
| Face identity | InsightFace ArcFace | чинний код |
| Pose | MediaPipe Pose | MMPose RTMPose |
| Detection | GroundingDINO | VLM boxes лише advisory |
| Mask refinement | SAM2 | чинний SAM1 |
| OCR/logo/text | PaddleOCR | VLM advisory |
| Holistic try-on | Qwen-Image-Edit-2511 full | Lightning draft |
| Local repair | QIE-2511 crop-and-stitch | specialized VTO bench |
| Fine-tuning | DiffSynth-Studio QIE-2511 LoRA | інший engine |

Qwen3.5 використовується зі strict structured JSON, temperature 0. FashionSigLIP
і FashionCLIP вибираються за Recall@K на власному каталозі, а не за загальною рекламою.

### 3.3 Що не робити product dependencies

- **OmniTry:** офіційний repository вказує minimum 28GB VRAM. Не локальний executor.
- **FastFit:** non-commercial license. Лише research benchmark після legal review.
- **Sapiens2:** license забороняє biometric processing і deepfake use. Не закладати
  в систему, що прямо працює зі збереженням identity.
- **4DHumans/SMPL:** monocular body shape неоднозначний, SMPL assets мають окремі
  умови. Лише майбутній research track, не foundation V1.

## 4. Нова структура репозиторію

```text
system/
  domain/
    identity_profile.py
    style_intent.py
    style_evidence.py
    garment_item.py
    outfit_blueprint.py
    outfit_candidate.py
    garment_evidence.py
    fidelity_report.py
    recommendation_bundle.py
  analysis/
    photo_qa.py
    face.py
    pose.py
    masks.py
    appearance.py
    person_analyzer.py
  catalog/
    db.py
    ingest.py
    item_analyzer.py
    evidence_builder.py
    availability.py
  retrieval/
    encoder.py
    qdrant_index.py
    search.py
    benchmark.py
  stylist/
    intent_parser.py
    blueprint_planner.py
    rules.py
    candidate_generator.py
    constraint_solver.py
    reranker.py
  tryon/
    planner.py
    holistic.py
    repair.py
    compositor.py
  evaluation/
    person_fidelity.py
    item_fidelity.py
    layering.py
    aggregate.py
  orchestration/
    resource_manager.py
    run_store.py
    pipeline.py
  ui/
    app.py

catalog/items/<item_id>/
  item.json
  source/
  normalized/
  details/
  masks/
  manifest.json

benchmarks/
  tryon_v1/
  stylist_v1/
  retrieval_v1/

runs/<run_id>/
  request.json
  person/
  stylist/
  tryon/
  evaluation/
  manifest.json
  events.jsonl
```

Pydantic models мають генерувати JSON Schema. Committed schema лишається artifact,
а тест перевіряє, що вона не розійшлася з Python type.

## 5. Domain contracts

### `IdentityProfile`

```text
person_id
source_image_sha256
face_embedding_ref
face_bbox
face_landmarks
hair_mask_ref
skin_mask_ref
pose_keypoints
visible_body_regions
photo_quality
identity_constraints
confidence_by_field
```

Face embedding не зберігати поза run за замовчуванням: це biometric artifact.

### `StyleEvidence`

```text
observable_only
skin_palette_lab + confidence
hair_palette_lab + confidence
appearance_contrast + confidence
visible_proportion_features + confidence
current_visual_style
photo_limitations[]
```

Не зберігати оцінні ярлики типу `body type = pear` як істину. Зберігати
вимірювані спостереження та uncertainty.

### `StyleIntent`

```text
scenario
season
weather_range
mood[]
style_tags[]
formality_range
budget
preferred_colors[]
excluded_colors[]
required_items[]
excluded_items[]
coverage_constraints
brand_constraints
size_constraints
hard_constraints[]
soft_preferences[]
assumptions[]
clarification_needed
```

### `GarmentItem`

```text
item_id, catalog_id, sku, title, brand, source_url
category, subcategory, colors_lab, pattern, material
silhouette, fit, length, season_tags, formality, style_tags
price, currency, sizes[], availability
reference_views[], critical_details[], layer_roles[]
embedding_refs, evidence_quality, source metadata, hashes
```

`critical_details` для blouse може містити `V neckline`, `central button row`,
`voluminous sleeves`, `peplum hem`. Evaluator зобов'язаний їх перевірити.

### `GarmentEvidencePack`

```text
item_id
canonical_front
canonical_back?
detail_crops[]
item_masks[]
palette
silhouette_mask
critical_details[]
unobserved_regions[]
source_quality_flags[]
hashes
```

Якщо back view відсутній, система не обіцяє exact back visualization.

### `OutfitBlueprint`

```text
blueprint_id, intent_id, concept_summary
slots[], palette_roles, silhouette_plan, material_plan
layer_graph, formality, season, reasoning_claims[]
```

Slot описує потребу, а не SKU: наприклад `structured V-neck blouse with waist
emphasis and medium visual volume`.

### `OutfitCandidate`

```text
candidate_id, blueprint_id, item_ids_by_slot
hard_constraint_verdicts, pairwise_compatibility, layer_graph
retrieval_scores, stylist_score, rationale, warnings[]
```

### `FidelityReport`

```text
person:
  face_identity, hair_color, hair_shape, skin_tone
  pose_geometry, body_shape_advisory
items[item_id]:
  presence, category, target_retrieval_rank
  silhouette, palette, pattern, material_advisory
  critical_details{}, layering, verdict, failure_reasons[]
whole_outfit_verdict
repairable_failures[]
unmeasured_risks[]
```

## 6. Person analysis: конкретна реалізація

### 6.1 `photo_qa.py`

До будь-якого styling виконуються детерміновані перевірки:

1. Decode, EXIF orientation, resolution і color profile.
2. Рівно одна dominant person detection.
3. Face detected і достатнього розміру.
4. Видима необхідна частина тіла залежно від requested outfit.
5. Blur та exposure score.
6. Occlusion flags.

Якщо користувач просить взуття, але ноги відсутні, UI просить full-body photo.
Фон не перевіряється як критична властивість.

### 6.2 Identity anchors

- InsightFace: face embedding і detection confidence.
- MediaPipe: face/pose landmarks.
- GroundingDINO + SAM2: face, hair, exposed skin і person masks.
- OpenCV/skimage: LAB distributions усередині eroded masks.

Skin/hair color не брати з VLM text. Обчислювати distribution після:

- erosion mask для видалення меж;
- rejection highlights і deep shadows;
- color clustering;
- confidence з mask area та illumination spread.

### 6.3 Style evidence

Qwen3.5 vision отримує фото й детерміновані measurements та повертає schema JSON:

- тільки видимі особливості;
- можливі color/silhouette directions;
- uncertainty;
- жодних категоричних тверджень "вам не личить".

VLM suggestion входить лише в soft ranking і не перекриває user preference.

### 6.4 Body preservation

Перша версія має два режими.

`controlled`: поза близька до input; порівнюються pose landmarks, exposed-body
geometry і human labels. Це benchmark та перший alpha.

`free_pose`: поза може змінитися; 2D silhouette width вимикається як body verdict.
Залишаються identity conditioning, coarse morphology evidence та explicit uncertainty.

Не заявляти точне збереження 3D body shape з одного фото, поки окремий інструмент
не відкалібрований на consented multi-view data.

## 7. Catalog: від товарного фото до `GarmentItem`

### 7.1 Curated catalog first

Не починати з web-scale scraping. Перший catalog: 120-200 перевірених речей,
приблизно 20-30 на ключову категорію:

- tops;
- bottoms;
- dresses;
- outerwear;
- shoes;
- bags;
- belts;
- jewelry.

Цього достатньо для retrieval і outfit assembly, але дані ще можна перевірити вручну.

### 7.2 Ingestion pipeline

```text
stylist catalog ingest catalog_source.csv --images catalog/raw
```

Для кожної речі:

1. Перевірити URL/files і порахувати hashes.
2. Нормалізувати orientation і color profile.
3. Виявити garment box з урахуванням known category.
4. GroundingDINO повертає boxes; deterministic selector обирає один.
5. SAM2 створює одну mask для обраного box.
6. Побудувати transparent canonical front.
7. Витягти detail crops у source resolution.
8. Qwen3.5 vision пропонує structured attributes.
9. Validator перевіряє vocabulary і ranges.
10. Людина підтверджує перший catalog та low-confidence fields.
11. FashionSigLIP embedding записується в Qdrant.

Не повторювати E-007: ніколи не union усі detections. Selection policy враховує
category, centrality, area, confidence та exclusion zones для face/skin.

### 7.3 Evidence quality gate

Item не допускається до exact visualization, якщо:

- garment займає надто малу частину reference;
- mask перетинає лице/шкіру product model;
- critical front view відсутня;
- source розмитий або надто малий;
- category confidence низька;
- hashes/source metadata відсутні.

Слабкий item може залишатися searchable, але visualization повертає warning або
пропонує альтернативний товар із кращими references.

### 7.4 Source of truth

- SQLite: item metadata, price, size, availability, timestamps.
- Filesystem: images, masks, detail crops, manifests.
- Qdrant: derived embeddings + `item_id` payload.
- Rebuild command повністю відновлює vector index.

## 8. Stylist: конкретний алгоритм

### 8.1 Intent parsing

Qwen3.5-9B отримує user text і повертає `StyleIntent` при temperature 0.
Після LLM validator:

- нормалізує scenario/season vocabulary;
- перевіряє budget;
- розділяє hard і soft constraints;
- знаходить конфлікти;
- визначає, чи потрібне одне уточнення.

### 8.2 Blueprint generation

LLM не вибирає SKU. Воно створює 3-5 структурно різних `OutfitBlueprint`:

- required slots;
- silhouette roles;
- palette roles;
- materials/season;
- layer graph;
- rationale claims.

### 8.3 Retrieval per slot

Для кожного slot:

1. Hard filter: category, availability, budget, size, season, exclusions.
2. FashionSigLIP text query, top 30.
3. Optional image query.
4. Attribute rerank, top 8-12.
5. Зберегти scores і причини відсіву.

FashionSigLIP або FashionCLIP вибирається за `Recall@10` на власному test set.

### 8.4 Outfit assembly

Не створювати повний Cartesian product. Використати beam search:

```text
beam size: 50
slot order: anchor -> top/bottom -> outerwear -> shoes -> accessories
after each addition:
  reject hard constraint violations
  score partial outfit
  keep best 50 diverse partial sets
```

Hard checks у Python:

- required slots complete;
- layer graph acyclic;
- season і formality compatible;
- budget not exceeded;
- forbidden colors/categories absent;
- availability/size valid;
- dress не конфліктує з top+bottom blueprint;
- outerwear/hem/layer rules виконані.

Початкова soft-score конфігурація:

```text
0.25 request-to-item relevance
0.20 scenario/season/formality fit
0.15 palette harmony
0.15 silhouette-plan fit
0.10 material compatibility
0.10 person StyleEvidence fit
0.05 user preference/history
```

Це product hypothesis. Weights зберігаються в config і змінюються лише після
labeled stylist benchmark.

### 8.5 LLM rerank і diversity

Qwen3.5 отримує максимум 10 готових sets з attributes, а не весь catalog.
Воно оцінює checklist і пояснює claims. Hard verdict LLM не може переписати.

Фінальні три candidates обираються через maximal marginal relevance, щоб вони
відрізнялися silhouette, palette й anchor item.

### 8.6 Feedback before generation

Користувач вибирає outfit або замінює одну річ до expensive visualization. Це:

- економить GPU;
- дає preference signal;
- відділяє помилку Stylist від помилки Try-On.

## 9. Try-on: двопрохідна архітектура

### 9.1 `TryOnPlanner`

Вхід: `IdentityProfile`, `OutfitCandidate`, `GarmentEvidencePack[]`.

Вихід:

- layer graph;
- composition board;
- high-resolution evidence per item;
- items для holistic pass;
- items для protected local pass;
- prompts, masks та expected visibility.

### 9.2 Розподіл речей

Holistic pass:

- top + bottom;
- dress;
- outerwear;
- великі взаємно перекриті garments.

Local pass candidates:

- shoes;
- bag;
- belt;
- earrings/jewelry;
- logos;
- buttons/buckles;
- локальні pattern/detail failures.

Це узагальнена чинна Strategy C, але рішення приймається item policy, а не вручну
для одного outfit.

### 9.3 Composition board

Board передає загальний outfit, labels, layer relations і visual balance.
Вона не є єдиним evidence source. Для кожної речі зберігаються full-resolution views.

Board builder повинен:

- не перезаписувати frozen asset;
- бути content-addressed;
- хешувати всі inputs;
- зберігати mapping cell -> item/view;
- давати anchor garments більше площі;
- підтримувати кілька boards при engine limits.

### 9.4 Holistic generation

Primary configurations:

1. Lightning 4-step: drafts.
2. Full QIE-2511, 20 steps, calibrated cfg: final baseline.
3. Full 40 steps: лише якщо 20 -> 40 дає measured gain.

Перед bench:

- `cfg`, sampler, scheduler, positive і negative доходять до workflow;
- після fill не лишаються placeholders;
- exact filled workflow зберігається;
- model/workflow/input hashes входять у run manifest.

### 9.5 Local repair

Для failed item:

1. Взяти generated item mask.
2. Розширити bbox на 15-25% context.
3. Crop image і mask.
4. Resize crop до engine resolution зі збереженням aspect ratio.
5. Передати crop + один evidence pack + critical-details prompt.
6. Generate repaired crop.
7. Composite назад через feathered target mask.
8. Перевірити outside-mask drift, identity і сусідні items.
9. Прийняти repair лише після незалежного покращення fidelity.

Для structural change mask може розширюватися. Тоді треба перерахувати сусідні
garment masks і повторно перевірити layer graph.

### 9.6 Retry policy

```text
max holistic attempts: 3
max repairs per item: 2
max generation calls: configurable, default 10
```

| Failure | Action |
|---|---|
| face identity fail | reject base; new seed/full model; face restore лише при compatible pose |
| missing large garment | regenerate holistic pass |
| wrong layering | regenerate з revised layer evidence |
| wrong shoes/accessory | local single-item pass |
| wrong color only | local repair; deterministic correction лише після independent A/B |
| wrong logo/buttons/detail | detail-focused local repair |
| body drift | reject base; не маскувати score postprocess |
| insufficient evidence | replace item/reference або warning |

## 10. Fidelity evaluation

Жодна окрема метрика не вирішує задачу. Потрібен ensemble із reason-coded output.

### 10.1 Person fidelity

Face:

- ArcFace cosine;
- face confidence;
- landmark sanity;
- human same-person labels для calibration.

Поточний threshold не переносити автоматично. Побудувати ROC на більшій вибірці
same/different/generated pairs.

Hair:

- mask presence/shape advisory;
- LAB distribution distance;
- VLM checklist: color/length/style changed?

Skin:

- exposed-skin masks;
- robust LAB distribution distance;
- окремий global illumination estimate;
- не один mean pixel value.

Body:

- controlled mode: pose-normalized landmarks + exposed contour;
- free-pose mode: advisory до calibration shape estimator;
- owner label є benchmark ground truth.

### 10.2 Item fidelity

Для кожної речі:

1. Segment generated item crop.
2. Category/presence verdict.
3. FashionSigLIP retrieval проти target SKU та same-category decoys.
4. DINOv2 coarse structural similarity.
5. Mask silhouette descriptors: aspect, contour, length/width.
6. Palette distribution/EMD.
7. Pattern/texture advisory features.
8. PaddleOCR/logo comparison, якщо critical.
9. Qwen structured checklist по `critical_details`.
10. Human item verdict у calibration і holdout.

`target_retrieval_rank` важливіший за raw cosine. Без decoys високий cosine не доводить,
що результат схожий саме на target item.

### 10.3 Layering fidelity

Layer graph є truth source. Evaluation перевіряє expected relations:

```text
belt occludes blouse at waist
blouse overlaps skirt waistband
outerwear occludes top at torso
```

Mask geometry використовується там, де relation видиме. VLM оцінює ambiguous cases
лише після agreement calibration.

### 10.4 Whole-outfit verdict

Не використовувати середній score:

```text
PASS only if:
  person critical checks pass
  AND every required visible item passes
  AND every required layer relation passes
```

Optional або повністю occluded items отримують окремий status.

### 10.5 Repair acceptance

Repair приймається лише якщо:

- target item покращився;
- жоден passed item не став fail;
- person identity не погіршилася;
- outside allowed region drift нижче calibrated limit.

## 11. Benchmark design

### 11.1 Smoke set

- 3 consented people;
- 3 outfits;
- 3-5 items each;
- solid, patterned, structured garment, shoes, small accessory;
- однакова поза для controlled diagnosis.

Дев'ять cases достатньо для відсіву слабкої architecture, але не для promotion.

### 11.2 Development set

- 5 people;
- 6 outfits;
- 30 person-outfit cases;
- різні skin/hair/body appearances;
- 3, 5 та 7+ items;
- clean та imperfect references;
- controlled і free-pose subsets.

### 11.3 Frozen holdout

- щонайменше 20 unseen cases;
- не використовувати для prompt/threshold tuning;
- owner labels записувати до перегляду aggregate metrics.

### 11.4 Item evaluator calibration

Щонайменше 200 labeled crops:

- exact/acceptable target;
- correct category but wrong SKU;
- correct color but wrong shape;
- correct shape but wrong print/detail;
- missing/occluded;
- same-category hard decoys.

### 11.5 Stylist benchmark

30-50 requests із зафіксованими constraints:

- hard constraint pass rate;
- top-3 acceptability;
- diversity;
- availability correctness;
- pairwise owner preference;
- explanation factuality.

## 12. Запропоновані decision gates

Це product gates для затвердження до benchmark, а не універсальні наукові пороги.

Retrieval MVP:

- known-item image query: target top-1 >= 95%;
- text/attribute query: relevant item top-10 >= 90%;
- unavailable item після hard filter: 0.

Stylist MVP:

- hard constraints: 100%;
- хоча б один top-3 outfit прийнятний: >= 80% requests;
- factual explanations: >= 98%;
- candidates materially diverse: >= 90% requests.

Try-on feasibility:

- human face/identity acceptance: >= 95%;
- all required items present: >= 95%;
- whole-outfit acceptance after bounded repair: >= 70% development;
- product alpha target: >= 80% frozen holdout;
- accepted repairs із видимою outside-region regression: 0;
- unrecoverable result ніколи не маскується як pass.

Architecture kill criteria після holistic + local-repair bench:

- `<40%` whole-outfit acceptance: off-the-shelf local stack непридатний;
  перейти до fine-tuning/new engine, не prompt tuning.
- `40-70%`: architecture перспективна, але fine-tuning імовірно потрібний.
- `>=70%`: інтегрувати alpha й усувати dominant residual defects.

## 13. Development plan

### WP0: Stabilize the laboratory

Мета: зробити чинні результати придатними для наступних рішень.

Роботи:

1. Remote/backup перед Git cleanup.
2. Прибрати GPU side effects із pytest collection.
3. Створити `.venv`, `pyproject.toml`, lockfile, Python pin.
4. Провести cfg/sampler/scheduler/negative у workflow.
5. Заборонити unresolved placeholders.
6. Один command для exact manual-outfit run.
7. Run manifest із hashes та filled workflow.
8. Позначити superseded/confounded experiments.

Acceptance:

- `pytest` не запускає generation;
- 100% request params видно у saved workflow;
- run переносимий відносними paths;
- однаковий run spec створює однаковий engine request.

Оцінка: 3-5 focused engineering days.

### WP1: Product contracts and data layout

Роботи:

1. Додати Pydantic models із розділу 5.
2. Мігрувати `outfit_001` у `GarmentItem` і `GarmentEvidencePack`.
3. Створити SQLite schema та artifact store.
4. Додати schema drift tests.
5. Визначити privacy policy для photos/face embeddings.

Acceptance:

- `outfit_001` не залежить від free-text-only critical semantics;
- кожний artifact має lineage/hash;
- invalid SKU/availability/layer graph не проходять validation.

Оцінка: 4-6 days.

### WP2: Correct Try-On Feasibility Gate

Роботи:

1. Побудувати smoke benchmark 3x3.
2. Додати item-level decoy evaluation.
3. Реалізувати QIE holistic baseline.
4. Реалізувати high-res single-item crop-and-stitch repair.
5. Порівняти:
   - board-only;
   - board + repair;
   - holistic clothing + local accessories;
   - один product-compatible specialized alternative, якщо є.
6. Застосувати kill criteria.

Acceptance:

- рішення приймається за whole-outfit pass rate;
- repair locality measured;
- є чіткий verdict: off-the-shelf або fine-tune.

Оцінка: 10-15 engineering days плюс GPU batches.

Це найвищий пріоритет після WP0-WP1.

### WP3: Person Analysis MVP

Роботи:

1. Photo QA.
2. ArcFace identity anchor.
3. MediaPipe pose.
4. GroundingDINO + SAM2 hair/skin/person masks.
5. LAB distributions.
6. Qwen observable `StyleEvidence`.
7. Confidence та limitations.

Acceptance:

- photo rejection reasons зрозумілі;
- deterministic measurements відтворювані;
- VLM output schema-valid;
- low-confidence fields не є hard styling rules.

Оцінка: 5-8 days.

### WP4: Curated Catalog MVP

Роботи:

1. Підготувати 120-200 items із source/license metadata.
2. Реалізувати ingestion/evidence pipeline.
3. Додати human approval UI/command.
4. Порівняти FashionSigLIP і FashionCLIP.
5. Побудувати Qdrant index.
6. Запустити retrieval benchmark.

Acceptance:

- кожний active item має valid evidence pack;
- retrieval досягає MVP gates;
- index rebuildable;
- availability не вигадується VLM.

Оцінка: 7-12 engineering days плюс підготовка даних.

### WP5: Stylist MVP

Роботи:

1. StyleIntent parser.
2. OutfitBlueprint planner.
3. Per-slot retrieval.
4. Beam-search assembly.
5. Deterministic constraints.
6. Qwen rerank.
7. Diversity selector.
8. Owner benchmark UI.

Acceptance:

- hard constraints 100%;
- top-3 acceptability target;
- rationale посилається лише на наявні attributes;
- заміна одного item не перезапускає незалежні stages.

Оцінка: 7-12 days.

### WP6: Integrated Alpha

```text
upload photo
-> enter request
-> see 3 exact outfits
-> replace one item if needed
-> select outfit
-> generate visualization
-> see fidelity warnings and links
```

Роботи:

1. Orchestrator state machine.
2. VRAM resource manager.
3. Gradio UI.
4. Resume/cancel.
5. Structured errors.
6. User feedback storage.

Acceptance:

- повний flow без ручного JSON;
- failure не втрачає run state;
- lineage доступний;
- replace-one-item перезапускає лише залежні stages.

Оцінка: 7-10 days.

### WP7: Fine-tuning, only if triggered

Trigger: WP2 не проходить feasibility bar через systematic item-identity/detail loss,
але local repair показує правильний напрям.

Роботи:

1. License review dataset/model.
2. Garments2Look-style tuples -> QIE edit training format.
3. Frozen split за people та outfits.
4. Train task LoRA через DiffSynth-Studio QIE-2511 script.
5. Не fine-tune на holdout SKU/person.
6. Порівняти whole-outfit acceptance.

Практично:

- inference залишається local;
- training планувати на rented Linux GPU 48-80GB;
- official script має CPU offload, але 16GB local training не робити основним планом.

Acceptance:

- material gain на frozen holdout;
- identity не погіршилась заради garment fidelity;
- gains переносяться на unseen categories.

## 14. Паралельність робіт

Після WP0:

```text
Track A: Try-On feasibility
  WP1 -> WP2 -> [WP7 if needed]

Track B: Product intelligence
  WP1 -> WP3 -> WP4 -> WP5

Both -> WP6 Integrated Alpha
```

Track B створює curated product skeleton, а не web-scale system. Якщо try-on провалиться,
catalog/stylist робота не втрачена, але exact visualization не можна обіцяти.

## 15. VRAM schedule for 16GB

```text
1. Load Qwen3.5 in LM Studio
   intent, person semantics, blueprint, rerank
2. Unload LM Studio
3. Load FashionSigLIP/DINO if needed
4. Release retrieval models
5. Run QIE in ComfyUI
6. POST /free
7. Run ArcFace / pose / GroundingDINO + SAM2 sequentially
8. Optional Qwen advisory evaluation
9. Unload
```

Catalog embeddings обчислюються offline, тому runtime retrieval майже не потребує GPU.

Resource manager логує model, load/unload time, provider, VRAM before/after та cleanup.

## 16. Безпосередньо наступні роботи

Не великий sampler bench і не Stage 3 VLM calibration. Спочатку:

1. Захистити pytest і runner reproducibility.
2. Виправити contract -> workflow parameters.
3. Додати `GarmentEvidencePack` для чинних п'яти речей.
4. Додати 20-50 same-category decoys для кожної категорії.
5. Побудувати item retrieval-rank evaluator.
6. Реалізувати один high-resolution local repair на shoes.
7. Повторити для blouse buttons/silhouette та earrings texture.
8. Порівняти board-only проти board + repair на тих самих seeds.
9. Додати ще дві consented людини й два outfits до smoke set.
10. Прийняти рішення: off-the-shelf architecture чи task LoRA.

Лише після пункту 10 варто витрачати великий час на shell, складний orchestrator
або широку engine config matrix.

## 17. Зовнішні першоджерела

- Qwen3.5-9B: https://huggingface.co/Qwen/Qwen3.5-9B
- Qwen3.6 repository: https://github.com/QwenLM/Qwen3.6
- LM Studio structured output: https://lmstudio.ai/docs/developer/core/structured-output
- FashionSigLIP: https://github.com/marqo-ai/marqo-FashionSigLIP
- FashionSigLIP model: https://huggingface.co/Marqo/marqo-fashionSigLIP
- Qdrant local mode: https://qdrant.tech/documentation/frameworks/langchain/
- DINOv2: https://github.com/facebookresearch/dinov2
- MediaPipe Pose: https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker
- GroundingDINO: https://github.com/IDEA-Research/GroundingDINO
- SAM2: https://github.com/facebookresearch/sam2
- MMPose: https://github.com/open-mmlab/mmpose
- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- Qwen-Image: https://github.com/QwenLM/Qwen-Image
- QIE-2511 LoRA script: https://github.com/modelscope/DiffSynth-Studio/blob/main/examples/qwen_image/model_training/lora/Qwen-Image-Edit-2511.sh
- FastFit and license: https://github.com/Zheng-Chong/FastFit
  and https://github.com/Zheng-Chong/FastFit/blob/main/LICENSE.md
- OmniTry: https://github.com/KiseKloset/OmniTry
- Sapiens2 and license: https://github.com/facebookresearch/sapiens2
  and https://github.com/facebookresearch/sapiens2/blob/main/LICENSE.md
- Garments2Look: https://arxiv.org/html/2603.14153v1
- HumanGPS: https://arxiv.org/html/2405.00627v1

## 18. Підсумкове рішення

Базова конструкція:

```text
structured stylist planning
+ deterministic catalog constraints
+ fashion-specific retrieval
+ holistic outfit generation
+ full-resolution per-item evidence
+ reason-coded item evaluation
+ protected local repair
+ bounded retry and honest uncertainty
```

Найближче технічне питання звучить не "який cfg кращий", а:

> Чи може QIE-2511 у схемі holistic board + high-resolution single-item repair
> пройти whole-outfit fidelity gate на кількох людях і outfits?

Відповідь визначить наступний великий крок: integrated alpha, task LoRA або зміна
engine/product promise.
