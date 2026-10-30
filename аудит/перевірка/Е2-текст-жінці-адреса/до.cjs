/* Запускає нові звірки на двох незмінених модулях початкової голови.
   --після залишає поточні модулі; --лише-адреса вибирає 18 звірок адреси.
   Решту шаблону й батарею читає з робочого дерева. Запуск — з кореня репозиторію. */
const fs = require('fs');
const path = require('path');
const {execFileSync} = require('child_process');
const корінь = process.cwd();
const база = 'fa8e5c305c5e6f2ec3faf8f1b5841760ce6b4bed';
const лишеАдреса = process.argv.includes('--лише-адреса');
const після = process.argv.includes('--після');
process.argv = process.argv.filter(а => !['--лише-адреса', '--після'].includes(а));
const модулі = new Map((після ? [] : ['мовний_шар.js', 'міст.js']).map(ім => [
  path.join(корінь, 'джерела', 'показ', ім),
  execFileSync('git', ['show', база + ':джерела/показ/' + ім], {encoding: 'utf8'}),
]));
const читати = fs.readFileSync;
fs.readFileSync = function(файл, параметри){
  const текст = typeof файл === 'string' && модулі.get(path.resolve(файл));
  if (текст !== false && текст !== undefined){
    const кодування = typeof параметри === 'string' ? параметри : параметри && параметри.encoding;
    return кодування ? текст : Buffer.from(текст, 'utf8');
  }
  return читати.apply(this, arguments);
};
if (лишеАдреса){
  const Module = require('module');
  const компілювати = Module.prototype._compile;
  Module.prototype._compile = function(код, файл){
    if (файл === path.join(корінь, 'джерела', 'тест_показу.js')){
      const початок = код.indexOf('(async () => {');
      const адреса = код.indexOf('  розділ("1д-7.');
      const наступний = код.indexOf('  розділ("1д-6.', адреса);
      const кінець = код.indexOf('  дійшлоДоКінця = true;');
      if ([початок, адреса, наступний, кінець].some(і => і < 0)) throw new Error('Не знайдено меж розділу адреси');
      код = код.slice(0, початок) + '(async () => {\n  батареяПочалась = true;\n'
        + код.slice(адреса, наступний) + код.slice(кінець);
    }
    return компілювати.call(this, код, файл);
  };
}
require(path.join(корінь, 'джерела', 'тест_показу.js'));
