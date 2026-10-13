# Концептуальний та продуктовий розбір Open Source Stylist

Дата: 2026-06-15

## 1. Виправлений вердикт

Попередня відповідь була надто загальною. Після трасування вимог до фактичного дизайну,
контрактів, експериментів і артефактів висновок такий:

1. **Почати з try-on було логічно.** Точне відтворення конкретного багатокомпонентного
   outfit є екзистенційним технічним ризиком продукту. Якщо це неможливо на доступному
   open-source стеку, складний Stylist і retrieval не врятують продукт.
2. **Поточний шлях у незміненому вигляді не приведе до завершеної системи.** Він може
   привести до локального дослідного try-on runner, але не перевіряє дві інші головні
   функції: персональне стилістичне рішення та вибір конкретних речей.
3. **Навіть try-on трек зараз оптимізує неповну ціль.** Він добре перевіряє identity face,
   приблизний колір і presence/layering, але не перевіряє identity речі: крій, характерні
   деталі, принт, фактуру, фурнітуру та SKU-level впізнаваність.
4. **Загальна генеративна стратегія в дизайні напрямково правильна:** holistic outfit pass
   для композиції і layering, потім single-item local repair. Помилка не в самій ідеї,
   а в тому, що тимчасова 768x768 reference board зараз одночасно виконує роль карти
   outfit і носія точних деталей.
5. **Потрібно не кидати поточний трек, а перевизначити його як короткий Try-On Feasibility
   Gate**, змінити benchmark і критерії, а паралельно зафіксувати архітектуру Stylist та
   curated catalog vertical slice.

## 2. Трасування кінцевих вимог

Кінцева задача:

```text
вхід: фото людини + короткий запит (стиль, сценарій, сезон, настрій)
вихід: конкретний рекомендований outfit + фото тієї самої людини в ньому
критично: обличчя, морфологія тіла, тон шкіри, волосся, точність конкретних речей
```

| Вимога | Що є зараз | Фактичний стан |
|---|---|---|
| Прийняти фото | `PersonProfile`, person asset | Частково: є input, немає analyzer |
| Прийняти стильовий запит | Описаний лише прозою для V2 | Немає schema, parser або tests |
| Визначити, що личить | `PersonProfile` описує збереження | Немає моделі стилістичного рішення |
| Скласти outfit | V1 отримує manual `OutfitPackage` | Рішення людини, не системи |
| Вибрати конкретні речі | Retrieval відкладений до V2 | Немає catalog/index/ranking |
| Перевірити availability/size | Полів немає | Не моделюється |
| Зберегти обличчя | ArcFace gate | Частково, калібрування слабке |
| Зберегти волосся | Лише текст у prompt | Не вимірюється |
| Зберегти тон шкіри | Лише текст у prompt/profile | Не вимірюється |
| Зберегти морфологію тіла | Silhouette widths | Метрика вимірює одягнену фігуру, не тіло |
| Точно відтворити кожну річ | Delta-E + VLM presence | Identity речі не вимірюється |
| Побудувати завершений loop | Orchestrator запланований | Не реалізований |

Початкова продуктова вимога збережена в `PROJECT_LEDGER.md:76-126`. Проте поточний
`BUILD_PLAN.md:458-461` явно виносить garment retrieval і wardrobe за межі V1, а V1
definition of done у `BUILD_PLAN.md:429` починається вже з готового `outfit package`.
Тобто V1 у документах є **Try-On V1**, а не **Open Source Stylist V1**.

## 3. Чому поточні контракти не описують продукт

Наявний ланцюг об'єктів добре описує редагування зображення:

```text
PersonProfile -> OutfitPackage -> GenerationRequest -> GenerationResult
              -> RegionMap -> EvaluationVerdict -> FinalOutput
```

Але між аналізом людини й готовим outfit відсутній весь процес прийняття рішення.

### Відсутні об'єкти

1. `StyleIntent`
   - scenario, season, mood, desired style;
   - hard constraints і soft preferences;
   - budget, dislikes, coverage, dress code;
   - inferred defaults та uncertainty.
2. `OutfitBlueprint`
   - потрібні slots/categories;
   - silhouette goals;
   - palette roles;
   - materials;
   - layer graph;
   - формальність і сезонність.
3. `GarmentItem`
   - catalog/SKU ID;
   - seller/source URL;
   - category, attributes, material, dimensions;
   - price, sizes, availability;
   - reference views, masks, detail crops;
   - evidence quality і unobserved details.
4. `OutfitCandidate`
   - concrete item IDs;
   - blueprint coverage;
   - internal compatibility;
   - hard-constraint verdict;
   - recommendation rationale.
5. `FidelityReport`
   - identity людини по окремих осях;
   - fidelity кожної речі по окремих ознаках;
   - outfit-level all-required-items verdict.
6. `UserFeedback`
   - вибраний/відхилений outfit;
   - причина;
   - заміна конкретної речі;
   - preference memory.

Поточний `PersonProfile` (`system/contracts/person_profile.json`) є preservation profile,
а не style profile. У ньому немає user preference, confidence або зв'язку між
спостереженням і рекомендацією. Поточний `OutfitPackage` починається вже з остаточного
списку речей і не містить SKU, material, fit, size, price, availability або critical
visual details.

## 4. Що насправді означає "визначити, що личить"

Це не одна VLM-функція. Треба розділити п'ять різних типів сумісності:

1. **Контекстна:** чи відповідає outfit сценарію, сезону, погоді та dress code.
2. **Візуальна:** як palette, contrast, silhouettes і proportions взаємодіють із
   видимою зовнішністю людини.
3. **Внутрішня сумісність outfit:** чи речі узгоджені між собою.
4. **Смак користувача:** що людина справді хоче носити.
5. **Фізичний fit:** чи річ підійде за розміром і посадкою.

З одного фото і короткого запиту можна більш-менш оцінити 1-3. Не можна надійно знати 4
без feedback/history і не можна гарантувати 5 без вимірів людини, size chart та даних про
конкретну річ. Це інформаційне обмеження, не проблема вибору LLM.

Тому перший реліз має формулювати обіцянку чесно:

> Візуально та контекстно сумісна рекомендація конкретних речей, а не гарантія фізичної
> посадки чи об'єктивний вирок про те, що людині "личить".

Система повинна генерувати кілька різних кандидатів і вчитися з вибору користувача,
замість удавати, що є одна об'єктивно правильна відповідь.

## 5. Чи правильна поточна try-on стратегія

### Що правильне

- Holistic pass краще підходить для взаємного layering великих речей, ніж незалежне
  послідовне надягання кожної речі.
- Reference board є корисною outfit-level композиційною умовою.
- Single-item local repair з повнорозмірним референсом логічний для взуття, аксесуарів,
  фурнітури й локальних дефектів.
- Strategy C у `SYSTEM_DESIGN.md:423-436` рухається в правильному напрямку: holistic
  clothing + protected accessory passes.
- Fine-tuning на outfit-level даних уже названий у `SYSTEM_DESIGN.md:535-537`; це не
  випадкова запасна ідея, а ймовірний необхідний quality lever.

### Що неправильне або недостатнє

#### 5.1 Reference board стала інформаційним bottleneck

Hybrid board має 768x768 і дев'ять комірок. Кожний reference стискається до максимуму
256x234 (`prepare_reference_boards.py:34,36,134`). Реальне стиснення:

| Reference | Source/crop | У board | Залишок пікселів |
|---|---:|---:|---:|
| blouse front | 612x685 | 209x234 | 11.67% |
| skirt front | 1920x1651 | 256x220 | 1.78% |
| belt | 1365x2048 | 156x234 | 1.31% |
| shoes | 1219x865 | 256x182 | 4.41% |
| earrings | 513x328 | 256x164 | 24.90% |

Це пояснює систематичну втрату buttons, shoe geometry, texture та дрібної фурнітури.
Board не треба прибирати. Треба змінити її роль:

```text
board = outfit composition/layering evidence
full-resolution item pack = item identity/detail evidence
```

#### 5.2 Поточний evaluator не вимірює "це та сама річ"

Delta-E може сказати, що область приблизно того самого кольору. Presence може сказати,
що на ногах є взуття. Жодна з цих перевірок не відрізняє конкретні wedge sandals від
інших зелених босоніжок.

Для кожної речі потрібні окремі осі:

- category/presence;
- silhouette і довжина;
- neckline/sleeve/closure;
- palette;
- pattern/logo/text;
- material/texture cue;
- named critical details;
- catalog identity retrieval rank;
- layering/occlusion relation.

Практичний автоматичний тест: crop згенерованої речі використовується як query проти
цільового SKU та набору візуально схожих catalog decoys. Якщо цільова річ не повертається
у top-K, item fidelity підозріла. Це не замінює human review, але набагато ближче до
продуктової вимоги, ніж середній колір.

#### 5.3 Успіх треба рахувати на рівні всього outfit

Для продукту середній score неприйнятний. Формула має бути:

```text
try_on_pass = person_identity_pass
              AND body_identity_pass
              AND hair_skin_pass
              AND layer_graph_pass
              AND ALL(required_item_pass)
```

Якщо кожна з п'яти речей відтворюється правильно з імовірністю 90%, і помилки умовно
незалежні, повний outfit проходить лише з імовірністю `0.9^5 = 59%`. Для 80% успіху
повного outfit кожна з п'яти речей має проходити приблизно у 95.6% випадків; для восьми
речей потрібно приблизно 97.2%. Це пояснює, чому per-item repair і суворий whole-outfit
verdict не є косметичними доповненнями.

#### 5.4 Body preservation не вирішено

Поточна метрика бере ширину одягненого person silhouette. Але новий одяг законно змінює
silhouette. Вона не може відділити body drift від peplum, широкого рукава чи об'ємної
спідниці.

Для controlled benchmark спочатку варто тримати позу сталою і порівнювати:

- pose/keypoint geometry;
- exposed body landmarks;
- estimated body-shape representation з confidence;
- human same-body-shape verdict.

Якщо production дозволяє нову позу, source-pixel face restore і 2D width comparison вже
не є загальним рішенням. Потрібне identity conditioning та переносима body-shape
representation; deterministic compositing залишається лише спеціальним режимом для
сумісного ракурсу.

#### 5.5 Background restoration не відповідає продукту

Фон не входить до критичних вимог. `background_restore` і вимога prompt зберігати фон
витрачають складність, звужують свободу генератора і створюють geometry/seam проблеми.
Фон можна зберігати в benchmark для контрольованого A/B, але не будувати навколо нього
product architecture.

## 6. Новий цільовий pipeline

```text
[A] Input & Photo QA
    photo + short request
        |
[B] Person Evidence Extractor
    identity anchors + observable appearance + uncertainty
        |
[C] Intent Parser
    StyleIntent: scenario/season/mood/constraints
        |
[D] Style Planner
    3-5 OutfitBlueprint candidates
        |
[E] Catalog Retrieval
    top-K concrete GarmentItem per slot
        |
[F] Outfit Set Reranker / Constraint Solver
    complete concrete OutfitCandidates
        |
[G] Try-On Planner
    layer graph + board + high-res item evidence + engine strategy
        |
[H] Try-On Engine
    holistic base image
        |
[I] Person & Item Fidelity Evaluator
    reason-coded failures
        |
[J] Local Repair / Regenerate
    single-item high-res references
        |
[K] Recommendation Bundle
    image + exact item list + rationale + confidence + warnings
        |
[L] User Feedback Memory
```

### B. Person Evidence Extractor

Не один текстовий VLM prompt, а поєднання:

- face embedding і face landmarks;
- hair/skin masks;
- color-constancy-aware skin/hair samples;
- pose/keypoints/human parsing;
- visible morphology observations з uncertainty;
- VLM лише для семантичного опису.

Треба розділити `IdentityProfile` (що зберігати) і `StyleEvidence` (що може впливати на
рекомендацію). Інакше одна помилкова VLM-ознака одночасно спотворить styling і контроль
ідентичності.

### D-F. Stylist і retrieval

Правильний Stylist не повинен одразу шукати один товар за одним vague prompt.

1. Побудувати `OutfitBlueprint`: slots, silhouettes, palette roles, materials, layers.
2. Виконати hard filters: category, season, occasion, availability, size якщо відомий.
3. Отримати top-K кандидатів на кожен slot через fashion embeddings/text search.
4. Ранжувати **набори речей**, а не незалежні nearest neighbors.
5. Перевірити layer graph і hard constraints детерміновано.
6. Повернути 3 різні завершені outfit, а не одну нібито абсолютну відповідь.

LLM тут планує і пояснює. Воно не повинно бути єдиним validator. Сезон, budget, category,
наявність, кількість шарів і complete slot coverage перевіряються кодом.

### G-J. Visualization

Рекомендована базова стратегія:

1. Holistic pass отримує person image + outfit board для глобальної композиції.
2. Board не замінює повнорозмірні item references.
3. Evaluation знаходить конкретні item-level failures.
4. Local repair отримує одну проблемну річ у максимальній якості та захищену mask zone.
5. Після кожного repair повторно перевіряється не лише цільова річ, а person identity,
   інші речі та outside-mask drift.
6. Після retry cap система показує warning, а не видає неточну візуалізацію за достовірну.

## 7. Як перебудувати чинний BUILD_PLAN

### Поточний Stage 0

**Залишити, але доповнити.** Виправити contract-to-workflow, provenance, side-effect tests.
Додати product contracts: `StyleIntent`, `OutfitBlueprint`, `GarmentItem`,
`OutfitCandidate`, `FidelityReport`, `RecommendationBundle`.

### Поточний Stage 1

**Не вважати measurement core завершеним.** ArcFace залишити face-only сигналом.
Proportions gate зняти з ролі body verdict. Color gate залишити вузьким індикатором.
Додати item identity benchmark і hair/skin/body evaluation plan.

### Поточний Stage 2

**Зберегти як baseline.** E-007 hybrid є корисним composition input, але не кандидатом
на остаточний формат доказів речі.

### Поточний Stage 3

Розділити на два deliverables:

1. `TryOnRunner`: відтворюваний photo + manual outfit -> result + fidelity report.
2. `ProductSkeleton`: photo + StyleIntent + curated catalog -> selected manual/automatic
   outfit package, навіть якщо перший try-on ще запускається окремо.

Не будувати великий VLM person-analysis модуль до визначення полів `StyleEvidence`.

### Поточний Stage 4

- `background_restore`: прибрати з critical path.
- `color_match`: не використовувати як доказ fidelity; лише опційний postprocess після
  незалежного A/B.
- `face_restore`: залишити тільки для compatible pose/alignment; не вважати універсальним
  identity mechanism.
- Замість shell як центральної ідеї створити `IdentityPreservationPolicy`.

### Поточний Stage 5

**Підняти пріоритет.** Single-item local repair є центральною частиною exact-outfit
архітектури. Тестувати не тільки shoes, а три класи:

- великий garment structure;
- pattern/detail;
- small accessory.

### Поточний Stage 6

Перетворити sampler/config bench на architecture bench:

| Row | Архітектура |
|---|---|
| A | holistic board only |
| B | holistic board + high-res local repairs |
| C | holistic clothing + protected accessory passes |
| D | specialized multi-garment VTO candidate |
| E | outfit-level fine-tuned editor, якщо A-D не проходять |

Sampler, cfg і steps оптимізуються тільки всередині архітектури, що вижила. Інакше багато
GPU-часу витрачається на tuning підходу, який принципово не несе достатньо item evidence.

### Поточний Stage 7

Перейменувати на `Try-On Feasibility Release`, а не V1-final продукту.

Definition of done:

- holdout people і outfits, не один pair;
- whole-outfit pass rate;
- person preservation по всіх критичних осях;
- per-item fidelity;
- documented failure reasons;
- чітке рішення: off-the-shelf достатньо / потрібен fine-tune / ціль недосяжна під
  локальними обмеженнями.

## 8. Реалістичний порядок побудови завершеної системи

### Milestone 0 — Product truth model

- Зафіксувати обіцянку продукту і те, чого він не гарантує.
- Визначити product objects та whole-outfit acceptance.
- Відділити identity, styling, retrieval і visualization scores.

### Milestone 1 — Corrected Try-On Feasibility Gate

- Виправити runner і provenance.
- Зібрати малий benchmark: кілька людей, outfits різної складності, fixed holdout.
- Створити `GarmentEvidencePack` з front/back/detail/masks/critical attributes.
- Побудувати item-fidelity evaluator.
- Порівняти architecture rows A-D.
- Якщо off-the-shelf не проходить, не будувати складний shell: переходити до E,
  outfit-level fine-tuning або нового engine.

### Milestone 2 — Curated Catalog Stylist

- Малий керований каталог із якісними reference packs.
- `StyleIntent` parser.
- Style knowledge base.
- OutfitBlueprint generation.
- Retrieval і deterministic constraint solver.
- Три конкретні outfit candidates без live internet search.

Цей етап дешевший за генерацію й повинен розроблятися паралельно з feasibility work,
але не потребує одразу складної персоналізації.

### Milestone 3 — Integrated Alpha

```text
photo + request
-> 3 concrete outfits
-> user selects one
-> exact try-on
-> fidelity report
-> replace-one-item flow
```

Selection перед expensive visualization зменшує GPU витрати і дає preference signal.

### Milestone 4 — Personalization

- Feedback memory.
- Preferred silhouettes/colors/brands/coverage.
- Optional measurements і size preferences.
- Ranking, що навчається на user choices.

### Milestone 5 — Catalog scale/productization

- live catalog ingestion;
- stock/price refresh;
- automatic reference quality gate;
- fallback на інший seller/view;
- cloud inference лише якщо quality/latency economics цього потребують.

## 9. Benchmark, без якого розвиток знову піде по колу

Поточні результати майже всі використовують одну людину й `outfit_001`. Це може знайти
локальні баги, але не може відповісти, чи працює архітектура.

Benchmark повинен змінювати незалежні осі:

- різні люди, hair/skin/face/body appearance;
- 3, 5 і 8 items;
- inner/outer layering;
- solid, patterned, reflective і textured garments;
- small accessories;
- clean packshots і imperfect retailer images;
- same pose controlled set та pose-change stress set;
- visually similar catalog decoys для item retrieval test.

Використовувати staged funnel:

1. малий smoke set для відсіву явно слабких стратегій;
2. development set для tuning;
3. frozen holdout тільки для рішення про promotion.

Не можна вибирати strategy і одночасно постійно змінювати acceptance set під її результати.

## 10. Головний конфлікт обмежень

Проєкт одночасно хоче:

- arbitrary concrete multi-item outfits;
- дуже високу detail fidelity;
- open source;
- local 16GB inference;
- no upfront investment;
- автоматичну роботу.

Не можна припускати, що всі шість умов сумісні. Нинішній kill criterion у BUILD_PLAN є
правильним наміром, але його треба застосувати раніше, після corrected architecture bench,
а не після побудови всього shell/orchestrator stack.

Ймовірний результат feasibility gate має бути одним із трьох:

1. Off-the-shelf local engine проходить bar — продовжувати.
2. Архітектура правильна, але general model втрачає item identity — потрібен outfit-level
   fine-tune на rented GPU, після чого inference може залишитися локальним.
3. Навіть fine-tuned/open engine не проходить bar — переглянути product promise або engine
   constraint, а не нескінченно tuning prompts.

## 11. Підсумкова відповідь

**Так, ядро поточного задуму може привести до мети, але не поточний roadmap буквально.**

Сильна частина шляху:

```text
outfit-level holistic generation
-> independent per-item evaluation
-> high-resolution single-item repair
-> bounded retry
```

Слабка частина:

```text
one person + one outfit
-> board/prompt/config experiments
-> color/face/silhouette scores
-> claim of progress toward a general stylist
```

Найважливіша зміна мислення:

> Reference board повинна представляти outfit як композицію. Конкретна річ повинна
> існувати в системі як багатий, повнорозмірний об'єкт із власними доказами, критичними
> деталями й незалежним fidelity verdict.

А завершений Open Source Stylist треба будувати не як один великий AI prompt, а як три
окремо перевірені системи — **Style Decision**, **Concrete Outfit Retrieval** і
**Identity-Preserving Exact Visualization** — з чіткими контрактами між ними.

## 12. Зовнішня перевірка напрямку

- Garments2Look підтверджує дві важливі для цього рішення речі: full-outfit try-on
  залишається складною задачею, а outfit-level board може бути сильнішим conditioning
  format, ніж передавання великої кількості окремих references. Це підтримує board як
  composition evidence, але не доводить її достатність для exact details:
  https://arxiv.org/html/2603.14153v1
- Та сама робота описує не одноразовий LLM prompt, а багатокрокову побудову outfit:
  style knowledge, user context, item synthesis, retrieval і rule validation. Це
  узгоджується з запропонованим поділом Style Planner / Retrieval / Constraint Solver.
- Personalized Fashion Recommendation формулює персоналізацію як моделювання контексту,
  історії та preferences користувача, а не як прямий висновок лише з одного фото:
  https://arxiv.org/html/2508.02342v1
- HumanGPS прямо вказує, що відновлення 3D geometry людини з одного RGB-зображення є
  ill-posed через occlusion і depth ambiguity. Тому body preservation при довільній
  зміні пози не можна чесно звести до трьох ширин 2D silhouette:
  https://arxiv.org/html/2405.00627v1
