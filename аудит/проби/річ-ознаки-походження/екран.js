const fs = require('fs'), path = require('path');
const root = process.cwd(), src = path.join(root, 'джерела');
const {chromium} = require(path.join(src, 'node_modules/playwright'));
const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(src, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(fs.readFileSync(path.join(src, 'показ.html'), 'utf8'), {
    __МОДУЛІ_ПОКАЗУ__: '', __ЗБІРКА_ПОКАЗУ__: 'походження', __ВІДБИТОК__: 'походження',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(src)
  });
  const browser = await chromium.launch({headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.route('**/*', route => route.abort());
    await page.setContent(html, {waitUntil: 'domcontentloaded'});
    console.log(await page.evaluate(() => {
      КОЛІР = {шкіра: '#deb295', волосся: '#523321', очі: '#735632', кільце: '#111111'};
      малюватиСвотчі();
      const swatches = document.getElementById('кол-свотчі');
      const screen = swatches.closest('.екран') || swatches.parentElement;
      document.querySelectorAll('.екран').forEach(el => { el.style.display = 'none'; });
      let node = screen;
      while (node && node !== document.body) { node.hidden = false; node.style.display = 'block'; node = node.parentElement; }
      swatches.scrollIntoView({block: 'center'});
      return {екран: screen.id, свотчів: swatches.querySelectorAll('.св').length};
    }));
    await page.screenshot({path: path.join(process.env.TEMP, 'портрет-390.png'), animations: 'disabled'});
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
