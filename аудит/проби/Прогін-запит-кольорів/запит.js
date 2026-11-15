/* Вада 9 живих «як людина» 13.11 і 14.11 (дошка 15407): поле «Запит для чату» на знайомстві. Зібраний показ-повний
   (index.html) у Chromium 390×844; Pyodide й мережа відрізані — знайомство й розкривач робить JS показу.
   Дії жінки: перший екран → «без портрета» (розкривач у «Твоїх кольорах») → «Скопіювати запит».
   Запуск: NODE_PATH=/opt/node-tools/node_modules node запит.js <index.html> <префікс знімків> */
const { chromium } = require('playwright');
const fs = require('fs');
const [файл, префікс] = process.argv.slice(2), html = fs.readFileSync(файл, 'utf8'), БАЗА = 'http://127.0.0.1:8765/';
const ЛАТИНИЦЯ = /[A-Za-z]{2,}/g;
async function сторінка(б, хеш, копія){
  const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
  await к.route('**/*', r => r.request().url().split('#')[0] === БАЗА ? r.fulfill({contentType: 'text/html', body: html}) : r.abort());
  const с = await к.newPage();
  await с.addInitScript(ок => { document.execCommand = () => { window.__копія = document.activeElement && document.activeElement.value; return ок; }; }, копія);
  await с.goto(БАЗА + хеш); await с.waitForSelector('#кол-блок', {state: 'attached'}); await с.waitForTimeout(800);
  return с;
}
/* видимий текст блоку «Твої кольори» разом зі вмістом видимих полів — те, що жінка читає */
const видиме = с => с.evaluate(() => {
  const б = document.getElementById('кол-блок'), поля = [...б.querySelectorAll('textarea, input')]
    .filter(п => п.offsetParent !== null && п.type !== 'hidden').map(п => п.value);
  return {текст: б.innerText, поля, запит_видно: document.getElementById('кол-запит').offsetParent !== null};
});
(async () => {
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined}), ф = {};
  let с = await сторінка(б, '', true);
  const кнопка = await с.$('#кол-без-портрета');
  if (кнопка) await кнопка.click(); else await с.evaluate(() => { document.getElementById('кол-інший-шлях').open = true; });
  await с.waitForTimeout(400);
  const в = await видиме(с), латиниця = (в.текст + '\n' + в.поля.join('\n')).match(ЛАТИНИЦЯ) || [];
  ф.розкривач = {запит_видно: в.запит_видно, латинських_слів: латиниця.length, перші: латиниця.slice(0, 6),
                 поля: в.поля.map(п => п.slice(0, 60))};
  await с.evaluate(() => document.getElementById('кол-інший-шлях').scrollIntoView({block: 'start'}));
  await с.screenshot({path: префікс + '_розкривач.png'});
  await с.click('#кол-копія'); await с.waitForTimeout(300);
  ф.копія = await с.evaluate(() => ({той_самий_промпт: window.__копія === ПРОМПТ_КОЛІР, довжина: (window.__копія || '').length,
                                     стан: document.getElementById('кол-стан').textContent}));
  /* копіювання не вдалося — запит лишається виділити руками: поле з’являється */
  с = await сторінка(б, '', false);
  await с.evaluate(() => { document.getElementById('кол-інший-шлях').open = true; }); await с.click('#кол-копія'); await с.waitForTimeout(300);
  ф.копія_не_вдалась = await с.evaluate(() => ({запит_видно: document.getElementById('кол-запит').offsetParent !== null,
    той_самий_промпт: document.getElementById('кол-запит').value === ПРОМПТ_КОЛІР, стан: document.getElementById('кол-стан').textContent}));
  /* власник: #службове=1 */
  с = await сторінка(б, '#службове=1', true);
  await с.evaluate(() => { document.getElementById('кол-інший-шлях').open = true; }); await с.waitForTimeout(300);
  ф.службове = await с.evaluate(() => ({запит_видно: document.getElementById('кол-запит').offsetParent !== null,
    той_самий_промпт: document.getElementById('кол-запит').value === ПРОМПТ_КОЛІР}));
  await б.close();
  console.log(JSON.stringify(ф, null, 1));
  console.log('латинських слів у «Твоїх кольорах» (текст і поля): ' + ф.розкривач.латинських_слів);
})().catch(e => { console.error(e); process.exit(1); });
