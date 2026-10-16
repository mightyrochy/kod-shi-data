// 5422: шапка над картками в справжньому Chromium 390×844 на ЗІБРАНІЙ сторінці. Шматки — вихід
// `паспорт_нагоди.паспорт_шматками_людині` на сцені `аудит/живі_12/А/08_ж7_мороз_без_відкритого` (replay
// `проби/паспорт_слова_5195.py`): ДО — main, ПІСЛЯ — ця гілка без слів шапки в записаному ході, ПІСЛЯ_СЛОВА — з
// `header` ходу (слова — заглушка мовної моделі, живий прогін їх не заміряв). Друкує текст шапки й знімок у тека.
// Запуск: node проби/шапка_5422.js <index.html> <тека>
const {chromium} = require('playwright'); const zlib = require('zlib'), fs = require('fs');
const [,, файл, тека] = process.argv; fs.mkdirSync(тека, {recursive: true});
const ш = (ключ, текст, звідки, код) => Object.assign({ключ, текст}, звідки ? {звідки} : {}, код ? {код} : {});
const ВАРІАНТИ = {
  до: [ш('нагода', 'Робота'), ш('місце', 'прогулянка'), ш('темп_c', '-15 °C'), ш('опади', 'сніг', null, 'сніг')],
  після: [ш('нагода', 'Робота', 'плитка'), ш('місце', 'Прогулянка', 'плитка')],
  після_слова: [ш('нагода', 'Робота', 'плитка'), ш('місце', 'Прогулянка', 'плитка'), ш('темп_c', "мінус п'ятнадцять", 'мова'),
                ш('опади', 'іде сніг', 'мова', 'сніг')]};
const карт = (рука, н) => ({рука, ітерацій: 1, викликів: 1, текст: 'Образ ' + рука, опис: 'Образ ' + рука, підпис: 'образ',
  речі: [{id: `ж-${н}1@g.com`, назва: 'Пальто', ціна: 3000, слот: 'верхній_шар', фото: null}], мітки: [], знахідки: [], питання: [],
  етапи: {викликів: 1, виклики: []}, свідомі: [], мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: []});
(async () => {
  const br = await chromium.launch({executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
  for (const [вар, шматки] of Object.entries(ВАРІАНТИ)) {
    const пакет = {в: 'ПОКАЗ-V1', збірка: 'знімок', каталог: 'знімок', профіль: 'Оля', розклад: '3142', прогін: 'пр-' + вар, пул: 1,
      випадок: шматки.map(х => х.текст).join(' · '), випадок_шматки: шматки, картки: ['3', '1', '4', '2'].map(р => карт(р, р))};
    const b64 = zlib.gzipSync(Buffer.from(JSON.stringify(пакет))).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
    const ctx = await br.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true, hasTouch: true});
    const p = await ctx.newPage(); const пом = []; p.on('pageerror', e => пом.push(String(e)));
    await p.route(/^https?:/, r => r.abort()); await p.goto('file://' + файл + '#' + b64);
    await p.waitForSelector('#картки .картка', {timeout: 90000});
    const т = await p.evaluate(() => [...document.querySelectorAll('#обр-випадок span')].map(s => s.textContent));
    const кодів = т.join(' ').match(/\b[a-z]+_[a-z_]+\b|\bunknown\b/g) || [];
    await p.screenshot({path: `${тека}/шапка_${вар}.png`, clip: {x: 0, y: 0, width: 390, height: 400}});
    console.log(`${вар}: ${т.join(' · ')} · кодів ${кодів.length} · помилок сторінки ${пом.length}`); await ctx.close();
  }
  await br.close();
})();
