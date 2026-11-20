/* СТЕНД МОСТА НА СИТУАЦІЇ ПРОГОНУ (наряд «Модель-збої-один-шлях», мірило 2 — без справжнього моста).
   Ситуацію (с8, с5) веде драйвер проби «Живий-через-міст» (`повтор_міст.js`: записані слова й дотики жінки з хід.md),
   а `/міст` замість воркера Cloudflare обслуговує САМ КОД МОСТА (`джерела/worker_джерело.js`) у цьому процесі —
   як `аудит/проби/модель-текст-claude/скрипти/стенд_моста.js`. Підмінено лише те, що міст шле назовні:
   · api.anthropic.com — імітація правил API, які видно в прогоні через справжній міст 20.11: нетипова `temperature`
     → 400 «Sampling parameters…»; блок фото `source:{type:"url"}`, якого не віддає крамниця, → 400 «Unable to download
     the file…» (чи віддає — справжній `curl` через проксі середовища); інакше відповідає модель продукту за підпискою
     (`claude -p`, як `скрипти/повтор.py`; ключа API в сесії нема);
   · фото крамниць, які тягне сам міст (`підготувати`), — справжній `curl`.
   Той самий запит сторінки паралельно йде ТІННЮ в код моста ДО (`main` до наряду) з тією ж імітацією, але без моделі
   (200 `{}`): так «було — стало» міряються на тих самих тілах сторінки, а сторінка дістає лише відповідь моста ПІСЛЯ.
   Драйвер не копіюється: його текст читається з шляху й у ньому підміняються два рядки (`route.fetch` → цей міст і віддача);
   обміни.jsonl пише він сам, як у прогоні через міст, тож `стенд/числа.py` тієї проби читає вивід без змін.
   Запуск (з кореня репозиторію; STOR — тека зі зібраним index.html, PYODIDE — кеш):
     STOR=… PYODIDE=/tmp/pyodide NODE_PATH=/opt/node-tools/node_modules node стенд_моста_ситуації.js \
       <повтор_міст.js> <ситуація> <тека виводу> <worker_джерело.js ПІСЛЯ> <worker_джерело.js ДО>
   Вивід, крім драйверового: <тека>/стенд/службове/<ситуація>/міст_стенд.jsonl — на кожен виклик сторінки: скільки
   запитів міст ПІСЛЯ і ДО надіслав провайдеру, скільки з них — фото за адресою, статуси, x-attempts. */
const fs = require('fs'), path = require('path'), os = require('os'), {execFile, spawn} = require('child_process');
const {pathToFileURL} = require('url');
const [ДРАЙВЕР, СИТУАЦІЯ, ВИХІД, ВОРКЕР_П, ВОРКЕР_Д] = process.argv.slice(2);
const МОДЕЛЬ_CLI = process.env.STAND_MODEL || 'claude-sonnet-5-5', ЗУСИЛЛЯ = process.env.STAND_EFFORT || 'low';
const БІН = process.env.CLAUDE_BIN || '/opt/node22/bin/claude';
const СИСТЕМНИЙ = 'You are the model behind a mobile styling app. The user message is the application prompt, '
  + 'verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code fence when it asks '
  + 'for JSON, plain prose when it asks for prose. No preamble, no commentary, no tools, no questions back.';
const ENV = {ALLOWED_ORIGINS: 'https://mightyrochy.github.io', TESTER_TOKENS: 'tok-stub', ANTHROPIC_API_KEY: 'sk-стенд',
             PROVIDER_TIMEOUT_S: '600'};   // стеля часу — не мірило тут: модель за підпискою повільніша за API
const json = (о, статус = 200) => new Response(JSON.stringify(о), {status: статус, headers: {'content-type': 'application/json'}});
const помилка = т => json({type: 'error', error: {type: 'invalid_request_error', message: т}}, 400);

/* фото — справжнім curl через проксі середовища, кеш на весь прогін */
const КЕШ = new Map();
function кадр(url){
  if (!КЕШ.has(url)) КЕШ.set(url, new Promise(р => execFile('curl', ['-sSfL', '--max-time', '20', '-A', 'Mozilla/5.0', url],
    {encoding: 'buffer', maxBuffer: 20 * 1024 * 1024}, (е, б) => р(!е && б && б.length ? б : null))));
  return КЕШ.get(url);
}
const тип = б => б[0] === 0x89 ? 'image/png' : б.slice(8, 12).toString() === 'WEBP' ? 'image/webp'
  : б.slice(0, 3).toString() === 'GIF' ? 'image/gif' : 'image/jpeg';

/* модель продукту за підпискою: тіло Anthropic → stream-json `claude -p` → відповідь у формі Messages API */
let іде = 0; const черга = [];
const слот = () => іде < 6 ? (іде++, Promise.resolve()) : new Promise(р => черга.push(р));
const звільнити = () => { const н = черга.shift(); if (н) н(); else іде--; };
async function модель(тіло, блоки){
  await слот();
  try {
    for (let спроба = 0; спроба < 3; спроба++) {
      const вихід = await new Promise(р => {
        const п = spawn(БІН, ['-p', '--model', МОДЕЛЬ_CLI, '--effort', ЗУСИЛЛЯ, '--tools', '', '--strict-mcp-config',
          '--no-session-persistence', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
          '--system-prompt', СИСТЕМНИЙ], {cwd: os.tmpdir(), env: {...process.env, CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1'}});
        let о = ''; п.stdout.on('data', д => о += д); п.on('close', () => р(о)); п.on('error', () => р(''));
        п.stdin.end(JSON.stringify({type: 'user', message: {role: 'user', content: блоки}}) + '\n');
      });
      const ітог = вихід.split('\n').map(л => { try { return JSON.parse(л); } catch (_) { return null; } })
        .filter(о => о && о.type === 'result').pop();
      if (ітог && ітог.subtype === 'success' && !ітог.is_error) {
        const u = ітог.usage || {};
        return json({id: 'msg_стенд', type: 'message', role: 'assistant', model: тіло.model,
          content: [{type: 'text', text: ітог.result || ''}], stop_reason: 'end_turn',
          usage: {input_tokens: u.input_tokens || 0, output_tokens: u.output_tokens || 0,
                  cache_creation_input_tokens: u.cache_creation_input_tokens || 0,
                  cache_read_input_tokens: u.cache_read_input_tokens || 0}});
      }
    }
    return json({type: 'error', error: {type: 'overloaded_error', message: 'стенд: claude -p не відповів тричі'}}, 529);
  } finally { звільнити(); }
}

/* що міст шле назовні; `рахунок` — запис виклику сторінки, куди лічаться запити провайдеру */
function назовні(з_моделлю, рахунок){
  return async (url, opts = {}) => {
    url = String(url);
    if (!/^https:\/\/api\.anthropic\.com\//.test(url)) {
      const б = await кадр(url);
      return б ? new Response(б, {status: 200, headers: {'content-type': тип(б)}}) : new Response('', {status: 404});
    }
    const тіло = JSON.parse(opts.body);
    const url_фото = [], блоки = [];
    for (const м of тіло.messages || []) for (const б of (Array.isArray(м.content) ? м.content
      : [{type: 'text', text: String(м.content)}])) {
      if (б.type === 'image' && б.source && б.source.type === 'url') url_фото.push(б.source.url);
      /* без `cache_control`: межу кешу моста CLI підписки не приймає поруч зі своєю (400 про ttl) */
      блоки.push(б.type === 'image' ? {type: 'image', source: б.source} : {type: 'text', text: String(б.text || '')});
    }
    рахунок.провайдеру++; рахунок.url_фото += url_фото.length;
    if (тіло.temperature !== undefined && тіло.temperature !== 1)
      return помилка('Sampling parameters `temperature` is not supported for this model; only the default is accepted.');
    for (const [і, б] of блоки.entries()) if (б.type === 'image' && б.source.type === 'url') {
      const к = await кадр(б.source.url);
      if (!к) { рахунок.фото_400++; return помилка('Unable to download the file. Please verify the URL and try again.'); }
      блоки[і] = {type: 'image', source: {type: 'base64', media_type: тип(к), data: к.toString('base64')}};
    }
    if (!з_моделлю) return json({id: 'msg_тінь', type: 'message', role: 'assistant', model: тіло.model,
      content: [{type: 'text', text: '{}'}], stop_reason: 'end_turn', usage: {input_tokens: 1, output_tokens: 1}});
    return модель(тіло, блоки);
  };
}

async function воркер(файл, ім){
  const сир = fs.readFileSync(файл, 'utf-8').replace(/^export default/m, 'const М =')
    .replace(/\bawait fetch\(/g, 'await globalThis.' + ім + '(');
  const мод = path.join(os.tmpdir(), '_стенд_моста_' + ім + '.mjs'); fs.writeFileSync(мод, сир + '\nexport {М};');
  return (await import(pathToFileURL(мод).href + '?' + Date.now())).М;
}

(async () => {
  const МП = await воркер(ВОРКЕР_П, '__міст_після'), МД = await воркер(ВОРКЕР_Д, '__міст_до');
  const журнал = path.join(path.resolve(ВИХІД), 'стенд/службове', СИТУАЦІЯ, 'міст_стенд.jsonl');
  let н = 0;
  /* Код моста кличе `fetch` провайдера всередині свого `fetch(запит, env)`: один глобальний обробник на версію, а
     рахунок — поточного виклику сторінки (виклики сторінки йдуть паралельно — рахунок кладеться в AsyncLocalStorage). */
  const {AsyncLocalStorage} = require('async_hooks'); const ал = new AsyncLocalStorage();
  globalThis.__міст_після = (...а) => назовні(true, ал.getStore())(...а);
  globalThis.__міст_до = (...а) => назовні(false, ал.getStore())(...а);
  const виклик = async (М, з, тіло, рахунок) => ал.run(рахунок, async () => {
    const в = await М.fetch(new Request('https://lyusterko-mist.mighty-rochy.workers.dev/', {method: 'POST',
      headers: з.headers(), body: тіло}), ENV);
    const заг = {}; в.headers.forEach((з, і) => { заг[і] = з; });
    return {в, заг, текст: await в.text()};
  });
  globalThis.__стенд_міст = async route => {
    const з = route.request(), тіло = з.postData() || '{}', і = н++, т0 = Date.now();
    const п = {провайдеру: 0, url_фото: 0, фото_400: 0}, д = {провайдеру: 0, url_фото: 0, фото_400: 0};
    const тінь = виклик(МД, з, тіло, д).catch(е => ({в: {status: 0}, заг: {}, текст: String(е)}));
    const {в, заг, текст} = await виклик(МП, з, тіло, п);
    const тд = await тінь;
    fs.mkdirSync(path.dirname(журнал), {recursive: true});
    fs.appendFileSync(журнал, JSON.stringify({і, час: new Date(т0).toISOString(), с: (Date.now() - т0) / 1000,
      модель: (() => { try { return JSON.parse(тіло).model; } catch (_) { return null; } })(),
      після: {статус: в.status, ...п, 'x-attempts': заг['x-attempts'], 'x-temperature': заг['x-temperature'],
              'x-images-dropped': заг['x-images-dropped']},
      до: {статус: тд.в.status, ...д, 'x-attempts': тд.заг['x-attempts'], 'x-temperature': тд.заг['x-temperature']}}) + '\n');
    return {status: () => в.status, headers: () => заг, text: async () => текст};
  };
  /* драйвер — без копії: один рядок (виклик справжнього моста) іде сюди */
  /* `fulfill({response})` бере статус і заголовки лише з APIResponse Playwright — тому й віддача сторінці явна */
  const заміни = [['const r=await route.fetch({timeout:960000});', 'const r=await globalThis.__стенд_міст(route);'],
                  ['await route.fulfill({response:r,body});', 'await route.fulfill({status:r.status(),headers:r.headers(),body});']];
  let текст = fs.readFileSync(ДРАЙВЕР, 'utf-8');
  for (const [було, стало] of заміни) {
    if (!текст.includes(було)) { console.error('у драйвері нема рядка «' + було + '» — стенд не підміняє'); process.exit(3); }
    текст = текст.replace(було, стало);
  }
  const копія = path.join(path.dirname(path.resolve(ДРАЙВЕР)), '_стенд_' + path.basename(ДРАЙВЕР));
  fs.writeFileSync(копія, текст);
  process.argv = [process.argv[0], копія, СИТУАЦІЯ, ВИХІД, '0'];
  require(копія);
})().catch(е => { console.error('стенд не піднявся:', е); process.exit(2); });
