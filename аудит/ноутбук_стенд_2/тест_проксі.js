/* Тест проксі без LM Studio: підробний upstream + підробний LMS_BIN. node аудит/ноутбук_стенд_2/тест_проксі.js */
const http = require('http'), fs = require('fs'), os = require('os'), path = require('path'), { spawn } = require('child_process');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'proxy-')), flag = path.join(dir, 'fail'), лог = path.join(dir, 'lms.log'), lms = path.join(dir, 'lms');
fs.writeFileSync(lms, `#!/bin/sh\necho "$@" >> ${лог}\n[ "$1" = load ] && [ -f ${flag} ] && exit 1\nexit 0\n`, {mode: 0o755});
const loads = () => (fs.existsSync(лог) ? fs.readFileSync(лог, 'utf8') : '').split('\n').filter(l => l.startsWith('load')).length;
const free = () => new Promise(r => { const s = http.createServer().listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => r(p)); }); });
const up = http.createServer((q, s) => { let b = ''; q.on('data', d => b += d); q.on('end', () => {
  if (b.includes('"drop"')) { s.writeHead(200, {'content-length': 100}); s.write('часткова'); setTimeout(() => s.socket.destroy(), 50); }
  else if (b.includes('"slow"')) { /* мовчить */ } else s.end('{"ok":1}'); }); });
const post = (port, model) => new Promise(r => { const q = http.request({host: '127.0.0.1', port, path: '/v1/chat/completions', method: 'POST'}, s => { let b = ''; s.on('data', d => b += d); s.on('end', () => r({код: s.statusCode, b})); s.on('aborted', () => r({код: s.statusCode, обрив: true})); s.on('error', () => r({код: s.statusCode, обрив: true})); }); q.on('error', () => r({код: 0})); q.end(JSON.stringify({model})); });
const та = (p, мс) => Promise.race([p, new Promise(r => setTimeout(() => r({код: 'висить'}), мс))]);
(async () => {
  await new Promise(r => up.listen(0, '127.0.0.1', r));
  const PORT = await free(), pr = spawn('node', [path.join(__dirname, 'проксі_почергове.js')], {env: {...process.env, PORT, UP_PORT: up.address().port, LMS_BIN: lms, ТАЙМАУТ_МС: 1500}, stdio: 'ignore'});
  await new Promise(r => setTimeout(r, 500));
  let ok = true; const t = (н, у) => { console.log((у ? '✔ ' : '✘ ') + н); ok = ok && у; };
  t('(1) щасливий запит', (await та(post(PORT, 'a'), 5000)).код === 200);
  fs.writeFileSync(flag, ''); const до = loads();
  t('(2) load падає → 503', (await та(post(PORT, 'b'), 20000)).код === 503);
  t('(2) повторна спроба в межах запиту', loads() - до === 2);
  fs.unlinkSync(flag); const до2 = loads();
  t('(2) наступний запит знову пробує load і проходить', (await та(post(PORT, 'b'), 20000)).код === 200 && loads() - до2 === 1);
  await та(post(PORT, 'drop'), 5000);
  t('(3) після обриву upstream черга жива', (await та(post(PORT, 'b'), 5000)).код === 200);
  t('(4) тайм-аут → 504', (await та(post(PORT, 'slow'), 5000)).код === 504);
  t('(4) після тайм-ауту черга жива', (await та(post(PORT, 'b'), 5000)).код === 200);
  pr.kill(); up.close(); process.exit(ok ? 0 : 1);
})();
