/* Дим показу з поточних джерел: каталог і фото локальні, викликів моделей немає. */
process.env.FOTO = '1';
const fs = require('fs'), path = require('path'), Module = require('module');
const root = path.resolve(__dirname, '../../../..'), source = path.join(root, 'джерела');
const file = path.join(source, 'тест_показу.js'), code = fs.readFileSync(file, 'utf8');
const mod = new Module(file); mod.filename = file; mod.paths = Module._nodeModulePaths(source);
mod._compile(code.slice(0, code.indexOf('(async () => {')) + '\nmodule.exports={сторінка};', file);
const {дом, w, d} = mod.exports.сторінка({url:'https://example.test/'});
const речі = JSON.parse(fs.readFileSync(path.join(__dirname, 'каталог-знімок.json'), 'utf8'));
for (const річ of речі) річ.фото = річ.фото.map(ф => 'data:image/jpeg;base64,' + fs.readFileSync(path.join(source, ф)).toString('base64'));
w.__речі = речі;
w.eval(`П = {картки: [{рука: '1', текст: 'Локальна проба показу', опис: 'Локальна проба показу', речі: window.__речі,
  мітки: [], знахідки: [], питання: [], етапи: {}, свідомі: [], фото_не_ті: [], дібрав_код_слоти: []}]};
  document.getElementById('картки').appendChild(рендерКартку(0));`);
for (const screen of d.querySelectorAll('.екран')) screen.style.display = 'none';
d.getElementById('картки').closest('.екран').style.display = 'block';
for (const script of d.querySelectorAll('script')) script.remove();
const html = дом.serialize(); w.close();
(async () => {
  const {chromium} = require(path.join(source, 'node_modules/playwright'));
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
    await page.route('**/*', route => route.abort());
    await page.setContent(html);
    await page.locator('#к-0').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(__dirname, '390x844.png'),animations:'disabled'});
    console.log(JSON.stringify({ширина:await page.evaluate(()=>document.documentElement.scrollWidth),viewport:390,FOTO:process.env.FOTO,
      текст:await page.locator('#к-0').innerText()}));
  } finally { await browser.close(); }
})().catch(error => { console.error(error);process.exitCode=1; });
