/* Е1-питання-без-запису-1411: ж2_помічниця_вітер_реагенти (#3319) — функція в Chromium на зібраній сторінці
   index.html: плитки «Вітер» і «Реагенти на дорогах» вибрано в екрані сценарію, сторінка (помічникП) шле міст
   `помічниця`; перехоплений вхід мосту друкується JSON-ом (його читає справжній Python у функція_помічниця_вітер.py).
   Запуск: node функція_помічниця_вітер.js <index.html> <вихід.json> */
const { chromium } = require('playwright');
const шлях = require('path').resolve(process.argv[2]);
(async () => {
  const b = await chromium.launch();
  const p = await (await b.newContext({viewport: {width: 390, height: 844}})).newPage();
  await p.goto('file://' + шлях + '#міст=http://localhost:8787&т=tok-a1');
  await p.waitForFunction(() => document.getElementById('сцн-новий') && typeof document.getElementById('сцн-новий').onclick === 'function', null, {timeout: 60000});
  const вих = {};
  for (const [назва, вітер, реаг] of [['сильний вітер, реагенти є', '2', '1'], ['безвітря, реагентів нема', '0', '0'], ['плитки не торкались', '', '']]) {
    вих[назва] = await p.evaluate(async ([в, р]) => {
      document.getElementById('сц-вітер').value = в; document.getElementById('сц-вітер').dispatchEvent(new Event('change'));
      document.getElementById('сц-реагенти').value = р; document.getElementById('сц-реагенти').dispatchEvent(new Event('change'));
      let вхід = null;
      містП = async (ім, вх) => { if (ім === 'помічниця' && !('відповідь_моделі' in вх)) вхід = вх; return {помилка: 'зупинено пробою'}; };
      try { await помічникП('Що вдягнути у вітряну погоду?', 'Ukrainian'); } catch (e) {}
      return вхід;
    }, [вітер, реаг]);
  }
  require('fs').writeFileSync(process.argv[3], JSON.stringify(вих, null, 1));
  console.log(Object.entries(вих).map(([н, в]) => { const п = ((в.стан || {}).сценарій || {}).поля || {}; return н + ': поля.вітер_бал=' + JSON.stringify(п.вітер_бал) + ' поля.реагенти=' + JSON.stringify(п.реагенти); }).join('\n'));
  await b.close();
})();
