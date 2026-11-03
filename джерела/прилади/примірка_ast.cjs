/* Розбирає JS та вбудовані скрипти HTML; продукт не виконує. Вхід/вихід — JSON. */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const zlib = require('node:zlib');
const модуль = {exports: {}};
vm.runInNewContext(zlib.gunzipSync(fs.readFileSync(__dirname + '/річ_запис_дані/acorn.cjs.gz')).toString('utf8'),
  {module: модуль, exports: модуль.exports});
const файли = JSON.parse(fs.readFileSync(0, 'utf8'));
const вихід = {};
for (const [шлях, текст] of Object.entries(файли)) {
  const частини = шлях.endsWith('.html')
    ? [...текст.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script\s*>/gi)]
      .filter(м => !/\bsrc\s*=|type\s*=\s*['"](?:application\/json|importmap)/i.test(м[1]))
      .map(м => [м[2], текст.slice(0, м.index + м[0].indexOf('>') + 1).split('\n').length - 1])
    : [[текст, 0]];
  вихід[шлях] = [];
  for (const [код, зсув] of частини) {
    try {
      const дерево = модуль.exports.parse(код, {ecmaVersion: 'latest', sourceType: 'module', locations: true});
      const зсунуті = new WeakSet();
      function зсунути(в) {
        if (!в || typeof в !== 'object') return;
        if (в.loc) for (const позиція of [в.loc.start, в.loc.end]) {
          if (!зсунуті.has(позиція)) { позиція.line += зсув; зсунуті.add(позиція); }
        }
        for (const [к, з] of Object.entries(в)) {
          if (к === 'loc') continue;
          if (Array.isArray(з)) з.forEach(зсунути); else if (з && typeof з.type === 'string') зсунути(з);
        }
      }
      зсунути(дерево);
      вихід[шлях].push(дерево);
    } catch (е) {
      process.stderr.write(`непрочитано: ${шлях}:${зсув + (е.loc?.line || 1)} — ${е.message}\n`);
      process.exitCode = 1;
    }
  }
}
process.stdout.write(JSON.stringify(вихід, (_к, з) => typeof з === 'bigint' ? String(з) : з));
