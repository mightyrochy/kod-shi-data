/* Жива рука 6в (вада 15106): «Зібрати образи» без нагоди на 390×844 у Chromium. Сторінка складена як у стенді показу.
   Запуск: node 6в_питання_нагоди.js <тека джерела> <знімок.png>. Друкує факти одним JSON. */
const path = require('path'), дж = path.resolve(process.argv[2]), знімок = process.argv[3];
const { chromium } = require('playwright');
const { прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу } = require(path.join(дж, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'тест', __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml',
    __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const б = await chromium.launch(), с = await б.newPage({viewport: {width: 390, height: 844}});
  const помилки = []; с.on('pageerror', e => помилки.push(String(e)));
  await с.route('**/*', r => r.request().url() === 'http://stend.test/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort());
  await с.goto('http://stend.test/');
  await с.waitForFunction(() => Екран.стан.вхід > 0 && Екран.стан.запущено, null, {timeout: 60000});
  await с.evaluate(() => режим('сценарій'));
  /* картка замість прикладів — її кнопкою; вона відкриває аркуш «Нагода», його закриваємо */
  await с.click('#сц-рукою-показати'); await с.waitForTimeout(500);
  const рукою = await с.evaluate(() => { const е = document.getElementById('ред-нагода-питання'); return е ? !е.hidden : null; });
  await с.click('#аркуш-готово'); await с.waitForTimeout(500);
  /* видно — вузол не схований і в його середині зверху стоїть він сам (а не аркуш над ним) */
  const стан = () => с.evaluate(() => {
    const видно = ід => { const е = document.getElementById(ід); if (!е) return null;
      const р = е.getBoundingClientRect(); if (е.hidden || !р.width) return false;
      const в = document.elementFromPoint(р.left + р.width / 2, р.top + р.height / 2);
      return !!в && (в === е || е.contains(в)) && р.top >= 0 && р.bottom <= innerHeight; };
    const а = Екран.стан.аркуш;
    return {аркуш: а ? а.вузол.id : null, статус: зрізЗбиранняП().статус.код, на_картці: видно('зб-питання'),
            в_аркуші: видно('ред-нагода-питання'), рядок: document.getElementById('зб-статус').textContent,
            оголошення: document.getElementById('зб-оголошення').textContent};
  });
  const факти = {в_аркуші_рукою: рукою};
  await с.click('#зб-зібрати'); await с.waitForFunction(() => зрізЗбиранняП().статус.код === 'бракує');
  факти.відмова = await стан();
  /* профіль «повний», міст «є», випадку нема: лишається питання нагоди */
  await с.evaluate(() => { window.чогоБракує = () => []; МІСТ_П.адреса = 'http://stend.test/міст'; МІСТ_П.токен = 'т'; });
  await с.click('#зб-зібрати'); await с.waitForFunction(() => зрізЗбиранняП().статус.код === 'питання' && !!Екран.стан.аркуш);
  await с.waitForTimeout(600);
  факти.питання = await стан(); await с.screenshot({path: знімок});
  await с.click('#сц-нагода-плитки .плитка'); await с.waitForTimeout(300);
  факти.після_плитки = await стан();
  await с.click('#аркуш-готово'); await с.waitForTimeout(400);
  факти.після_готово = await стан();
  console.log(JSON.stringify({факти, помилки}, null, 1)); await б.close();
})().catch(e => { console.error(e); process.exit(1); });
