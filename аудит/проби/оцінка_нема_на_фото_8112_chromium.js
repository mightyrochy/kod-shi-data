/* Рядок 8112 (п.9): «На фото нема …» в оцінці — повний перелік видимим текстом на 390 px, у справжньому Chromium на
   ЗІБРАНІЙ сторінці. Картка оцінки малюється із заглушки (5–6 предметів, яких нема на фото), міряється видимий текст
   рядка (innerText), число рядків і чи вміщується в екран; знімок рядка.
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/оцінка_нема_на_фото_8112_chromium.js <index.html> <знімок.png> */
const { chromium } = require('playwright'), path = require('path');
const [, , СТОРІНКА, ЗНІМОК] = process.argv;
(async () => {
  const б = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium',
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const с = await (await б.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await с.goto('file://' + path.resolve(СТОРІНКА), { waitUntil: 'load', timeout: 180000 });
  await с.waitForFunction(() => typeof малюватиКарткуОцінкиП === 'function', null, { timeout: 120000 });
  for (const коди of [['bag', 'gloves', 'tights', 'jewelry', 'necklace'], ['bag', 'gloves', 'tights', 'jewelry', 'necklace', 'shoes']]) {
    const р = await с.evaluate(коди => {
      ОЦ.фото = []; ОЦ.етапи = { мова_шару: [] }; ОЦ.перелік = { так: true };
      ОЦ.результат = { картка: { відповідь: 'Вдягай як є.', вдало: [], змінити: [], не_знаю: [], нема_на_фото: { коди } }, сценарій: {}, допит: [] };
      for (let а = document.getElementById('оц-результат'); а && а !== document.documentElement; а = а.parentElement){
        а.hidden = false; if (getComputedStyle(а).display === 'none') а.style.display = 'block'; }   // екран оцінки показано
      малюватиКарткуОцінкиП();
      const е = document.querySelector('.оц-нема-на-фото'); е.scrollIntoView({ block: 'center' });
      const г = е.getBoundingClientRect(), рядок = parseFloat(getComputedStyle(е).lineHeight);
      return { текст: е.innerText, title: е.title || null, рядків: Math.round(г.height / рядок), ширина: Math.round(г.width), вмістилось: г.right <= innerWidth && е.scrollWidth <= е.clientWidth };
    }, коди);
    console.log(JSON.stringify(р));
  }
  await с.locator('.оц-нема-на-фото').screenshot({ path: ЗНІМОК });
  await б.close();
})();
