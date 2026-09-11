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
    запит: т => { const р = {...т}; delete р._думки; return р; },
    відповідь: д => д,
  },
  {
    ім: "gemini", префікс: "gemini-", ключ: "GEMINI_API_KEY",
    адреса: м => "https://generativelanguage.googleapis.com/v1beta/models/"
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
    запит: т => ({
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
      for (const з of здобуті) {
        if (!з) { випало++; continue; }
        if (разом + з.байти.length > СТЕЛЯ_ФОТО_РАЗОМ) { випало++; continue; }
        разом += з.байти.length;
        let бін = ""; const шм = 0x8000;
        for (let i = 0; i < з.байти.length; i += шм) бін += String.fromCharCode.apply(null, з.байти.subarray(i, i + шм));
        з.б.source = {type:"base64", media_type: з.тип, data: btoa(бін)};
      }
      return випало;
    },
    відповідь: д => {
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
        usage: {input_tokens: u.promptTokenCount || 0,
                output_tokens: (u.candidatesTokenCount || 0) + (u.thoughtsTokenCount || 0),
                // ОКРЕМИМ ЧИСЛОМ. Разом із текстовими токенами воно ховає
                // причину порожньої відповіді за словом «вихід».
                thinking_tokens: u.thoughtsTokenCount || 0},
        _провайдер: "gemini", _причина_сира: к.finishReason || null,
      };
    },
  },
];

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
      "retry-after, x-runs-left, x-provider, x-thinking, x-images-dropped, x-model, x-attempts",
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
          // 400 НЕ через мислення — чужа помилка, віддаємо як є, не крутимо каскад
          const т400 = await відп.clone().text();
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
    вих.set("x-attempts", спроби.join(" "));

    const сире = await відп.text();
    if (відп.status === 504 || відп.status === 524)
      return відмова(504, "провайдер не відповів за " + Math.round((Date.now() - почато) / 1000)
                          + " с (стеля " + стеля_с + " с на спробу; спроби: " + спроби.join(", ") + "). "
                          + "Це латентність моделі, не міст: спробуй інше ім'я моделі або задай GEMINI_FALLBACK.", п);
    if (!відп.ok) return new Response(сире, {status:відп.status, headers:вих});
    let дані;
    try { дані = JSON.parse(сире); }
    catch { return відмова(502, "провайдер віддав не JSON: " + сире.slice(0,300), п); }
    return new Response(JSON.stringify(пров.відповідь(дані)),
                        {status:200, headers:вих});
  },
};


/* ── ВКЛАДЕНА СТОРІНКА-ПРОБА (GET) ────────────────────────────────────────
   Вона ж лежить окремим файлом `проба.html` — на випадок, коли треба
   перевірити ще й CORS зі СПРАВЖНЬОГО походження Pages, чого запит із
   самого воркера не перевіряє: там походження своє. */

const ПРОБА = `<!doctype html>\n<html lang="uk">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1">\n<title>Проба мосту · Люстерко</title>\n<!--\n  НАВІЩО ЦЯ СТОРІНКА, А НЕ curl.\n  curl НЕ ПЕРЕВІРЯЄ CORS. Він шле запит і читає відповідь незалежно від того,\n  що сказав «Access-Control-Allow-Origin», — бо CORS накладає БРАУЗЕР, а не\n  сервер. Тобто зелений curl нічого не доводить про те, чи запрацює показ.\n  Ця сторінка ходить тим самим шляхом, що й показ: із того самого походження,\n  тим самим заголовком токена, тим самим тілом. Що спрацювало тут — спрацює там.\n\n  ДРУГЕ: вона на телефоні. curl на Android — це Termux і півгодини; ця\n  сторінка — посилання й одна кнопка.\n\n  ТРЕТЄ: вона окремо називає ТРИ різні поломки, які інакше зливаються в одне\n  «не працює»: міст не піднявся · міст живий, але не пускає · міст пускає,\n  а провайдер відмовляє (найчастіше — невірне ім'я моделі, 404).\n-->\n<style>\n  :root { color-scheme: light dark; }\n  body { font: 16px/1.5 system-ui, sans-serif; margin: 0; padding: 18px;\n         max-width: 720px; }\n  h1 { font-size: 20px; margin: 0 0 4px; }\n  p.тьм { color: #6b6b6b; margin: 4px 0 16px; font-size: 14px; }\n  label { display: block; font-size: 13px; color: #6b6b6b; margin: 12px 0 3px; }\n  input { width: 100%; box-sizing: border-box; padding: 10px; font-size: 15px;\n          border: 1px solid #bbb; border-radius: 8px; font-family: ui-monospace, monospace; }\n  button { margin-top: 16px; padding: 12px 18px; font-size: 16px; border: 0;\n           border-radius: 8px; background: #1a1a1a; color: #fff; width: 100%; }\n  button:disabled { opacity: .5; }\n  pre { white-space: pre-wrap; word-break: break-word; background: #f4f4f4;\n        padding: 12px; border-radius: 8px; font-size: 13px; margin-top: 16px;\n        font-family: ui-monospace, monospace; }\n  @media (prefers-color-scheme: dark) { pre { background: #1e1e1e; } }\n  .добре { color: #0a7d32; } .зле { color: #b00020; }\n</style>\n</head>\n<body>\n<h1>Проба мосту</h1>\n<p class="тьм">Три невідомих одразу: чи піднявся міст, чи пускає він це\nпоходження й токен, чи існує така модель. Кожне називається окремо.</p>\n\n<label>Адреса мосту</label>\n<input id="адреса" placeholder="https://lyusterko-mist.ТВІЙ.workers.dev" autocapitalize="off" spellcheck="false">\n<label>Токен (латиницею — кирилиця в заголовку HTTP не проходить)</label>\n<input id="токен" placeholder="tok-a1" autocapitalize="off" spellcheck="false">\n<label>Ім'я моделі</label>\n<input id="модель" value="gemini-3.5-flash-lite" autocapitalize="off" spellcheck="false">\n\n<button id="пуск">Перевірити міст</button>\n<pre id="вивід">Заповніть поля або відкрийте цю сторінку з хешем:\n#міст=АДРЕСА&amp;т=ТОКЕН&amp;модель=ІМ'Я</pre>\n\n<script>\n"use strict";\nconst $ = і => document.getElementById(і);\nconst в = $("вивід");\n\n/* Ті самі ключі, що читає показ, — щоб заповнене тут працювало і там. */\n(function(){\n  try{\n    const h = new URLSearchParams((location.hash || "").replace(/^#/, ""));\n    $("адреса").value = h.get("міст")   || localStorage.getItem("міст:адреса") || "";\n    $("токен").value  = h.get("т")      || localStorage.getItem("міст:токен")  || "";\n    $("модель").value = h.get("модель") || localStorage.getItem("міст:модель") || "gemini-3.5-flash-lite";\n  }catch(_){}\n})();\n\nfunction рядок(о){ return Object.entries(о).map(([к,з])=>к+"="+з).join("\\n"); }\n\n$("пуск").onclick = async () => {\n  const адреса = $("адреса").value.trim();\n  const токен  = $("токен").value.trim();\n  const модель = $("модель").value.trim();\n  if (!адреса || !токен){ в.textContent = "Потрібні адреса й токен."; return; }\n  /* Не-ASCII тут падає ще до мережі — краще сказати це словами, ніж дати\n     людині дивитись на TypeError у консолі, якої на телефоні нема. */\n  if (/[^\\x00-\\x7F]/.test(токен)){\n    в.textContent = "✗ Токен має не-ASCII символ. Заголовки HTTP приймають лише "\n                  + "латиницю й цифри — кириличний токен не пройде навіть до мосту.";\n    return;\n  }\n  try{\n    localStorage.setItem("міст:адреса", адреса);\n    localStorage.setItem("міст:токен", токен);\n    localStorage.setItem("міст:модель", модель);\n  }catch(_){}\n\n  $("пуск").disabled = true;\n  в.textContent = "Стукаю…\\nпоходження: " + location.origin;\n  const почато = Date.now();\n  let відп;\n  try{\n    відп = await fetch(адреса, {\n      method: "POST",\n      headers: {"Content-Type":"application/json", "x-lyusterko-token": токен},\n      /* Найдешевший можливий запит: одне слово, стеля 16 токенів. Мета —\n         перевірити ШЛЯХ, а не якість моделі. Стеля 256, а не 16: Flash мислить\n         за замовчуванням, і думки рахуються ПРОТИ неї — на 16 весь бюджет\n         з'їдали думки, текст був порожній, а виглядало це як «модель мовчить». */\n      body: JSON.stringify({model: модель, max_tokens: 256,\n        messages: [{role:"user", content:[{type:"text",\n          text:"Відповідай одним словом українською: яка зараз пора року в Україні у вересні?"}]}]}),\n    });\n  }catch(e){\n    в.innerHTML = '<span class="зле">✗ Не достукався взагалі.</span>\\n\\n'\n      + String(e) + "\\n\\n"\n      + "Найчастіші причини, у порядку ймовірності:\\n"\n      + "· адреса з друкарською помилкою або воркер не задеплоєний\\n"\n      + "· у ДОЗВОЛЕНІ_ПОХОДЖЕННЯ немає «" + location.origin + "»\\n"\n      + "  (саме це походження треба вписати у worker.js і передеплоїти)\\n"\n      + "· браузер зарізав змішаний вміст: сторінка http, міст https";\n    $("пуск").disabled = false; return;\n  }\n\n  const заг = {};\n  відп.headers.forEach((з,і)=>{ заг[і] = з; });\n  const сире = await відп.text();\n  const час = ((Date.now()-почато)/1000).toFixed(1);\n\n  if (!відп.ok){\n    let підказка = "";\n    if (відп.status === 403) підказка = "Міст ЖИВИЙ, але не пускає це походження.\\n"\n      + "Впиши «" + location.origin + "» у ДОЗВОЛЕНІ_ПОХОДЖЕННЯ й передеплой.";\n    else if (відп.status === 401 && /ACCESS_TOKEN_TYPE_UNSUPPORTED|invalid authentication/i.test(сире))\n      підказка = "МІСТ ПРАЦЮЄ. Відмовив САМ GOOGLE: ключ формату AQ. його\\n"\n      + "Generative Language API не приймає для цього проєкту.\\n"\n      + "Це відома біда переходу AIza → AQ, і вона не в твоєму коді.\\n"\n      + "Що робити: натисни «Copy cURL quickstart» на сторінці ключа —\\n"\n      + "там Google сам пише, як зараз кликати. Якщо там інший заголовок\\n"\n      + "або інша адреса — покажи мені, і я поправлю міст за десять хвилин.";\n    else if (відп.status === 401 && /"м/.test(сире)) підказка = "Міст живий і пускає "\n      + "походження, але ТОКЕН невідомий.\\nПеревір секрет TESTER_TOKENS — через кому, без пробілів.";\n    else if (відп.status === 401) підказка = "401 прийшов від провайдера, не від мосту:\\n"\n      + "ключ не підійшов. Дивись тіло нижче — воно від Google.";\n    else if (відп.status === 400) підказка = "Міст живий, але не впізнав модель.\\n"\n      + "Ім'я має починатись на gemini- або claude-.";\n    else if (відп.status === 404) підказка = "МОДЕЛІ З ТАКИМ ІМЕНЕМ НЕМА.\\n"\n      + "Це найчастіша поломка: каталог Google рухається, і ім'я треба звірити\\n"\n      + "в AI Studio. Пробуй інші, міняючи лише поле «модель».";\n    else if (відп.status === 429) підказка = "Квота вичерпана або запити занадто часті.\\n"\n      + "На дармовому тарифі Gemini це 10–15 запитів на хвилину.";\n    else if (відп.status === 503) підказка =\n      "МОДЕЛЬ ПЕРЕВАНТАЖЕНА (сплеск попиту в Google, тимчасово). Міст уже спробував\\n"\n      + "двічі. Що робити: повторити за хвилину, або задати на воркері\\n"\n      + "GEMINI_FALLBACK=gemini-3.5-flash-lite — тоді міст сам перейде на неї,\\n"\n      + "а яка модель відповіла, покаже рядок «відповіла».";\n    else if (відп.status === 504 || відп.status === 524) підказка =\n      "МІСТ ПРАЦЮЄ — МОВЧИТЬ МОДЕЛЬ. Спроби й секунди — у тілі нижче.\\n"\n      + "Це латентність провайдера, не міст. Що робити: інше ім'я моделі в полі\\n"\n      + "«модель» (напр. gemini-2.5-flash-lite), змінна GEMINI_THINKING=off,\\n"\n      + "і GEMINI_FALLBACK=gemini-2.5-flash-lite,gemini-2.5-flash на воркері —\\n"\n      + "тоді міст сам перейде на наступну, коли основна мовчить.";\n    else if (відп.status === 500 && /секрета/.test(сире)) підказка =\n      "Міст живий, але секрета з ключем на ньому нема.\\n"\n      + "Додай GEMINI_API_KEY (або ANTHROPIC_API_KEY) у Variables and Secrets.";\n    в.innerHTML = '<span class="зле">✗ HTTP ' + відп.status + '</span>  ·  ' + час + " с\\n\\n"\n      + (підказка ? підказка + "\\n\\n" : "")\n      + "тіло відповіді:\\n" + сире.slice(0, 900) + "\\n\\nзаголовки:\\n" + рядок(заг);\n    $("пуск").disabled = false; return;\n  }\n\n  let д; try{ д = JSON.parse(сире); }catch{ д = null; }\n  const текст = д && (д.content||[]).map(б=>б.text||"").join(" ").trim();\n  const u = (д && д.usage) || {};\n  в.innerHTML = '<span class="добре">✓ Міст працює.</span>  ·  ' + час + " с\\n\\n"\n    + "провайдер   : " + (заг["x-provider"] || "?") + "\\n"\n    + "відповіла   : " + (заг["x-model"] || "?") + (заг["x-attempts"] ? "  (спроби: " + заг["x-attempts"] + ")" : "") + "\\n"\n    + "модель      : " + модель + "\\n"\n    + "відповідь   : " + (текст || "(порожньо)") + "\\n"\n    + "токени      : вхід " + (u.input_tokens ?? "?") + " · вихід " + (u.output_tokens ?? "?")\n    + (u.thinking_tokens ? " (з них думок " + u.thinking_tokens + ")" : "") + "\\n"\n    + "мислення    : " + ({"thinkingLevel":"обмежене (рівень)",\n                          "thinkingBudget":"обмежене (бюджет)",\n                          "as-is":"як у моделі за замовчуванням",\n                          "dropped-after-400":"⚠ модель не приймає це поле — знято"}\n                         [заг["x-thinking"]] || заг["x-thinking"] || "?") + "\\n"\n    + "stop_reason : " + (д && д.stop_reason) + "\\n"\n    + "прогонів    : " + (заг["x-runs-left"] || "n/a") + "\\n\\n"\n    + "Тепер це саме ім'я моделі можна ставити в МОДЕЛЬ_П у показі,\\n"\n    + "а показ відкривати з #міст=" + адреса + "&т=" + токен;\n  $("пуск").disabled = false;\n};\n</script>\n</body>\n</html>\n`;
