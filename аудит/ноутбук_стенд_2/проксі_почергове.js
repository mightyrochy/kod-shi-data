/* Стендовий проксі :1235 → LM Studio :1234. Дві моделі на 16 ГБ разом не стоять, тому перед
   кожним запитом потрібна модель завантажується ЯВНО (lms load, свій контекст, parallel 1),
   а попередня вивантажується: JIT LM Studio завантажив би її з 4096/parallel 4. Запити — по черзі. */
const http = require('http'), { execFileSync } = require('child_process');
const LMS = process.env.LMS_BIN || 'C:/Users/Admin/.lmstudio/bin/lms.exe';
const CTX = JSON.parse(process.env.CTX || '{}');           // {"id моделі": контекст}
let поточна = null, черга = Promise.resolve(), перемикань = 0, мс = 0;
function потрібна(м){
  if (поточна === m_(м)) return; const t = Date.now();
  execFileSync(LMS, ['unload', '--all'], {stdio: 'ignore'});
  execFileSync(LMS, ['load', м, '--context-length', String(CTX[м] || 16384), '--gpu', 'max', '--parallel', '1', '-y'], {stdio: 'ignore', timeout: 300000});
  поточна = м; перемикань++; мс += Date.now() - t;
  console.log('перемикання #' + перемикань + ' → ' + м + ' ctx ' + (CTX[м] || 16384) + ' · ' + (Date.now() - t) + ' мс');
}
const m_ = x => x;
http.createServer((req, res) => {
  const ч = []; req.on('data', d => ч.push(d)); req.on('end', () => {
    const тіло = Buffer.concat(ч);
    черга = черга.then(() => new Promise(ok => {
      try { if (req.method === 'POST' && /chat\/completions/.test(req.url)) потрібна(JSON.parse(тіло.toString()).model); }
      catch (e) { console.log('помилка завантаження: ' + e); }
      const спроба = (n) => {
        const up = http.request({host: '127.0.0.1', port: 1234, path: req.url, method: req.method, headers: req.headers, agent: false}, r => {
          res.writeHead(r.statusCode, r.headers); r.pipe(res); r.on('end', ok);
        });
        up.on('error', e => { if (n < 2) { console.log('повтор після ' + e); return setTimeout(() => спроба(n + 1), 3000); } res.writeHead(502); res.end(String(e)); ok(); });
        up.end(тіло);
      };
      спроба(0);
    }));
  });
}).listen(1235, '127.0.0.1', () => console.log('проксі на :1235'));
process.on('SIGTERM', () => { console.log('ПІДСУМОК перемикань ' + перемикань + ' · ' + мс + ' мс'); process.exit(0); });
