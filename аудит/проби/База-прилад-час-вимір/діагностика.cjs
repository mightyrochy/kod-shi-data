/* Показує останню файлову операцію самоперевірки перед аварією Node, не міняючи її аргументів. */
const fs = require('fs'), path = require('path'), cp = require('child_process');
for (const name of ['mkdtempSync', 'mkdirSync', 'cpSync', 'rmSync', 'writeFileSync']) {
  const original = fs[name];
  fs[name] = (...args) => {
    process.stderr.write(name + ' ' + JSON.stringify(args.slice(0, name === 'cpSync' ? 2 : 1)) + '\n');
    return original(...args);
  };
}
const spawn = cp.spawnSync;
cp.spawnSync = (...args) => {
  process.stderr.write('spawnSync ' + JSON.stringify(args.slice(0, 2)) + '\n');
  return spawn(...args);
};
require(path.join(__dirname, '../перевірити_нову_базу.js'));
