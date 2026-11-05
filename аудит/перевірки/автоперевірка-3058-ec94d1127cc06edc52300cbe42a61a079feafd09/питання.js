/* Відтворення зауваження Codex: node питання.js <дерево PR> <тека знімка>. */
const fs = require('fs'), path = require('path'), assert = require('node:assert/strict');
const root = path.resolve(process.argv[2]), src = path.join(root, 'джерела');
const out = path.resolve(process.argv[3]);
const {chromium} = require(path.join(src, 'node_modules/playwright'));
const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(src, 'показ_шаблон'));
const html = підставитиШаблон(fs.readFileSync(path.join(src, 'показ.html'), 'utf8'), {
  __МОДУЛІ_ПОКАЗУ__:'', __ЗБІРКА_ПОКАЗУ__:'перевірка-3058', __ВІДБИТОК__:'перевірка-3058',
  __ФІД_ПОКАЗУ__:'', __КАТАЛОГ_ПОКАЗУ__:'', __ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(src),
  __ПРОМПТ_КОЛІР_ПОКАЗУ__:'', __ВИБІРКА_ПОКАЗУ__:'{}'
});
(async () => {
  const browser = await chromium.launch({headless:true, args:['--disable-gpu']});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844}});
    page.on('pageerror', e => console.error(String(e)));
    await page.route('**/*', route => route.request().url() === 'https://example.test/'
      ? route.fulfill({contentType:'text/html; charset=utf-8',body:html}) : route.abort());
    await page.goto('https://example.test/');
    await page.waitForFunction(() => !!document.getElementById('сц-новий').onclick);
    const result = await page.evaluate(async () => {
      режим('бібліотека');
      const container = $('біб-список');
      container.innerHTML = '<details open><summary>Питання про образ · 2</summary><div class="задум"><div id="питання-збережене">Чи зручно тобі в цьому взутті?</div></div></details>';
      const details = container.firstElementChild, old = $('питання-збережене');
      const card = {рука:'1', питання_жінці:['Чи зручно тобі в цьому взутті?']};
      чекаютьРозгортанняП = () => 1;
      питаннямиП = async () => {throw new Error('наведений збій доповнення');};
      await дописатиРозгорнутіП(card, details);
      const once = old.isConnected && details.querySelectorAll('.задум-збій').length === 1;
      await дописатиРозгорнутіП(card, details);
      return {збережено_той_самий_вузол:once && old.isConnected,
        збоїв:details.querySelectorAll('.задум-збій').length,
        текст:details.textContent, зайнято:ПИШУТЬСЯ_РОЗГОРНУТІ_П.has(card)};
    });
    assert(result.збережено_той_самий_вузол);
    assert.equal(result.збоїв,1); assert.equal(result.зайнято,false);
    fs.mkdirSync(out,{recursive:true});
    await page.screenshot({path:path.join(out,'питання-після-збою.png'),animations:'disabled'});
    console.log(JSON.stringify(result));
  } finally {await browser.close();}
})().catch(e => {console.error(e);process.exitCode=1;});
