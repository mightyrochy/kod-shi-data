/* Вимірює виклики тесту без зміни аргументів, результатів і таймаутів. */
const cp = require('node:child_process');
const fs = require('node:fs');
const original = cp.spawnSync;
cp.spawnSync = function (command, args, options) {
  const start = performance.now();
  const result = original.apply(this, arguments);
  fs.appendFileSync(process.env.LYUSTERKO_CHILD_TIMINGS, JSON.stringify({
    час_utc: new Date().toISOString(), команда: String(command),
    аргумент_0: args?.[0], мс: Math.round(performance.now() - start),
    код: result.status, помилка: result.error?.code || null
  }) + '\n');
  return result;
};
