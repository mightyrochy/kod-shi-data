/* Прогін МОСТУ (worker.js) у node без мережі: `fetch` підмінено заглушкою, яка
   ЗАПИСУЄ, що воркер послав би провайдеру, і віддає канонну відповідь.
   Ловить те, чого не бачить ні `node --check`, ні проба в браузері:
   що саме йде в Anthropic/Google, як перекладається відповідь, чи каскад
   мислення справді крутиться.

   Запуск:  python3 скласти.py && node тест_мосту.js
   (тестується СКЛАДЕНИЙ worker.js — те, що деплоїться, а не джерело). */
const fs = require("fs");
const path = require("path");

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
  fs.writeFileSync("/tmp/_міст_тест.mjs", сир + "\nexport {М};");
  const {М} = await import("/tmp/_міст_тест.mjs");

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
  тест("модель, стеля, повідомлення доїхали як є",
       а.body && а.body.model === "claude-sonnet-5" && а.body.max_tokens === 800
       && а.body.messages[0].content[0].text === "привіт", а.body);
  тест("відповідь 200 віддається як є", в.status === 200 && (await в.clone().json()).content[0].text === "ок", в.status);
  тест("заголовки лімітів Anthropic проходять наскрізь і відкриті для сторінки",
       в.headers.get("anthropic-ratelimit-requests-remaining") === "49"
       && /anthropic-ratelimit-requests-remaining/.test(в.headers.get("Access-Control-Expose-Headers")),
       [...в.headers.keys()]);
  тест("x-provider=anthropic, x-thinking=as-is (каскаду для claude нема)",
       в.headers.get("x-provider") === "anthropic" && в.headers.get("x-thinking") === "as-is",
       [в.headers.get("x-provider"), в.headers.get("x-thinking")]);
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
  тест("claude: temperature 0 доїжджає верхнім полем тіла, x-temperature=0",
       вихідні.length === 1 && вихідні[0].body.temperature === 0
       && в.headers.get("x-temperature") === "0", вихідні[0] && вихідні[0].body);
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", temperature:null, messages:[{role:"user", content:"x"}]});
  тест("claude: temperature null знімається з тіла (Anthropic віддав би 400)",
       вихідні.length === 1 && !("temperature" in вихідні[0].body)
       && в.headers.get("x-temperature") === "n/a", вихідні[0] && вихідні[0].body);

  /* М-6: сучасні моделі Anthropic (Opus 4.7+, Sonnet 5, Fable 5) приймають `temperature`
     лише типовим значенням, НЕтипове = 400 «Sampling parameters rejected». Отже рішення
     «температура 0» на цьому маршруті впало б 400 на першому ж виклику — тож міст знімає
     поле й повторює запит, як робить із полем мислення Gemini, і каже це заголовком. */
  let стуків = 0;
  відповідач = () => (++стуків === 1
    ? new Response(JSON.stringify({type:"error", error:{type:"invalid_request_error",
        message:"temperature: Sampling parameters are not supported for this model."}}), {status:400})
    : new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn",
        usage:{input_tokens:5, output_tokens:1}}), {status:200}));
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", temperature:0, messages:[{role:"user", content:"x"}]});
  тест("claude: 400 через вибірку → поле знято, запит повторено, відповідь 200",
       в.status === 200 && вихідні.length === 2 && вихідні[0].body.temperature === 0
       && !("temperature" in вихідні[1].body), [в.status, вихідні.map(x=>x.body.temperature)]);
  тест("claude: x-temperature=dropped, і службового поля провайдер не бачить",
       в.headers.get("x-temperature") === "dropped" && !("_без_темп" in вихідні[1].body)
       && /temperature dropped/.test(в.headers.get("x-attempts") || ""),
       [в.headers.get("x-temperature"), в.headers.get("x-attempts")]);
  стуків = 0;
  відповідач = () => new Response(JSON.stringify({type:"error", error:{message:"model not found"}}), {status:400});
  вихідні.length = 0;
  в = await зап({model:"claude-sonnet-5", temperature:0, messages:[{role:"user", content:"x"}]});
  тест("claude: 400 НЕ через вибірку — поле не знімається й повтору нема (чужа помилка як є)",
       в.status === 400 && вихідні.length === 1 && в.headers.get("x-temperature") === "0",
       [в.status, вихідні.length, в.headers.get("x-temperature")]);
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
        {type:"image", source:{type:"url", url:"https://img.example/1.jpg"}}, {type:"text", text:"опиши"}]}]});
  тест("claude-: блок url їде як є, воркер фото НЕ тягне", вихідні[0].body.messages[0].content[0].source.type === "url"
       && фотоЗапити.length === 0 && в.headers.get("x-images-dropped") === "0", [вихідні[0].body.messages[0].content[0].source, фотоЗапити]);
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
