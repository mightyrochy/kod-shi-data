/* Прогін МОСТУ (worker.js) у node без мережі: `fetch` підмінено заглушкою, яка
   ЗАПИСУЄ, що воркер послав би провайдеру, і віддає канонну відповідь.
   Ловить те, чого не бачить ні `node --check`, ні проба в браузері:
   що саме йде в Anthropic/Google, як перекладається відповідь, чи каскад
   мислення справді крутиться.

   Запуск:  python3 скласти.py && node тест_мосту.js
   (тестується СКЛАДЕНИЙ worker.js — те, що деплоїться, а не джерело). */
const fs = require("fs");
const path = require("path");
const os = require("os");
const {pathToFileURL} = require("url");

let провалів = 0;
const тест = (н, у, що) => { if (у) console.log("  ✓ " + н);
  else { провалів++; console.log("  ✗ " + н + "  →  " + JSON.stringify(що)); } };

/* ── ФІКСТУРА ФОТО: СПРАВЖНЯ СИГНАТУРА І НЕ МЕНША ЗА 1 КБ ───────────────────
   Тут довго лежали «фото» на 8 і 4 байти й буфер із самих нулів. Воркер 04.09
   навчився відсівати заглушки крамниць саме за цими двома ознаками
   (`сигнатура_картинки` + `байти.length < 1024` у `підготувати`), і відтоді ВСІ
   п'ять звірок про фото були червоні — не тому, що міст їх не тягне, а тому,
   що фікстура подавала йому рівно те, що він зобов'язаний викидати. Звірки
   описували продукт вірно, брехала фікстура. Тепер вона віддає те, що віддала
   б крамниця: PNG-сигнатура попереду, вага понад кілобайт. */
const пнг = байтів => {
  const б = new Uint8Array(Math.max(1024, байтів));
  б.set([137, 80, 78, 71, 13, 10, 26, 10]);   // \x89PNG\r\n\x1a\n
  return б;
};

(async () => {
  const тут = __dirname;
  const сир = fs.readFileSync(path.join(тут, "worker.js"), "utf-8")
    .replace(/export\s*\{\s*worker_default as default\s*\}\s*;?/, "const М = worker_default;")
    .replace(/^export default/m, "const М =");
  const тимчасовийМодуль = path.join(os.tmpdir(), "_міст_тест.mjs");
  fs.writeFileSync(тимчасовийМодуль, сир + "\nexport {М};");
  const {М} = await import(pathToFileURL(тимчасовийМодуль).href);

  /* заглушка провайдера: пам'ятає кожен вихідний виклик */
  const вихідні = [];
  let відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}],
      stop_reason:"end_turn", usage:{input_tokens:5, output_tokens:1}}),
    {status:200, headers:{"anthropic-ratelimit-requests-remaining":"49"}});
  /* фото за адресою: воркер тягне їх сам — заглушка віддає «картинку» на
     img.example і 404 на dead.example; такі виклики в `вихідні` не йдуть */
  const фотоЗапити = [];
  globalThis.fetch = async (url, opts) => {
    const u = String(url);
    if (/img\.example|dead\.example/.test(u)) {
      фотоЗапити.push(u);
      if (/dead/.test(u)) return new Response("нема", {status:404});
      return new Response(пнг(2048), {status:200, headers:{"content-type":"image/png"}});
    }
    вихідні.push({url:u, headers:opts.headers, body:JSON.parse(opts.body)});
    /* як справжній fetch: abort через signal → відхилення, навіть якщо провайдер висить */
    return new Promise((рез, від) => {
      if (opts.signal) opts.signal.addEventListener("abort", () => від(new Error("AbortError: стеля часу")));
      Promise.resolve(відповідач(вихідні.length)).then(рез, від);
    });
  };
  const env = {ALLOWED_ORIGINS:"https://mightyrochy.github.io", TESTER_TOKENS:"tok-a1,tok-b2",
               ANTHROPIC_API_KEY:"sk-тест", GEMINI_API_KEY:"AQ.тест"};
  const зап = (тіло, {origin="https://mightyrochy.github.io", токен="tok-a1", method="POST"}={}) =>
    М.fetch(new Request("https://w.workers.dev/", {method,
      headers:{"content-type":"application/json", "Origin":origin, "x-lyusterko-token":токен},
      body: method === "POST" ? JSON.stringify(тіло) : undefined}), env);

  console.log("1. ДВЕРІ: походження, токен, метод");
  let в = await М.fetch(new Request("https://w.workers.dev/", {method:"GET"}), env);
  тест("GET віддає сторінку-пробу (200, html, кнопка є)",
       в.status === 200 && /text\/html/.test(в.headers.get("content-type"))
       && /Перевірити міст/.test(await в.text()), в.status);
  в = await зап({model:"claude-sonnet-5", messages:[]}, {origin:"https://evil.example"});
  тест("чуже походження → 403", в.status === 403, в.status);
  в = await зап({model:"claude-sonnet-5", messages:[]}, {токен:"tok-zz"});
  тест("невідомий токен → 401", в.status === 401, в.status);
  в = await зап({model:"gpt-5", messages:[]});
  тест("модель без відомого префікса → 400 і названо префікси",
       в.status === 400 && /claude-.*gemini-|gemini-.*claude-/.test(await в.text()), в.status);
  в = await зап({model:"claude-sonnet-5", messages:[]}, {origin:"https://w.workers.dev"});
  тест("власне походження воркера пускається завжди (проба стукає сама до себе)",
       в.status === 200, в.status);

  console.log("2. МАРШРУТ claude-: рідний формат БЕЗ службового поля");
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", max_tokens:800,
                 messages:[{role:"user", content:[{type:"text", text:"привіт"}]}]});
  const а = вихідні[0] || {};
  тест("один виклик, на api.anthropic.com", вихідні.length === 1 && /api\.anthropic\.com/.test(а.url), а.url);
  тест("ключ і версія у заголовках", а.headers && а.headers["x-api-key"] === "sk-тест"
       && a_версія(а.headers), а.headers);
  тест("у тілі НЕМА `_думки` (Anthropic на зайве поле віддає 400)",
       а.body && !("_думки" in а.body), Object.keys(а.body || {}));
  тест("модель і повідомлення доїхали як є; max_tokens = стеля сторінки + запас на думки (12000)",
       а.body && а.body.model === "claude-sonnet-5" && а.body.max_tokens === 800 + 12000
       && а.body.messages[0].content[0].text === "привіт", а.body);
  тест("effort low за замовчуванням — полем output_config (Claude 5.5 мислить завжди)",
       а.body && а.body.output_config && а.body.output_config.effort === "low" && !("thinking" in а.body), а.body);
  тест("відповідь 200 віддається як є", в.status === 200 && (await в.clone().json()).content[0].text === "ок", в.status);
  тест("заголовки лімітів Anthropic проходять наскрізь і відкриті для сторінки",
       в.headers.get("anthropic-ratelimit-requests-remaining") === "49"
       && /anthropic-ratelimit-requests-remaining/.test(в.headers.get("Access-Control-Expose-Headers")),
       [...в.headers.keys()]);
  тест("x-provider=anthropic, x-thinking=effort",
       в.headers.get("x-provider") === "anthropic" && в.headers.get("x-thinking") === "effort",
       [в.headers.get("x-provider"), в.headers.get("x-thinking")]);
  вихідні.length = 0;
  в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":"https://mightyrochy.github.io", "x-lyusterko-token":"tok-a1"},
      body:JSON.stringify({model:"claude-sonnet-5-5", messages:[{role:"user", content:"x"}]})}), {...env, CLAUDE_EFFORT:"as-is"});
  тест("CLAUDE_EFFORT=as-is → поля effort нема, x-thinking=as-is; стеля без max_tokens сторінки — 4000 + запас",
       в.status === 200 && !("output_config" in вихідні[0].body) && вихідні[0].body.max_tokens === 16000
       && в.headers.get("x-thinking") === "as-is", [вихідні[0].body, в.headers.get("x-thinking")]);
  вихідні.length = 0;
  в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":"https://mightyrochy.github.io", "x-lyusterko-token":"tok-a1"},
      body:JSON.stringify({model:"claude-sonnet-5-5", messages:[{role:"user", content:"x"}]})}), {...env, CLAUDE_EFFORT:"medium", GEMINI_THINKING:"high"});
  тест("CLAUDE_EFFORT=medium → effort medium; змінна Gemini маршрут claude не чіпає",
       вихідні[0].body.output_config && вихідні[0].body.output_config.effort === "medium", вихідні[0].body);
  {
    let стук = 0;
    відповідач = () => (++стук === 1
      ? new Response(JSON.stringify({type:"error", error:{type:"invalid_request_error",
          message:"output_config.effort: This model does not support the effort parameter."}}), {status:400})
      : new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn",
          usage:{input_tokens:5, output_tokens:1}}), {status:200}));
    вихідні.length = 0;
    в = await зап({model:"claude-haiku-4-5", messages:[{role:"user", content:"x"}]});
    тест("400 через effort (стара модель) → повтор без поля, відповідь 200, x-thinking=dropped",
         в.status === 200 && вихідні.length === 2 && вихідні[0].body.output_config.effort === "low"
         && !("output_config" in вихідні[1].body) && в.headers.get("x-thinking") === "dropped",
         [в.status, вихідні.map(x => x.body.output_config), в.headers.get("x-thinking")]);
    /* кредити з підписки скінчились: Anthropic відповідає 400 з текстом про баланс */
    відповідач = () => new Response(JSON.stringify({type:"error", error:{type:"invalid_request_error",
        message:"Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits."}}), {status:400});
    вихідні.length = 0;
    в = await зап({model:"claude-sonnet-5-5", temperature:0, messages:[{role:"user", content:"x"}]});
    const тк = await в.clone().json().catch(() => ({}));
    тест("кредити скінчились → 402 credits_exhausted, один виклик (каскад і температура не крутяться)",
         в.status === 402 && (тк.error || {}).type === "credits_exhausted" && вихідні.length === 1
         && /credit balance is too low/.test((тк.error || {}).message || ""),
         [в.status, тк, вихідні.length]);
    відповідач = () => new Response(JSON.stringify({type:"error", error:{type:"billing_error", message:"billing issue"}}), {status:402});
    в = await зап({model:"claude-sonnet-5-5", messages:[{role:"user", content:"x"}]});
    тест("402 billing_error → теж credits_exhausted",
         в.status === 402 && ((await в.clone().json()).error || {}).type === "credits_exhausted", в.status);
    відповідач = () => new Response(JSON.stringify({type:"error", error:{message:"credit balance is too low"}}), {status:400});
    вихідні.length = 0;
    в = await зап({model:"gemini-3.8-flash", messages:[{role:"user", content:"x"}]});
    тест("маршрут gemini- той самий текст не перекладає в credits_exhausted (розпізнання — провайдера anthropic)",
         в.status !== 402, в.status);
    відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}],
        stop_reason:"end_turn", usage:{input_tokens:5, output_tokens:1}}), {status:200,
        headers:{"anthropic-ratelimit-requests-remaining":"49"}});
  }
  function a_версія(h){ return !!h["anthropic-version"]; }

  console.log("3. МАРШРУТ gemini-: переклад туди й назад");
  вихідні.length = 0;
  відповідач = () => new Response(JSON.stringify({
    candidates:[{content:{parts:[{text:"Осінь"}, {inlineData:{mimeType:"image/png", data:"AAAA"}}]},
                 finishReason:"MAX_TOKENS"}],
    usageMetadata:{promptTokenCount:100, candidatesTokenCount:13, thoughtsTokenCount:117}}), {status:200});
  в = await зап({model:"gemini-flash-latest", max_tokens:9999,
                 messages:[{role:"user", content:[{type:"image", source:{type:"base64", media_type:"image/jpeg", data:"BBBB"}},
                                                   {type:"text", text:"хто на фото"}]},
                           {role:"assistant", content:"жінка"},
                           {role:"user", content:"опиши"}]});
  const г = вихідні[0] || {};
  тест("адреса generateContent з іменем моделі", /generativelanguage.*gemini-flash-latest:generateContent/.test(г.url), г.url);
  тест("ключ у x-goog-api-key", г.headers && г.headers["x-goog-api-key"] === "AQ.тест", г.headers);
  тест("ролі: assistant → model, картинка → inline_data",
       г.body && г.body.contents[1].role === "model"
       && г.body.contents[0].parts[0].inline_data && г.body.contents[0].parts[0].inline_data.data === "BBBB", г.body);
  тест("стеля виводу обрізана до СТЕЛІ мосту (4000), мислення задане (thinkingLevel minimal за замовчуванням)",
       г.body && г.body.generationConfig.maxOutputTokens === 4000
       && г.body.generationConfig.thinkingConfig && г.body.generationConfig.thinkingConfig.thinkingLevel === "minimal",
       г.body && г.body.generationConfig);
  const дг = await в.json();
  тест("відповідь у контракті Anthropic: text + image блоки",
       дг.content && дг.content[0].type === "text" && дг.content[0].text === "Осінь"
       && дг.content[1].type === "image" && дг.content[1].source.data === "AAAA"
       && дг.content[1].source.media_type === "image/png", дг.content);
  тест("MAX_TOKENS → stop_reason max_tokens", дг.stop_reason === "max_tokens", дг.stop_reason);
  тест("вихідні токени = текст + думки, думки окремим числом",
       дг.usage.input_tokens === 100 && дг.usage.output_tokens === 130 && дг.usage.thinking_tokens === 117, дг.usage);
  тест("x-provider=gemini, x-thinking=thinkingLevel",
       в.headers.get("x-provider") === "gemini" && в.headers.get("x-thinking") === "thinkingLevel",
       [в.headers.get("x-provider"), в.headers.get("x-thinking")]);

  console.log("3т. ТЕМПЕРАТУРА ДОХОДИТЬ ДО ОБОХ ПРОВАЙДЕРІВ (рядок 158)");
  /* Показ шле `temperature: 0` (`мовний_шар.ВИБІРКА`), бо «однакова репліка → один
     паспорт» тримається лише на ній. Маршрут `gemini-` будує тіло нанову, тож поле
     треба перекласти в `generationConfig`; маршрут `claude-` віддає тіло як є. */
  відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}],
      usageMetadata:{}}), {status:200});
  вихідні.length = 0;
  в = await зап({model:"gemini-flash-latest", temperature:0, messages:[{role:"user", content:"x"}]});
  тест("gemini: temperature 0 → generationConfig.temperature 0 (не зникає)",
       вихідні.length === 1 && вихідні[0].body.generationConfig.temperature === 0,
       вихідні[0] && вихідні[0].body.generationConfig);
  тест("gemini: заголовок x-temperature називає, що поїхало, і відкритий сторінці",
       в.headers.get("x-temperature") === "0"
       && /x-temperature/.test(в.headers.get("Access-Control-Expose-Headers")), в.headers.get("x-temperature"));
  вихідні.length = 0;
  в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]});
  тест("gemini без температури: поля в generationConfig нема, x-temperature=n/a",
       вихідні.length === 1 && !("temperature" in вихідні[0].body.generationConfig)
       && в.headers.get("x-temperature") === "n/a", вихідні[0] && вихідні[0].body.generationConfig);
  вихідні.length = 0;
  в = await зап({model:"gemini-flash-latest", temperature:"нуль", messages:[{role:"user", content:"x"}]});
  тест("gemini: не-число знімає поле (інакше 400 «temperature» замість відповіді)",
       вихідні.length === 1 && !("temperature" in вихідні[0].body.generationConfig)
       && в.headers.get("x-temperature") === "n/a", вихідні[0] && вихідні[0].body.generationConfig);
  відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}],
      stop_reason:"end_turn", usage:{input_tokens:5, output_tokens:1}}), {status:200});
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", temperature:0, messages:[{role:"user", content:"x"}]});
  тест("claude: temperature 0 до Anthropic не їде (Claude 5 відкидає нетипову — другий виклик), x-temperature=n/a",
       вихідні.length === 1 && !("temperature" in вихідні[0].body)
       && в.headers.get("x-temperature") === "n/a", вихідні[0] && вихідні[0].body);
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", temperature:null, messages:[{role:"user", content:"x"}]});
  тест("claude: temperature null знімається з тіла (Anthropic віддав би 400)",
       вихідні.length === 1 && !("temperature" in вихідні[0].body)
       && в.headers.get("x-temperature") === "n/a", вихідні[0] && вихідні[0].body);

  /* Наряд «Модель-збої-один-шлях»: доти міст слав `temperature: 0`, діставав 400 «Sampling parameters…», знімав поле
     й повторював — 38 з 67 викликів с8 ішли двічі. Тепер поле не їде, і 400 зі словом sampling — чужа помилка як є,
     один виклик, без повтору. */
  відповідач = () => new Response(JSON.stringify({type:"error", error:{type:"invalid_request_error",
      message:"temperature: Sampling parameters are not supported for this model."}}), {status:400});
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", temperature:0, messages:[{role:"user", content:"x"}]});
  тест("claude: 400 зі словом sampling — один виклик, повтору нема, x-attempts з одним записом",
       в.status === 400 && вихідні.length === 1 && !/dropped/.test(в.headers.get("x-attempts") || "")
       && (в.headers.get("x-attempts") || "").split(" ").length === 1,
       [в.status, вихідні.length, в.headers.get("x-attempts")]);
  відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}],
      stop_reason:"end_turn", usage:{input_tokens:5, output_tokens:1}}), {status:200});

  console.log("3к. КЕШ НЕЗМІННОГО ПОЧАТКУ ЗАПИТУ (наряд К-4)");
  /* Збирач ставить `task` ПЕРШИМ (`збирач_промптів.зібрати`), і міст ріже перший
     текстовий блок рівно на його закритій дужці: Anthropic пише кеш на межі
     `cache_control`, Gemini тримає неявний кеш сам на сталому префіксі. Склеєний текст
     мусить лишитись байт у байт тим самим — інакше змінився б промпт, а не лише ціна. */
  {
    const промпт = JSON.stringify({version:"1", task:{role:"r", rules:["a\"}b", "{c}"], answer_schema:{x:["<y>"]},
                                   input:["\"pool\" — items"], statement_codes:{too_few_items:"…"}},
                                   pool:[{n:"#1·01"}], outfits_wanted:4});
    const межа = промпт.indexOf(',"input"');
    відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn",
        usage:{input_tokens:5, output_tokens:1, cache_read_input_tokens:1200, cache_creation_input_tokens:0}}), {status:200});
    вихідні.length = 0;
    в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:[{type:"text", text:промпт}]}]});
    const бл = вихідні[0].body.messages[0].content;
    тест("claude: перший блок — рівно до коми перед «input» (далі — зібране з цих даних), cache_control ephemeral",
         бл.length === 2 && бл[0].text === промпт.slice(0, межа)
         && JSON.stringify(бл[0].cache_control) === '{"type":"ephemeral"}' && !бл[1].cache_control, бл);
    тест("claude: склеєні блоки — той самий промпт байт у байт (модель бачить те саме)",
         бл.map(б => б.text).join("") === промпт, бл.length);
    тест("прочитане з кешу видно заголовком x-cached-tokens, і він відкритий сторінці",
         в.headers.get("x-cached-tokens") === "1200"
         && /x-cached-tokens/.test(в.headers.get("Access-Control-Expose-Headers")), в.headers.get("x-cached-tokens"));
    /* Фото попереду — префікс несталий: різати нічого, інакше кеш лише писався б. */
    вихідні.length = 0;
    в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:[
      {type:"image", source:{type:"base64", media_type:"image/jpeg", data:"BBBB"}}, {type:"text", text:промпт}]}]});
    тест("claude: коли перед текстом стоїть фото, міст не ріже й не кешує нічого",
         вихідні[0].body.messages[0].content.length === 2
         && !вихідні[0].body.messages[0].content.some(б => б.cache_control), вихідні[0].body.messages[0].content);
    /* Промпт іншої будови (завдання не на початку) — теж без межі. */
    вихідні.length = 0;
    в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:[{type:"text",
      text:JSON.stringify({version:"1", pool:[1,2,3], task:{role:"r"}})}]}]});
    тест("claude: завдання не на початку промпта → межі нема, блок один",
         вихідні[0].body.messages[0].content.length === 1
         && !вихідні[0].body.messages[0].content[0].cache_control, вихідні[0].body.messages[0].content);
    /* Gemini: поля в тілі нема (неявний кеш), а `cachedContentTokenCount` ВІДНІМАЄТЬСЯ
       від `promptTokenCount` — Google рахує кеш усередині нього, показ додав би двічі. */
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}],
        usageMetadata:{promptTokenCount:5000, cachedContentTokenCount:4200, candidatesTokenCount:100}}), {status:200});
    в = await зап({model:"gemini-3.5-flash-lite", messages:[{role:"user", content:[{type:"text", text:промпт}]}]});
    const тг = вихідні[0].body.contents[0].parts;
    const дг = await в.json();
    тест("gemini: тіло як доти — один part, жодного cache_control (неявний кеш поля не просить)",
         тг.length === 1 && тг[0].text === промпт && !/cache_control/.test(JSON.stringify(вихідні[0].body)), тг);
    тест("gemini: кеш окремим числом, вхід без нього (5000 − 4200 = 800), x-cached-tokens=4200",
         дг.usage.input_tokens === 800 && дг.usage.cache_read_input_tokens === 4200
         && в.headers.get("x-cached-tokens") === "4200", дг.usage);
  }

  console.log("4. КАСКАД МИСЛЕННЯ: 400 через thinking → наступна форма → без поля");
  вихідні.length = 0;
  let n = 0;
  відповідач = () => { n++;
    if (n <= 3) return new Response(JSON.stringify({error:{message:"Unknown name thinkingLevel in thinkingConfig"}}), {status:400});
    return new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200});
  };
  в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]});
  /* 02.09: між minimal і budget з'явився щабель low (3.8 Flash minimal не знає) */
  тест("чотири спроби: thinkingLevel minimal → low → thinkingBudget → без поля", вихідні.length === 4
       && вихідні[0].body.generationConfig.thinkingConfig.thinkingLevel === "minimal"
       && вихідні[1].body.generationConfig.thinkingConfig.thinkingLevel === "low"
       && вихідні[2].body.generationConfig.thinkingConfig.thinkingBudget === 0
       && !("thinkingConfig" in вихідні[3].body.generationConfig), вихідні.map(x=>x.body.generationConfig));
  тест("вихід 200, x-thinking=dropped, stop_reason=stop", в.status === 200 && в.headers.get("x-thinking") === "dropped"
       && (await в.json()).stop_reason === "stop", в.headers.get("x-thinking"));
  вихідні.length = 0; n = 0;
  відповідач = () => new Response(JSON.stringify({error:{message:"API key not valid"}}), {status:400});
  в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]});
  тест("400 НЕ про мислення → каскад не крутиться, помилка як є", вихідні.length === 1 && в.status === 400, вихідні.length);
  вихідні.length = 0;
  в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]}, {}) ;
  вихідні.length = 0;
  const env2 = {...env, GEMINI_THINKING:"як є"};
  в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
      body:JSON.stringify({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]})}), env2);
  тест("GEMINI_THINKING=«як є» → жодного thinkingConfig, x-thinking=as-is",
       вихідні.length === 1 && !("thinkingConfig" in вихідні[0].body.generationConfig)
       && в.headers.get("x-thinking") === "as-is", вихідні[0] && вихідні[0].body.generationConfig);

  console.log("4б. ФОТО ЗА АДРЕСОЮ: Anthropic бере url сам, для Gemini тягне воркер");
  вихідні.length = 0; фотоЗапити.length = 0;
  відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn", usage:{}}), {status:200});
  в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:[
        {type:"text", text:"Photo 1:"}, {type:"image", source:{type:"url", url:"https://img.example/1.jpg"}},
        {type:"text", text:"Photo 2:"}, {type:"image", source:{type:"url", url:"https://dead.example/2.jpg"}},
        {type:"text", text:"Photo 3:"}, {type:"image", source:{type:"url", url:"https://img.example/3.jpg"}},
        {type:"text", text:"опиши"}]}]});
  /* Наряд «Модель-збої-один-шлях»: Anthropic сам кадру крамниці не діставав — 400 «Unable to download the file» на
     весь виклик (21 з 513 прогону через міст 20.11). Тепер фото тягне міст, як для Gemini й OpenAI. */
  const кл = вихідні[0].body.messages[0].content;
  тест("claude-: фото за адресою тягне міст — base64 у рідному блоці, url до Anthropic не йде",
       фотоЗапити.length === 3 && кл[1].type === "image" && кл[1].source.type === "base64"
       && кл[1].source.media_type === "image/png" && /^iVBOR/.test(кл[1].source.data)
       && !кл.some(б => б.source && б.source.type === "url"), кл.map(б => б.type + ":" + ((б.source || {}).type || б.text)));
  тест("claude-: мертве фото лишає своє місце «not delivered», третє лишається третім, виклик один, x-images-dropped=1",
       вихідні.length === 1 && кл.length === 7 && кл[3].type === "text" && /not delivered/.test(кл[3].text)
       && кл[4].text === "Photo 3:" && кл[5].type === "image" && кл[5].source.type === "base64"
       && в.status === 200 && в.headers.get("x-images-dropped") === "1",
       [вихідні.length, кл.map(б => б.type + ":" + ((б.source || {}).type || б.text)), в.headers.get("x-images-dropped")]);
  вихідні.length = 0; фотоЗапити.length = 0;
  відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200});
  в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:[
        {type:"image", source:{type:"url", url:"https://img.example/1.jpg"}},
        {type:"image", source:{type:"url", url:"https://dead.example/2.jpg"}},
        {type:"text", text:"опиши"}]}]});
  const частини = вихідні[0].body.contents[0].parts;
  /* ФОТО-513: мертве фото не зникає, а лишає своє місце текстом — номери кадрів за ним не зсуваються */
  тест("gemini-: воркер стягнув фото й вклав inline_data (image/png, base64), мертве фото лишило місце «not delivered», текст на місці",
       фотоЗапити.length === 2 && частини.length === 3 && частини[0].inline_data
       && частини[0].inline_data.mime_type === "image/png" && /^iVBOR/.test(частини[0].inline_data.data)
       && /not delivered/.test(частини[1].text) && !частини[1].inline_data && частини[2].text === "опиши",
       частини.map(ч => ч.text || "inline_data"));
  тест("x-images-dropped=1 і заголовок відкритий сторінці", в.headers.get("x-images-dropped") === "1"
       && /x-images-dropped/.test(в.headers.get("Access-Control-Expose-Headers")), в.headers.get("x-images-dropped"));

  /* Справжній декодований WebP 24×24 без MIME-заголовка.
     Anthropic завантажує URL сам: тут перевіряємо передачу URL і відмови,
     не приписуємо локальній заглушці перевірку байтів самим провайдером. */
  {
    const вебп = Buffer.from("UklGRhYHAABXRUJQVlA4TAkHAAAvF8AFAIVCAAAI27Zt27Zt27Zt27Zt27ZtWxsSAAAg28a2bdu2bdu2bdu2bdveMtu2fUoAAIBgE9u2bVvDbdu2bdu2bdu2bdvM9T/igM5Pd3Vgvilx5pqwOOPwwrJHb0J7dghe+VGfp4Sbb9O6BGuNZrxnYO+B3G2vR6QxjifPf/EtGqrUP16CZz4dL0igD9UnqmlvqAzFzrWIzb1hEUGFAkR6/ZL+kUi7TyO833q4vYvGuWYurOe2sRZDkIuPCPjoXyPU4ucdAsRR/b5uhXMN/FRv+aKwAVgzbQ7qr1EWYDDYsOkJx2IPbtzesT3OvkELALauE0TGD8KyOYHE/K1OptSgOlG1Ffal0DoeFvUSeGjL7Y+fnWyg1Vv9edIu+cNdVB4OzmtzD1GdC2E37EpZkWWe4LCi3N5Ft+vM0YsRQ3qqKJgBk2MrkM5/PGSznSD+oszgNHGEhHbnqh52Fg2qQVwxDWXMWQrlXevamRzyyb6lNoWShaFac0RsEU2uWPDzUD08ey/hKwLX7B2x9khk+6iRCwIfXGIIBn2GuORwmYhE0naR19bQd/f4XsZmRG/mt9S+LLWqxPNrN6UIXpzHj3e6TPxP/XeVEo69U4pPP4k1EoCT71EJuYt6c9u+v8zJhYvQteek+b2ETI9p5CoLZWncLm++3RhSuYaHdXboy898URYrsgLFi8W6+OfbwJlo+SYiEDXRKmCDvx9lSPwBKY80MXGRF20vDKDZaIqrDoeOqhxkM0IaCtm3aEZi7SSASd5GDhWk4juDL+D/liKEEFQTGZ74TjeICtOdfvPU0ciqaWDkioZINQEtNrMUrPqC5bT/bGHvINQbJy63KbW6Yd22BbZcyaNLT/senoKzJVbMzC25L0oLFfokxLJyVt1U5Ky9WLA5ta1jVA9hs0/L/Ja1uhHLu26k5FLZ5eMmheJfTFIBH9sQI3nYsg80Owaqu1UDxftZIdCJ1RRHWgCiPDo3h2CvRFtJzWooazwTCKpK+zYXB8/dXlJe636yaOpLoO+siaoVXzrDQGfJsxV3P3UhOvCCQaBtOADoqGgDTrgzYkbJcl59gfqJHQ9TxBVo5hJms/qSBqaLCe4mr0zg9plwHufsgYev77Iul90mASxzpa5tuWAAXUKSTApuYHHTg/z56jlkQvetslEoXRuJciZTiIMSiR5WIZTC65Fx4PG+4+Rk0okqD9vmw6hNTogUXzRrk1q9Skvv565wMI6m3omWqU2nAmiE7+UpsuOuFUd3rxGK4SOcRAFKxsECJYCxRpkvgnkxjDTQK3zenIu6zAatc7JQwDioyPMrfZIRNxyKdmNKu/mQBzuANzWQ+wP9X6rcrgB17Do290x+EJixhMX1wyzOaokKhPqGNDLEKni6BB7szUA2RWNIcEwBA9PbLAWQMQxn0em5Rz0sco/AkPtHD0xJta0Sj9iCmyw0b9tTixnSRyBl/GR3FLDs5Vl1+wrp5yv6dzB1QZ7Q7eGsDWkn1sEJdiHY26RuMvfqwEDBqk5uyuYdKRNORJcejegsqO0KU8Dh69z6p/zkPcUX39Jv569GSBTRj+B5V9H4CqpzLqRnhaR8IkgQK35M5yi0X1gMilNC5H9gePISD01QNF0cB2arCRE2xP9pEYqROMdYnvZnDi/qHkDTRiGjU7MpTKkEdMDBeabJN0w+jEG/yYyTvrU8kWF+W0nZhpKyOSRwzrU88m82ij7W+aZB1nGNHZYvzQ1nqNxgUJuLqGQjkZ2iGJQgj20hVR1+1meq3ku/kvIH3iqUhiDoYp+y3JIekCU3EfXGgxc2HF2Lx3P8Td6x9rQOK7k0c/mIpg/1/1Pol5uOC5YcTqYgdoRXawxEyeFwFu9vIRXVoBuevbY9mUJNEGsZuyMNMXcMHd4rK7OWNgzlyTIDMLoFHn+etboVBfypzkChBwxw9GOV3u3kT/2RUBj6IxM0hML3FacxoUEXd/2MrPQHTOiOBWybyi9ofAm4X5+fERLnEss/AusZ/g11i13T44wsFtWMfXFqTRX4k6GSfL/V01yBpy3SFQBWapno8cRuDD3q8blQIyDN4FEC2QGzwh27pX3jCD6XgzcNfSLUqyd2+YORY1xt3vQO3iiY0n9qFeX3cpA+YbdfEhQbJZuif9GGf/JWi2JInC+kR5FSYU9XsEW6CHPEkZhr2i6OYxgSULd+Nvg7xQQytzrWMf1zPDnu8d7djwsx7dlBiXnH4+lAtePdad+kR6ze2g8EmbioBH2eBqxtUxwocbh0PJ/Ht6xZhKoMUWYvp4oAF3LYci35D3gyH372xcQt7UZ9vp4hmF7uO1cY5vn90EvDs1agVVEvxXl9XkfdUEL7stY1MVxi2DAzLljns8CcaEXVbH+1qer9Z/TxsNA8BIsP/M5FsLAEAA==", "base64");
    const адреса = "https://img.example/no-content-type.webp";
    const старий = globalThis.fetch;
    let байти = вебп;
    globalThis.fetch = async (url, opts) => String(url) === адреса
      ? (фотоЗапити.push(адреса), new Response(байти, {status:200})) : старий(url, opts);
    for (const картинка of [true, false]) {
      байти = картинка ? вебп : new TextEncoder().encode("<html>не фото</html>".repeat(100));
      вихідні.length = 0; фотоЗапити.length = 0;
      відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}]}), {status:200});
      в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:[
        {type:"image", source:{type:"url", url:адреса}}]}]});
      const кадр = вихідні[0].body.contents[0].parts[0];
      тест("Gemini: 200 без content-type — " + (картинка ? "WebP доходить без втрат" : "не-картинка випадає"),
        в.status === 200 && фотоЗапити.length === 1 && в.headers.get("x-images-dropped") === (картинка ? "0" : "1")
        && (картинка ? кадр.inline_data?.mime_type === "image/webp" && кадр.inline_data.data === вебп.toString("base64")
                     : !кадр.inline_data && /not delivered/.test(кадр.text)), кадр);
      /* Anthropic — той самий шлях фото, що й Gemini (наряд «Модель-збої-один-шлях»): міст тягне байти сам */
      вихідні.length = 0; фотоЗапити.length = 0;
      відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"є"}], usage:{}}), {status:200});
      в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:[
        {type:"image", source:{type:"url", url:адреса}}]}]});
      const блок = вихідні[0].body.messages[0].content[0];
      тест("Anthropic: 200 без content-type — " + (картинка ? "WebP доходить base64 без втрат" : "не-картинка випадає, виклик іде"),
        в.status === 200 && фотоЗапити.length === 1 && в.headers.get("x-images-dropped") === (картинка ? "0" : "1")
        && (картинка ? блок.source && блок.source.type === "base64" && блок.source.media_type === "image/webp"
                       && блок.source.data === вебп.toString("base64")
                     : !блок.source && /not delivered/.test(блок.text)), блок);
    }
    globalThis.fetch = старий;
  }

  console.log("4б-2. ФОТО ТЯГНУТЬСЯ ПАРАЛЕЛЬНО Й ІЗ СПІЛЬНОЮ СТЕЛЕЮ ВАГИ");
  {
    вихідні.length = 0; фотоЗапити.length = 0;
    /* важкі фото: кожне 5 МБ, у стелю 14 МБ влізе лише два з чотирьох */
    const важке = пнг(3.5 * 1024 * 1024);
    const старий = globalThis.fetch;
    globalThis.fetch = async (url, opts) => {
      const u = String(url);
      if (/img\.example/.test(u)) { фотоЗапити.push(u);
        return new Response(важке, {status:200, headers:{"content-type":"image/jpeg"}}); }
      return старий(url, opts);
    };
    відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200});
    в = await зап({model:"gemini-3.6-flash", messages:[{role:"user", content:[
      {type:"image", source:{type:"url", url:"https://img.example/1.jpg"}},
      {type:"image", source:{type:"url", url:"https://img.example/2.jpg"}},
      {type:"image", source:{type:"url", url:"https://img.example/3.jpg"}},
      {type:"image", source:{type:"url", url:"https://img.example/4.jpg"}},
      {type:"text", text:"опиши"}]}]});
    const ч = вихідні[0].body.contents[0].parts.filter(x=>x.inline_data);
    тест("чотири фото по 3.5 МБ → у запит увійшли перші чотири (14 МБ рівно); п'яте випало б",
         фотоЗапити.length === 4 && ч.length === 4 && в.headers.get("x-images-dropped") === "0",
         [фотоЗапити.length, ч.length, в.headers.get("x-images-dropped")]);
    вихідні.length = 0; фотоЗапити.length = 0;
    в = await зап({model:"gemini-3.6-flash", messages:[{role:"user", content:[
      ...[1,2,3,4,5].map(i=>({type:"image", source:{type:"url", url:"https://img.example/" + i + ".jpg"}})),
      {type:"text", text:"опиши"}]}]});
    const ч5 = вихідні[0].body.contents[0].parts.filter(x=>x.inline_data);
    тест("п'ять по 3.5 МБ → чотири в запиті, одне випало (спільна стеля 14 МБ), виклик НЕ впав",
         ч5.length === 4 && в.headers.get("x-images-dropped") === "1" && в.status === 200,
         [ч5.length, в.headers.get("x-images-dropped"), в.status]);
    /* мертве фото серед живих не валить решту */
    вихідні.length = 0;
    globalThis.fetch = async (url, opts) => {
      const u = String(url);
      if (/dead\.example/.test(u)) return new Response("нема", {status:404});
      if (/img\.example/.test(u)) return new Response(пнг(2048), {status:200, headers:{"content-type":"image/png"}});
      return старий(url, opts);
    };
    в = await зап({model:"gemini-3.6-flash", messages:[{role:"user", content:[
      {type:"image", source:{type:"url", url:"https://img.example/1.jpg"}},
      {type:"image", source:{type:"url", url:"https://dead.example/2.jpg"}},
      {type:"image", source:{type:"url", url:"https://img.example/3.jpg"}},
      {type:"text", text:"опиши"}]}]});
    const чм = вихідні[0].body.contents[0].parts.filter(x=>x.inline_data);
    тест("мертве фото серед живих: живі доїхали, мертве випало, виклик 200",
         чм.length === 2 && в.headers.get("x-images-dropped") === "1" && в.status === 200,
         [чм.length, в.headers.get("x-images-dropped")]);
    globalThis.fetch = старий;
  }

  console.log("4б-3. КАСКАД МИСЛЕННЯ: minimal → low → budget 0 → без поля (3.8 Flash minimal не знає)");
  {
    вихідні.length = 0;
    let n = 0;
    відповідач = () => { n++;
      const форма = вихідні[n-1].body.generationConfig.thinkingConfig;
      if (форма && форма.thinkingLevel === "minimal")
        return new Response(JSON.stringify({error:{message:"thinking_level MINIMAL is not supported for this model"}}), {status:400});
      return new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200}); };
    в = await зап({model:"gemini-3.8-flash", messages:[{role:"user", content:"x"}]});
    тест("minimal відхилено → друга спроба low → 200; x-attempts несе причину відмови",
         в.status === 200 && n === 2 && вихідні[1].body.generationConfig.thinkingConfig.thinkingLevel === "low"
         && /minimal.*not supported/i.test(в.headers.get("x-attempts")) && в.headers.get("x-thinking") === "thinkingLevel",
         [n, в.headers.get("x-attempts")]);
  }

  console.log("4в. СТЕЛЯ ЧАСУ Й ДРАБИНА МОДЕЛЕЙ (524 → чесний 504, або наступна модель)");
  {
    /* провайдер віддає чужий 524 — воркер не пускає його далі, а каже 504 словами */
    вихідні.length = 0;
    відповідач = () => new Response("error code: 524", {status:524});
    в = await зап({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]});
    const т524 = await в.json();
    тест("524 від провайдера → 504 JSON із секундами й переліком спроб, x-attempts у заголовку",
         в.status === 504 && /не відповів за \d+ с/.test(т524.error.message) && /спроби:/.test(т524.error.message)
         && вихідні.length >= 1, [в.status, т524]);
    /* провайдер мовчить довше за стелю — драбина бере наступну модель */
    вихідні.length = 0;
    let n2 = 0;
    відповідач = () => { n2++;
      if (n2 === 1) return new Promise(() => {});                      // висить назавжди
      return new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200}); };
    const env_Д = {...env, PROVIDER_TIMEOUT_S:"5", GEMINI_FALLBACK:"gemini-2.5-flash-lite", GEMINI_THINKING:"як є"};
    const почато = Date.now();
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]})}), env_Д);
    const с = (Date.now() - почато) / 1000;
    тест("основна модель мовчить → після стелі (5 с) береться gemini-2.5-flash-lite → 200; x-model називає її; спроби в x-attempts",
         в.status === 200 && в.headers.get("x-model") === "gemini-2.5-flash-lite" && с >= 4.5 && с < 8
         && /gemini-flash-latest:as-is=504 gemini-2\.5-flash-lite:as-is=200/.test(в.headers.get("x-attempts"))
         && /generativelanguage.*gemini-2\.5-flash-lite:generateContent/.test(вихідні[1].url),
         [в.status, в.headers.get("x-model"), в.headers.get("x-attempts"), с.toFixed(1)]);
    /* без драбини — 504 після стелі, а не 125 с чужого 524 */
    вихідні.length = 0;
    відповідач = () => new Promise(() => {});
    const env_Б = {...env, PROVIDER_TIMEOUT_S:"5", GEMINI_THINKING:"як є"};
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gemini-flash-latest", messages:[{role:"user", content:"x"}]})}), env_Б);
    тест("без драбини: 504 після стелі, повідомлення радить інше ім'я моделі або GEMINI_FALLBACK",
         в.status === 504 && /GEMINI_FALLBACK/.test((await в.json()).error.message), в.status);
    /* стеля не заважає швидкій відповіді; claude- драбини не має */
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn", usage:{}}), {status:200});
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"claude-sonnet-5", messages:[{role:"user", content:"x"}]})}), {...env, GEMINI_FALLBACK:"gemini-2.5-flash"});
    тест("claude-: драбина Gemini не застосовується, один виклик, x-model=claude-sonnet-5",
         в.status === 200 && вихідні.length === 1 && в.headers.get("x-model") === "claude-sonnet-5", в.headers.get("x-attempts"));
  }

  console.log("4г. 503 «HIGH DEMAND»: повтор тієї самої моделі, лише потім драбина");
  {
    вихідні.length = 0;
    let n3 = 0;
    відповідач = () => { n3++;
      if (n3 === 1) return new Response(JSON.stringify({error:{code:503, message:"high demand", status:"UNAVAILABLE"}}), {status:503});
      return new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200}); };
    const env_Г = {...env, GEMINI_THINKING:"як є", GEMINI_FALLBACK:"gemini-3.5-flash-lite"};
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gemini-3.6-flash", messages:[{role:"user", content:"x"}]})}), env_Г);
    тест("503 → через 2.5 с та сама модель → 200; драбина не чіпалась; x-attempts показує обидві спроби",
         в.status === 200 && в.headers.get("x-model") === "gemini-3.6-flash" && n3 === 2
         && в.headers.get("x-attempts") === "gemini-3.6-flash:as-is=503 gemini-3.6-flash:as-is=200",
         [в.status, в.headers.get("x-model"), в.headers.get("x-attempts")]);
    вихідні.length = 0; n3 = 0;
    відповідач = () => { n3++;
      if (n3 <= 2) return new Response(JSON.stringify({error:{code:503, message:"high demand"}}), {status:503});
      return new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200}); };
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gemini-3.6-flash", messages:[{role:"user", content:"x"}]})}), env_Г);
    тест("503 двічі поспіль → драбина: gemini-3.5-flash-lite відповідає, x-model називає її",
         в.status === 200 && в.headers.get("x-model") === "gemini-3.5-flash-lite" && n3 === 3
         && /gemini-3\.6-flash:as-is=503 gemini-3\.6-flash:as-is=503 gemini-3\.5-flash-lite:as-is=200/.test(в.headers.get("x-attempts")),
         [в.status, в.headers.get("x-model"), в.headers.get("x-attempts")]);
    вихідні.length = 0; n3 = 0;
    відповідач = () => { n3++; return new Response(JSON.stringify({error:{code:503, message:"high demand"}}), {status:503}); };
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gemini-3.6-flash", messages:[{role:"user", content:"x"}]})}), {...env, GEMINI_THINKING:"як є"});
    тест("без драбини: 503 віддається як є після двох спроб (сторінка перечекає сама)", в.status === 503 && n3 === 2, [в.status, n3]);
  }

  console.log("4д. КАРТИНКОВА МОДЕЛЬ: responseModalities обов'язкові, драбина не підміняє її текстовою");
  {
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[
      {text:"ось"}, {inlineData:{mimeType:"image/png", data:"AAAA"}}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200});
    в = await зап({model:"gemini-3.1-flash-image", max_tokens:4000, messages:[{role:"user", content:[
      {type:"image", source:{type:"base64", media_type:"image/jpeg", data:"BBBB"}}, {type:"text", text:"одягни"}]}]});
    const гк = вихідні[0].body.generationConfig;
    тест("картинкова модель: responseModalities [TEXT,IMAGE] задано, thinkingConfig НЕ задано",
         JSON.stringify(гк.responseModalities) === '["TEXT","IMAGE"]' && !("thinkingConfig" in гк), гк);
    const дк = await в.json();
    тест("картинка доїхала блоком image у контракті Anthropic",
         дк.content.some(б=>б.type === "image" && б.source.data === "AAAA"), дк.content);
    вихідні.length = 0;
    let n5 = 0;
    відповідач = () => { n5++; return new Response(JSON.stringify({error:{code:503, message:"high demand"}}), {status:503}); };
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gemini-3.1-flash-image", messages:[{role:"user", content:"x"}]})}),
        {...env, GEMINI_FALLBACK:"gemini-3.5-flash-lite"});
    тест("503 на картинковій → драбина НЕ бере текстову модель (інакше був би опис замість картинки)",
         в.status === 503 && !/gemini-3\.5-flash-lite/.test(в.headers.get("x-attempts")), в.headers.get("x-attempts"));
    /* текстова модель — усе як було */
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[{text:"є"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200});
    в = await зап({model:"gemini-3.6-flash", messages:[{role:"user", content:"x"}]});
    тест("текстова модель: responseModalities НЕ додається, мислення задане",
         !("responseModalities" in вихідні[0].body.generationConfig)
         && !!вихідні[0].body.generationConfig.thinkingConfig, вихідні[0].body.generationConfig);
  }

  console.log("4е. NANO BANANA 2.1: маршрут Interactions поруч із generateContent (рядок 1600)");
  {
    const тілоП = (модель, зайве) => Object.assign({model:модель, max_tokens:4000, temperature:0, messages:[{role:"user", content:[
      {type:"image", source:{type:"base64", media_type:"image/jpeg", data:"WOMAN"}},
      {type:"image", source:{type:"base64", media_type:"image/png", data:"COAT"}},
      {type:"text", text:"одягни"}]}]}, зайве || {});
    /* NB2: той самий запит, що й до правки — generateContent, inline_data, responseModalities */
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({candidates:[{content:{parts:[
      {text:"ось"}, {inlineData:{mimeType:"image/png", data:"AAAA"}}]}, finishReason:"STOP"}],
      usageMetadata:{promptTokenCount:300, candidatesTokenCount:1290, thoughtsTokenCount:10}}), {status:200});
    в = await зап(тілоП("gemini-3.1-flash-image"));
    let г2 = вихідні[0];
    тест("NB2: /models/gemini-3.1-flash-image:generateContent, contents/inline_data, responseModalities, без input",
         /\/v1beta\/models\/gemini-3\.1-flash-image:generateContent$/.test(г2.url)
         && г2.body.contents[0].parts[0].inline_data.data === "WOMAN" && !("input" in г2.body)
         && JSON.stringify(г2.body.generationConfig.responseModalities) === '["TEXT","IMAGE"]', [г2.url, Object.keys(г2.body)]);
    let дд = await в.json();
    тест("NB2: відповідь і токени як було (вхід 300, вихід 1300, думок 10), x-route=generateContent",
         дд.usage.input_tokens === 300 && дд.usage.output_tokens === 1300 && дд.usage.thinking_tokens === 10
         && дд.content[1].source.data === "AAAA" && в.headers.get("x-route") === "generateContent", [дд.usage, в.headers.get("x-route")]);

    /* 2.1: POST /v1beta/interactions, input = [text/image…], response_format image, generation_config */
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({id:"v1_x", object:"interaction", model:"gemini-nano-banana-2.1", status:"completed",
      steps:[{type:"thought", summary:[{type:"image", data:"INTERIM", mime_type:"image/png"}]},
             {type:"model_output", content:[{type:"text", text:"ось"}, {type:"image", data:"CCCC", mime_type:"image/jpeg"}]}],
      usage:{total_input_tokens:300, total_output_tokens:1290, total_thought_tokens:10, total_cached_tokens:0, total_tokens:1600}}), {status:200});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    г2 = вихідні[0];
    тест("2.1: POST https://generativelanguage.googleapis.com/v1beta/interactions, ключ у x-goog-api-key",
         г2.url === "https://generativelanguage.googleapis.com/v1beta/interactions"
         && г2.headers["x-goog-api-key"] === "AQ.тест", [г2.url, г2.headers]);
    тест("2.1: тіло — model, input (image WOMAN, image COAT, text) у порядку, response_format image; без contents/generationConfig",
         г2.body.model === "gemini-nano-banana-2.1" && JSON.stringify(г2.body.input) === JSON.stringify([
           {type:"image", mime_type:"image/jpeg", data:"WOMAN"}, {type:"image", mime_type:"image/png", data:"COAT"},
           {type:"text", text:"одягни"}])
         && JSON.stringify(г2.body.response_format) === '{"type":"image"}'
         && !("contents" in г2.body) && !("generationConfig" in г2.body) && !("thinkingConfig" in (г2.body.generation_config || {})), г2.body);
    тест("2.1: generation_config.max_output_tokens=4000 і temperature=0 (так само, як для NB2)",
         г2.body.generation_config.max_output_tokens === 4000 && г2.body.generation_config.temperature === 0
         && в.headers.get("x-temperature") === "0", г2.body.generation_config);
    дд = await в.json();
    тест("2.1: відповідь — та сама структура: text + image (лише model_output, проміжну картинку thought не береться)",
         дд.content.length === 2 && дд.content[0].text === "ось" && дд.content[1].type === "image"
         && дд.content[1].source.data === "CCCC" && дд.content[1].source.media_type === "image/jpeg"
         && дд.stop_reason === "end_turn", дд.content);
    тест("2.1: токени тією ж структурою (вхід 300, вихід 1290+10, думок 10), x-route=interactions, x-route відкритий сторінці",
         дд.usage.input_tokens === 300 && дд.usage.output_tokens === 1300 && дд.usage.thinking_tokens === 10
         && дд.usage.cache_read_input_tokens === 0 && в.headers.get("x-route") === "interactions"
         && /x-route/.test(в.headers.get("Access-Control-Expose-Headers")), [дд.usage, в.headers.get("x-route")]);

    /* кеш віднімається від входу, як і в generateContent */
    відповідач = () => new Response(JSON.stringify({status:"completed", steps:[{type:"model_output", content:[{type:"image", data:"D", mime_type:"image/png"}]}],
      usage:{total_input_tokens:300, total_output_tokens:5, total_cached_tokens:100}}), {status:200});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    дд = await в.json();
    тест("2.1: кеш віднімається від входу (200 + 100 з кешу), x-cached-tokens=100",
         дд.usage.input_tokens === 200 && дд.usage.cache_read_input_tokens === 100 && в.headers.get("x-cached-tokens") === "100", дд.usage);

    /* фото за адресою тягне воркер і для 2.1 */
    вихідні.length = 0;
    в = await зап({model:"gemini-nano-banana-2.1", messages:[{role:"user", content:[
      {type:"image", source:{type:"url", url:"https://img.example/1.jpg"}}, {type:"text", text:"x"}]}]});
    тест("2.1: фото за адресою стягнуте воркером і вкладене як image/base64 у input",
         вихідні[0].body.input[0].type === "image" && вихідні[0].body.input[0].mime_type === "image/png"
         && /^iVBOR/.test(вихідні[0].body.input[0].data), вихідні[0].body.input[0]);

    /* температуру 2.1 не приймає → 400 зі словом temperature знімає її один раз */
    вихідні.length = 0;
    let n6 = 0;
    відповідач = () => ++n6 === 1
      ? new Response(JSON.stringify({error:{code:400, message:"Unsupported field: generation_config.temperature"}}), {status:400})
      : new Response(JSON.stringify({status:"completed", steps:[{type:"model_output", content:[{type:"image", data:"E", mime_type:"image/png"}]}], usage:{}}), {status:200});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    тест("2.1: 400 про temperature → повтор без неї (x-temperature=dropped)",
         в.status === 200 && вихідні.length === 2 && !("temperature" in вихідні[1].body.generation_config)
         && в.headers.get("x-temperature") === "dropped", [в.status, вихідні.length]);

    /* помилки провайдера не ковтаються */
    відповідач = () => new Response(JSON.stringify({error:{code:403, message:"Image generation is not enabled for this project", status:"PERMISSION_DENIED"}}), {status:403});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    let сир6 = await в.text();
    тест("2.1: HTTP-помилка Google віддається як є (403 і її текст)", в.status === 403 && /not enabled for this project/.test(сир6), [в.status, сир6]);
    відповідач = () => new Response(JSON.stringify({status:"failed", steps:[], errors:[{code:"https://errors.example/safety", message:"blocked by safety"}]}), {status:200});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    сир6 = await в.text();
    тест("2.1: 200 зі status=failed і errors → 422 (не 502: показ повторює 502 і платить прогони) з кодом і текстом Google, не порожній успіх",
         в.status === 422 && /status=failed/.test(сир6) && /blocked by safety/.test(сир6) && /errors\.example\/safety/.test(сир6), [в.status, сир6]);
    відповідач = () => new Response(JSON.stringify({status:"completed", steps:[{type:"model_output", content:[]}], usage:{}}), {status:200});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    сир6 = await в.text();
    тест("2.1: completed без тексту й картинки → 422 «нема ні тексту, ні картинки»", в.status === 422 && /нема ні тексту, ні картинки/.test(сир6), [в.status, сир6]);
    відповідач = () => new Response(JSON.stringify({status:"incomplete", steps:[{type:"model_output", content:[{type:"text", text:"обірвано"}]}], usage:{}}), {status:200});
    в = await зап(тілоП("gemini-nano-banana-2.1"));
    дд = await в.json();
    тест("2.1: status=incomplete → stop_reason max_tokens (сторінка скаже «обрізано»)", в.status === 200 && дд.stop_reason === "max_tokens", дд);

    /* історія повідомлень Interactions не підтримує — чесний 400 до мережі */
    вихідні.length = 0;
    в = await зап({model:"gemini-nano-banana-2.1", messages:[{role:"user", content:"a"}, {role:"assistant", content:"b"}, {role:"user", content:"c"}]});
    тест("2.1: три повідомлення → 400 до мережі з поясненням, провайдеру нічого не пішло",
         в.status === 400 && /одне повідомлення user/.test(await в.text()) && вихідні.length === 0, [в.status, вихідні.length]);

    /* 400 до мережі НЕ їсть добовий прогін: лічильник (KV) мовчить, поки запит не пішов до Google */
    {
      const сховище = {}; let путів = 0;
      const env6 = {...env, COUNTER:{get: async к => сховище[к] || null, put: async (к, з) => { путів++; сховище[к] = з; }}};
      const зап6 = тіло => М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify(тіло)}), env6);
      вихідні.length = 0;
      відповідач = () => new Response(JSON.stringify({status:"completed", steps:[{type:"model_output", content:[{type:"image", data:"F", mime_type:"image/png"}]}], usage:{}}), {status:200});
      в = await зап6({model:"gemini-nano-banana-2.1", messages:[{role:"user", content:"a"}, {role:"assistant", content:"b"}]});
      тест("2.1: 400 на кілька повідомлень — лічильник не чіпано (put 0), x-runs-left відсутній",
           в.status === 400 && путів === 0 && вихідні.length === 0, [в.status, путів]);
      в = await зап6({model:"gemini-nano-banana-2.1", messages:[{role:"user", content:"a"}]});
      тест("2.1: нормальний запит після нього — рівно один прогін списано (put 1, x-runs-left=39)",
           в.status === 200 && путів === 1 && в.headers.get("x-runs-left") === "39", [в.status, путів, в.headers.get("x-runs-left")]);
    }

    /* Anthropic і текстовий Gemini — без x-route=interactions */
    відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn", usage:{input_tokens:5, output_tokens:1}}), {status:200});
    в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:"x"}]});
    тест("claude-: x-route=messages", в.headers.get("x-route") === "messages", в.headers.get("x-route"));
  }

  console.log("4ж. OPENAI images/edits: заглушка за документованим форматом (наряд «Модель-примірка-на-OpenAI»)");
  {
    /* Формат — з developers.openai.com (довідник «Create image edit», 19.11.2026), живого виклику НЕ було. */
    const envО = {...env, OPENAI_API_KEY:"sk-openai-тест"};
    const запО = тіло => М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
      body:JSON.stringify(тіло)}), envО);
    const фото = {type:"image", source:{type:"base64", media_type:"image/jpeg", data:"QUJD"}};
    const ід = k => ({type:"image", source:{type:"url", url:"https://img.example/" + k + ".png"}});
    вихідні.length = 0; фотоЗапити.length = 0;
    відповідач = () => new Response(JSON.stringify({created:1, output_format:"png", quality:"medium", size:"1024x1536",
      data:[{b64_json:"R0lG"}],
      usage:{input_tokens:3000, input_tokens_details:{image_tokens:2500, text_tokens:500}, output_tokens:1000, total_tokens:4000}}), {status:200});
    в = await запО({model:"gpt-image-2.6-sunburst", max_tokens:800,
      messages:[{role:"user", content:[{type:"text", text:"Одягни її"}, фото, ід("a"), {type:"text", text:"Речі — далі"}]}]});
    const о = вихідні[0], тіло_о = о && о.body, д_о = await в.json();
    тест("openai: адреса images/edits, Bearer ключа, JSON", о && о.url === "https://api.openai.com/v1/images/edits"
         && о.headers.authorization === "Bearer sk-openai-тест" && о.headers["content-type"] === "application/json", о && о.url);
    тест("openai: model, prompt з текстових блоків, images у порядку (data:-URL, фото за адресою вже base64)",
         тіло_о.model === "gpt-image-2.6-sunburst" && тіло_о.prompt === "Одягни її\n\nРечі — далі"
         && тіло_о.images.length === 2 && тіло_о.images[0].image_url === "data:image/jpeg;base64,QUJD"
         && /^data:image\/png;base64,/.test(тіло_о.images[1].image_url), тіло_о);
    тест("openai: у тілі нема службових полів Anthropic/Gemini", !("messages" in тіло_о) && !("max_tokens" in тіло_о)
         && !("_думки" in тіло_о) && !("temperature" in тіло_о), Object.keys(тіло_о));
    тест("openai: одна спроба без каскаду, x-provider=openai, x-route=images-edits, x-thinking=as-is",
         вихідні.length === 1 && в.headers.get("x-provider") === "openai" && в.headers.get("x-route") === "images-edits"
         && в.headers.get("x-thinking") === "as-is", в.headers.get("x-attempts"));
    тест("openai: відповідь у форматі Anthropic — блок image base64 image/png, usage 3000/1000",
         в.status === 200 && д_о.content.length === 1 && д_о.content[0].type === "image"
         && д_о.content[0].source.type === "base64" && д_о.content[0].source.media_type === "image/png"
         && д_о.content[0].source.data === "R0lG" && д_о.usage.input_tokens === 3000 && д_о.usage.output_tokens === 1000, д_о);
    /* 2500·8 + 500·5 + 1000·30 = 20000 + 2500 + 30000 = 52500 / 1e6 = $0.0525 */
    тест("openai: x-cost-usd = токени × ціна (0.0525)", в.headers.get("x-cost-usd") === "0.0525", в.headers.get("x-cost-usd"));
    вихідні.length = 0;
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[{type:"text", text:"x"}]}]});
    тест("openai: без фото — 400 до мережі", в.status === 400 && вихідні.length === 0, в.status);
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[фото]}, {role:"assistant", content:"b"}]});
    тест("openai: кілька повідомлень — 400 до мережі", в.status === 400 && вихідні.length === 0, в.status);
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[{type:"text", text:"x"}, ...Array.from({length:17}, () => фото)]}]});
    тест("openai: понад 16 зображень — 400 до мережі", в.status === 400 && вихідні.length === 0, в.status);
    в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
      body:JSON.stringify({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[фото]}]})}), env);
    тест("openai: без секрета → 500 і названо OPENAI_API_KEY", в.status === 500 && /OPENAI_API_KEY/.test(await в.text()), в.status);
    /* ВАДА 16833: фото за адресою, що не дійшло, — 422 ДО платного виклику (масив зсунув би номери речей) */
    вихідні.length = 0;
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[{type:"text", text:"x"}, фото,
      {type:"image", source:{type:"url", url:"https://dead.example/z.png"}}, ід("ok")]}]});
    тест("openai: одне мертве фото → 422, виклику OpenAI нема, x-images-dropped=1",
         в.status === 422 && вихідні.length === 0 && в.headers.get("x-images-dropped") === "1", [в.status, вихідні.length]);
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[{type:"text", text:"x"},
      {type:"image", source:{type:"url", url:"https://dead.example/a.png"}}]}]});
    тест("openai: усі фото мертві → 422, без images:[] у OpenAI", в.status === 422 && вихідні.length === 0, [в.status, вихідні.length]);
    /* ВАДА 16838: 422 за мертвим фото — дешева відмова, виклику OpenAI нема, тож добового прогону вона не списує */
    {
      const сховище = {}; let путів = 0;
      const env7 = {...envО, COUNTER:{get: async к => сховище[к] || null, put: async (к, з) => { путів++; сховище[к] = з; }}};
      вихідні.length = 0;
      в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
        headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
        body:JSON.stringify({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[{type:"text", text:"x"}, фото,
          {type:"image", source:{type:"url", url:"https://dead.example/z.png"}}]}]})}), env7);
      const ключ = Object.keys(сховище)[0];
      тест("openai: 422 за мертвим фото повертає взятий прогін (лічильник 0, x-runs-left=40) — дошка 16838",
           в.status === 422 && сховище[ключ] === "0" && вихідні.length === 0 && в.headers.get("x-runs-left") === "40",
           [в.status, сховище, в.headers.get("x-runs-left")]);
    }
    /* ВАДА 16868: паралельні виклики одного токена з фото за адресою. Прогін резервується ДО фото: читання й запис
       лічильника не розділені завантаженням фото, тож N паралельних викликів списують N прогонів. KV — із затримкою
       get/put, фото — із затримкою 300 мс, старт кожні 60 мс (як у звірці перевірки #4512). */
    {
      const сховище = {}, пауза = мс => new Promise(р => setTimeout(р, мс));
      const env8 = {...env, COUNTER:{get: async к => { await пауза(20); return сховище[к] || null; },
                                     put: async (к, з) => { await пауза(20); сховище[к] = з; }}};
      const старий = globalThis.fetch;
      globalThis.fetch = async (url, opts) => /slow\.example/.test(String(url))
        ? (await пауза(300), new Response(пнг(2048), {status:200, headers:{"content-type":"image/png"}})) : старий(url, opts);
      вихідні.length = 0;
      відповідач = () => new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn",
        usage:{input_tokens:5, output_tokens:1}}), {status:200});
      const N = 8, виклики = [];
      for (let і = 0; і < N; і++){
        виклики.push(М.fetch(new Request("https://w.workers.dev/", {method:"POST",
          headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-b2"},
          body:JSON.stringify({model:"claude-sonnet-5-5", messages:[{role:"user", content:[{type:"text", text:"x"},
            {type:"image", source:{type:"url", url:"https://slow.example/" + і + ".png"}}]}]})}), env8));
        await пауза(60);
      }
      const відп = await Promise.all(виклики);
      globalThis.fetch = старий;
      const провайдеру = вихідні.length; вихідні.length = 0;
      const списано = Number(Object.values(сховище)[0]) || 0;
      тест("16868: " + N + " паралельних викликів із фото й затримкою KV — провайдеру " + N + ", списано " + N + " з " + N,
           відп.every(в => в.status === 200) && провайдеру === N && списано === N,
           {статуси: відп.map(в => в.status), провайдеру, списано, лишилось: відп.map(в => в.headers.get("x-runs-left"))});
    }
    /* ВАДА 16836: температури нема — заголовок n/a, 400 про sampling не повторюється */
    відповідач = () => new Response(JSON.stringify({error:{message:"unsupported sampling parameter"}}), {status:400});
    в = await запО({model:"gpt-image-2.6-flare", temperature:1, messages:[{role:"user", content:[фото]}]});
    тест("openai: 400 зі словом sampling — один виклик (без повтору), x-temperature=n/a",
         в.status === 400 && вихідні.length === 1 && в.headers.get("x-temperature") === "n/a", [вихідні.length, в.headers.get("x-temperature")]);
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({created:1, output_format:"png", data:[{b64_json:"R0lG"}], usage:{input_tokens:1, output_tokens:1}}), {status:200});
    в = await запО({model:"gpt-image-2.6-flare", temperature:1, messages:[{role:"user", content:[фото]}]});
    тест("openai: 200 з temperature у запиті сторінки — x-temperature=n/a", в.status === 200 && в.headers.get("x-temperature") === "n/a", в.headers.get("x-temperature"));
    /* відмова безпеки й порожня відповідь */
    вихідні.length = 0;
    відповідач = () => new Response(JSON.stringify({error:{code:"moderation_blocked", message:"blocked"}}), {status:400});
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[фото]}]});
    тест("openai: moderation_blocked 400 — віддано як є, один виклик", в.status === 400 && вихідні.length === 1
         && /moderation_blocked/.test(await в.text()), в.status);
    відповідач = () => new Response(JSON.stringify({data:[], usage:{}}), {status:200});
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[фото]}]});
    тест("openai: 200 без картинки — 422, а не «успіх»", в.status === 422, в.status);
    відповідач = () => new Response(JSON.stringify({error:{code:"insufficient_quota", message:"You exceeded your current quota"}}), {status:429});
    в = await запО({model:"gpt-image-2.6-flare", messages:[{role:"user", content:[фото]}]});
    тест("openai: insufficient_quota → 402 credits_exhausted", в.status === 402 && /credits_exhausted/.test(await в.text()), в.status);
  }

  console.log("5. СТЕЛІ");
  в = await зап({model:"claude-sonnet-5", messages:[{role:"user", content:"x".repeat(400001)}]});
  тест("запит понад стелю входу → 413", в.status === 413, в.status);
  в = await зап({model:"claude-sonnet-5", messages:[]}, {});
  const env3 = {...env}; delete env3.ANTHROPIC_API_KEY;
  в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":env.ALLOWED_ORIGINS, "x-lyusterko-token":"tok-a1"},
      body:JSON.stringify({model:"claude-sonnet-5", messages:[]})}), env3);
  тест("без секрета провайдера → 500 і названо, якого", в.status === 500 && /ANTHROPIC_API_KEY/.test(await в.text()), в.status);

  console.log(провалів ? ("ВПАЛО " + провалів) : "МІСТ: усе зелене");
  process.exit(провалів ? 1 : 0);
})().catch(e => { console.error("тест не запустився:", e); process.exit(2); });
