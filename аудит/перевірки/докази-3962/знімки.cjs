// Картки реальних речей на зібраній голові #3962. Фікстура показу, без мовної моделі.
const fs = require('fs'), path = require('path'), {createRequire} = require('module');
const дерево = path.resolve(process.argv[2]), вихід = path.resolve(process.argv[3]);
const {chromium} = createRequire(path.join(дерево, 'джерела/package.json'))('playwright');
const прочитати = ім => JSON.parse(fs.readFileSync(path.join(вихід, ім), 'utf8').replace(/^\uFEFF/, ''));
(async () => {
  const браузер = await chromium.launch({headless: true, args: ['--disable-gpu']});
  const записи = [], кеш = new Map(), мережа = [];
  if (fs.existsSync(path.join(вихід, 'знімки.json'))) {
    for (const р of прочитати('знімки.json').мережа || []) {
      if (р.код === 403) { кеш.set(р.url, {status: 403, body: ''}); мережа.push({...р, з_кеша: true}); }
    }
  }
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    const помилки = [];
    сторінка.on('pageerror', e => помилки.push(e.message));
    await сторінка.route('**/*', async запит => {
      const url = запит.request().url();
      if (url.startsWith('http://127.0.0.1:8765/')) {
        if (new URL(url).pathname === '/build.txt')
          return запит.fulfill({contentType: 'text/plain', body: '3228666ac70c8fdf897aaa2129d5d9e648c7930e'});
        return запит.fulfill({contentType: 'text/html; charset=utf-8', body: fs.readFileSync(path.join(дерево, 'index.html'))});
      }
      if (запит.request().method() !== 'GET' || !['image', 'font', 'stylesheet'].includes(запит.request().resourceType()))
        return запит.abort();
      try {
        if (!кеш.has(url)) {
          const р = await запит.fetch({timeout: 12000});
          кеш.set(url, {status: р.status(), headers: р.headers(), body: await р.body()});
          мережа.push({url, код: р.status()});
        }
        await запит.fulfill(кеш.get(url));
      } catch (е) { мережа.push({url, помилка: е.message}); await запит.abort(); }
    });
    await сторінка.goto('http://127.0.0.1:8765/', {waitUntil: 'domcontentloaded'});
    await сторінка.waitForFunction(() => typeof Екран !== 'undefined' && Екран.стан.запущено === true);
    await сторінка.evaluate(() => document.fonts.ready);
    for (const стан of ['до', 'після']) {
      for (const [номер, зразок] of прочитати('зразки-' + стан + '.json').entries()) {
        const картка = {рука: '1', ітерацій: 1, викликів: 0, текст: '', опис: '', підпис: '',
          речі: зразок.речі.map(р => ({...р, урл: р.url,
            фото: Array.isArray(р.фото) ? р.фото[0] : р.фото,
            фото_усі: Array.isArray(р.фото) ? р.фото : (р.фото_усі || [])})),
          знахідки: зразок.review, мітки: [], питання: [], свідомі: [],
          етапи: {викликів: 0, виклики: []}, мова: [], мова_спроб: 0, мова_видано: 'так',
          фото_не_ті: [], дібрав_код_слоти: []};
        const пакет = {в: 'ПОКАЗ-V1', збірка: '3228666ac70c8fdf897aaa2129d5d9e648c7930e',
          каталог: 'Повний каталог', профіль: '', розклад: '1', прогін: 'огляд-3962-' + стан + номер,
          випадок_рядок: '', пул: 27525, картки: [картка]};
        await сторінка.evaluate(п => { П = п; рендер(); }, пакет);
        await сторінка.waitForFunction(() => document.querySelectorAll('#к-0 .список .річ').length === 4);
        await сторінка.waitForFunction(() => [...document.querySelectorAll('#к-0 img')].every(x => x.complete && x.naturalWidth > 0));
        const файл = стан + '-' + зразок.фокус[0] + '-390x844.png';
        await сторінка.screenshot({path: path.join(вихід, файл), animations: 'disabled'});
        const відомості = await сторінка.evaluate(ід => ({
          фото: [...document.querySelectorAll('#к-0 img')].map(x => ({адреса: x.currentSrc || x.src, ширина: x.naturalWidth})),
          фото_акценту: document.querySelector('#к-0 [data-id="' + ід + '"] img')?.naturalWidth || 0,
          текст: document.querySelector('#к-0').innerText,
          ширина: document.documentElement.scrollWidth
        }), зразок.акцент);
        записи.push({стан, акцент: зразок.акцент, файл, ...відомості});
      }
    }
    fs.writeFileSync(path.join(вихід, 'знімки.json'), JSON.stringify({записи, помилки, мережа}, null, 2));
    console.log(JSON.stringify({знімків: записи.length, помилки,
      фото: записи.map(x => ({стан: x.стан, акцент: x.акцент, кадрів: x.фото.length, битих: x.фото.filter(ф => !ф.ширина).length})),
      помилки_мережі: мережа.filter(x => x.помилка || x.код !== 200).slice(0, 3)}));
    if (записи.some(x => !x.фото_акценту || x.фото.some(ф => !ф.ширина))) process.exitCode = 1;
  } finally { await браузер.close(); }
})().catch(e => {console.error(e.stack); process.exitCode = 1;});
