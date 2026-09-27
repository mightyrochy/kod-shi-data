/* Ф-143 очима (CLAUDE.md п.10): картка, де в однієї речі кадр ЖИВИЙ, у другої адреса
   МЕРТВА, а третя без кадрів зовсім. Друкує, що стоїть у кожному рядку списку й у
   колажі, і кладе знімок картки — щоб силует дивились оком, а не лічили в DOM.
   Запуск: CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=<тека з playwright> \
     node проби/kadr_syluet_f143.js <корінь зі зібраним index.html> <знімок.png> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const КОРІНЬ = process.argv[2] || '/tmp/стенд', ЗНІМОК = process.argv[3] || '/tmp/kadr_syluet_f143.png';
const БАЗА = 'http://127.0.0.1:8765';
const ЖИВЕ = 'https://www.sunwin-store.com/wp-content/uploads/2026/07/2968_champagne_2.webp';
const МЕРТВЕ = 'https://www.sunwin-store.com/wp-content/uploads/2026/07/НЕМА-ТАКОГО.webp';
const річ = (н, назва, слот, ф, усі) => ({id: 'ж-0' + н + '@sunwin-store.com', назва, слот, ціна: 1000 * н, фото: ф, фото_усі: усі});
const карт = {рука: '1', ітерацій: 1, викликів: 1, текст: 'образ', опис: 'образ', підпис: 'образ',
  речі: [річ(1, 'Светр оверсайз', 'верх', ЖИВЕ, [ЖИВЕ]), річ(2, 'Штани палацо', 'низ', МЕРТВЕ, [МЕРТВЕ, МЕРТВЕ]),
         річ(3, 'Сумка шкіряна', 'сумка', null, [])],
  мітки: [], знахідки: [], питання: [], етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null,
  різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: []};
const б64 = zlib.gzipSync(Buffer.from(JSON.stringify({в: 'ПОКАЗ-V1', збірка: 'ф143', каталог: 'каталог · 3 речі',
  профіль: 'Оля', розклад: '1234', випадок: 'Робота · офіс корпоративний', пул: 100, картки: [карт]})))
  .toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
(async () => {
  const бр = await chromium.launch({executablePath: process.env.CHROMIUM});
  const ст = await (await бр.newContext({viewport: {width: 390, height: 844}})).newPage();
  await ст.route(u => u.origin === new URL(БАЗА).origin, async r => {
    const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\//, '') || 'index.html';
    const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return r.fulfill({status: 404, body: 'нема ' + ім});
    await r.fulfill({status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain', body: fs.readFileSync(ф)});
  });
  /* той самий таймаут на кадр, що в стенді (Ф-143): крамниця не тримає прилад */
  await ст.route(u => u.origin !== new URL(БАЗА).origin, async r => {
    try { await r.fulfill({response: await r.fetch({timeout: 12000})}); } catch (_) { try { await r.abort(); } catch (__) {} } });
  await ст.goto(БАЗА + '/index.html#' + б64, {waitUntil: 'domcontentloaded'});
  await ст.waitForFunction(() => document.querySelectorAll('#картки .картка .список .річ').length === 3, null, {timeout: 60000});
  await ст.waitForTimeout(8000);          // два кола ряду плюс запас на мережу
  console.log(JSON.stringify(await ст.evaluate(() => ({
    список: [...document.querySelectorAll('#картки .картка .список .річ')].map(р =>
      ((р.querySelector('a, .назва') || {}).textContent || '') + ' → ' + (р.querySelector('img') ? 'кадр' : р.querySelector('i.арка') ? 'силует' : 'ПОРОЖНЬО')),
    колаж: {кадрів: document.querySelectorAll('.колаж img').length, силуетів: document.querySelectorAll('.колаж i.арка').length},
    фраз_коду: /знімок крамниці не відкрився/.test(document.body.innerText)})), null, 1));
  await (await ст.$('#картки .картка')).screenshot({path: ЗНІМОК});
  console.log('знімок: ' + ЗНІМОК + ' ' + fs.statSync(ЗНІМОК).size + ' Б');
  await бр.close();
})();
