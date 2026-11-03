/* Інвентар подій для лічби Е2. Не класифікує продукт і не є приладом кореня. */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const zlib = require('node:zlib');
const модуль = {exports: {}};
vm.runInNewContext(zlib.gunzipSync(fs.readFileSync(__dirname + '/річ_запис_дані/acorn.cjs.gz')).toString('utf8'),
  {exports: модуль.exports, module: модуль});
const acorn = модуль.exports;
const вхід = JSON.parse(fs.readFileSync(0, 'utf8'));
const вихід = [];
function пройти(вузол, дія, функція = '') {
  if (!вузол || typeof вузол.type !== 'string') return;
  if (вузол.type === 'FunctionDeclaration' && вузол.id) функція = вузол.id.name;
  дія(вузол, функція);
  for (const [ключ, значення] of Object.entries(вузол)) {
    if (ключ === 'loc') continue;
    for (const дитина of Array.isArray(значення) ? значення : [значення])
      if (дитина && typeof дитина.type === 'string') пройти(дитина, дія, функція);
  }
}
function назва(в) {
  if (!в) return '';
  if (в.type === 'Identifier') return в.name;
  if (в.type === 'Literal') return String(в.value);
  if (в.type === 'MemberExpression') return назва(в.object) + '.' + назва(в.property);
  if (в.type === 'ChainExpression') return назва(в.expression);
  return '';
}
for (const ф of вхід) {
  const дерево = acorn.parse(ф.код, {ecmaVersion: 2022, locations: true, allowReturnOutsideFunction: true});
  function додати(подія, обробник, вузол, функція) {
    const виклики = [];
    пройти(обробник, в => {
      if (в.type === 'CallExpression' || в.type === 'NewExpression') {
        const виклик = назва(в.callee);
        if (виклик) виклики.push(виклик);
      }
    });
    if (обробник.type === 'Identifier' || обробник.type === 'MemberExpression') виклики.unshift(назва(обробник));
    вихід.push({файл: ф.файл, рядок: ф.рядок + вузол.loc.start.line - 1, подія,
      функція, виклики: [...new Set(виклики)], код: ф.код.slice(обробник.start, обробник.end)});
  }
  if (ф.атрибут) додати(ф.атрибут, дерево, дерево, '');
  else пройти(дерево, (в, функція) => {
    if (в.type === 'AssignmentExpression' && в.left.type === 'MemberExpression') {
      const властивість = назва(в.left.property);
      if (/^on(?:click|change|input|submit|keydown|keyup)$/.test(властивість)) додати(властивість, в.right, в, функція);
    }
    if (в.type === 'CallExpression' && в.callee.type === 'MemberExpression' &&
        назва(в.callee.property) === 'addEventListener' && в.arguments.length >= 2 &&
        в.arguments[0].type === 'Literal' && /^(?:click|change|input|submit|keydown|keyup)$/.test(в.arguments[0].value))
      додати(в.arguments[0].value, в.arguments[1], в, функція);
  });
}
process.stdout.write(JSON.stringify(вихід));
