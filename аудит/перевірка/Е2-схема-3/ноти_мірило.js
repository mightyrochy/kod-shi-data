/* Власна проба причини червоної звірки: той самий JSDOM і код сторінки,
   затримка транспорту 60 мс; відрізняється лише спосіб запуску другого запиту. */
const fs = require('fs'), path = require('path'), Module = require('module');
const sourcePath = path.resolve(__dirname, '../../../джерела/тест_показу.js');
const source = fs.readFileSync(sourcePath, 'utf8');
const prelude = source.slice(0, source.indexOf('(async () => {'));
const start = source.indexOf('  розділ("2е-б.');
const end = source.indexOf('    /* помади: ПОМАДИ_П', start);
let section = source.slice(start, end);
section = section.replace('const м = ++__х; await new Promise',
  'const м = ++__х; (window.__початіНоти ||= []).push(м); if (window.__першіНоти) window.__першіНоти(); await new Promise');
section = section.replace('w._затримки.push(0, 0);', 'w._затримки.push(60, 0);');
section = section.replace('const в = w.eval("оновитиПалітруП()");',
  'const початі = new Promise(r => w.__першіНоти = r); const в = w.eval("оновитиПалітруП()");');
const output = path.join(__dirname, 'ноти-мірило.json');
const program = prelude + '\n(async () => { const докази = [];\n' +
  `for (const спосіб of ['пауза-30мс', 'початок-перших-нот']) {\n` +
  section.replace('await new Promise(р => setTimeout(р, 30));',
                  "if (спосіб === 'пауза-30мс') await new Promise(р => setTimeout(р, 30)); else await початі;") +
  `докази.push({спосіб, початі_ноти: w.__початіНоти, нота: $('пал-нота').textContent}); w.close();\n}\n}\n` +
  `fs.writeFileSync(${JSON.stringify(output)}, JSON.stringify(докази, null, 2)); console.log(JSON.stringify(докази));\n` +
  `})().catch(e => {console.error(e); process.exitCode = 1;});`;
const mod = new Module(sourcePath, module);
mod.filename = sourcePath;
mod.paths = Module._nodeModulePaths(path.dirname(sourcePath));
mod._compile(program, sourcePath);
