# Повний аудит Open Source Stylist

Дата: 2026-06-15  
Область: весь `C:\Users\Admin\Open Source Stylist`, включно з `.git`, кешами,
bytecode, архівом, експериментальними результатами та діалогом із попереднім ШІ-агентом.

## 1. Підсумковий вердикт

Проєкт зараз є **дослідницьким репозиторієм із кількома корисними компонентами**, але
не завершеною системою стиліста. Це чесно написано в `README.md:21`: автоматичного
end-to-end конвеєра проєкт не заявляє.

Головна проблема не в кількості дрібних дефектів. Вона системна:

1. Контракти, документація, експерименти та runtime не утворюють одну виконувану модель.
2. Частина параметрів існує лише на папері й ігнорується workflow.
3. Декілька ключових метрик вимірюють не те, що стверджує документація.
4. Значна частина старих експериментальних висновків конфаунднута або спирається на
   пошкоджені маски, але продовжує виглядати як Verified у старих conclusion-файлах.
5. Поточний найкращий результат візуально ближчий до цілі, але все ще не проходить
   заявлену продуктову планку: точна ідентичність, пропорції, форма, колір, текстура та
   всі деталі комплекту не збережені одночасно.

Висновок: **продовжувати нарощувати експерименти поверх поточної основи не варто**.
Спершу треба виправити лінію `контракт -> workflow -> артефакт -> вимірювання -> verdict`,
а також очистити канонічне знання від суперечливих статусів.

## 2. Що саме перевірено

- Прочитано й SHA-256-хешовано всі **1 067 файлів**, сумарно **646 840 882 байти**.
- Перевірено всі **51 Python-файл**: UTF-8, AST, компіляція.
- Перевірено всі **60 JSON-файлів**: синтаксис і дубльовані ключі. Дубльованих ключів немає.
- Перевірено всі **773 зображення**: декодування, розміри, режими. Пошкоджених, порожніх
  або аномально малих файлів не знайдено.
- Перевірено всі **4 CSV**: структура рядків узгоджена.
- Перевірено **33 `.pyc`** системним Python 3.10: bytecode валідний, джерела існують.
- Перевірено `.pytest_cache`, усі `__pycache__`, архівний код і збережені run-state файли.
- Перевірено всі **65 файлів `.git`**, Git refs, reflog, pack-файли та object database.
- Витягнуто й прочитано Word-діалог: **267 абзаців, 6 таблиць, 52 726 символів**.
  Візуальний рендер DOCX не виконано, бо в середовищі немає LibreOffice/soffice; для
  діалогового тексту це не вплинуло на змістовний аналіз.
- Візуально зіставлено оригінал, референсні борди, E-001, E-005, E-006, E-007, E-008,
  маски та результат `generated_colormatch.png`.

Розподіл основного обсягу:

| Каталог | Файлів | Розмір |
|---|---:|---:|
| `.git` | 65 | 313.8 MB |
| `experiments` | 736 | 277.2 MB |
| `archive` | 147 | 42.0 MB |
| `assets` | 29 | 13.4 MB |
| `system` | 70 | 0.19 MB |

## 3. Критичні проблеми

### P0-1. End-to-end системи фактично немає

`BUILD_PLAN.md` очікує:

- `system/analysis/` (`BUILD_PLAN.md:280`);
- `system/evaluation/` (`BUILD_PLAN.md:286`);
- `system/orchestrator.py` (`BUILD_PLAN.md:288`);
- `system/shell/face_restore.py` (`BUILD_PLAN.md:309`);
- `system/repair/` (`BUILD_PLAN.md:348`).

Жодного з цих компонентів немає. Наявні клієнти, адаптер, сегментація, три gates та два
shell-модулі не з'єднані в один виконуваний цикл. Схеми `GenerationResult`,
`EvaluationVerdict`, `RepairPlan`, `FinalOutput` не мають runtime-власників.

Практичний наслідок: немає команди `photo + outfit -> final image + verified report`,
немає retry policy, repair routing, VRAM sequencing, provenance або фінального verdict.

### P0-2. GenerationRequest не керує фактичним workflow

`system/contracts/generation_request.json:28-37` вимагає `cfg`, `sampler`, `scheduler`;
`system/adapter/adapter.py:54-63` також формує negative prompt і ці параметри.

Але:

- `system/workflows/qie2511_vton.json:66-68` жорстко задає `cfg=1.0`, `euler`, `simple`;
- Lightning workflow робить те саме в рядках 76-78;
- negative prompt у workflow завжди порожній (`qie2511_vton.json:48`, Lightning:58);
- `system/workflows/__init__.py:12-20` не має placeholders для цих полів;
- E-007 передає у `fill_workflow()` лише image/prompt/seed/steps/size/prefix
  (`run_e007.py:188-197`).

Виконувана перевірка показала: request із `cfg=4.5` створюється валідно, але заповнений
KSampler усе одно має `cfg=1.0`. Це прямо ламає заплановані no-Lightning bench rows і E-014.

Додатково `fill_workflow()` мовчки залишає невідомий `__TYPO_PLACEHOLDER__` у JSON,
хоча docstring обіцяє fail-loud поведінку.

### P0-3. Історична доказова база частково недійсна

Поточний sanity guard, запущений на збережених масках, знайшов:

| Експеримент | Наборів масок | Наборів із flags |
|---|---:|---:|
| E-005 | 5 | 1 |
| E-006 | 15 | 8 |
| E-007 active results | 15 | 4 |
| E-008 | 5 | 3 |

E-005, E-006 та E-008 обчислювали метрики для частини цих пошкоджених масок без
`SKIP_SANITY`. Наприклад, E-005 seed 123 має 99.8% belt-mask усередині bottom-mask, але
зберігає belt/bottom color verdicts як звичайні PASS. E-008 seeds 123/456 мають top-mask,
що поглинає майже весь bottom, але `measurements.json` не містить sanity layer.

E-007 v2 вже пропускає color metrics для flagged regions, що є правильнішим, але сам
generic overlap detector також дає сумнівні flags на легітимних межах `top/bottom` і
`belt/top`. Отже, guard ще не є валідованим семантичним інструментом.

Окремо E-005/E-006/E-008 виконували стару, неправильно сформульовану задачу. Це визнано
в `knowledge/verified.md:493-517`, але їхні conclusion-файли досі містять формулювання
`Promoted to Verified` (`E-005:79-84`, `E-006:131`, `E-008:110`). Читач окремого файла
отримує протилежний висновок від канонічного erratum.

### P0-4. Метрики не покривають заявлені критерії

#### Color gate

`delta_e_p90` у `system/gates/color.py:126-132` порівнює кожен output-піксель із
**середнім кольором** референсу. Це не відстань між двома розподілами й не mismatch p90.
На абсолютно однаковому зображенні та однаковій масці отримано:

```text
delta_e_mean = 0.01
delta_e_p90  = 9.41
```

Тобто p90 переважно вимірює внутрішню кольорову варіативність/текстуру output-регіону.
Назва та інтерпретація вводять в оману. Додатково `normalize_l=True` навмисно ігнорує
абсолютну світлоту, тому gate не може підтвердити точний відтінок або washed-out вигляд.
Заявлений у design `palette` mode відсутній; реалізовано лише mean-color mode.

#### Proportions gate

`system/gates/proportions.py:68-105` рахує кількість foreground-пікселів у рядку маски
одягненого силуету. Це не плечі/талія/стегна тіла:

- об'ємні рукави змінюють `shoulder_width` без зміни тіла;
- peplum і пояс змінюють `waist`;
- спідниця змінює `hip`;
- мінімум ширини в зоні чутливий до дірок маски й розділення ніг.

E-004 калібрує метрику горизонтальним resize тієї самої маски. Результати майже точно
повторюють внесене масштабування: 10.19%, 20.18%, 30.22%. Це перевірка арифметики,
а не здатності відрізнити деформацію тіла від зміни одягу. Natural pair відрізняється
лише на 0.35% і фактично є близьким повтором тієї самої людини/пози.

#### Identity gate

ArcFace покриває обличчя, але не волосся, шкіру, тіло, позу або фон. E-003 має лише одну
same-person пару з cosine 0.9896 і три different-person пари. Поріг 0.57 є midpoint
малого набору, а не production calibration. Позначати весь критерій `same person identity`
як covered некоректно.

### P0-5. Deterministic shell дає оманливе покращення

У Word-діалозі попередній агент прямо визнав: падіння color score після `color_match`
майже тавтологічне, бо код зсуває mean LAB до mean того самого референсу, а потім міряє
відстань до нього. Він також визнав, що така корекція може зламати природне освітлення.

Код підтверджує ризик:

- `color_match.py:82-83` конвертує **все** зображення LAB -> BGR після локального shift;
- на реальному `generated_colormatch.png` змінилися 735 023 із 737 280 пікселів
  (99.69%); поза union garment masks змінилося 582 189 пікселів;
- поза маскою це переважно квантування на 1 рівень каналу, але твердження
  «інші пікселі не чіпаються» є фактично хибним;
- variance не гарантовано зберігається через gamut clipping і round-trip;
- тест дозволяє до 20% відхилення variance, тому не доводить `untouched`;
- немає feathering, overlap policy, позитивної валідації `max_shift`;
- `correct()` мовчки пропускає регіон без reference (`color_match.py:99-101`).

`background_restore.py` не можна застосувати до поточного реального output без
попередньої геометричної політики: original має 938x1344, generated 720x1024. Реальний
виклик падає з `Shape mismatch`. Навіть при однаковому розмірі використовується жорстка
бінарна межа без feathering, що ризикує створити halo/seam.

Shell ніде не під'єднаний до runner/orchestrator. `generated_colormatch.png` не має
відтворюваного tracked runner або запису точних reference/mask/max_shift inputs.

## 4. Високі ризики

### P1-1. Pytest може запускати реальну GPU-генерацію під час collection

`experiments/005_variance_baseline/test_layers1.py` не має main guard і виконує upload,
submit, poll, download та `/free` на верхньому рівні модуля. Під час аудиту саме
`pytest --collect-only` запустив реальну задачу й перезаписав п'ять PNG. Ці файли були
повернуті до початкового Git-вмісту.

Це критичний operational defect: інструмент, що має лише знаходити тести, виконує GPU-job
і змінює експериментальні артефакти. `test_configs.py` також створює каталоги та клієнт на
import. Обидва файли мають бути перейменовані у scripts і захищені main guard.

`system/tests` окремо проходить: **26 passed**. Це не покриває живу інтеграцію,
відтворюваність експериментів або end-to-end acceptance.

### P1-2. Контракти синтаксично валідні, але семантично слабкі

`system/contracts/validate.py` дає 10/10 PASS, бо перевіряє переважно форму JSON.
Патологічні приклади, які схема приймає як VALID:

- `overall_verdict="pass"`, порожній `regions={}`, `repair_needed=true`;
- `FinalOutput`, де всі чотири критерії мають `skip`;
- `RegionMap` із неіснуючими/несумісними mask paths без dimensions, hash або coordinate space.

Інші прогалини:

- `EvaluationVerdict` не дозволяє `null` для ArcFace/no-face і numeric proportion gaps;
- немає умов між `overall_verdict`, per-region verdicts, `repair_needed` і `repair_plan_id`;
- `GenerationResult` не доводить, що engine/params відповідають request;
- немає content hashes, model hashes, workflow hash, dimensions, timestamps;
- `OutfitPackage` не зв'язує labels із items і не вимагає унікальних priorities;
- `FinalOutput` не має source result/verdict lineage та дублює report structure;
- `negative_constraints` фактично мертві в runtime.

### P1-3. Експерименти недостатньо відтворювані

- Активні state-файли містять абсолютні `C:\Users\Admin\...` paths.
- E-007 original phase не resumable: якщо state існує, runner відмовляється стартувати
  (`run_e007.py:128`), хоча state записується ще до завершення всіх seeds.
- Original E-007 outputs не мають SHA-256; hybrid має hashes, але validation неповна.
- Не зберігається повний filled workflow/request на кожен seed.
- E-005 historical runner більше не виконується: він викликає `build_panel()`, який тепер
  навмисно кидає RuntimeError.
- `results_invalid_2026-06-13/phase1_state.json` має 13 абсолютних paths, і всі 13 вже
  не існують після перенесення результатів.
- Архівні manifests/state часто посилаються на старі `runs/...`, тому архів не є
  self-contained.

### P1-4. Канонічна документація суперечлива й частково протухла

Append-only policy (`METHODOLOGY.md:28`, `:165`) конфліктує з роллю канонічної
документації. Git уже зберігає історію; canonical docs повинні показувати чинний стан.

Наслідки:

- `knowledge/verified.md` містить одночасно старий Verified, reversal і erratum;
- V-SEG-003 називає пропущені buttons прийнятними, хоча E-007 потім потребував manual mask repair;
- V-REF-003 піднятий до Verified з owner observation без ізольованого A/B;
- E-005/E-006/E-008 conclusions суперечать пізнішому erratum;
- `PROJECT_LEDGER.md` має щонайменше 34 references на вже перенесені `runs/`, `docs/`,
  `schemas/`, `prompts/`, `tools/` paths;
- Stage 1 у ранній частині `BUILD_PLAN.md` названий not complete, хоча нижче вже є closure;
- design обіцяє `solid/palette`, але код має лише solid mean;
- instrument ledger перебільшує покриття identity, color/texture та proportions.

### P1-5. Поточний продукт не проходить власну ціль

Візуальна перевірка артефактів:

- E-005: близька людина й композиція, але великі/спрощені earrings, нестабільне взуття,
  пласка текстура, зміна силуету.
- E-006: на high/high_plus часто інша людина, head crop, інша поза/фон; більшість identity
  verdicts FAIL або no-face.
- E-008: усі п'ять outputs фактично інша модель; identity collapse видно без метрики.
- E-007 hybrid: найкращий із наявних, buttons і shoes помітно кращі, але blouse shade,
  silhouette/body shape, garment texture, earrings і точна shoe geometry не стабільні.

Отже, hybrid є корисним candidate input, але не доказом, що система досягла потрібного
результату. Один outfit і одна person photo також не дають підстав для generalization.

## 5. Середні проблеми

### P2-1. Sanity guard має власні прогалини

- RGB ndarray з foreground падає з `ValueError: too many values to unpack` у centroid logic.
- Shape mismatch у pairwise overlap мовчки пропускається.
- Thresholds не перевіряються на діапазон 0..1.
- Generic overlap не розуміє семантично припустимі вкладення/межі (belt/top, top/bottom).
- Earrings containment усередині person silhouette може давати false positive.
- Flags advisory; не кожен старий runner їх застосовує.

### P2-2. Reference-board preparation не настільки frozen, як заявлено

`prepare_reference_boards.py`:

- docstring каже «two boards» і «same sources/order/labels», але будує три, а hybrid має
  9 cells та інший layout;
- перезаписує frozen PNG, corrected mask і manifest без confirmation/versioning;
- manifest і OutfitPackage дублюють board metadata, але немає sync validator;
- manifest не хешує source/mask/crop/layout inputs;
- button repair є hardcoded ROI для одного конкретного blouse asset, а не general method.

### P2-3. Environment/setup не повністю відтворювані

- `requirements.txt` pinned, `pip check` чистий.
- Немає virtual environment policy, lockfile з hashes або Python version enforcement.
- `system/setup_python.ps1` використовує будь-який `python` із PATH і змінює глобальне
  середовище; на машині одночасно є Python 3.10 і 3.14.
- Last live check: ComfyUI 0.24.1 доступний, усі workflow/segmentation nodes і потрібні
  model dropdown entries знайдені; LM Studio недоступний; `env_check` = RED.
- `env_check.py` сам не перевіряє required model filenames, custom nodes, upload/run/download
  round-trip або load/unload timings, хоча Stage 0 цього очікує.
- Ruff і mypy не встановлені; static typing/lint не перевірені.

### P2-4. Git здоровий, але важкий і без зовнішньої страховки

- Branch: `master`; commits: 67; remote: відсутній.
- 694 tracked files, із них 524 images.
- Поточні tracked images займають 236.5 MB із 237.4 MB tracked working content.
- `.git` займає 313.8 MB; packs = 293.75 MiB.
- `git fsck --full --no-reflogs`: corruption/missing objects не знайдено.
- Є 225 dangling trees і 2 dangling blobs; це не corruption, але залишковий object clutter.
- LFS section у `.git/config` є, але `.gitattributes` відсутній і LFS files = 0.
- Немає remote backup, тому history rewrite або aggressive prune зараз небезпечні.
- 50 dirty entries були присутні до аудиту; їх не змінювали й не відкотили.
- Немає `.gitattributes`; Git попереджає про LF -> CRLF для багатьох файлів.
- `.claude/settings.local.json` tracked і містить 130 machine-specific allow rules та
  локальні paths. `.gitignore` pattern `*.local` його не покриває.

### P2-5. Архів містить виконувані небезпечні залишки

- `archive/tools/upscale.py:75` завантажує model із `verify=False` без checksum.
- Там же hardcoded `C:/Users/Admin/ComfyUI` і можливий overwrite input.
- Архівний evaluator створює temp PNG без cleanup.
- Архівний confirm tool дозволяє human overall pass, що може суперечити per-criterion flags.
- Чотири Markdown links у starter archive docs зламані.

Це архів, тому ризик нижчий, але виконувані `.py` варто або чітко quarantine, або зробити
неімпортованими/невиконуваними за замовчуванням.

## 6. Hygiene та кеші

- `.pytest_cache` коректно ignored, але містить stale `lastfailed` для
  `test_layers1.py` та nodeids уже видалених тестів.
- Усі 33 `.pyc` валідні для Python 3.10; stale orphan bytecode не знайдено.
- `__pycache__` і `.pytest_cache` не є причиною логічних помилок, але їх слід очищати
  перед контрольним reproducibility run.
- Знайдено 22 duplicate-content groups / 62 duplicate files. Переважно це навмисні
  копії inputs в archive runs, але вони збільшують Git та ускладнюють provenance.
- Один archived prompt має mixed line endings; 6 рядків trailing whitespace у трьох файлах.
- Секретів, API keys, private keys або bearer tokens у текстових файлах не знайдено.

## 7. Що в системі зроблено добре

Це не «все зламано». Корисна основа є:

- frozen board hash verification у `system/adapter/panel.py`;
- content-qualified ComfyUI upload filenames;
- poll error handling і mocked client tests;
- schema `additionalProperties=false` у більшості контрактів;
- чітке розділення Verified/Hypothesis як намір;
- реальні артефакти, fixed seeds, contact sheets і збережені measurements;
- E-007 v2 вже зберігає більше provenance й використовує `SKIP_SANITY`;
- README чесно не видає компонентний стан за готовий продукт;
- зовнішня research direction загалом обґрунтована.

Зовнішні першоджерела підтверджують, що outfit-level multi-reference try-on справді
складний: Garments2Look показує проблеми повних outfit, layering та зростання складності
з кількістю references. Його supplement також справді каже, що FastFit мав найнижчий
layering preference через single-layer processing, а QIE-2509 fine-tune підняв 0.41 -> 0.627.
Tstars-Tryon підтверджує промисловий напрям multi-image + engineered identity/background
control. Але ці джерела **не доводять**, що локальна реалізація вже робить це правильно.

## 8. Рекомендований порядок наведення ладу

### Крок 0. Зафіксувати й убезпечити

1. Не робити history rewrite: remote відсутній.
2. Створити backup/remote перед будь-яким Git cleanup.
3. Зафіксувати поточний dirty worktree окремою гілкою/commit після ручного перегляду.
4. Перейменувати side-effect scripts `test_*.py` і додати main guards.

### Крок 1. Один канонічний стан

1. Прибрати append-only правило для canonical docs; історію залишити Git.
2. Зробити короткий `CURRENT_STATE.md`: що працює, що не працює, який evidence чинний.
3. Старі E-005/E-006/E-008 conclusions позначити зверху `SUPERSEDED/CONFOUNDED`.
4. Перемістити `PROJECT_LEDGER.md` в archive або переписати paths на актуальні.
5. Ввести machine-readable registry для fact status: active/superseded/refuted.

### Крок 2. Виправити contract -> workflow

1. Додати placeholders для cfg/sampler/scheduler/negative prompt.
2. Зробити exhaustive placeholder validation після fill.
3. Зберігати filled workflow + request + hashes для кожного run.
4. Додати semantic contract tests: invalid pass/skip combinations мають падати.
5. Додати RegionMap dimensions, source hash, mask hashes, coordinate space.

### Крок 3. Перевизначити інструменти

1. Color: залишити mean CIEDE2000 як обмежений hue/chroma indicator; перейменувати p90
   або замінити distribution metric (palette/histogram/EMD) і окремо вимірювати lightness/texture.
2. Identity: ArcFace = face-only. Додати окремі hair/background/pose/body checks або чесно
   залишити їх owner-only до калібрування.
3. Proportions: не робити body verdict із clothed silhouette. Потрібні body landmarks,
   dense pose/human parsing або стратегія protect-by-construction.
4. Калібрувати пороги на labeled accept/reject dataset, не на одному same pair і
   синтетичному resize.

### Крок 4. Мінімальний вертикальний зріз

Побудувати один реальний command path:

```text
validated inputs
-> exact generation request
-> exact filled workflow
-> output + hashes
-> segmentation + sanity
-> limited honest gates
-> owner checkpoint
-> final report
```

Без repair і VLM на першому проході. Спершу довести, що один run відтворюваний і кожен
параметр доходить до engine.

### Крок 5. Лише потім shell/repair/bench

1. Color shell приймати тільки за independent perceptual/owner A/B, не за метрикою,
   яку він оптимізує за побудовою.
2. Background restore спершу отримує явну geometry/alignment/feather policy.
3. Bench rows виконувати лише після виправлення cfg/negative placeholders.
4. Додати щонайменше holdout людей, outfit, backgrounds і pose; один person/outfit не
   може бути acceptance batch.
5. Встановити kill criterion із числовою product bar, budget і строком.

## 9. Пріоритетний backlog

| Пріоритет | Робота | Результат |
|---|---|---|
| P0 | Забрати side effects із pytest collection | безпечний test discovery |
| P0 | Провести cfg/sampler/scheduler/negative до workflow | bench стає реальним |
| P0 | Позначити superseded experiments | припинити хибні Verified-висновки |
| P0 | Перевизначити proportions verdict | не плутати одяг із тілом |
| P0 | Припинити приймати color_match за власним score | незалежна оцінка змін |
| P1 | Побудувати minimal orchestrated vertical slice | один відтворюваний run |
| P1 | Посилити contracts/provenance | доказовість артефактів |
| P1 | Зробити state relative/resumable/content-addressed | переносимість |
| P1 | Очистити canonical docs | один чинний стан |
| P2 | Додати venv/Python pin/CI/lint | відтворюване середовище |
| P2 | Винести binary history strategy/LFS після backup | контроль Git size |
| P2 | Quarantine archived executables | менший operational risk |

## 10. Фінальна оцінка

Архітектурна ідея `editing engine + deterministic preservation + measured acceptance`
має сенс і відповідає напрямку сучасних досліджень. Але поточна реалізація ще не довела
найважливіше: що вона стабільно створює правильний outfit на тій самій людині, а її
інструменти коректно відрізняють добрий результат від поганого.

Найкращий наступний крок не «ще один великий експеримент». Це короткий ремонт основи:
чесні контракти, один відтворюваний vertical slice, незалежні метрики та чистий
канонічний стан. Після цього експерименти знову почнуть накопичувати знання, а не борг.

## 11. Зовнішні першоджерела

- Garments2Look: https://arxiv.org/html/2603.14153v1
- Tstars-Tryon 1.0: https://arxiv.org/abs/2604.19748
- OmniTry: https://arxiv.org/abs/2508.13632
- FastFit: https://ar5iv.labs.arxiv.org/html/2508.20586v1
- QIE-2511 Lightning model card: https://huggingface.co/lightx2v/Qwen-Image-Edit-2511-Lightning
- Qwen-Image official repository: https://github.com/QwenLM/Qwen-Image

