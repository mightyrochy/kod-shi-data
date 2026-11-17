// node знімок.cjs <дерево призначеної голови> <тимчасова тека знімка>
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const джерела = path.resolve(process.argv[2], 'джерела');
const вихід = path.resolve(process.argv[3]); fs.mkdirSync(вихід, {recursive:true});
const {chromium} = require(path.join(джерела, 'node_modules/playwright'));
const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(джерела, 'показ_шаблон.js'));
const html = підставитиШаблон(fs.readFileSync(path.join(джерела, 'показ.html'), 'utf8'), {
  __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка-4080', __ВІДБИТОК__: '1db51694',
  __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: 'каталог без перезбору', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(джерела),
});
const файл = path.join(вихід, 'показ4080.html'); fs.writeFileSync(файл, html);
(async () => {
  const браузер = await chromium.launch({headless:true, args:['--disable-gpu']});
  try {
    const сторінка = await браузер.newPage({viewport:{width:390, height:844}, deviceScaleFactor:1});
    const помилки = []; сторінка.on('pageerror', e => помилки.push(String(e)));
    await сторінка.route(/^https?:/, r => r.abort());
    await сторінка.goto(pathToFileURL(файл).href);
    await сторінка.waitForLoadState('load');
    await сторінка.screenshot({path:path.join(вихід,'показ4080-390x844.png'), animations:'disabled'});
    fs.writeFileSync(path.join(вихід,'показ4080.json'), JSON.stringify({голова:'1db5169480208fde21e2003dc58c84257b369a51',розмір:[390,844],помилки,межі:'Початковий екран шаблону голови, без викликів моделей і перезбору каталогу.'},null,2));
    console.log(JSON.stringify({помилки,знімок:'показ4080-390x844.png'}));
  } finally {await браузер.close();}
})().catch(e => {console.error(e); process.exitCode=1;});
