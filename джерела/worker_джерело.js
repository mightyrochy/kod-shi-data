/* ─────────────────────────────────────────────────────────────────────────────
   МІСТ ДО МОДЕЛІ — ключі живуть тут, а не в тестувальниці.

   НАВІЩО. Сторінка кличе api без ключа лише в пісочниці артефакта, і платить
   там ГЛЯДАЧ: прогін тестувальниці з'їдав ЇЇ ліміт. На звичайній сторінці
   ключа в браузері бути не може — його побачить кожен, хто відкрив devtools.
   Отже ключ лежить тут, а сторінка ходить сюди.

   ДВА ПРОВАЙДЕРИ, ОДИН ФОРМАТ. Сторінка завжди шле й читає формат Anthropic;
   переклад у бік Google живе ТІЛЬКИ тут. Тому зміна моделі — це правка рядка
   `МОДЕЛЬ_П` у показі, і більше нічого: маршрут вибирається за префіксом імені.
   Розбір відповіді, лічба токенів, читання `stop_reason` у сторінці лишаються
   тим самим кодом для обох провайдерів — інакше кожна нова модель тягла б за
   собою другу гілку розбору, і вони розійшлися б на першій правці.

   ДЕ ЦЕ ЖИВЕ: Cloudflare Workers (безкоштовний тариф). Ключі — секретами:
       GEMINI_API_KEY    — секрет: ключ з aistudio.google.com (починається на AIza)
       ANTHROPIC_API_KEY — секрет: потім, коли перейдемо на Claude
       TESTER_TOKENS     — секрет: токени через кому, ЛИШЕ латиниця (tok-a1,tok-b2)
       ALLOWED_ORIGINS   — звичайна змінна: https://твій.github.io
       GEMINI_THINKING   — звичайна змінна, необов'язкова. Скільки Gemini
                           дозволено мислити: minimal | low | medium | high
                           (покоління 3), число або `off` (покоління 2.5),
                           `як є` — не чіпати. Без змінної: minimal.
       GEMINI_FALLBACK   — звичайна змінна, необов'язкова: моделі через кому,
                           які пробуються по черзі, коли основна мовчить довше
                           за стелю або віддає 503/429/524.
                           Напр.: gemini-2.5-flash-lite,gemini-2.5-flash
       PROVIDER_TIMEOUT_S — стеля секунд на одну спробу (типово 85; Cloudflare
                           ріже мовчазний підзапит на ~100 с).

   ПРАВИТИ КОД ПЕРЕД ДЕПЛОЄМ НЕ ТРЕБА. Відкрий адресу воркера в браузері: GET
   віддає вкладену сторінку-пробу, яка перевіряє все й називає кожну поломку
   окремо, замість одного «не працює».
   ───────────────────────────────────────────────────────────────────────────── */

/* ── ПОХОДЖЕННЯ ЗАДАЄТЬСЯ ЗМІННОЮ, А НЕ ПРАВКОЮ КОДУ ────────────────────────
   Правка коду перед деплоєм — зайвий крок, на якому легко помилитись і важко
   помітити помилку: 403 виглядає так само, як «міст не працює». Тому список
   їде змінною ALLOWED_ORIGINS (через кому). Порожня змінна = не пускається
   ніхто, крім самого воркера: мовчазний «пускаю всіх» був би гіршим за
   помилку, бо ключ роздавав би кредити невідомо кому.
   Власне походження воркера дозволене завжди — інакше вкладена проба нижче
   не могла б постукати сама до себе. */
function дозволені(env) {
  return (env.ALLOWED_ORIGINS || "").split(",").map(s => s.trim()).filter(Boolean);
}

const СТЕЛЯ_ВИХОДУ     = 4000;
const СТЕЛЯ_ВХОДУ_СИМВ = 400000;   // виміряно: рука з пулом ≈ 130 000 симв
const ПРОГОНІВ_НА_ДОБУ = 40;

/* ── ТЕМПЕРАТУРА ДОХОДИТЬ ДО ОБОХ ПРОВАЙДЕРІВ (рядок 158 дошки, 27.09.2026) ──
   ЩО БУЛО. Показ шле `temperature: 0` у тілі запиту (`мовний_шар.ВИБІРКА` →
   `_дзвінокП`), бо рішення власника «температура мовного шару 0» тримається на
   тому, що ОДНАКОВА РЕПЛІКА дає ОДИН ПАСПОРТ. Маршрут `claude-` віддає тіло як
   є, тож там поле доїжджало. Маршрут `gemini-` будує тіло НАНОВО
   (`contents` + `generationConfig`) і брав із нього лише `max_tokens` і
   мислення — температура мовчки зникала, а модель шару відповідала з
   температурою за замовчуванням провайдера (для Gemini це 1.0). Тобто
   стабільність паспорта не гарантувалась НІЧИМ саме на тому провайдері, на
   якому крутиться шар (`МОДЕЛЬ_МОВИ_П` — gemini-).

   ЩО ТЕПЕР. Одне правило на обидва маршрути: число з `temperature` тіла їде
   провайдеру його власним полем (Anthropic — верхній рівень, Gemini —
   `generationConfig.temperature`), і що саме поїхало, видно в заголовку
   `x-temperature` — без нього «дійшла чи ні» лишалось би твердженням.

   ЧОМУ ЛИШЕ ЧИСЛО Й ЛИШЕ ЦЕ ПОЛЕ. Не-число (null, рядок, NaN) поле ЗНІМАЄ, а не
   перетворює: `{"temperature": null}` у `generationConfig` Gemini відкидає 400,
   і причина 400 виглядала б як поломка моделі. Решти полів вибірки (`top_p`,
   `top_k`, `seed`) показ не шле — додавати їх наперед означало б зашити здогад
   про імена, яких ніхто не виміряв. Межі значення міст НЕ править: Anthropic
   приймає 0..1, Gemini 0..2, і тихе підганяння дало б модель, що відповідає не
   з тією температурою, яку просили; чуже 400 із текстом провайдера чесніше. */
/* ── 400 ЧЕРЕЗ САМЕ ЦЕ ПОЛЕ — ЗНЯТИ Й СКАЗАТИ (М-6, 28.09.2026) ──────────────
   Сучасні моделі Anthropic (Opus 4.7 і новіші, Sonnet 5, Fable 5) приймають
   `temperature` ЛИШЕ типовим значенням: НЕтипове дає 400 «Sampling parameters
   rejected» (документація міграції Anthropic). Тобто рішення «температура шару 0»
   (#413) на маршруті `claude-` упало б 400 на першому ж виклику — рівно та сама
   хвороба, що службове поле `_думки` 02.09, і лікується так само, як каскад
   мислення Gemini: на 400 ЧЕРЕЗ ЦЕ ПОЛЕ міст повторює запит без нього й каже про
   це заголовком (`x-temperature: dropped`). Вгадувати покоління за іменем моделі
   ми не будемо — ім'я задає сторінка, а протухлий список моделей брехав би мовчки. */
const температура_тіла = т => {
  if (т && т._без_темп) return null;
  const з = Number(т && т.temperature);
  return (т && т.temperature !== null && т.temperature !== undefined && Number.isFinite(з)) ? з : null;
};

/* ── КЕШ НЕЗМІННОГО ПОЧАТКУ ЗАПИТУ (наряд К-4, 27.09.2026) ───────────────────
   СЛОВО ВЛАСНИКА 27.09: «незмінна частина кожного запиту збирання образів (словник
   кодів, правила, роль, схема полів) стає закешованим початком запиту. Швидкість та
   сама, а платимо за цю частину значно менше.»

   ЩО САМЕ НЕЗМІННЕ. Збирач промптів ставить обʼєкт `task` («завдання» в українському
   шаблоні) ПЕРШИМ, а дані виклику — після нього (`збирач_промптів.зібрати`, К-4). Отже
   незмінний початок — від `{` повідомлення до коми перед `input`: усередині `task` збирач
   так само ставить незмінне (роль, правила, межі, мова, імʼя відповіді, схема) перед тим,
   що зібране з даних цього виклику (`input`, `statement_codes`).

   ДВА ПРОВАЙДЕРИ — ДВА РІЗНІ МЕХАНІЗМИ, І ЛИШЕ ОДИН ПОТРЕБУЄ ПОЛЯ В ТІЛІ.
   · Anthropic: кеш пишеться на ЯВНІЙ МЕЖІ `cache_control` в кінці блоку, який має
     лишатись однаковим (документація «Prompt caching», Messages API). Одним текстовим
     блоком межу поставити нікуди — вона впала б у кінець усього промпта, тобто за
     пулом, і кожен виклик лише ПИСАВ би кеш (125 % ціни) без жодного влучання. Тому
     міст ріже перший текстовий блок надвоє рівно на цій межі; склеєний текст
     байт у байт той самий, що й був, — модель бачить те саме повідомлення.
   · Gemini: неявний кеш (implicit caching) вмикається сам на моделях 2.5+ і тримається
     на СТАЛОМУ ПРЕФІКСІ запиту — поля в тілі для нього нема взагалі. Явне кешування
     (`cachedContents`) обрано НЕ БУЛО, і не «бо складніше», а ЗА ЧИСЛАМИ. Воно вимагає
     окремого ресурсу (створити, тримати ключ десь між викликами — у воркера для цього
     є лише KV, — і видалити) і ПЛАТИ ЗА ЗБЕРІГАННЯ: $1.00 за мільйон токенів на годину
     (прайс Google). Наш незмінний початок складання — 1 642 токени (вимір
     `проби/кеш_незмінне.py`): година зберігання коштує $0.0016, а одне влучання
     економить 1 642 × ($0.30 − $0.03)/10⁶ = $0.00044. Тобто явний кеш окупається лише
     від чотирьох влучань на годину — на одну жінку з її чотирма руками він був би
     ЗБИТКОМ. Неявний кеш не коштує нічого й дає ту саму знижку 90 %.
     ЧОГО ВІН НЕ ДАЄ, СКАЗАНО ЧЕСНО: неявний кеш має поріг спільного префікса —
     2 048 токенів на 2.5 Flash і 4 096 на 3.x Flash. Наші 1 642 його не досягають, тож
     на `gemini-3.x` знижки поки не буде; на маршруті `claude-` (поріг 1 024 для Sonnet 5,
     512 для Opus 5) — буде. Це межа виміряна, а не здогадана, і лежить рядком дошки.

   ЧОМУ БЕЗ `ttl`. Типовий TTL Anthropic — 5 хвилин, і запис у такий кеш коштує 125 %
   базової ціни входу; година коштує 200 % і (на час написання) окремого заголовка
   `anthropic-beta`. Один збір образів — це десятки секунд, тобто всі виклики прогону
   влазять у пʼять хвилин. Беремо дешевше й без беженого заголовка.

   ЧОМУ ЛИШЕ ПЕРШИЙ БЛОК І ЛИШЕ КОЛИ ВІН ПЕРШИЙ. Перед текстом у повідомленні можуть
   стояти фото (`модельП` кладе блоки `image` попереду). Фото — це саме те, що між
   викликами міняється, тож префікс із ним несталий: кеш писався б і не влучав, а запис
   дорожчий за звичайний вхід. Коли текст не перший — міст не чіпає нічого. */
function межа_кешу(текст) {
  // Завдання мусить бути ПЕРШИМ ключем повідомлення (після необовʼязкової «версії») —
  // саме так його ставить збирач. Промпт іншої будови (складений рядком у показі, чи
  // старого порядку «дані першими») межі не дістає: там вона різала б навпіл змінне.
  const м = /^\{(?:"(?:version|версія)":"[^"]*",)?"(?:task|завдання)":\s*\{/.exec(текст || "");
  if (!м) return -1;
  let глибина = 0, у_рядку = false, екран = false;
  for (let і = м[0].length - 1; і < текст.length; і++) {
    const з = текст[і];
    if (екран) { екран = false; continue; }
    if (з === "\\") { екран = true; continue; }
    if (з === '"') { у_рядку = !у_рядку; continue; }
    if (у_рядку) continue;
    /* МЕЖА — ПЕРЕД «input», А НЕ В КІНЦІ ЗАВДАННЯ. Кеш Anthropic збігається лише тоді,
       коли ВЕСЬ текст до межі той самий; за межею вміст може бути будь-який. А в кінці
       завдання стоять два розділи, зібрані з даних ЦЬОГО виклику: «input» (лише наявні
       поля) і «statement_codes» (лише наявні коди). Поставити межу за ними означало б
       писати кеш, який не влучить, щойно у виклику зʼявилось інше поле: на ремонті це
       160 токенів спільного початку замість ~980 (вимір `проби/кеш_незмінне.py`). Тому
       ріжемо там, де збирач кінчає незмінне, — на комі перед «input»/«вхід». */
    if (глибина === 1 && з === "," && (текст.startsWith(',"input":', і) || текст.startsWith(',"вхід":', і)))
      return і;
    if (з === "{") глибина++;
    else if (з === "}" && --глибина === 0) return і + 1;
  }
  return -1;
}
const з_кешем = т => {
  const п = (т.messages || [])[0];
  if (!п || !Array.isArray(п.content) || !п.content.length) return т;
  const б = п.content[0];
  if (!б || б.type !== "text" || б.cache_control) return т;
  const к = межа_кешу(б.text);
  if (к <= 0 || к >= String(б.text || "").length) return т;
  return {...т, messages: [{...п, content: [
    {type: "text", text: б.text.slice(0, к), cache_control: {type: "ephemeral"}},
    {type: "text", text: б.text.slice(к)},
    ...п.content.slice(1),
  ]}, ...т.messages.slice(1)]};
};

/* ── ПРОВАЙДЕРИ ─────────────────────────────────────────────────────────────
   ІМЕНА МОДЕЛЕЙ НЕ ВШИТІ НАВМИСНО. Каталог Google рухається швидко (лінія 2.5
   гаситься восени 2026), і зашитий список моделей протух би мовчки, віддаючи
   404 замість відповіді. Тут стоїть лише ПРЕФІКС — маршрут; точне ім'я задає
   сторінка, і воно видно в помилці, якщо не існує. */
const ПРОВАЙДЕРИ = [
  {
    ім: "anthropic", префікс: "claude-", ключ: "ANTHROPIC_API_KEY",
    адреса: () => "https://api.anthropic.com/v1/messages",
    шапка: k => ({"content-type":"application/json", "x-api-key":k,
                  "anthropic-version":"2023-06-01"}),
    /* РІДНИЙ ФОРМАТ, АЛЕ БЕЗ СЛУЖБОВОГО ПОЛЯ (02.09.2026). Каскад мислення
       нижче пише в тіло `_думки` (для Gemini — `null`, «без поля»), і доти
       `запит: т => т` віддавав його Anthropic як є. API Anthropic на невідоме
       поле відповідає 400 «Extra inputs are not permitted», тобто маршрут
       `claude-` не працював би з першого ж виклику — рівно в момент, коли
       систему роздають тестувальницям. Gemini не зачеплено: його `запит`
       будує нове тіло. */
    запит: т => { const р = з_кешем({...т}); delete р._думки; delete р._без_темп;
                  const темп = температура_тіла(т);
                  if (темп === null) delete р.temperature; else р.temperature = темп;
                  return р; },
    відповідь: д => д,
  },
  {
    ім: "gemini", префікс: "gemini-", ключ: "GEMINI_API_KEY",
    /* ДВА МАРШРУТИ GOOGLE В ОДНОМУ ПРОВАЙДЕРІ (08.10.2026). Старі моделі (NB2
       `gemini-3.1-flash-image`, текстові) — `:generateContent`; Nano Banana 2.1
       і далі — лише `/v1beta/interactions` (див. `через_interactions`). Решта
       провайдера — ключ, шапка, стеля часу, драбина, заголовки — спільна. */
    адреса: м => через_interactions(м)
      ? "https://generativelanguage.googleapis.com/v1beta/interactions"
      : "https://generativelanguage.googleapis.com/v1beta/models/"
        + encodeURIComponent(м) + ":generateContent",
    шапка: k => ({"content-type":"application/json", "x-goog-api-key":k}),
    /* ── МИСЛЕННЯ З'ЇДАЄ СТЕЛЮ ВИВОДУ (01.09.2026, спіймано першим живим прогоном) ─
       Flash-моделі Gemini мислять за замовчуванням, і `thoughtsTokenCount`
       рахується ПРОТИ `maxOutputTokens`. Проба зі стелею 16 віддала
       `finishReason: MAX_TOKENS`, 13 токенів виходу й ПОРОЖНІЙ текст. У
       реальному прогоні це вбивало б кожну руку: показ читає `stop_reason` і
       кидає «відповідь обрізано», бо судити обрізаний образ не можна.

       ЧОМУ НЕ ПРОСТО `thinkingBudget: 0`. Поле залежить від покоління:
       2.5 розуміє `thinkingBudget` (0 = вимкнути), 3.x — `thinkingLevel`
       ("minimal"/"low"/…), і надіслати обидва разом = 400. А `gemini-flash-latest`
       це АЛІАС: яке саме покоління за ним стоїть сьогодні, звідси не видно.
       Тому налаштування ЗАДАЄТЬСЯ ЗМІННОЮ, а на 400 через саме це поле міст
       ПОВТОРЮЄ запит без нього й каже про це заголовком. Вгадувати покоління
       за іменем аліаса означало б будувати на здогаді, який мовчки протухне. */
    думки: н => {
      const з = String(н || "").trim().toLowerCase();
      if (з === "as-is" || з === "як є") return [];
      if (з === "off") return [{thinkingBudget: 0}];
      if (/^\d+$/.test(з)) return [{thinkingBudget: parseInt(з, 10)}];
      if (з) return [{thinkingLevel: з}];
      /* «minimal» → «low» → budget 0 → без поля. 3.8 Flash (02.09.2026) minimal
         НЕ підтримує (документація: «minimal is not supported on 3.8 Flash»,
         підлога — low); без цього щабля каскад падав у thinkingBudget, який
         покоління 3 теж відкидає, і далі — у мислення за замовчуванням,
         тобто high: повільно й дорого (думки рахуються як вихід). Так 3.7
         Flash висів 85 с на пробі 02.09. */
      return [{thinkingLevel: "minimal"}, {thinkingLevel: "low"}, {thinkingBudget: 0}];
    },
    /* ── МОДЕЛЬ КАРТИНОК ВИМАГАЄ `responseModalities` (02.09.2026) ─────────
       СПІЙМАНО ПЕРШИМ ПРОГОНОМ: «Приміряти» повернуло ТЕКСТ — «Ось опис
       згенерованого фотореалістичного зображення…». Документація Google
       каже прямо: щоб модель віддала зображення, у `generationConfig`
       МУСИТЬ стояти `responseModalities: ["TEXT","IMAGE"]`; без нього
       image-модель чесно описує картинку словами. Мислення таким моделям
       не задаємо — воно для них не діє й лише ризикує 400. */
    картинкова: м => /image|nano-banana/i.test(String(м || "")),
    запит(т) { return через_interactions(т.model) ? запит_interactions(т) : this.запит_generate(т); },
    /* Interactions приймає одне повідомлення `user` (`input`); історія в нього —
       `previous_interaction_id`, якого міст не веде. Багатоповідомленевий запит
       на такій моделі — чесний 400 до мережі, а не мовчазне склеювання ролей. */
    перевірити_запит: т => {
      if (!через_interactions(т.model)) return null;
      const пов = т.messages || [];
      return (пов.length === 1 && пов[0].role === "user") ? null
        : "модель «" + т.model + "» іде через Interactions API: міст передає їй рівно одне повідомлення user, "
          + "отримано " + пов.length + (пов.length ? " (перше: " + (пов[0].role || "?") + ")" : "");
    },
    запит_generate: т => ({
      contents: (т.messages || []).map(п => ({
        // Gemini кличе бік моделі «model», Anthropic — «assistant». Роль
        // важить: без неї модель на третій репліці переказує саму себе.
        role: п.role === "assistant" ? "model" : "user",
        parts: (Array.isArray(п.content) ? п.content : [{type:"text", text:п.content}])
          .filter(б => б.type !== "image" || (б.source && б.source.data))
          .map(б => б.type === "image"
            ? {inline_data: {mime_type: б.source.media_type, data: б.source.data}}
            : {text: б.text}),
      })),
      generationConfig: Object.assign({maxOutputTokens: т.max_tokens},
        температура_тіла(т) === null ? {} : {temperature: температура_тіла(т)},
        /image|nano-banana/i.test(String(т.model || ""))
          ? {responseModalities: ["TEXT", "IMAGE"]}
          : (т._думки ? {thinkingConfig: т._думки} : {})),
    }),
    /* ── ФОТО ЗА АДРЕСОЮ: ТЯГНЕ ВОРКЕР, НЕ ТЕЛЕФОН (02.09.2026) ───────────
       Сторінка шле блок image із `source:{type:"url"}` — Anthropic такий блок
       розуміє сам. Google — ні, тож байти тягне воркер: він сервер, CORS
       магазинів на нього не діє, і 46 політик перестають бути питанням.
       Фото, яке не завантажилось, ВИПАДАЄ з запиту (не валить його) і
       рахується в заголовку `x-images-dropped`, щоб сторінка назвала це. */
    підготувати: async т => {
      let випало = 0;
      /* ── ПАРАЛЕЛЬНО Й ІЗ СПІЛЬНОЮ СТЕЛЕЮ ВАГИ (02.09.2026) ─────────────────
         Доти фото тяглись ПО ЧЕРЗІ (одинадцять товарних фото = десятки секунд
         усередині стелі 85 с) і без спільної межі: Google приймає в одному
         запиті близько 20 МБ inline, а товарне фото буває 2–3 МБ, тож образ із
         десяти речей міг дати 400 самою вагою. Тепер тягнемо разом, кожне фото
         ≤ `СТЕЛЯ_ФОТО`, усі разом ≤ `СТЕЛЯ_ФОТО_РАЗОМ`; що не влізло —
         випадає й рахується в `x-images-dropped`, а не валить виклик. */
      const СТЕЛЯ_ФОТО = 4 * 1024 * 1024, СТЕЛЯ_ФОТО_РАЗОМ = 14 * 1024 * 1024;
      const блоки = [];
      for (const п of (т.messages || [])) {
        if (!Array.isArray(п.content)) continue;
        for (const б of п.content)
          if (б.type === "image" && б.source && б.source.type === "url") блоки.push(б);
      }
      const тягнути = async б => {
        try {
          const в = await fetch(б.source.url, {headers: {"accept": "image/*"}});
          const тип = (в.headers.get("content-type") || "").split(";")[0].trim();
          if (!в.ok || !тип_картинки(тип)) return null;
          const байти = new Uint8Array(await в.arrayBuffer());
          if (байти.length > СТЕЛЯ_ФОТО) return null;
          /* СИГНАТУРА, НЕ ЗАГОЛОВОК (04.09.2026): content-type крамниці бреше, а
             Gemini на чужі байти відповідає 400 «Unable to process input image»
             і валить увесь виклик. GIF Gemini не приймає взагалі; < 1 КБ — заглушка. */
          const справжній = сигнатура_картинки(байти);
          if (!справжній || байти.length < 1024) return null;
          return {б, тип: справжній, байти};
        } catch (_) { return null; }
      };
      const здобуті = await Promise.all(блоки.map(тягнути));
      let разом = 0;
      /* ФОТО-513: кадр, що не дійшов, ЛИШАЄ СВОЄ МІСЦЕ — текстом «not delivered». Доти він просто
         зникав із запиту, і модель, яка лічить зображення, віддавала наступній речі чужий кадр. */
      const випав = б => { б.type = "text"; б.text = "(image not delivered)"; delete б.source; };
      for (let i = 0; i < здобуті.length; i++) {
        const з = здобуті[i];
        if (!з) { випало++; випав(блоки[i]); continue; }
        if (разом + з.байти.length > СТЕЛЯ_ФОТО_РАЗОМ) { випало++; випав(блоки[i]); continue; }
        разом += з.байти.length;
        let бін = ""; const шм = 0x8000;
        for (let i = 0; i < з.байти.length; i += шм) бін += String.fromCharCode.apply(null, з.байти.subarray(i, i + шм));
        з.б.source = {type:"base64", media_type: з.тип, data: btoa(бін)};
      }
      return випало;
    },
    відповідь(д, модель) {
      return через_interactions(модель) ? відповідь_interactions(д) : this.відповідь_generate(д);
    },
    відповідь_generate: д => {
      const к = (д.candidates || [])[0] || {};
      const частини = (к.content || {}).parts || [];
      const текст = частини.map(ч => ч.text || "").filter(Boolean).join("\n");
      /* ── КАРТИНКИ ПРОВОДЯТЬСЯ, А НЕ ВИКИДАЮТЬСЯ (01.09.2026) ───────────────
         Перекладач брав лише текстові частини, тож будь-яка згенерована
         картинка мовчки зникала: виклик «успішний», відповідь порожня. Для
         приміряння образу на власне фото це рівно та частина, заради якої
         виклик і робиться. Формат Anthropic має свій блок `image`, тож
         переклад іде в НЬОГО — сторінка й далі читає один контракт. */
      const картинки = частини
        .filter(ч => ч.inlineData || ч.inline_data)
        .map(ч => { const д2 = ч.inlineData || ч.inline_data;
          return {type:"image", source:{type:"base64",
                  media_type: д2.mimeType || д2.mime_type || "image/png",
                  data: д2.data}}; });
      const u = д.usageMetadata || {};
      return {
        content: [...(текст ? [{type:"text", text:текст}] : []), ...картинки],
        // `finishReason: "MAX_TOKENS"` мусить стати `stop_reason:"max_tokens"`,
        // інакше сторінка не помітить обрізаного хвоста й тестувальниця
        // судитиме стелю виводу замість образу.
        stop_reason: (к.finishReason === "MAX_TOKENS") ? "max_tokens"
                   : (к.finishReason || "end_turn").toLowerCase(),
        /* ── КЕШОВАНІ ТОКЕНИ — ОДНИМ ІМЕНЕМ НА ОБОХ ПРОВАЙДЕРАХ (К-4) ──────────
           Сторінка читає формат Anthropic, де `input_tokens` — це вхід БЕЗ кешу, а
           прочитане з кешу стоїть окремо в `cache_read_input_tokens`. Google рахує
           інакше: документація generateContent про `promptTokenCount` каже прямо —
           «this is still the total effective prompt size meaning this includes the
           number of tokens in the cached content». Тож віддавати `cachedContentTokenCount`
           поруч із повним `promptTokenCount` означало б порахувати кеш ДВІЧІ (показ
           додає обидва поля). Тому тут кеш ВІДНІМАЄТЬСЯ — і два провайдери починають
           означати те саме число тим самим словом. */
        usage: {input_tokens: Math.max(0, (u.promptTokenCount || 0) - (u.cachedContentTokenCount || 0)),
                cache_read_input_tokens: u.cachedContentTokenCount || 0,
                output_tokens: (u.candidatesTokenCount || 0) + (u.thoughtsTokenCount || 0),
                // ОКРЕМИМ ЧИСЛОМ. Разом із текстовими токенами воно ховає
                // причину порожньої відповіді за словом «вихід».
                thinking_tokens: u.thoughtsTokenCount || 0},
        _провайдер: "gemini", _причина_сира: к.finishReason || null,
      };
    },
  },
];

/* ── NANO BANANA 2.1 І ДАЛІ — INTERACTIONS API, А НЕ generateContent (08.10.2026) ──
   ЩО ВІДОМО (ai.google.dev/gemini-api/docs/nanobanana і /interactions, прочитано 08.10):
   · модель `gemini-nano-banana-2.1` (GA 06.10); зразки коду для неї — лише
     `POST /v1beta/interactions`, а `generateContent` Google називає legacy:
     «all new models … will launch on the Interactions API»;
   · запит: `{model, input:[{type:"text",text}, {type:"image",mime_type,data}…],
     response_format:{type:"image"}, generation_config:{max_output_tokens,…}}`;
   · відповідь: `{status, steps:[{type:"model_output", content:[{type:"text",text} |
     {type:"image",data,mime_type}]}, …], usage:{total_input_tokens,
     total_output_tokens, total_thought_tokens, total_cached_tokens,
     total_tokens}, errors:[{code,message}]}`. Кроки `thought` можуть нести проміжні
     картинки — їх не беремо, лише `model_output`.
   НЕ ЗРОБЛЕНО НАВМИСНО: NB2 лишається на generateContent (його гасять пізніше, а
   шлях працює); перемикача в показі нема — маршрут визначає ім'я моделі.
   ЩО ТРЕБА ВИМІРЯТИ ЖИВИМ ПРОГОНОМ (з мережею): чи `total_input_tokens` включає
   кеш (тут, як у `promptTokenCount`, вважаємо, що ТАК), і чи приймає 2.1
   `temperature` (якщо ні — 400 із цим словом знімає поле сам, `x-temperature:
   dropped`). Список моделей — РЕГЕКС, а не перелік імен (див. коментар до
   ПРОВАЙДЕРИ): нове покоління nano-banana піде цим шляхом саме. */
function через_interactions(м) {
  return /nano-banana-(?:2\.[1-9]\d*|[3-9])/i.test(String(м || ""));
}

function запит_interactions(т) {
  const вхід = [];
  for (const п of (т.messages || [])) {
    for (const б of (Array.isArray(п.content) ? п.content : [{type:"text", text:п.content}])) {
      if (б.type === "image") {
        if (б.source && б.source.data)
          вхід.push({type:"image", mime_type: б.source.media_type, data: б.source.data});
      } else if (б.type === "text") вхід.push({type:"text", text: б.text});
    }
  }
  const темп = температура_тіла(т);
  return {
    model: т.model,
    input: вхід,
    response_format: {type: "image"},
    generation_config: Object.assign({max_output_tokens: т.max_tokens},
                                     темп === null ? {} : {temperature: темп}),
  };
}

/* Те саме, що віддає `відповідь_generate`: `content` (text/image у форматі Anthropic),
   `stop_reason`, `usage`. ПОМИЛКА ПРОВАЙДЕРА НЕ КОВТАЄТЬСЯ (СТАНДАРТ_КОДУ п.14): Interactions
   може віддати 200 зі `status:"failed"` або `errors` — це `_помилка`, яку воркер перетворює
   на 502 з текстом Google; порожня відповідь без помилки теж помилка, а не «успіх без картинки». */
function відповідь_interactions(д) {
  const статус = String((д && д.status) || "");
  const вихід = ((д && д.steps) || []).filter(к => к && к.type === "model_output")
    .flatMap(к => Array.isArray(к.content) ? к.content : []);
  const текст = вихід.filter(б => б.type === "text" && б.text).map(б => б.text).join("\n");
  const картинки = вихід.filter(б => б.type === "image" && б.data)
    .map(б => ({type:"image", source:{type:"base64", media_type: б.mime_type || "image/png", data: б.data}}));
  const помилки = ((д && д.errors) || []).map(е => ((е && е.code) ? String(е.code).slice(0, 120) + ": " : "") + ((е && е.message) || ""));
  const збій = ["failed", "cancelled"].includes(статус) || (помилки.length && !текст && !картинки.length)
    || (статус && !["completed", "incomplete"].includes(статус))
    || (!текст && !картинки.length);
  if (збій)
    return {_помилка: "Interactions API: status=" + (статус || "(нема)")
                      + (помилки.length ? " · " + помилки.join(" | ").slice(0, 400) : "")
                      + (!помилки.length && !текст && !картинки.length ? " · у відповіді нема ні тексту, ні картинки" : "")};
  const u = (д && д.usage) || {};
  return {
    content: [...(текст ? [{type:"text", text:текст}] : []), ...картинки],
    // `incomplete` — Google обірвав вихід (стеля токенів): сторінка читає це як max_tokens.
    stop_reason: статус === "incomplete" ? "max_tokens" : "end_turn",
    usage: {input_tokens: Math.max(0, (u.total_input_tokens || 0) - (u.total_cached_tokens || 0)),
            cache_read_input_tokens: u.total_cached_tokens || 0,
            // total_output_tokens БЕЗ думок (документований приклад: 7 + 20 + 22 = 49) —
            // як `candidatesTokenCount`, тож думки додаються, а не рахуються двічі.
            output_tokens: (u.total_output_tokens || 0) + (u.total_thought_tokens || 0),
            thinking_tokens: u.total_thought_tokens || 0},
    _провайдер: "gemini", _причина_сира: статус || null,
  };
}

function тип_картинки(т) {
  return /^image\/(jpeg|png|webp)$/i.test(т || "");
}

function сигнатура_картинки(б) {
  if (!б || б.length < 12) return null;
  if (б[0] === 0xFF && б[1] === 0xD8 && б[2] === 0xFF) return "image/jpeg";
  if (б[0] === 0x89 && б[1] === 0x50 && б[2] === 0x4E && б[3] === 0x47) return "image/png";
  if (б[0] === 0x52 && б[1] === 0x49 && б[2] === 0x46 && б[3] === 0x46
      && б[8] === 0x57 && б[9] === 0x45 && б[10] === 0x42 && б[11] === 0x50) return "image/webp";
  return null;
}

function заголовки(п) {
  return {
    "Access-Control-Allow-Origin": п,
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "content-type, x-lyusterko-token",
    // `_межіП()` у показі читає саме ці заголовки. Через проксі пісочниці їх не
    // було взагалі, і 429 на четвертій руці лишився без причини. Anthropic їх
    // шле; Gemini — ні, і тоді показ чесно скаже «заголовків лімітів нема».
    "Access-Control-Expose-Headers":
      "anthropic-ratelimit-requests-remaining, anthropic-ratelimit-requests-reset, " +
      "anthropic-ratelimit-tokens-remaining, anthropic-ratelimit-tokens-reset, " +
      "anthropic-ratelimit-input-tokens-remaining, anthropic-ratelimit-output-tokens-remaining, " +
      "retry-after, x-runs-left, x-provider, x-thinking, x-images-dropped, x-model, x-attempts, " +
      "x-temperature, x-cached-tokens, x-route",
    "Access-Control-Max-Age": "86400",
  };
}

const відмова = (код, чому, п) =>
  new Response(JSON.stringify({error:{type:"міст", message:чому}}),
               {status:код, headers:{...заголовки(п), "content-type":"application/json"}});

export default {
  async fetch(запит, env) {
    const своє = new URL(запит.url).origin;
    // GET — сторінка-проба. Класти її нікуди не треба: досить відкрити адресу
    // воркера в браузері. Вона ж і перевіряє все, що нижче.
    if (запит.method === "GET")
      return new Response(ПРОБА, {status:200,
        headers:{"content-type":"text/html; charset=utf-8"}});
    const п = запит.headers.get("Origin") || "";
    if (п !== своє && !дозволені(env).includes(п))
      return відмова(403, "походження не в списку: " + (п || "(порожнє)")
                        + " · дозволені: "
                        + (дозволені(env).join(", ") || "(ALLOWED_ORIGINS не задано)"),
                     п || "null");
    if (запит.method === "OPTIONS")
      return new Response(null, {status:204, headers:заголовки(п)});
    if (запит.method !== "POST") return відмова(405, "лише POST або GET", п);

    const токен = запит.headers.get("x-lyusterko-token") || "";
    const відомі = (env.TESTER_TOKENS || "").split(",").map(s=>s.trim()).filter(Boolean);
    if (!відомі.includes(токен)) return відмова(401, "невідомий токен", п);

    let тіло;
    try { тіло = await запит.json(); } catch { return відмова(400, "тіло не JSON", п); }

    const пров = ПРОВАЙДЕРИ.find(x => String(тіло.model || "").startsWith(x.префікс));
    if (!пров)
      return відмова(400, "невідомий провайдер для моделі «" + тіло.model + "» — "
                        + "ім'я мусить починатись на "
                        + ПРОВАЙДЕРИ.map(x=>x.префікс).join(" або "), п);
    const ключ = env[пров.ключ];
    if (!ключ) return відмова(500, "на мості нема секрета " + пров.ключ, п);

    тіло.max_tokens = Math.min(Number(тіло.max_tokens) || СТЕЛЯ_ВИХОДУ, СТЕЛЯ_ВИХОДУ);
    const розмір = JSON.stringify(тіло.messages || []).length;
    if (розмір > СТЕЛЯ_ВХОДУ_СИМВ)
      return відмова(413, "запит " + розмір + " симв — понад стелю " + СТЕЛЯ_ВХОДУ_СИМВ, п);

    // ЧЕСНО ПРО МЕЖУ: без KV лічильник не переживає перезапуск ізоляту, тобто
    // стеля м'яка. Тверда стеля живе не тут: у Anthropic — місячний ліміт
    // воркспейса й вимкнений автодолив; у Gemini — сама дармова квота.
    // ЗНАЧЕННЯ ЗАГОЛОВКА — ТЕЖ ASCII. Тире «—» тут кидало TypeError ще до
    // мережі (спіймано пробою). Те саме стосується ТОКЕНА: кириличний токен
    // тестувальниці не пройшов би вже в браузері, тож роздавати лише ASCII.
    let лишилось = "n/a";
    if (env.COUNTER) {
      const к = "д:" + токен + ":" + new Date().toISOString().slice(0,10);
      const було = Number(await env.COUNTER.get(к)) || 0;
      if (було >= ПРОГОНІВ_НА_ДОБУ)
        return відмова(429, "добова межа токена вичерпана: " + ПРОГОНІВ_НА_ДОБУ, п);
      await env.COUNTER.put(к, String(було+1), {expirationTtl: 172800});
      лишилось = String(ПРОГОНІВ_НА_ДОБУ - було - 1);
    }

    const неприйнятне = пров.перевірити_запит && пров.перевірити_запит(тіло);
    if (неприйнятне) return відмова(400, неприйнятне, п);

    // Фото за адресою для провайдера, який сам їх не тягне (Gemini)
    const випало_фото = пров.підготувати ? await пров.підготувати(тіло) : 0;
    /* ── СТЕЛЯ ЧАСУ Й ДРАБИНА МОДЕЛЕЙ (02.09.2026, спіймано пробою) ────────
       Cloudflare ріже підзапит воркера, що мовчить ~100 с, і віддає йому
       відповідь 524 «error code: 524»; воркер віддавав її сторінці як є —
       125.6 с чекання й незрозумілий код. Проба на одне речення до
       `gemini-flash-latest` (форма thinkingBudget) висіла довше за цю стелю.
       Тепер: (1) кожен виклик провайдера має власну стелю `PROVIDER_TIMEOUT_S`
       (типово 85 с — нижче за чужі 100); (2) після стелі або 524/503/429
       береться НАСТУПНА модель із `GEMINI_FALLBACK` (через кому, напр.
       `gemini-2.5-flash-lite,gemini-2.5-flash`), і яка відповіла — у заголовку
       `x-model`; (3) коли драбина скінчилась — чесний 504 JSON із секундами й
       переліком спроб, а не чужий 524. Що моделі різні за швидкістю — вимір
       01.09: 14 → 3 → 72 с на однаковому запиті одного аліаса. */
    const стеля_с = Math.max(5, Number(env.PROVIDER_TIMEOUT_S) || 85);
    /* Драбина НЕ підміняє картинкову модель текстовою: `GEMINI_FALLBACK`
       містить текстові імена, і перехід на них дав би опис замість картинки
       (та сама вада, що й брак `responseModalities`, тільки мовчазна). */
    const _картинкова = пров.картинкова && пров.картинкова(тіло.model);
    const драбина = [тіло.model].concat(
      (пров.ім === "gemini" && !_картинкова ? (env.GEMINI_FALLBACK || "") : "").split(",")
        .map(s => s.trim()).filter(s => s && s !== тіло.model && s.startsWith(пров.префікс)));
    const стук = async (модель) => {
      const ctrl = new AbortController();
      const таймер = setTimeout(() => ctrl.abort(), стеля_с * 1000);
      try {
        return await fetch(пров.адреса(модель), {
          method:"POST", headers:пров.шапка(ключ),
          body:JSON.stringify(пров.запит(Object.assign({}, тіло, {model: модель}))),
          signal: ctrl.signal,
        });
      } catch (e) {
        // стеля часу або мережа — синтетична відповідь, щоб драбина йшла далі
        return new Response("міст: провайдер не відповів за " + стеля_с + " с (" + String(e).slice(0, 80) + ")",
                            {status: 504});
      } finally { clearTimeout(таймер); }
    };
    // ── КАСКАД ФОРМ, А НЕ ОДИН ЗДОГАД (01.09.2026, виміряно живим прогоном) ──
    // `thinkingLevel` розуміє покоління 3, `thinkingBudget` — 2.5, і надіслати
    // обидва разом = 400. Аліас `-latest` не каже, яке покоління за ним стоїть
    // СЬОГОДНІ: прогін показав, що `thinkingLevel` він відхилив. Зашити тепер
    // `thinkingBudget` означало б замінити один здогад іншим і мовчки
    // зламатись, коли аліас переїде. Тому форми пробуються по черзі, і лише
    // потім поле знімається зовсім. Порожній хвіст `null` — це «без поля».
    const форми = (пров.думки && !_картинкова ? пров.думки(env.GEMINI_THINKING) : []).concat([null]);
    let відп = null, думки_стан = "as-is", модель_ок = тіло.model;
    const спроби = [];
    const почато = Date.now();
    щабель: for (const модель of драбина) {
      модель_ок = модель;
      for (let i = 0; i < форми.length; i++) {
        тіло._думки = форми[i];
        думки_стан = форми[i] ? Object.keys(форми[i])[0] : (i ? "dropped" : "as-is");
        відп = await стук(модель);
        спроби.push(модель + ":" + думки_стан + "=" + відп.status);
        if (відп.status === 400) {
          const т400 = await відп.clone().text();
          /* 400 через саме поле вибірки (див. `температура_тіла`): знімаємо його ОДИН раз і
             повторюємо той самий щабель тією самою формою мислення — інакше «модель не
             приймає температуру» виглядало б як поломка моделі. */
          if (/temperature|top_p|top_k|sampling/i.test(т400) && !тіло._без_темп
              && температура_тіла(тіло) !== null) {
            тіло._без_темп = true;
            спроби[спроби.length - 1] += "(temperature dropped)";
            i--;            // та сама форма мислення, вже без температури
            continue;
          }
          // 400 НЕ через мислення — чужа помилка, віддаємо як є, не крутимо каскад
          if (!/thinking|thought/i.test(т400)) break щабель;
          /* ПРИЧИНА ВІДМОВИ — У СПРОБАХ (02.09: `gemini-3.7-flash` відхилив
             `thinkingLevel`, і чому — не було видно; наступна форма коштувала
             503 і 85 с тиші). Короткий текст помилки Google — ASCII-безпечно. */
          let чому = ""; try { чому = (JSON.parse(т400).error || {}).message || ""; } catch (_) { чому = т400; }
          спроби[спроби.length - 1] += "(" + чому.replace(/[^\x20-\x7E]/g, "?").replace(/\s+/g, " ").slice(0, 90) + ")";
          continue;
        }
        /* 503 «high demand» (спіймано пробою 02.09 на gemini-3.6-flash за 0.5 с) —
           сплеск, «зазвичай тимчасовий». Одна повторна спроба ТІЄЇ САМОЇ моделі
           через 2.5 с — дешевша за перехід на слабшу; лише потім драбина. */
        if (відп.status === 503 && !спроби.some(x => x.startsWith(модель + ":") && x.endsWith("=503") && x !== спроби[спроби.length - 1])) {
          await new Promise(r => setTimeout(r, 2500));
          відп = await стук(модель);
          спроби.push(модель + ":" + думки_стан + "=" + відп.status);
        }
        // стеля часу / чужий 524 / перевантаження / квота — наступний щабель драбини
        if ([504, 524, 503, 429].includes(відп.status)) continue щабель;
        break щабель;
      }
    }

    const вих = new Headers();
    for (const [і,з] of Object.entries(заголовки(п))) вих.set(і,з);
    відп.headers.forEach((з,і) => {
      if (/^(anthropic-ratelimit|retry-after)/i.test(і)) вих.set(і,з);
    });
    вих.set("content-type", "application/json");
    вих.set("x-runs-left", лишилось);
    вих.set("x-provider", пров.ім);
    вих.set("x-thinking", думки_стан);
    вих.set("x-images-dropped", String(випало_фото));
    вих.set("x-model", модель_ок);
    /* ЯКИМ МАРШРУТОМ ПІШОВ ЗАПИТ — заголовком, щоб A/B між NB2 і 2.1 було видно на відповіді. */
    вих.set("x-route", пров.ім !== "gemini" ? "messages"
                       : (через_interactions(модель_ок) ? "interactions" : "generateContent"));
    вих.set("x-attempts", спроби.join(" "));
    /* ASCII, як і решта значень (кирилиця в заголовку кидає TypeError ще до мережі):
       «n/a» — тим самим словом, що й `x-runs-left`, коли числа нема. */
    вих.set("x-temperature", тіло._без_темп ? "dropped"
                            : (температура_тіла(тіло) === null ? "n/a" : String(температура_тіла(тіло))));

    const сире = await відп.text();
    if (відп.status === 504 || відп.status === 524)
      return відмова(504, "провайдер не відповів за " + Math.round((Date.now() - почато) / 1000)
                          + " с (стеля " + стеля_с + " с на спробу; спроби: " + спроби.join(", ") + "). "
                          + "Це латентність моделі, не міст: спробуй інше ім'я моделі або задай GEMINI_FALLBACK.", п);
    if (!відп.ok) return new Response(сире, {status:відп.status, headers:вих});
    let дані;
    try { дані = JSON.parse(сире); }
    catch { return відмова(502, "провайдер віддав не JSON: " + сире.slice(0,300), п); }
    const наш = пров.відповідь(дані, модель_ок);
    /* Збій, який провайдер віддав під 200 (Interactions: `status:"failed"`, `errors`), — це 502
       з його текстом, а не «успіх» без картинки (СТАНДАРТ_КОДУ п.14). */
    if (наш && наш._помилка)
      return new Response(JSON.stringify({error:{type:"провайдер", message: наш._помилка}}),
                          {status:502, headers:вих});
    /* СКІЛЬКИ ВХОДУ ПРИЙШЛО З КЕШУ — ЗАГОЛОВКОМ (К-4). Без нього «кеш працює» лишалось
       би твердженням: тіло читає показ, а ручний огляд і проби дивляться на заголовки.
       ASCII, як і решта значень; `0` — кеш не влучив, і це теж факт. */
    вих.set("x-cached-tokens", String(((наш || {}).usage || {}).cache_read_input_tokens || 0));
    return new Response(JSON.stringify(наш), {status:200, headers:вих});
  },
};


/* ── ВКЛАДЕНА СТОРІНКА-ПРОБА (GET) ────────────────────────────────────────
   Вона ж лежить окремим файлом `проба.html` — на випадок, коли треба
   перевірити ще й CORS зі СПРАВЖНЬОГО походження Pages, чого запит із
   самого воркера не перевіряє: там походження своє. */
