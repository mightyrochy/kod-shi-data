// Відкрити сторінки звичайним Chromium без профілю й обходу захистів; зберегти DOM у gzip.
// Запуск: node річ_запис_рендер.js вхід.json вихідна_тека результат.json
// вхід: [{файл, url}]; результат: [{файл, url, http, кінцева, байтів, помилка}]
const { chromium } = require('playwright');
const fs = require('fs'), zlib = require('zlib'), path = require('path');
(async () => {
  const [вхід, тека, вихід] = process.argv.slice(2);
  const список = JSON.parse(fs.readFileSync(вхід, 'utf8'));
  const б = await chromium.launch();
  const к = await б.newContext({ locale: 'uk-UA' });
  const результат = [];
  let наступний = 0;
  async function робітник() {
    while (наступний < список.length) {
      const р = список[наступний++];
      const о = { файл: р.файл, url: р.url };
      const с = await к.newPage();
      try {
        const в = await с.goto(р.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
        await с.waitForTimeout(3000);
        const html = await с.content();
        o_http = в ? в.status() : null;
        о.http = o_http; о.кінцева = с.url(); о.байтів = html.length;
        if (o_http === 200) fs.writeFileSync(path.join(тека, р.файл), zlib.gzipSync(Buffer.from(html, 'utf8'), { level: 9 }));
      } catch (e) { о.помилка = String(e).split('\n')[0]; }
      await с.close();
      результат.push(о);
    }
  }
  await Promise.all([1, 2, 3, 4].map(робітник));
  fs.writeFileSync(вихід, JSON.stringify(результат.sort((а, б) => а.url < б.url ? -1 : 1), null, 2) + '\n');
  await б.close();
})();
