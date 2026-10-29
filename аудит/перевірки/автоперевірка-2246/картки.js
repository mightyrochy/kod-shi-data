/* Керовані офлайн-відповіді, справжній шаблон голови та Chromium 390×844. */
const fs = require('fs'), path = require('path');
const root = path.resolve(process.argv[2]), out = path.resolve(process.argv[3]);
const code = path.join(root, 'джерела');
const {chromium} = require(path.join(code, 'node_modules/playwright'));
const {зібратиШаблонПоказу, підставитиШаблон, прочитатиДовідникJSON} = require(path.join(code, 'показ_шаблон.js'));
const data = JSON.parse(fs.readFileSync(path.join(out, 'межі.json'), 'utf8'));
async function main() {
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(code, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: '1be2220cf', __ВІДБИТОК__: 'офлайн-2246',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'офлайн',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(code)
  });
  const browser = await chromium.launch({headless: true, args: ['--disable-gpu']});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.route('**/*', route => {
      const req = route.request();
      if (req.url() === 'http://offline.local/') return route.fulfill({contentType: 'text/html', body: html});
      if (req.resourceType() === 'image') return route.continue();
      return route.abort();
    });
    await page.goto('http://offline.local/');
    await page.waitForFunction(() => !!document.getElementById('вк-сценарій').onclick);
    const facts = [];
    for (const mode of ['до-шаблону', 'після-шаблону', 'без-абзаців']) {
      const fact = await page.evaluate(({data, mode}) => {
        ЗБ = {діагноз: []};
        const raw = {опис: JSON.parse(JSON.stringify(data.розбір))};
        if (mode === 'без-абзаців') raw.опис.про_речі = [];
        const result = mode === 'до-шаблону' ? raw : шаблонОписуП(raw, 1, 'незалежна-проба');
        П = {картки: [{рука: 1, речі: data.речі, опис: result.опис.текст,
          про_речі: result.опис.про_речі, як_носити: result.опис.як_носити,
          без_опису: result.опис.текст ? '' : 'Пояснення цього образу не надійшло.'}], відповіді: [{}]};
        const cards = document.getElementById('картки');
        cards.replaceChildren(рендерКартку(0));
        режим('образи');
        return {режим: mode, опис: result.опис.текст, порад: result.опис.як_носити.length,
          абзаців: result.опис.про_речі.length, діагноз: ЗБ.діагноз.filter(x => x.includes('description_template'))};
      }, {data, mode});
      await page.locator('#к-0 img').evaluateAll(async imgs => {
        await Promise.all(imgs.map(img => img.complete ? Promise.resolve() : new Promise(resolve => {
          img.addEventListener('load', resolve, {once: true});
          img.addEventListener('error', resolve, {once: true});
        })));
      });
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({path: path.join(out, mode + '-фото.png'), animations: 'disabled'});
      await page.locator('#к-0 .к-текст').evaluate(el => el.scrollIntoView({block: 'start'}));
      await page.screenshot({path: path.join(out, mode + '-текст.png'), animations: 'disabled'});
      fact.фото = await page.locator('#к-0 img').evaluateAll(xs => xs.map(x => ({src: x.currentSrc, завантажено: x.naturalWidth > 0})));
      facts.push(fact);
    }
    if (errors.length) throw new Error(errors.join('\n'));
    if (facts[1].опис.includes('сумку') || facts[1].порад || facts[1].абзаців !== 2 || facts[2].опис) throw new Error('Шаблон не втримав межу');
    fs.writeFileSync(path.join(out, 'картки.json'), JSON.stringify(facts, null, 2));
    console.log('Chromium 390×844: 3 стани, 6 знімків; шаблон лишив 2 абзаци, порад 0; без абзаців — без опису.');
    console.log(JSON.stringify(facts.map(x => ({режим: x.режим, фото: x.фото})), null, 2));
  } finally { await browser.close(); }
}
main().catch(e => {console.error(e); process.exitCode = 1;});
