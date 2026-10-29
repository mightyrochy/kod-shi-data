const fs = require('fs'), path = require('path');
const root = path.resolve(process.argv[2]);
const source = path.join(root, 'джерела');
const {chromium} = require(path.join(source, 'node_modules/playwright'));
const {прочитатиДовідникJSON, підставитиШаблон} = require(path.join(source, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(fs.readFileSync(path.join(source, 'показ.html'), 'utf8'), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка-2278', __ВІДБИТОК__: 'd96e2267',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(source)
  });
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width:390,height:844}, deviceScaleFactor:1});
    await page.route('**/*', route => route.abort());
    await page.setContent(html, {waitUntil:'domcontentloaded'});
    const result = await page.evaluate(() => {
      режим('сценарій');
      ПАСПОРТ_П = {джерело:'модель',подія:'Співбесіда в офісі',нагода:'співбесіда',місце:'офіс',ошатність:[7,7],причина_ошатності:'evaluated',джерело_полів:{ошатність:'розмова'}};
      ВИПАДОК_ЗМІНЕНО_П = false;
      застосуватиПаспортДоЕкрана(ПАСПОРТ_П);
      малюватиКарткуСценарію();
      const card = document.getElementById('сц-картка');
      card.hidden = false;
      card.scrollIntoView({block:'center'});
      малюватиНотиСхем([{і:'проба',схема:'raw_scheme_key'}], {'рідша.проба':'Це пояснення варіанта.'});
      const nodes = document.createElement('div');
      nodes.appendChild(document.createTextNode('Перевірений текст'));
      const target = document.createElement('div');
      target.replaceChildren(...nodes.childNodes);
      return {картка:card.textContent.trim(),пропущений_вхід:document.getElementById('пал-рідші').textContent,типи_вузлів:[...target.childNodes].map(n=>n.nodeType)};
    });
    await page.screenshot({path:process.argv[3],animations:'disabled'});
    console.log(JSON.stringify(result));
  } finally { await browser.close(); }
})().catch(error => { console.error(error);process.exitCode=1; });
