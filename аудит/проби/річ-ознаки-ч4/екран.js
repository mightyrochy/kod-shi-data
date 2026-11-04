/* Офлайн-шаблон 390×844 із фактичною відповіддю ендпойнта помади; модель і мережа відсутні. */
const fs = require('fs'), path = require('path'), cp = require('child_process');
const корінь = path.resolve(__dirname, '../../..'), дж = path.join(корінь, 'джерела');
const { chromium } = require(path.join(дж, 'node_modules/playwright'));
const ш = require(path.join(дж, 'показ_шаблон.js'));
const пітон = код => cp.execFileSync('python', ['-W', 'ignore', '-X', 'utf8', '-c', код],
  { cwd: дж, encoding: 'utf8' }).trim();

async function main() {
  const дані = JSON.parse(пітон("import json, pathlib, міст_основи as м; ж=json.loads(pathlib.Path('../аудит/проби/жінки/ж4.json').read_text('utf-8')); print(м.помади(dict(шкіра=ж['skin'], волосся=ж['hair'], очі=ж['eyes'])))"));
  fs.writeFileSync(path.join(__dirname, 'помади.json'), JSON.stringify(дані, null, 2));
  const html = ш.підставитиШаблон(path.join(дж, 'показ.html'), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'офлайн-огляд', __ВІДБИТОК__: 'ч4',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'офлайн-шаблон',
    __ДОВІДНИК_ПОКАЗУ__: ш.прочитатиДовідникJSON(дж)
  }).replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/,
    '<script>window.loadPyodide=null;</script>');
  const br = await chromium.launch({ headless: true, executablePath: 'C:/Program Files/Google/Chrome/Application/chrome.exe' });
  try {
    const page = await br.newPage({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 1 });
    const помилки = [];
    page.on('pageerror', e => помилки.push(String(e)));
    await page.route('**/*', route => route.request().url() === 'http://review.test/'
      ? route.fulfill({ contentType: 'text/html', body: html }) : route.abort());
    await page.goto('http://review.test/');
    await page.waitForFunction(() => typeof (document.getElementById('сцн-новий') || {}).onclick === 'function');
    await page.evaluate(р => {
      режим('сценарій');
      document.getElementById('сц-макіяж').value = 'помітний';
      перемкнутиРедактор('ред-макіяж');
      ПОМАДИ_П = р;
      малюватиСходинкуПомадП();
    }, дані);
    await page.screenshot({ path: path.join(__dirname, 'помада-390x844.png'), animations: 'disabled' });
    const факт = await page.evaluate(() => ({ текст: document.getElementById('сц-губи-стан').textContent,
      відтінків: document.querySelectorAll('#сц-губи-ряд [role="button"]').length,
      переповнення: document.documentElement.scrollWidth > innerWidth }));
    fs.writeFileSync(path.join(__dirname, 'екран.json'), JSON.stringify({ ...факт, помилки }, null, 2));
    console.log(JSON.stringify({ ...факт, помилки }));
    if (помилки.length || факт.відтінків !== 20 || факт.переповнення) process.exitCode = 1;
  } finally { await br.close(); }
}
main().catch(e => { console.error(e); process.exitCode = 1; });
