/* Підйом моста: скільки коштує розпакування МОДУЛІ_ПОКАЗУ (base64 у зібраній сторінці) тим способом, що в
   `підняти_міст_показу` (`Uint8Array.from(atob(…), c => c.charCodeAt(0))`), проти циклу без колбека.
   Запуск: node аудит/огляд_коду/скрипти/показ/підйом.js <index.html стенда> — медіана 5 повторів у V8 Node. */
const fs = require('fs');
const html = fs.readFileSync(process.argv[2], 'utf8');
const м = /const МОДУЛІ_ПОКАЗУ\s*=\s*["']([A-Za-z0-9+/=]+)["']/.exec(html);
if (!м) { console.log('МОДУЛІ_ПОКАЗУ не знайдено'); process.exit(1); }
const б64 = м[1];
const мед = ф => { const т = []; for (let і = 0; і < 5; і++){ const п = performance.now(); ф(); т.push(performance.now() - п); } return т.sort((а, б) => а - б)[2].toFixed(0); };
const атоб = мед(() => atob(б64));
const з = мед(() => Uint8Array.from(atob(б64), c => c.charCodeAt(0)));
const цикл = мед(() => { const с = atob(б64), б = new Uint8Array(с.length); for (let і = 0; і < с.length; і++) б[і] = с.charCodeAt(і); return б; });
const буфер = мед(() => Buffer.from(б64, 'base64'));
console.log('base64 %d символів → %d байтів; atob %s мс; atob + Uint8Array.from(колбек) %s мс; atob + цикл %s мс; декодер без рядка (Buffer, як Uint8Array.fromBase64) %s мс',
  б64.length, Math.floor(б64.length * 3 / 4), атоб, з, цикл, буфер);
