/* Рядки 5742, 5811, 5812: «Що не так?» (слова й голос) у кроці переліку речей — справжній Chromium 390×844 на ЗІБРАНІЙ сторінці
   (Pyodide з її кодом). Модель — заглушка: «речі» віддають записані речі, перекладач `review_items_fix` — готові дії (він читає
   КОНТЕКСТ.items з промпта, тож перевіряється й контекст), мережі нема. Мікрофон — підставний SpeechRecognition (у headless його нема).
   Міряє: (А) «там не штани, а вершкові ботильйони, чорні — запасні» → 3 дії на перелік; (Б) після «✕ н2 + нова» ід не повторюється;
   (В) дотик під час перемальовування не губиться — `locator.tap` по фото в редакторі при штормі `малюватиПерелікП`, вузли живуть;
   рядок 6112 у (А): дописані словами ботильйони мають назву, яку мовна модель написала з коду виду.
   Запуск: NODE_PATH=<тека з playwright> CHROMIUM=/opt/pw-browsers/chromium [ДО=1] node проби/речі_голосом_5742.js <html> <тека pyodide> <тека знімків>
   ДО=1 — зібрана сторінка `main` (без «Що не так?»): пропускає (А) і ловить лише (В); без нього перевіряє все. */
const fs = require('fs'), path = require('path'), assert = require('assert'), { chromium } = require('playwright');
const [, , html, текаPyodide, тека] = process.argv;
const ДО = process.env['ДО'] === '1';
fs.mkdirSync(тека, { recursive: true });
const вивід = [];
const лог = (...а) => { const р = а.join(' '); вивід.push(р); console.log(р); };
const ФРАЗА = 'там не штани, а вершкові ботильйони, чорні — запасні';
const РЕЧІ = [
  { photo: 'ф1', name: 'white blouse', kind: 'blouse', slot: 'top', color: 'white', pattern: 'solid', formality: 5, in_outfit: true, frame: { left: 100, top: 60, right: 900, bottom: 480 } },
  { photo: 'ф1', name: 'black trousers', kind: 'trousers', slot: 'bottom', color: 'black', pattern: 'solid', formality: 5, in_outfit: true, frame: { left: 100, top: 500, right: 900, bottom: 980 } },
  { photo: 'ф2', name: 'black ankle boots', kind: 'ankle_boots', slot: 'shoes', color: 'black', pattern: 'solid', formality: 5, in_outfit: true, frame: { left: 100, top: 300, right: 900, bottom: 900 } }];
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, reducedMotion: 'reduce' });
    page.setDefaultTimeout(90000);
    await page.route('**/*', r => {
      const u = new URL(r.request().url());
      if (u.hostname === 'probe.invalid' && u.pathname === '/') return r.fulfill({ contentType: 'text/html', body: fs.readFileSync(html, 'utf8') });
      if (u.hostname === 'cdn.jsdelivr.net' && u.pathname.includes('/pyodide/')) {
        const ім = u.pathname.split('/').pop(), ф = path.join(текаPyodide, ім);
        const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
        return fs.existsSync(ф) ? r.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф) }) : r.abort();
      }
      return r.abort();
    });
    page.on('pageerror', e => лог('PAGEERROR', e.message));
    page.on('console', m => { if (/error/i.test(m.type())) лог('CONSOLE', m.type(), m.text().slice(0, 300)); });
    await page.addInitScript(ф => {
      /* підставний розпізнавач: на start() за 80 мс віддає одну фінальну фразу, на stop() кличе onend */
      window.SpeechRecognition = window.webkitSpeechRecognition = class {
        start() { this._т = setTimeout(() => { this.onresult && this.onresult({ results: [Object.assign([{ transcript: ф }], { isFinal: true })] }); }, 80); }
        stop() { clearTimeout(this._т); setTimeout(() => this.onend && this.onend(), 0); }
      };
    }, ФРАЗА);
    await page.goto('https://probe.invalid/#model_mova=stub');
    await page.waitForFunction(() => typeof document.getElementById('оц-оцінити').onclick === 'function');
    await page.evaluate(async ([речі, фраза]) => {
      КОЛІР = { шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae', кільце: null, точки: null };
      for (const [і, v] of [['мр-зріст', 167], ['мр-плечі', 96], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 100]]) document.getElementById(і).value = v;
      МІСТ_П.адреса = 'https://model.invalid/v1'; МІСТ_П.токен = 't';
      const jpeg = (ш, в, малювати) => { const к = document.createElement('canvas'); к.width = ш; к.height = в; малювати(к.getContext('2d'), ш, в);
        return к.toDataURL('image/jpeg', 0.92).split(',')[1]; };
      window.__фото = {
        ф1: jpeg(600, 800, (c, w, h) => { c.fillStyle = '#e9e4dc'; c.fillRect(0, 0, w, h); c.fillStyle = '#f4f1ea'; c.fillRect(w * .15, h * .08, w * .7, h * .4); c.fillStyle = '#1d1c1c'; c.fillRect(w * .2, h * .52, w * .6, h * .4); }),
        ф2: jpeg(600, 800, (c, w, h) => { c.fillStyle = '#8c96a0'; c.fillRect(0, 0, w, h); c.fillStyle = '#e6dfd2'; c.fillRect(w * .12, h * .35, w * .3, h * .5); c.fillStyle = '#1d1c1c'; c.fillRect(w * .58, h * .35, w * .3, h * .5); })};
      window.__переклади = [];
      /* перекладач: читає КОНТЕКСТ.items із промпта й будує дії за видом, а не за id (id — її дріт p1-2, не вгадується) */
      /* рядок 6191: промпт перекладачки — JSON шаблону збирача (`task.answer` — вид входу, `items`, `her_words`); рядок 6112:
         перекладачка виходу дає назву речі переліку — і з коду виду для речі, дописаної словами (`add` з `kind`) */
      window.__назви = [];
      const НАЗВИ = { 'white blouse': 'Біла блуза', 'black trousers': 'Чорні штани', 'black ankle boots': 'Чорні черевики',
                      ankle_boots: 'Ботильйони' };
      window.модельМовиП = async function (промпт, вибірка, запис) {
        if (/\nТЕКСТИ:\n/.test(промпт)) {
          const тексти = JSON.parse(промпт.split('\nТЕКСТИ:\n')[1]); window.__назви.push(тексти.map(т => т.текст));
          return JSON.stringify(Object.fromEntries(тексти.map(т => [т.н, НАЗВИ[т.текст] || 'Річ'])));
        }
        let о = {}; try { о = JSON.parse(промпт); } catch (e) {}
        if ((о.task || {}).answer !== 'review_items_fix') return '{}';
        const кт = о, штани = кт.items.find(х => х.item_type === 'trousers');
        window.__переклади.push({ слова: о.her_words, речі: кт.items.map(х => х.id + ':' + х.item_type + ':' + х.color_name), штани: штани && штани.id });
        return JSON.stringify({ actions: [{ op: 'remove', item: штани.id }, { op: 'add', kind: 'ankle_boots', color: 'cream' },
                                          { op: 'add', kind: 'ankle_boots', color: 'black', in_outfit: false }] });
      };
      _дзвінокП = async (повідомлення) => {
        const т = JSON.stringify(повідомлення), речі = /you list the items that make it up/.test(т);
        const текст = речі ? JSON.stringify({ items: window.__РЕЧІ })
          : '{"answer":"Заглушка: образ оцінено.","verdict":"wear_as_is","works":[],"change":[],"unknown":[]}';
        return new Response(JSON.stringify({ content: [{ type: 'text', text: текст }], usage: { input_tokens: 1, output_tokens: 1 } }),
                            { status: 200, headers: { 'content-type': 'application/json', 'x-model': 'stub' } });
      };
      window.__РЕЧІ = речі;
      режим('оцінка');
    }, [РЕЧІ, ФРАЗА]);
    const чекати = (умова, арг) => page.waitForFunction(умова, арг, { timeout: 90000 });
    const рядки = () => page.evaluate(() => [...document.querySelectorAll('#оц-речі .оц-річ')].map(x => x.dataset.ід + ':' + x.querySelector('.оц-слот').textContent
      + ':' + (x.querySelector('.оц-кр').style.background ? 'кр' : '-') + (x.querySelector('.оц-замість') ? ':замість' : '')));
    const знімок = async ім => { const б = page.locator('#оц-речі'); await б.scrollIntoViewIfNeeded(); await page.waitForTimeout(100); await б.screenshot({ path: path.join(тека, ім) }); };
    await page.evaluate(async () => {
      const ф = id => ({ ід: id, тип: 'image/jpeg', дані: __фото[id], ширина: 600, висота: 800 });
      ОЦ.фото = [ф('ф1'), ф('ф2')]; малюватиОцінкуП(); window.__біг = оцінитиОбразП();
    });
    await чекати(() => !document.getElementById('оц-речі').hidden && document.querySelectorAll('#оц-речі .оц-річ').length > 0);
    лог('перелік:', JSON.stringify(await рядки()));

    if (!ДО) {
      /* ═══ А. слова й голос ═══ */
      assert.ok(await page.locator('#оц-слова-поле').isVisible() && await page.locator('#оц-слова-мік').isVisible(), 'нема «Що не так?»');
      const вузолПоля = await page.locator('#оц-слова-поле').elementHandle();
      await знімок('а_1_перелік.png');
      await page.locator('#оц-слова-мік').tap();                                    // дотик 1: мікрофон
      await чекати(() => document.getElementById('оц-слова-поле').value.length > 0);
      const надиктовано = await page.locator('#оц-слова-поле').inputValue(); лог('надиктовано:', надиктовано); assert.strictEqual(надиктовано, ФРАЗА);
      await page.evaluate(() => малюватиПерелікП());                                // перемальовування посеред диктування
      assert.ok(await вузолПоля.evaluate(в => в.isConnected && в.value.length > 0), 'поле з надиктованим відʼєдналось при перемальовуванні');
      await page.locator('#оц-слова-мік').tap();                                    // дотик 2: стоп
      await знімок('а_2_надиктовано.png');
      await page.locator('#оц-слова-слати').tap();                                  // дотик 3: «Виправити»
      /* рядок дописаної речі — у DOM, а не лише в стані: перелік перемальовується після виміру кружечків */
      await чекати(() => [...document.querySelectorAll('#оц-речі .оц-річ')].some(х => х.dataset.ід === 'н2'));
      const р1 = await рядки(); лог('після слів:', JSON.stringify(р1));
      const пер = await page.evaluate(() => window.__переклади); лог('перекладач бачив:', JSON.stringify(пер));
      assert.strictEqual(пер.length, 1); assert.strictEqual(пер[0].слова, ФРАЗА); assert.strictEqual(пер[0].штани, 'p1-2');
      assert.deepStrictEqual(р1.map(х => х.split(':')[0]), ['ф1', 'ф2', 'н1', 'н2']); assert.ok(/замість/.test(р1[3]), 'чорні мусять бути запасними');
      const звіт = await page.evaluate(() => JSON.parse(JSON.stringify(ОЦ.перелік.звіт)));
      лог('звіт: дотиків', звіт.дотиків, 'слова', JSON.stringify(звіт.слова), 'дії', звіт.дії.map(д => д.op + ':' + д.ід + ':' + д.поле).join(' '));
      assert.strictEqual(звіт.слова[0].від_перекладача, 3); assert.strictEqual(звіт.слова[0].спосіб, 'voice'); assert.strictEqual(звіт.дотиків, 3);
      assert.strictEqual(await page.locator('#оц-слова-поле').inputValue(), '', 'поле мусить очиститись після виправлення');
      await знімок('а_3_виправлено.png');
      /* рядок 6112: дописані словами ботильйони (н1, н2) — з назвою, яку мовна модель написала з коду виду */
      await чекати(() => ['н1', 'н2'].every(ід => (ОЦ.перелік.назви || {})[ід]));
      const назви = await page.evaluate(() => [...document.querySelectorAll('#оц-речі .оц-річ')].map(x => x.dataset.ід + ':' + x.querySelector('.оц-назва').textContent));
      лог('назви рядків:', JSON.stringify(назви), '| шар бачив:', JSON.stringify(await page.evaluate(() => window.__назви)));
      assert.ok(назви.includes('н1:Ботильйони') && назви.includes('н2:Ботильйони'), 'дописана річ без назви з коду виду');
      await знімок('а_4_назви_дописаних.png');

      /* ═══ Б. ід не повторюється (5811) ═══ */
      await page.locator('#оц-речі .оц-річ[data-ід="н2"] .оц-х').tap();
      await чекати(() => !ОЦ.перелік.речі.some(р => р.ід === 'н2'));
      await page.locator('#оц-плюс-річ').tap(); await page.locator('#оц-додати .чип', { hasText: /^Верх$/ }).tap();
      await чекати(() => ОЦ.перелік.речі.some(р => р.ід === 'н3'));
      const ід = await page.evaluate(() => ({ речі: ОЦ.перелік.речі.map(р => р.ід), дії: ОЦ.перелік.звіт.дії.map(д => д.ід + ':' + д.op), лічильник: ОЦ.перелік.лічильник }));
      лог('після «✕ н2 + нова»:', JSON.stringify(ід));
      assert.deepStrictEqual(ід.речі, ['ф1', 'ф2', 'н1', 'н3']); assert.strictEqual(new Set(ід.речі).size, ід.речі.length); assert.strictEqual(ід.лічильник, 3);
    } else {
      await page.locator('#оц-плюс-річ').tap(); await page.locator('#оц-додати .чип', { hasText: /^Верх$/ }).tap();
      await чекати(() => ОЦ.перелік.речі.some(р => /^н/.test(р.ід)));
    }

    /* ═══ В. дотик під час перемальовування (5812): шторм `малюватиПерелікП` кожні 4 мс, tap по фото в редакторі дописаної речі ═══ */
    const нова = await page.evaluate(() => ОЦ.перелік.речі.filter(р => /^н/.test(р.ід)).pop().ід);
    if (!(await page.locator('.оц-ред[data-ід="' + нова + '"]').count())) await page.locator('#оц-речі .оц-річ[data-ід="' + нова + '"]').tap();
    await page.waitForSelector('.оц-ред .оц-дотик-фото img[data-фото="ф2"]');
    const фото = await page.locator('.оц-ред .оц-дотик-фото img[data-фото="ф2"]').elementHandle();
    await page.evaluate(() => { window.__шторм = setInterval(() => малюватиПерелікП(), 4); });
    let впало = null;
    try { await page.locator('.оц-ред .оц-дотик-фото img[data-фото="ф2"]').tap({ timeout: 8000 }); } catch (e) { впало = String(e.message).split('\n')[0]; }
    await page.evaluate(() => clearInterval(window.__шторм));
    const живе = await фото.evaluate(в => в.isConnected);
    лог('tap під штормом:', впало ? 'ВПАВ — ' + впало : 'ок', '| вузол фото живий:', живе);
    if (!ДО) {
      assert.strictEqual(впало, null, 'tap впав: ' + впало); assert.ok(живе, 'вузол фото замінено');
      await чекати(() => { const р = ОЦ.перелік.речі.find(р => /^н/.test(р.ід) && р.дотик); return !!р; });
      лог('дотик по фото дописав рамку:', JSON.stringify(await page.evaluate(() => ОЦ.перелік.речі.filter(р => р.дотик).map(р => р.ід + ':' + р.фото))));
    }
    fs.writeFileSync(path.join(тека, 'вивід.txt'), вивід.join('\n') + '\n');
    лог(ДО ? 'ДО (main): готово' : 'OK');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
