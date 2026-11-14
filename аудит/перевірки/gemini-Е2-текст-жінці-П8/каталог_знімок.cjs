const fs = require('fs'), path = require('path'), cp = require('child_process');
const корінь = process.cwd(), до = process.argv[2] === 'до';
const теки = path.join(корінь, 'аудит', 'перевірки', 'gemini-Е2-текст-жінці-П8');
const підготовка = require(path.join(корінь, 'джерела', 'показ_шаблон.js'));
let html = підготовка.зібратиШаблонПоказу(path.join(корінь, 'джерела', 'показ.html'));
if (до) for (const ім of ['картки.js', 'мовний_шар.js']) {
  const тепер = fs.readFileSync(path.join(корінь, 'джерела', 'показ', ім), 'utf8');
  const раніше = cp.execFileSync('git', ['show', '095fe349fee07bb113af22103a6c26be947848e8:джерела/показ/' + ім], {encoding: 'utf8', maxBuffer: 500000});
  if (!html.includes(тепер)) throw Error('Не знайдено модуля ' + ім);
  html = html.replace(тепер, () => раніше);
}
html = підготовка.підставитиШаблон(html, {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'проба П8',
  __ВІДБИТОК__: 'проба', __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '',
  __ДОВІДНИК_ПОКАЗУ__: підготовка.прочитатиДовідникJSON(path.join(корінь, 'джерела'))})
  .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
const звіт = JSON.parse(fs.readFileSync(path.join(корінь, 'аудит', 'проби', 'Е1-нічний-живий-20261107', 'ж5_співбесіда_без', 'вердикти.txt'), 'utf8'));
const запис = звіт.прогони[0].вердикти.find(в => в.рука === '1' || в.рука === 1);
const картка = {...запис, рука: '1', речі: запис.речі_образу, мітки: [], знахідки: [], питання: [], етапи: {},
  свідомі: [], фото_не_ті: [], дібрав_код_слоти: []};
const сервер = require('http').createServer((з, в) => {в.setHeader('Content-Type', 'text/html; charset=utf-8'); в.end(html);});
(async () => {
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  const браузер = await require(path.join(корінь, 'джерела', 'node_modules', 'playwright')).chromium.launch({headless: true});
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}});
    await сторінка.route('**/*', р => р.request().url().startsWith('http://127.0.0.1:') ||
      (process.env.FOTO === '1' && р.request().resourceType() === 'image') ? р.continue() : р.abort());
    await сторінка.goto('http://127.0.0.1:' + сервер.address().port + '/#модель_мови=нема');
    await сторінка.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
    await сторінка.evaluate(к => {window.__к = к; eval('П = {картки: [window.__к]}; рендер();');}, картка);
    await сторінка.evaluate(async () => {
      await Promise.all([...document.querySelectorAll('#картки img')].map(і => і.complete ? null : new Promise(р => {
        і.addEventListener('load', р, {once: true}); і.addEventListener('error', р, {once: true}); setTimeout(р, 12000);
      })));
      window.scrollTo(0, document.querySelector('#картки .картка').getBoundingClientRect().top + scrollY);
    });
    const стан = await сторінка.evaluate(() => ({фото: [...document.querySelectorAll('#картки img')].map(і => ({адреса: і.src, ширина: і.naturalWidth})),
      переповнення: document.documentElement.scrollWidth > innerWidth, текст: document.querySelector('#картки .картка').textContent}));
    const етап = до ? 'до' : 'після';
    fs.writeFileSync(path.join(теки, етап + '-каталог.json'), JSON.stringify(стан, null, 2));
    await сторінка.screenshot({path: path.join(теки, етап + '-каталог-390x844.png')});
    console.log(JSON.stringify({...стан, текст: undefined}));
  } finally {await браузер.close(); сервер.close();}
})().catch(е => {console.error(е); сервер.close(); process.exitCode = 1;});
