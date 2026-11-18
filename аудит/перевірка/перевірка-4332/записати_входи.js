// Входи мосту сцени для `знімок_мосту_pyodide.js` (перевірка #4332).
// node записати_входи.js <дерево стенда> <тека зі збіркою index.html> <тека живого запису з повтор.json | -> <тека виходу>
// Запис — REPLAY_EXCHANGE з VIDPOVIDI/обмін; «-» — заглушка моделі, FOTO=1. Вихід: входи.jsonl, лог.txt, знімки/.
const path = require('path'), fs = require('fs');
const [дерево, збірка, запис, вихід] = process.argv.slice(2);
const П = require(path.join(дерево, 'аудит/проби/приймання_записів.js'));
const стенд = path.join(дерево, 'аудит/проби/рв6_стенд.js');
let сцена, env;
if (запис === '-') { сцена = {сід: 3}; env = {...process.env, FOTO: '1', ZNIMKY: path.join(вихід, 'знімки')}; }
else {
  const паспорт = JSON.parse(fs.readFileSync(path.join(запис, 'повтор.json'), 'utf8'));
  сцена = {змінні: паспорт.змінні, жінка: паспорт.жінка, сід: паспорт.сід, обмін: path.join(запис, 'VIDPOVIDI/обмін')};
  env = П.середовищеСцени(сцена, вихід, стенд);
}
fs.mkdirSync(вихід, {recursive: true});
env.ZAPYS_VYKLYKIV = path.join(вихід, 'входи.jsonl');
env.CHROMIUM = '/opt/pw-browsers/chromium';
const t0 = Date.now();
const р = П.запуститиСтенд(збірка, '/tmp/pyodide', сцена.сід, env, вихід, стенд);
console.log(path.basename(запис), path.basename(збірка), 'rc', р.status, р.error ? String(р.error) : '', ((Date.now() - t0) / 1000).toFixed(0) + ' с');
