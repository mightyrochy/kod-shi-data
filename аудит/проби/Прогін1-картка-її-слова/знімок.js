// Знімок картки сценарію с4 (вада 5) на зібраній сторінці: 390×844, той самий паспорт ДО і ПІСЛЯ.
const { chromium } = require('playwright');
const [,, шлях, вихід] = process.argv;
(async () => {
  const б = await chromium.launch();
  const с = await б.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const збої = []; с.on('pageerror', e => збої.push(String(e)));
  await с.goto('file://' + шлях, { waitUntil: 'load', timeout: 180000 });
  await с.waitForTimeout(4000);
  const р = await с.evaluate(() => {
    режим('сценарій');
    ЧАТ_П.push({хто: 'людина', текст: 'побачення в ресторані ввечері, о 19:30', тема: 'сценарій'});
    ЧАТ_П.push({хто: 'ші', текст: 'Я записала: у тебе побачення в ресторані ввечері.', тема: 'сценарій'});
    ПАСПОРТ_П = {джерело: 'модель', нагода: 'побачення', місце: 'ресторан_повсякденний', місце_слова: 'Ресторан',
                 пора: 'вечір', ошатність: [3, 5], подія: 'побачення в ресторані ввечері, о 19:30',
                 цитати_полів: {нагода: 'побачення в ресторані', місце: 'ресторані', пора: 'ввечері'},
                 джерело_полів: {нагода: 'conversation', місце: 'conversation', пора: 'conversation', ошатність: 'conversation'},
                 вето: {типи: [], тканини: [], принти: [], кольори: [], зони: []}};
    ВИПАДОК_ЗМІНЕНО_П = false;
    застосуватиПаспортДоЕкрана(ПАСПОРТ_П);
    малюватиЧатП(); малюватиКарткуСценарію();
    const к = document.getElementById('сц-картка');
    к.scrollIntoView({block: 'center'});
    return {картка: к.innerText, слова: (document.getElementById('зн-слова') || {}).textContent || null};
  });
  await с.waitForTimeout(800);
  await с.screenshot({ path: вихід });
  console.log(JSON.stringify(р), збої.slice(0, 3));
  await б.close();
})();
