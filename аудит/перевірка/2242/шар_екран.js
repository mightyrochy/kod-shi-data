// 11290 наскрізно: шар приймає повідомлення (той самий шлях, що й живий), картки перемальовано; потім пакет з `свої_шару` у новій вкладці.
const {chromium} = require('playwright'); const zlib = require('zlib'), fs = require('fs');
const [,, файл, тека] = process.argv; fs.mkdirSync(тека, {recursive: true});
const src = fs.readFileSync(__dirname + '/знімки.js', 'utf8');
const пакет = eval(src.slice(src.indexOf('const річ ='), src.indexOf('const b64')) + ';пакет');
const хеш = п => zlib.gzipSync(Buffer.from(JSON.stringify(п))).toString('base64').replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/, '');
const лік = async p => p.evaluate(() => ({шаблонів: (document.getElementById('картки').innerText.match(/— без тексту/g) || []).length,
  журнал: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.map(з => з.причина)}));
(async () => {
  const br = await chromium.launch();
  const нова = async (п) => { const ctx = await br.newContext({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true});
    const p = await ctx.newPage(); p.помилки = []; p.on('pageerror', e => p.помилки.push(String(e)));
    await p.route(/^https?:/, r => r.abort()); await p.goto('file://' + файл + '#' + хеш(п));
    await p.waitForSelector('#картки .картка', {timeout: 90000}); await p.waitForTimeout(1200); return p; };
  let p = await нова(пакет);
  const без_шару = await лік(p);
  const з1 = пакет.картки[0].замінено, з2 = пакет.картки[1].неповний;
  await p.evaluate(([з1, з2]) => {
    перевіритиКінцевуВідповідьШаруП({тексти: {}, заяви: [
      {ключ: 'замінено', повідомлення: 'замінено', заяви: [{code: 'item_replaced', values: {removed_item: 'Жіноча Кросбоді з ланцюгом Сromia MINA'}}], текст: з1},
      {ключ: 'неповний', повідомлення: 'неповний', заяви: [{code: 'item_removed', values: {item: 'вовняне бежеве пальто casual'}}], текст: з2}]});
    ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.length = 0; рендер();
  }, [з1, з2]);
  await p.waitForTimeout(800);
  const після_шару = await лік(p);
  await p.evaluate(() => { if (window.показатиОбраз) window.показатиОбраз(0); });
  await (await p.$('#к-0')).screenshot({path: `${тека}/картка1_ПІСЛЯ_доробки.png`});
  const П2 = await p.evaluate(() => JSON.parse(JSON.stringify(П)));
  const свої = П2.картки.map(к => к.свої_шару || null);
  await p.context().close();
  p = await нова(П2);   // нова вкладка: сесійного набору нема, лише `свої_шару` з пакета
  const з_пакета = await лік(p);
  const помилки = p.помилки; await br.close();
  const вивід = {без_шару, після_шару, свої_шару: свої, з_пакета, помилки};
  fs.writeFileSync(`${тека}/шар_екран.json`, JSON.stringify(вивід, null, 1)); console.log(JSON.stringify(вивід));
})().catch(e => { console.error(e); process.exit(1); });
