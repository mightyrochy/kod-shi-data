/* Offline-перевірка справжнього проксі: http/child_process підробні, сокетів і моделей немає. */
const fs = require('fs'), vm = require('vm'), assert = require('assert');
const {EventEmitter} = require('events');
const джерело = fs.readFileSync(require('path').join(__dirname, 'проксі_почергове.js'), 'utf8');
const вхід = process.argv[2] ? JSON.parse(fs.readFileSync(process.argv[2], 'utf8')) :
  {method: 'POST', path: '/v1/chat/completions', headers: {'x-lyusterko-once': '5190-once-v1'}, body: '{"model":"mamaylm-gemma-3-12b-it-v2.0"}'};

async function проба(запит) {
  let прийняти, спроби = 0, завантаження = 0;
  const http = {
    createServer(функція) { прийняти = функція; return {listen() {}, keepAliveTimeout: 0}; },
    request() {
      спроби++;
      const р = new EventEmitter();
      р.destroy = () => {};
      р.end = () => queueMicrotask(() => р.emit('error', new Error('ECONNRESET після прийняття POST')));
      return р;
    }
  };
  const середовище = {Buffer, console: {log() {}}, process: {env: {}, on() {}},
    setTimeout(дія, мс) { if (мс === 3000) queueMicrotask(дія); return 1; }, clearTimeout() {},
    require(назва) {
      if (назва === 'http') return http;
      if (назва === 'child_process') return {execFile(файл, аргументи, опції, кінець) {
        завантаження++; queueMicrotask(() => кінець(null));
      }};
      throw Error('Неочікуваний імпорт ' + назва);
    }
  };
  vm.runInNewContext(джерело, середовище, {filename: 'проксі_почергове.js'});
  return new Promise(готово => {
    const req = new EventEmitter(), res = new EventEmitter();
    Object.assign(req, {method: запит.method, url: запит.path, headers: запит.headers});
    res.headersSent = false;
    res.writeHead = код => { res.statusCode = код; res.headersSent = true; };
    res.end = тіло => { res.writableFinished = true; готово({спроби, завантаження, код: res.statusCode, тіло}); };
    res.destroy = () => готово({спроби, завантаження, код: res.statusCode});
    прийняти(req, res);
    req.emit('data', Buffer.from(запит.body || ''));
    req.emit('end');
  });
}

(async () => {
  const можливість = await проба({method: 'GET', path: '/.well-known/lyusterko-5190', headers: {}});
  assert.deepStrictEqual(JSON.parse(можливість.тіло), {protocol: '5190-once-v1', post_retries: 0});
  assert.strictEqual(можливість.спроби, 0);
  assert.strictEqual(можливість.завантаження, 0);
  assert.strictEqual(вхід.path, '/v1/chat/completions');
  assert.strictEqual(вхід.headers['x-lyusterko-once'], '5190-once-v1');
  const лишеРаз = await проба(вхід), звичайний = await проба({...вхід, headers: {}});
  assert.strictEqual(лишеРаз.спроби, 1);
  assert.strictEqual(лишеРаз.код, 502);
  assert.strictEqual(звичайний.спроби, 3);
  assert.strictEqual(звичайний.код, 502);
  process.stdout.write(JSON.stringify({capability_posts: 0, once_posts: лишеРаз.спроби, ordinary_posts: звичайний.спроби}) + '\n');
})().catch(помилка => { console.error(помилка); process.exitCode = 1; });
