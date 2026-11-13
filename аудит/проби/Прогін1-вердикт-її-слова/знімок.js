// Вада 1 прогону 13.11: вона пише «Своїми словами» й тисне «Записати вердикт», не торкаючись «Вдягнеш?».
// Зібрана сторінка, 390×844 (масштаб 2), той самий прогін із чотирьох карток ДО і ПІСЛЯ; міст «вердикт», «мова» й перекладач
// підмінено (офлайн, без моделей). Знімки: <префікс>-1-картка.png, -2-усі-образи.png, -3-файл.png; файл вердиктів —
// <префікс>-вердикти.json (те, що віддала кнопка «Зберегти всі вердикти файлом», або нічого).
const { chromium } = require('playwright');
const fs = require('fs');
const [,, шлях, префікс] = process.argv;
const СЛОВА = 'Сукня гарна, але для новорічної вечірки замало блиску — я б додала сережки й узяла туфлі на нижчому підборі.';
const картка = рука => ({рука, збій: false, ітерацій: 1, викликів: 1, текст: 'Образ ' + рука + '.', опис: 'Образ ' + рука + '.',
  як_носити: [], речі: [{id: 'ж-' + рука + '@g.com', назва: 'Сукня ' + рука, ціна: 3000, слот: 'сукня'}],
  мітки: [], знахідки: [], питання: [], етапи: {прогін: {пул_речей: 100}, викликів: 1, виклики: [], суд: {}},
  свідомі: [], невиконано: null, різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [],
  дібрав_код_слоти: []});
(async () => {
  const б = await chromium.launch();
  const к = await б.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, acceptDownloads: true });
  const с = await к.newPage();
  const збої = []; с.on('pageerror', e => збої.push(String(e)));
  await с.goto('file://' + шлях, { waitUntil: 'load', timeout: 180000 });
  await с.waitForFunction(() => typeof (document.getElementById('сцн-новий') || {}).onclick === 'function', null, {timeout: 120000});
  await с.evaluate(п => {
    const містБуло = містП;
    містП = async (ім, вх) => (ім === 'вердикт' ? [] : ім === 'мова' ? {не_ця: [], додано: null} : містБуло(ім, вх));
    перекластиП = async вид => ({внутрішня: {}, запис: {вид}});
    П = п; П.прогін = новийІдПрогону(); П.випадок_рядок = 'Новорічна вечірка · вечір';
    режим('образи'); рендер();
  }, {в: 'ПОКАЗ-V1', збірка: 'знімок-вердикт', каталог: 'каталог', профіль: 'Оля', розклад: '1234', пул: 100,
      картки: ['1', '2', '3', '4'].map(картка)});
  await с.waitForFunction(() => document.querySelectorAll('#картки .картка').length === 4);
  await с.fill('#ком-0', СЛОВА);
  await с.click('#зап-0');
  // ДО — статус одразу; ПІСЛЯ — чекаємо кінця запису («Записано.» під кнопкою першої картки)
  await с.waitForFunction(() => /Записано|Обери|Напиши/.test(document.getElementById('вст-0').textContent), null, {timeout: 60000});
  await с.waitForTimeout(500);
  const стан = await с.evaluate(() => ({статус: document.getElementById('вст-0').textContent,
    видно: [...document.querySelectorAll('#картки .картка')].findIndex(к => !к.hidden),
    лічба: (document.querySelector('#пейджер .пж-оц') || {}).textContent || ''}));
  // знімок — перша картка з кнопкою і статусом під нею
  // ПІСЛЯ запис веде на наступну неоцінену — повертаємось на першу тим самим пейджером, що й вона
  await с.evaluate(() => { window.показатиОбраз(0); document.getElementById('вст-0').scrollIntoView({block: 'center'}); });
  await с.waitForTimeout(400);
  await с.screenshot({ path: префікс + '-1-картка.png' });
  // «Усі образи»: плитка цього прогону, журнал, «Зберегти всі вердикти файлом»
  await с.evaluate(() => режим('бібліотека'));
  await с.waitForTimeout(1500);
  await с.evaluate(() => { document.getElementById('журнал').open = true; });
  const чекати = с.waitForEvent('download', {timeout: 5000}).catch(() => null);
  await с.click('#ж-файл');
  const файл = await чекати;
  if (файл) await файл.saveAs(префікс + '-вердикти.json');
  await с.waitForTimeout(600);
  const біб = await с.evaluate(() => ({плитка: (document.querySelector('#біб-список .біб-образ em') || {}).textContent || '',
    журнал: document.getElementById('ж-список').textContent, файл: document.getElementById('ж-стан').textContent}));
  await с.evaluate(() => { const п = document.querySelector('#біб-список h2, #біб-список .біб-образ'); if (п) п.scrollIntoView({block: 'start'}); });
  await с.waitForTimeout(300);
  await с.screenshot({ path: префікс + '-2-усі-образи.png' });
  await с.evaluate(() => document.getElementById('ж-стан').scrollIntoView({block: 'center'}));
  await с.waitForTimeout(300);
  await с.screenshot({ path: префікс + '-3-файл.png' });
  console.log(JSON.stringify({стан, біб, файл: !!файл, збої: збої.slice(0, 3)}));
  await б.close();
})();
