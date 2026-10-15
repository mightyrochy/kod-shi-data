/* Рядки 5745–5747: «на фото нема» в оцінці — у справжньому Chromium, на ЗІБРАНІЙ сторінці, без моделі.
   Вхід — записані Б4 (живі_1510_Б/04) і 6б (живі_16/А/10): `вердикти.txt` (етапи.суд.речі з виміром, вхід прогону) і
   записана відповідь `ОЦІНКА` (той самий файл VIDPOVIDI). Міст сторінки: крок «суд» (рівень, блокери, не_на_фото),
   «оцінка_промпт» (чи модель бачить not_in_photo і блокери), «оцінка» з записаною відповіддю (коди рядка картки).
   Б4 — ще й при +2 і −10 °C (пальто в холод, 5745). Pyodide — з jsdelivr через проксі сесії.
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/оцінка_нема_на_фото_5745_chromium.js <index.html> <вердикти.txt> <відповідь.txt> [ще пара…] */
const { chromium } = require('playwright'), fs = require('fs');
const [, , СТОРІНКА, ...ПАРИ] = process.argv;
const запис = т => JSON.parse(т.slice(т.indexOf('{'), т.lastIndexOf('}') + 1));
(async () => {
  const б = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium',
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const с = await (await б.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await с.goto('file://' + require('path').resolve(СТОРІНКА), { waitUntil: 'load', timeout: 180000 });
  await с.waitForFunction(() => typeof містП === 'function', null, { timeout: 120000 });
  for (let і = 0; і < ПАРИ.length; і += 2) {
    const д = JSON.parse(fs.readFileSync(ПАРИ[і], 'utf8')), т = fs.readFileSync(ПАРИ[і + 1], 'utf8');
    const е = д.прогони.flatMap(п => п.вердикти).map(в => в.етапи || {}).find(е => е.суд && е.суд.образ);
    const промпт = запис(т.split('── ВІДПОВІДЬ')[0]), відповідь = т.split('── ВІДПОВІДЬ')[1].replace(/^[^\n]*\n/, '');
    for (const темп of [null, 2, -10]) {
      const вх = Object.assign({}, д.спільне.вхід_прогону, { крок: 'суд', речі: е.суд.речі, пікселі: {}, крамниця: false,
        сценарій_оцінки: Object.assign({}, е.сценарій_екрана || {}, темп === null ? {} : { темп_c: темп }) });
      delete вх.каталог;
      const р = await с.evaluate(async ([вх, питання, відповідь]) => {
        const суд = await містП('оцінка', вх);
        const п = JSON.parse((await містП('оцінка', { крок: 'оцінка_промпт', суд, питання })).промпт);
        const к = await містП('оцінка', { крок: 'оцінка', суд, відповідь_моделі: відповідь });
        return { рівень: суд.рівень, блокери: суд.суд.blockers.map(б => б.код), гейти: суд.суд.findings.filter(з => з.регістр === 'гейт').map(з => з.правило),
          K_WEA_01: суд.суд.findings.filter(з => з.правило === 'K-WEA-01').length, не_на_фото: [...new Set((суд.не_на_фото || []).map(х => х.слот))],
          промпт_блокери: ((п.check || {}).blockers || []).map(б => б.code), промпт_not_in_photo: п.not_in_photo || null,
          правило_на_фото: JSON.stringify(п.task || {}).includes('not_in_photo'), картка_нема_на_фото: (к.картка || {}).нема_на_фото };
      }, [вх, промпт.question, відповідь]);
      console.log(ПАРИ[і].split('/').slice(-3, -1).join('/'), 'темп', темп, JSON.stringify(р));
      if (е.суд.образ.length < 2) break;            // одна річ (6б): холод не міняє питання
    }
  }
  await б.close();
})();
