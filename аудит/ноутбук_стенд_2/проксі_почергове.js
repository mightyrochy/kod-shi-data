/* Стендовий проксі :1235 → LM Studio :1234. Дві моделі на 16 ГБ разом не стоять, тому перед
   кожним запитом потрібна модель завантажується ЯВНО (lms або LMS_MODE=http, свій контекст, parallel 1),
   а попередня вивантажується: JIT LM Studio завантажив би її з 4096/parallel 4. Запити — по черзі.
   Збій завантаження → одна повторна спроба, далі 503 (до чужої моделі не пересилаємо); черга рушає
   рівно раз на будь-якому кінці запиту (end/close/error/aborted) і за тайм-аутом (ТАЙМАУТ_МС → 504).
   Перемикання моделі — АСИНХРОННЕ (рядок 2246): `execFileSync` на 4–12 с вставав у циклі подій усього проксі, і
   з'єднання, що простоювало на боці сервера понад `keepAliveTimeout` (5 с), закривалось раніше, ніж проксі встигав
   прочитати запит, що вже лежав у сокеті, — клієнт бачив `read ECONNRESET` за 3–7 с, у логу проксі нічого.
   Відтворено на підробному lms із затримкою 7 с: дві руки паралельно → друга руки діставала ECONNRESET щоразу. */
const http = require('http'), { execFile } = require('child_process');
const виконати = (аргументи, тайм) => new Promise((ok, no) => execFile(LMS, аргументи, {timeout: тайм, windowsHide: true}, е => е ? no(е) : ok()));
const E = process.env;
const LMS = E.LMS_BIN || 'C:/Users/Admin/.lmstudio/bin/lms.exe';
const PORT = +E.PORT || 1235, UP_PORT = +E.UP_PORT || 1234, ТАЙМАУТ_МС = +E.ТАЙМАУТ_МС || 15 * 60000;
const CTX = JSON.parse(E.CTX || '{}');           // {"id моделі": контекст}
const РЕЖИМ_HTTP = E.LMS_MODE === 'http', власні = new Set();
let поточна = null, черга = Promise.resolve(), перемикань = 0, мс = 0;
function api(шлях, тіло, тайм = 120000) {
  // Керує тим самим локальним сервером, до якого йдуть запити inference.
  return new Promise((ok, no) => {
    const дані = тіло === undefined ? null : Buffer.from(JSON.stringify(тіло));
    const q = http.request({host: '127.0.0.1', port: UP_PORT, path: '/api/v1/models' + шлях,
      method: дані ? 'POST' : 'GET', agent: false,
      headers: дані ? {'content-type': 'application/json', 'content-length': дані.length} : {}}, r => {
      let b = ''; r.setEncoding('utf8'); r.on('data', d => b += d);
      r.on('error', no); r.on('aborted', () => no(Error('обрив REST API')));
      r.on('end', () => {
        try {
          const v = JSON.parse(b);
          if (r.statusCode !== 200 || v.error) throw Error('REST ' + r.statusCode + ': ' + b);
          ok(v);
        } catch (e) { no(e); }
      });
    });
    const таймер = setTimeout(() => q.destroy(Error('тайм-аут REST API')), тайм);
    q.on('close', () => clearTimeout(таймер)); q.on('error', no); q.end(дані);
  });
}
async function екземпляри() {
  // Перелік містить фактичні параметри, а не лише успішний статус POST load.
  const v = await api('');
  if (!Array.isArray(v.models)) throw Error('REST: нема переліку models');
  return v.models.flatMap(m => m.loaded_instances.map(i => ({...i, model: m.key})));
}
async function вивантажитиВласні() {
  // Чужих екземплярів API ніколи не вивантажує.
  for (const i of await екземпляри()) if (власні.has(i.id)) {
    await api('/unload', {instance_id: i.id}); власні.delete(i.id);
  }
}
async function завантажитиHTTP(м) {
  // Відмова при чужій моделі зберігає межу між сесіями на спільній GPU.
  const до = await екземпляри();
  if (до.some(i => !власні.has(i.id))) throw Error('REST: сервер тримає чужу модель');
  await вивантажитиВласні();
  const v = await api('/load', {model: м, context_length: CTX[м] || 16384, parallel: 1, echo_load_config: true}, 300000);
  if (v.status !== 'loaded' || !v.instance_id) throw Error('REST: нема завантаженого instance_id');
  власні.add(v.instance_id);
  console.log('HTTP власний екземпляр ' + v.instance_id);
  const i = (await екземпляри()).find(i => i.id === v.instance_id && i.model === м);
  if (!i || i.config.context_length !== (CTX[м] || 16384) || i.config.parallel !== 1)
    throw Error('REST: не підтверджено контекст і parallel=1: ' + JSON.stringify(i));
  console.log('HTTP екземпляр ' + i.id + ' · ' + JSON.stringify(i.config));
}
async function потрібна(м){
  if (РЕЖИМ_HTTP && поточна === м) {
    const всі = await екземпляри();
    if (всі.some(i => !власні.has(i.id))) throw Error('REST: сервер тримає чужу модель');
    const i = всі.find(i => власні.has(i.id) && i.model === м);
    if (!i || i.config.context_length !== (CTX[м] || 16384) || i.config.parallel !== 1) поточна = null;
  }
  if (поточна === м) return; const t = Date.now();
  for (let n = 1; ; n++) {
    поточна = null;                            // після unload «поточної» нема, поки load не вдався
    try {
      if (РЕЖИМ_HTTP) await завантажитиHTTP(м);
      else {
        await виконати(['unload', '--all'], 120000);
        await виконати(['load', м, '--context-length', String(CTX[м] || 16384), '--gpu', 'max', '--parallel', '1', '-y'], 300000);
      }
      break;
    } catch (e) { console.log('збій завантаження ' + м + ' (спроба ' + n + '): ' + String(e.message).split('\n')[0]); if (n >= 2) throw e; }
  }
  поточна = м; перемикань++; мс += Date.now() - t;
  console.log('перемикання #' + перемикань + ' → ' + м + ' ctx ' + (CTX[м] || 16384) + ' · ' + (Date.now() - t) + ' мс');
}
const сервер = http.createServer((req, res) => {
  // Прилад 5190 перевіряє цю можливість ДО POST: старий проксі може його повторити.
  if (req.method === 'GET' && req.url === '/.well-known/lyusterko-5190') {
    res.writeHead(200, {'content-type': 'application/json'});
    res.end(JSON.stringify({protocol: '5190-once-v1', post_retries: 0}));
    return;
  }
  const безПовтору5190 = req.method === 'POST' && req.url === '/v1/chat/completions'
    && req.headers['x-lyusterko-once'] === '5190-once-v1';
  const ч = []; req.on('data', d => ч.push(d)); req.on('end', () => {
    const тіло = Buffer.concat(ч);
    черга = черга.then(() => new Promise(рух => {
      let кінець = false, up = null, таймер = null;
      const ok = чому => { if (кінець) return; кінець = true; clearTimeout(таймер); if (чому) console.log(req.method + ' ' + req.url + ': ' + чому); рух(); };
      const відповісти = (код, текст) => { if (!res.headersSent) { res.writeHead(код); res.end(текст); } else res.destroy(); };
      res.on('close', () => { if (up) up.destroy(); ok(res.writableFinished ? '' : 'клієнт обірвав'); });
      req.on('aborted', () => { if (up) up.destroy(); ok('клієнт обірвав'); });
      таймер = setTimeout(() => { відповісти(504, 'тайм-аут ' + ТАЙМАУТ_МС + ' мс'); if (up) up.destroy(); ok('тайм-аут ' + ТАЙМАУТ_МС + ' мс'); }, ТАЙМАУТ_МС);
      const спроба = n => {
        if (кінець) return;
        up = http.request({host: '127.0.0.1', port: UP_PORT, path: req.url, method: req.method, headers: req.headers, agent: false}, r => {
          res.writeHead(r.statusCode, r.headers); r.pipe(res);
          r.on('end', () => ok());
          for (const ev of ['aborted', 'error', 'close']) r.on(ev, () => { if (!r.complete) { ok('upstream обірвав відповідь'); res.destroy(); } });
        });
        up.on('error', e => {
          if (кінець) return;
          if (!безПовтору5190 && n < 2 && !res.headersSent) { console.log('повтор після ' + e); return setTimeout(() => спроба(n + 1), 3000); }
          відповісти(502, String(e)); ok('502 ' + e);
        });
        up.end(тіло);
      };
      (async () => {
        try { if (req.method === 'POST' && /chat\/completions/.test(req.url)) await потрібна(JSON.parse(тіло.toString()).model); }
        catch (e) {
          if (e instanceof SyntaxError) console.log('тіло не JSON: ' + e.message);
          else { відповісти(503, 'модель не завантажилась: ' + String(e.message).split('\n')[0]); return ok('503, модель не завантажилась'); }
        }
        if (!кінець) спроба(0);
      })();
    }));
  });
});
сервер.keepAliveTimeout = 120000;                // не 5 с за замовчуванням: стенд тримає з'єднання між викликами
сервер.listen(PORT, '127.0.0.1', () => console.log('проксі на :' + PORT));
process.on('SIGTERM', async () => {
  console.log('ПІДСУМОК перемикань ' + перемикань + ' · ' + мс + ' мс');
  try { if (РЕЖИМ_HTTP) await вивантажитиВласні(); process.exit(0); }
  catch (e) { console.error(e); process.exit(1); }
});
