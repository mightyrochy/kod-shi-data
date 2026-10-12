const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('playwright');
(async () => {
  const browser = await chromium.launch({executablePath:'/usr/bin/chromium', headless:true, args:['--no-sandbox']});
  const output = {sha:'6f7f3ffdb5e48573cd68f1f31015247b9f28a7f8', base:'286b310328eb3f981e403ae9b4ddcabd667b2f97', browser:await browser.version(),viewport:{width:390,height:844},runs:{}};
  try {
    for (const phase of ['before','after']) {
      const context = await browser.newContext({viewport:output.viewport,hasTouch:true,isMobile:true,deviceScaleFactor:1,reducedMotion:'reduce'});
      const page = await context.newPage(); page.setDefaultTimeout(180000);
      const record = {errors:[],blocked:[],modelRequests:0,states:{}};
      page.on('pageerror', e => record.errors.push(String(e)));
      await page.route('**/*', async route => {
        const url = new URL(route.request().url());
        if (/anthropic|openai|1234|\/v1\/(chat|responses)/.test(url.href)) record.modelRequests++;
        if (url.hostname === 'review975.test') return route.fulfill({path:`/tmp/review975/${phase}/index.html`,contentType:'text/html'});
        if (url.pathname.includes('/pyodide/')) {
          const file = path.join('/tmp/974-pyodide',path.basename(url.pathname));
          if (fs.existsSync(file)) return route.fulfill({path:file,contentType:file.endsWith('.js')?'application/javascript':file.endsWith('.wasm')?'application/wasm':'application/octet-stream'});
        }
        record.blocked.push(url.href); return route.abort();
      });
      await page.goto('http://review975.test/index.html');
      await page.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
      await page.locator('[id="пр-імʼя"]').fill('Перевірка 5203');
      await page.locator('#пр-згода').check();
      for(let i=0;i<3;i++) await page.locator('#н-далі').tap();
      await page.waitForFunction(() => РЕЖИМ === 'сценарій');
      await page.evaluate(() => режим('палітра'));
      await page.locator('#пал-кольори').waitFor({state:'visible'});
      record.empty = await page.evaluate(() => ({text:document.getElementById('пал-стан').textContent,button:document.getElementById('пал-кольори').textContent,mode:РЕЖИМ,colors:КОЛІР}));
      if(phase==='after') {
        assert.strictEqual(record.empty.text,'Кольорів шкіри, волосся й очей у профілі ще нема — від них рахується палітра.');
        assert.strictEqual(record.empty.button,'Додати кольори в профілі');
      }
      await page.screenshot({path:`/tmp/review975/${phase}/empty.png`,animations:'disabled'});
      await page.locator('#пал-кольори').tap();
      await page.locator('#аркуш').waitFor({state:'visible'});
      record.tap = await page.evaluate(() => ({mode:РЕЖИМ,sheet:document.getElementById('аркуш').innerText}));
      assert.strictEqual(record.tap.mode,'профіль'); assert(record.tap.sheet.includes('Твої кольори'));
      await page.screenshot({path:`/tmp/review975/${phase}/tap.png`,animations:'disabled'});
      await page.locator('#аркуш-готово').tap();
      for (const mask of [1,2,3,4,5,6,7]) {
        await page.evaluate(async m => {
          КОЛІР = {шкіра:m&1?'#f0d5c8':null,волосся:m&2?'#4a4644':null,очі:m&4?'#6b8cae':null,кільце:null,точки:null};
          document.getElementById('мр-зріст').value=167;
          for(const [id,key] of ПОЛЯ_ОБХВАТІВ) { const value={плечі:96,груди:92,талія:74,стегна:100}[key]; if(value) document.getElementById(id).value=value; }
          режим('палітра'); await оновитиПалітруП();
        },mask);
        record.states[mask] = await page.evaluate(() => ({text:document.getElementById('пал-стан').textContent,intro:document.getElementById('пал-вступ').hidden,choice:document.getElementById('пал-вибір').hidden,empty:document.getElementById('пал-порожньо').hidden,html:document.getElementById('пал-вибір').innerHTML,palette:ПАЛІТРА,colors:КОЛІР}));
      }
      assert(record.states[7].palette, 'Повний профіль мусить дати розраховану палітру');
      assert(!record.states[7].text.includes('не порахувалась'), record.states[7].text);
      output.runs[phase] = record; await context.close();
    }
    assert.deepStrictEqual(output.runs.after.states,output.runs.before.states);
    for (const record of Object.values(output.runs)) {assert.strictEqual(record.modelRequests,0); assert.deepStrictEqual(record.errors,[]);}
    output.equalOtherStates = true;
  } finally {fs.writeFileSync('/tmp/review975/facts.json',JSON.stringify(output,null,2));await browser.close();}
  console.log(JSON.stringify({sha:output.sha,browser:output.browser,viewport:output.viewport,equalOtherStates:output.equalOtherStates,states:Object.keys(output.runs.after.states),after:output.runs.after.empty,tap:output.runs.after.tap,errors:output.runs.after.errors,modelRequests:output.runs.after.modelRequests}));
})().catch(e => {console.error(e);process.exitCode=1;});
