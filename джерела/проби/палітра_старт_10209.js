/* Повтор штатного браузерного шляху до старту збирання; відповіді дає replay_сцени.py.
   Після спостереження старту браузер закривається: це мірило переходу, а не якості образів. */
const fs = require('fs'), path = require('path'), Module = require('module');
const [збірка, кеш, запис] = process.argv.slice(2);
const корінь = path.resolve(__dirname, '../..');
const стенд = path.join(корінь, 'аудит/проби/рв6_стенд.js');
let код = fs.readFileSync(стенд, 'utf8');
const кінець = "await збиранняСтартувало(стор, браузер, 'збір 1');";
if (!код.includes(кінець)) throw new Error('не знайдено межу старту збирання');
код = код.replace(кінець, () => `${кінець}
  const стан = await стор.показПідЧасМоста.evaluate(() => ({
    режим: РЕЖИМ, готово: ЗБ.готово, стадія: ЗБ.стадії[0].код,
    паспорт: {нагода: ПАСПОРТ_П.нагода, намір: ПАСПОРТ_П.намір},
    три_питання: !!document.querySelector('#пал-підтон button'),
    міст: [...ЧЕКАЮТЬ_МОСТА_П.values()].map(ч => ({ім: ч.ім, асинх: ч.асинх})),
    час: Date.now() - ЗБ.почато}));
  if (стан.режим !== 'очікування' || стан.готово) throw new Error('збирання не стартувало');
  const вихід = process.env.ZNIMKY;
  await стор.знімокПосеред({path: path.join(вихід, 'старт.png')});
  fs.writeFileSync(path.join(вихід, 'старт.json'), JSON.stringify(стан, null, 2));
  const до = fs.readFileSync(path.join(${JSON.stringify(запис)}, 'лог.txt'), 'utf8');
  const таймаут = /ТАЙМАУТ очікування стану «?„?збирання стартувало чи питання нагоди/.test(до);
  console.log('МІРИЛО ' + path.basename(${JSON.stringify(запис)}) + ' · ДО (запис): '
    + (таймаут ? 'таймаут стенда' : 'старт спостережено') + ' · ПІСЛЯ: старт · ' + JSON.stringify(стан));
  await браузер.close(); process.exit(0);`);
process.argv = ['node', стенд, 'http://127.0.0.1:8765', збірка, кеш, '3'];
const модуль = new Module(стенд, module);
модуль.filename = стенд;
модуль.paths = Module._nodeModulePaths(path.dirname(стенд));
модуль._compile(код, стенд);
