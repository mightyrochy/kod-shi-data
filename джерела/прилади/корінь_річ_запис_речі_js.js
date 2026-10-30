// Помічник приладу `корінь_річ_запис_речі.py`: розбір JS у дерево (acorn із самого node, без npm) і друк JSON.
// Запуск: node --expose-internals <цей файл> <файл.js> [<файл.js> …] > дерево.json. Файл, що не розібрано, — {"помилка": …}.
// Лише розбирає: нічого не лічить і не править.
const fs = require('fs');
let acorn = null;
for (const шлях of ['internal/deps/acorn/acorn/dist/acorn', 'acorn']) {
  try { acorn = require(шлях); break; } catch (е) { /* наступний */ }
}
if (!acorn) { console.log(JSON.stringify({ помилка: 'acorn недоступний' })); process.exit(0); }
const вихід = {};
for (const файл of process.argv.slice(2)) {
  let текст = fs.readFileSync(файл, 'utf8');
  try {
    let дерево;
    try { дерево = acorn.parse(текст, { ecmaVersion: 'latest', locations: true, sourceType: 'script', allowReturnOutsideFunction: true }); }
    catch (е) { дерево = acorn.parse(текст, { ecmaVersion: 'latest', locations: true, sourceType: 'module' }); }
    вихід[файл] = JSON.parse(JSON.stringify(дерево, (к, з) => {
      if (к === 'loc') return undefined;
      if (з && typeof з === 'object' && !Array.isArray(з) && з.loc) { з.line = з.loc.start.line; }
      if (к === 'start' || к === 'end' || к === 'raw') return undefined;
      if (з instanceof RegExp) return undefined;
      return з;
    }));
  } catch (е) { вихід[файл] = { помилка: String(е.message || е).slice(0, 120) }; }
}
process.stdout.write(JSON.stringify(вихід));
