/* Запускає незмінену звірку нот зі штатними JSDOM-помічниками.
   Мутація забирає лише захист старих нот у копії шаблону в пам'яті. */
const fs = require('fs'), path = require('path'), Module = require('module');
const режим = process.argv[2], затримка = Number(process.argv[3]);
if (!['штатний', 'мутація'].includes(режим) || !Number.isFinite(затримка))
  throw new Error('Потрібні режим штатний/мутація й затримка транспорту в мс');
const корінь = process.env.LYUSTERKO_TEST_ROOT || path.resolve(__dirname, '../../..');
const шлях = path.join(корінь, 'джерела/тест_показу.js');
const код = fs.readFileSync(process.env.LYUSTERKO_TEST_SOURCE || шлях, 'utf8');
const початок = код.indexOf('  розділ("2е-б.');
const кінець = код.indexOf('    /* помади: ПОМАДИ_П', початок);
if (початок < 0 || кінець < 0) throw new Error('Не знайдено штатного розділу нот');
let вступ = код.slice(0, код.indexOf('(async () => {'));
let звірка = код.slice(початок, кінець);
const транспорт = 'w._затримки.push(0, 0);';
if (!звірка.includes(транспорт)) throw new Error('Не знайдено транспорту мовних нот');
звірка = звірка.replace(транспорт, `w._затримки.push(${затримка}, 0);`);
if (режим === 'мутація') {
  вступ = вступ.replace('const шаблон = зібратиШаблонПоказу', 'let шаблон = зібратиШаблонПоказу');
  вступ += `\nconst захист = "if (!чиннеМістуП('палітри', пок)) return;   // за час мовної моделі вхід змінився: ноти ті, що від нового";
    if (шаблон.split(захист).length !== 2) throw new Error('Захист нот має бути рівно один');
    шаблон = шаблон.replace(захист, '/* захист нот навмисно вилучено в пам’яті */');\n`;
}
process.argv = [process.argv[0], шлях];
const програма = вступ + '\n(async () => {\n' + звірка
  + `\nconsole.log('ДОКАЗ ' + JSON.stringify({режим: ${JSON.stringify(режим)},
       транспорт_мс: ${затримка}, нота: $('пал-нота').textContent,
       звірок: виконано, провалів}));
     w.close(); process.exitCode = провалів ? 1 : 0;
  }\n})().catch(e => { console.error(e); process.exitCode = 2; });`;
const модуль = new Module(шлях, module);
модуль.filename = шлях;
модуль.paths = Module._nodeModulePaths(path.dirname(шлях));
модуль._compile(програма, шлях);
