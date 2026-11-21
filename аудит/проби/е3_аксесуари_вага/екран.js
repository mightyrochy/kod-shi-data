/* Картка зі справжнім фото каталогу, без моделі; аргумент — тека знімків. */
const fs = require('fs'), path = require('path'), Module = require('module'), zlib = require('zlib');
const корінь = path.resolve(__dirname, '../../..'), джерела = path.join(корінь, 'джерела');
const текаЗнімків = path.resolve(process.argv[2]); process.argv = process.argv.slice(0, 2);
const файл = path.join(джерела, 'тест_показу.js'), код = fs.readFileSync(файл, 'utf8');
const мод = new Module(файл); мод.filename = файл; мод.paths = Module._nodeModulePaths(джерела);
мод._compile(код.slice(0, код.indexOf('(async () => {')) + '\nmodule.exports={сторінка};', файл);
const {JSDOM} = require(path.join(джерела, 'node_modules/jsdom'));
const сирий = zlib.gunzipSync(fs.readFileSync(path.join(корінь, 'каталог_повний.xml.gz'))).toString();
const оф = cat => {
  const уривок = [...сирий.matchAll(/<offer\b[\s\S]*?<\/offer>/g)].find(m => m[0].includes('<categoryId>'+cat+'</categoryId>') && m[0].includes('<picture>'))[0];
  return new JSDOM(уривок, {contentType:'text/xml'}).window.document.querySelector('offer');
};
const річ = (o, слот) => ({id:o.id, назва:o.querySelector('name').textContent, ціна:+o.querySelector('price').textContent,
  слот, фото:o.querySelector('picture').textContent, url:o.querySelector('url').textContent});
const речі = [річ(оф('1'), 'сукня'), річ(оф('10'), 'взуття')];
const {дом, w, d} = мод.exports.сторінка({url:'https://example.test/'});
w.__пакет = {в:'ПОКАЗ-V1', збірка:'проба ваги', каталог:'повний каталог', профіль:'Оля', розклад:'1234',
  прогін:'е3-вага-аксесуари', випадок_рядок:'Робота · офіс', пул:27525,
  картки:[{рука:'1', ітерацій:1, викликів:0, текст:'Сукня та взуття з каталогу. Проба відображення картки.',
    опис:'Робота', підпис:'образ', речі, мітки:[], знахідки:[], питання:[], етапи:{викликів:0, виклики:[]},
    свідомі:[], невиконано:null, різноманітність:null, мова:[], фото_не_ті:[], дібрав_код_слоти:[]}]};
w.eval('П = window.__пакет; рендер();');
for (const e of d.querySelectorAll('.екран')) e.style.display = 'none';
d.getElementById('е-образи').style.display = 'block';
for (const s of d.querySelectorAll('script')) s.remove();
const html = дом.serialize(); w.close();
(async () => {
  const {chromium} = require(path.join(джерела, 'node_modules/playwright'));
  const б = await chromium.launch({executablePath:process.env.CHROMIUM || 'C:/Program Files/Google/Chrome/Application/chrome.exe', headless:true});
  try {
    const с = await б.newPage({viewport:{width:390,height:844}, deviceScaleFactor:1});
    await с.setContent(html, {waitUntil:'networkidle'});
    const фото = await с.locator('#картки img').evaluateAll(xs => xs.map(x => ({src:x.src, завантажено:x.complete && x.naturalWidth>0})));
    if (!фото.some(x => x.завантажено)) throw Error('Фото каталогу не завантажилося');
    await с.locator('#картки').scrollIntoViewIfNeeded();
    const тека = текаЗнімків; fs.mkdirSync(тека, {recursive:true});
    await с.screenshot({path:path.join(тека, '390x844.png')});
    fs.writeFileSync(path.join(тека, 'факти.json'), JSON.stringify({фото, ширина:await с.evaluate(()=>document.documentElement.scrollWidth)}, null, 2));
    console.log('Картка 390×844, фото:', фото.filter(x=>x.завантажено).length);
  } finally {await б.close();}
})().catch(e => {console.error(e); process.exitCode=1});
