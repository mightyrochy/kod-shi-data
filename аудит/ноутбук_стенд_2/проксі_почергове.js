/* Стендовий проксі :1235 → LM Studio :1234. Дві моделі на 16 ГБ разом не стоять, тому перед
   кожним запитом потрібна модель завантажується ЯВНО (lms load, свій контекст, parallel 1),
   а попередня вивантажується: JIT LM Studio завантажив би її з 4096/parallel 4. Запити — по черзі.
   Збій завантаження → одна повторна спроба, далі 503 (до чужої моделі не пересилаємо); черга рушає
   рівно раз на будь-якому кінці запиту (end/close/error/aborted) і за тайм-аутом (ТАЙМАУТ_МС → 504). */
const http = require('http'), { execFileSync } = require('child_process');
const E = process.env;
const LMS = E.LMS_BIN || 'C:/Users/Admin/.lmstudio/bin/lms.exe';
const PORT = +E.PORT || 1235, UP_PORT = +E.UP_PORT || 1234, ТАЙМАУТ_МС = +E.ТАЙМАУТ_МС || 15 * 60000;
const CTX = JSON.parse(E.CTX || '{}');           // {"id моделі": контекст}
let поточна = null, черга = Promise.resolve(), перемикань = 0, мс = 0;
function потрібна(м){
  if (поточна === м) return; const t = Date.now();
  for (let n = 1; ; n++) {
    поточна = null;                            // після unload «поточної» нема, поки load не вдався
    try {
      execFileSync(LMS, ['unload', '--all'], {stdio: 'ignore'});
      execFileSync(LMS, ['load', м, '--context-length', String(CTX[м] || 16384), '--gpu', 'max', '--parallel', '1', '-y'], {stdio: 'ignore', timeout: 300000});
      break;
    } catch (e) { console.log('збій завантаження ' + м + ' (спроба ' + n + '): ' + String(e.message).split('\n')[0]); if (n >= 2) throw e; }
  }
  поточна = м; перемикань++; мс += Date.now() - t;
  console.log('перемикання #' + перемикань + ' → ' + м + ' ctx ' + (CTX[м] || 16384) + ' · ' + (Date.now() - t) + ' мс');
}
http.createServer((req, res) => {
  const ч = []; req.on('data', d => ч.push(d)); req.on('end', () => {
    const тіло = Buffer.concat(ч);
    черга = черга.then(() => new Promise(рух => {
      let кінець = false, up = null, таймер = null;
      const ok = чому => { if (кінець) return; кінець = true; clearTimeout(таймер); if (чому) console.log(req.method + ' ' + req.url + ': ' + чому); рух(); };
      const відповісти = (код, текст) => { if (!res.headersSent) { res.writeHead(код); res.end(текст); } else res.destroy(); };
      res.on('close', () => { if (up) up.destroy(); ok(res.writableFinished ? '' : 'клієнт обірвав'); });
      req.on('aborted', () => { if (up) up.destroy(); ok('клієнт обірвав'); });
      таймер = setTimeout(() => { відповісти(504, 'тайм-аут ' + ТАЙМАУТ_МС + ' мс'); if (up) up.destroy(); ok('тайм-аут ' + ТАЙМАУТ_МС + ' мс'); }, ТАЙМАУТ_МС);
      try { if (req.method === 'POST' && /chat\/completions/.test(req.url)) потрібна(JSON.parse(тіло.toString()).model); }
      catch (e) {
        if (e instanceof SyntaxError) console.log('тіло не JSON: ' + e.message);
        else { відповісти(503, 'модель не завантажилась: ' + String(e.message).split('\n')[0]); return ok('503, модель не завантажилась'); }
      }
      const спроба = n => {
        if (кінець) return;
        up = http.request({host: '127.0.0.1', port: UP_PORT, path: req.url, method: req.method, headers: req.headers, agent: false}, r => {
          res.writeHead(r.statusCode, r.headers); r.pipe(res);
          r.on('end', () => ok());
          for (const ev of ['aborted', 'error', 'close']) r.on(ev, () => { if (!r.complete) { ok('upstream обірвав відповідь'); res.destroy(); } });
        });
        up.on('error', e => {
          if (кінець) return;
          if (n < 2 && !res.headersSent) { console.log('повтор після ' + e); return setTimeout(() => спроба(n + 1), 3000); }
          відповісти(502, String(e)); ok('502 ' + e);
        });
        up.end(тіло);
      };
      спроба(0);
    }));
  });
}).listen(PORT, '127.0.0.1', () => console.log('проксі на :' + PORT));
process.on('SIGTERM', () => { console.log('ПІДСУМОК перемикань ' + перемикань + ' · ' + мс + ' мс'); process.exit(0); });
