// Chromium 390×844: ДО/ПІСЛЯ рядків 5506–5507 на ЗІБРАНІЙ сторінці. node знімки.js <index.html> <тека>
const {chromium} = require('playwright');
const zlib = require('zlib'), fs = require('fs');
const [,, файл, тека] = process.argv; fs.mkdirSync(тека, {recursive: true});
const карт = (рука, речі) => ({рука, ітерацій: 1, викликів: 1, текст: 'Образ руки ' + рука + '. Світла сукня і тонкий пасок.',
  опис: 'Образ руки ' + рука, підпис: 'образ', речі, мітки: [], знахідки: [], питання: [], етапи: {викликів: 1, виклики: []},
  свідомі: [], невиконано: null, різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: []});
const речі = н => [{id: `ж-${н}1@g.com`, назва: 'Сукня', ціна: 3000, слот: 'сукня', фото: null},
                  {id: `ж-${н}2@g.com`, назва: 'Пасок', ціна: 500, слот: 'пояс', фото: null}];
const пакет = {в: 'ПОКАЗ-V1', збірка: 'знімок', каталог: 'каталог_стенд.xml · 639 речей', профіль: 'Оля', розклад: '3142',
  прогін: 'пр-знімок-1', випадок: 'Робота · офіс', пул: 100,
  картки: [карт('3', речі(3)), карт('1', речі(1)), карт('4', речі(4)), карт('2', речі(2))]};
const b64 = zlib.gzipSync(Buffer.from(JSON.stringify(пакет))).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const вивід = {};
(async () => {
  const br = await chromium.launch({executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
  const відкрити = async () => {
    const ctx = await br.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true, hasTouch: true});
    const p = await ctx.newPage(); p.помилки = []; p.on('pageerror', e => p.помилки.push(String(e)));
    await p.addInitScript(() => { try { localStorage.setItem('міст:службове', '1'); } catch (e) {} });
    await p.route(/^https?:/, r => r.abort());
    await p.goto('file://' + файл + '#' + b64);
    await p.waitForSelector('#картки .картка .список .річ', {timeout: 60000});
    return p;
  };
  const шот = async (p, ім, сел) => { const e = await p.$(сел); await e.scrollIntoViewIfNeeded(); await e.screenshot({path: `${тека}/${ім}.png`}); };
  const відкритиБатьків = (p, ід) => p.evaluate(ід => { let д = document.getElementById(ід); while (д) { if (д.tagName === 'DETAILS') д.open = true; д = д.parentElement; } }, ід);
  const діагноз = p => p.evaluate(() => { const е = document.getElementById('зб-діагноз'); return е.style.display === 'none' ? '(порожньо)' : е.textContent; });
  const список = async (p, ім) => {
    await p.evaluate(() => режим('бібліотека')); await відкритиБатьків(p, 'жв-список');
    const т = await p.evaluate(async () => { await малюватиВибірВивантаженняП(); return [...document.querySelectorAll('#жв-список label')].map(л => л.textContent); });
    if (ім) await шот(p, ім, '#ж-вибір');
    await p.evaluate(() => режим('образи')); return т; };
  const вердикт = async (p, j) => {
    await p.evaluate(j => { if (window.показатиОбраз) window.показатиОбраз(j); }, j);
    await p.locator(`#к-${j} .ряд[data-поле="верд"] .чип`).first().click();
    await p.waitForFunction(j => В[j] && В[j].записано, j, {timeout: 30000});
  };

  // ── 5506: сліпота до кінця
  let p = await відкрити();
  await p.evaluate(() => {
    ЗБ = {картки: П.картки, стадії: [], етап: [], ключ: [3, 1, 4, 2], готово: true, успіх: true, діагноз: [
      'hand_1 · blocks=3 · with_id=3', 'control · hand_2_broken=temperature · drawn_from=temperature,hour',
      'control · trace · breakage=temperature · packet_fields=temp · brief_rows_changed=1']};
    малюватиДіагнозП(); document.getElementById('службове').open = true; });
  вивід['5506_службове_0з4'] = await діагноз(p);
  await шот(p, '1_службове_0з4', '#службове');
  вивід['5506_список_0з4'] = await список(p, '3_список_0з4');
  for (let j = 0; j < 4; j++){
    await вердикт(p, j);
    вивід[`5506_службове_${j + 1}з4`] = await діагноз(p);
    вивід[`5506_список_${j + 1}з4`] = await список(p, (j === 0 || j === 3) ? `3_список_${j + 1}з4` : null);
    if (j === 0 || j === 3) await шот(p, `2_службове_${j + 1}з4`, '#службове');
  }
  вивід.помилки_5506 = p.помилки; await p.context().close();

  // ── 5507: «чому» після «замінити»
  p = await відкрити();
  await p.evaluate(() => { if (window.показатиОбраз) window.показатиОбраз(0); });
  const картка0 = '#к-0';
  await шот(p, '4_картка_до_дотику', картка0);
  await p.locator(`${картка0} button.замін`).first().click();
  await p.waitForFunction(() => !ЗАМІНИ_П.has(П.картки[0]), null, {timeout: 30000});
  вивід['5507_рядів_чому'] = await p.locator(`${картка0} .чому-не-ця .ряд`).count();
  вивід['5507_мітка'] = await p.locator(`${картка0} .чому-не-ця .мітка-тиха`).allTextContents();
  вивід['5507_чипи'] = await p.locator(`${картка0} .чому-не-ця .чип`).allTextContents();
  await шот(p, '5_після_замінити', картка0);
  if (вивід['5507_рядів_чому']){
    await p.locator(`${картка0} .чому-не-ця .чип`, {hasText: 'зручність'}).click();
    await шот(p, '6_чому_зручність', картка0); }
  await p.locator(`${картка0} .ряд[data-поле="верд"] .чип`).first().click();
  await p.waitForFunction(() => В[0] && В[0].записано, null, {timeout: 30000});
  // контроль: картка 1 — «замінити» без дотику по «чому»
  await p.evaluate(() => { if (window.показатиОбраз) window.показатиОбраз(1); });
  await p.locator('#к-1 button.замін').first().click();
  await p.waitForFunction(() => !ЗАМІНИ_П.has(П.картки[1]), null, {timeout: 30000});
  await p.locator('#к-1 .ряд[data-поле="верд"] .чип').first().click();
  await p.waitForFunction(() => В[1] && В[1].записано, null, {timeout: 30000});
  вивід['5507_записи'] = await p.evaluate(async () => (await усіВердикти()).map(з => ({позиція: з.позиція, замінити: з.замінити,
    замінити_чому: з.замінити_чому, about_items: (з.зведено || {}).about_items, джерело: (з.зведено || {}).джерело, розбіжності: (з.зведено || {}).розбіжності})));
  вивід.помилки_5507 = p.помилки;
  fs.writeFileSync(`${тека}/вивід.json`, JSON.stringify(вивід, null, 1));
  console.log(JSON.stringify(вивід, null, 1));
  await br.close();
})().catch(e => { console.error('ПАДІННЯ', e); process.exit(1); });
