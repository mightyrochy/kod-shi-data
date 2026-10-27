/* Офлайн-знімки 390×844: записані паспорти й чинний показ, без викликів моделей. */
const fs = require('fs'), path = require('path'), {execFileSync} = require('child_process');
const {chromium} = require('../../джерела/node_modules/playwright');
const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require('../../джерела/показ_шаблон.js');
const корінь = path.resolve(__dirname, '../..'), код = path.join(корінь, 'джерела');
const тека = path.resolve(process.argv[2] || path.join(корінь, 'аудит/огляд_коду/доробка_1873_2'));
const входи = require('../огляд_коду/доробка_1873/входи.json');
const {міст} = require('./доробка_1873.js');
async function main(){
  fs.mkdirSync(тека, {recursive: true});
  const шаблон = зібратиШаблонПоказу(path.join(код, 'показ.html'));
  const html = підставитиШаблон(шаблон, {__МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: 'replay-1873',
    __ВІДБИТОК__: 'replay-1873', __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'офлайн',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(код)});
  const браузер = await chromium.launch({headless: true, args: ['--disable-gpu'],
    ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {})});
  try{
    for (const до of [true, false]) for (const сцена of входи.чат){
      const стор = await браузер.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
      const помилки = []; стор.on('pageerror', е => помилки.push(String(е)));
      const сторінка = до ? html.replace(fs.readFileSync(path.join(код, 'показ/паспорт.js'), 'utf8'),
        execFileSync('git', ['show', '68e5ef3e7:джерела/показ/паспорт.js'], {cwd: корінь, encoding: 'utf8'})) : html;
      await стор.exposeFunction('містОфлайн', міст);
      await стор.route('**/*', маршрут => маршрут.request().url() === 'http://offline.local/'
        ? маршрут.fulfill({contentType: 'text/html', body: сторінка}) : маршрут.abort());
      await стор.goto('http://offline.local/#model_mova=offline');
      await стор.waitForFunction(() => !!document.getElementById('вк-сценарій').onclick);
      await стор.evaluate(async сцена => {
        ЧАТ_П = [{хто: 'людина', тема: 'сценарій', текст: сцена.слова}];
        ПАСПОРТ_П = null;
        містП = async (_, вхід) => window.містОфлайн(вхід);
        модельМовиП = async () => '';
        оновитиДовідникП = async () => {};
        паспортПоРозмовіП = async () => ({паспорт: сцена.паспорт});
        повідомленнямП = async () => ({тексти: {}, записи: []});
        мовоюП = async тексти => ({тексти, записи: []});
        await розмоваЯкMainП(сцена.слова, [], false, 'сценарій', [{причина: 'only_questions'}], () => true);
        режим('сценарій'); малюватиЧатП();
        window.scrollTo(0, 0);
      }, сцена);
      if (помилки.length) throw new Error(помилки.join('\n'));
      const файл = path.join(тека, (до ? 'до_' : 'після_') + сцена.сцена + '.png');
      await стор.screenshot({path: файл, animations: 'disabled'}); console.log(файл);
      await стор.close();
    }
  }finally{ await браузер.close(); }
}
if (require.main === module) main().catch(е => {console.error(е); process.exitCode = 1;});
