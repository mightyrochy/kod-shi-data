const fs = require('fs');
const Module = require('module');
const sourcePath = require('path').resolve(process.argv[2] || 'джерела/тест_показу.js');
const text = fs.readFileSync(sourcePath, 'utf8');
const main = text.indexOf('(async () => {');
const start = text.indexOf('  розділ("1е-і.');
const end = text.indexOf('  розділ("1є.', start);
if (!(main > 0 && start > main && end > start)) throw new Error('не знайдено меж розділу');
const body = text.slice(0, main) + '(async () => { батареяПочалась = true;\n'
  + text.slice(start, end)
  + '\nдійшлоДоКінця = true; console.log("ЗВІРОК " + виконано + "; ВПАЛО " + провалів); process.exitCode = провалів ? 1 : 0;'
  + '})().catch(e => { console.error(e); process.exitCode = 1; });';
process.argv = [process.execPath, sourcePath];
const target = new Module(sourcePath, module);
target.filename = sourcePath;
target.paths = Module._nodeModulePaths(require('path').dirname(sourcePath));
target._compile(body, sourcePath);
