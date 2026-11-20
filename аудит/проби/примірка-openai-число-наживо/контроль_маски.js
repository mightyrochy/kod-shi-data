/* Безкоштовний контроль маски «та сама людина» на манекені: сама постать → сама постать, і постать → результат моделі.
   Запуск: STOR=… PYODIDE=… node контроль_маски.js <тека з вона_манекен.jpg і результат.png>. Міст не викликається. */
const fs = require('fs'), path = require('path'); const {chromium} = require('playwright');
const т = path.resolve(process.argv[2]), база = 'https://mightyrochy.github.io';
(async () => {
  const б = await chromium.launch({headless:true, proxy: process.env.HTTPS_PROXY ? {server:process.env.HTTPS_PROXY, bypass:'localhost,127.0.0.1'} : undefined});
  const стор = await (await б.newContext({ignoreHTTPSErrors:true})).newPage(); стор.setDefaultTimeout(0);
  await стор.route(u => u.origin === база, async r => { const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/kod-shi-data\//,'').replace(/^\//,'')||'index.html'; const ф=path.join(process.env.STOR,ім); await r.fulfill({status:fs.existsSync(ф)?200:404, contentType:'text/html; charset=utf-8', body:fs.existsSync(ф)?fs.readFileSync(ф):'нема'}); });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async r => { const ім=new URL(r.request().url()).pathname.split('/').pop(), ф=path.join(process.env.PYODIDE,ім); await r.fulfill({status:fs.existsSync(ф)?200:404, contentType: ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream', body:fs.existsSync(ф)?fs.readFileSync(ф):''}); });
  await стор.route(u => u.origin !== база && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), async r => { try { await r.fulfill({response: await r.fetch({timeout:60000})}); } catch(_) { await r.abort().catch(()=>{}); } });
  await стор.goto(база + '/kod-shi-data/index.html', {waitUntil:'load', timeout:180000}); await стор.waitForTimeout(6000);
  const р = await стор.evaluate(async ({в, р}) => {
    const її = {тип:'image/jpeg', дані:в, ширина:614, висота:1024}; const вих = {};
    вих.сама_на_себе = JSON.parse(JSON.stringify((await повернутиЛюдинуП(підготуватиПоверненняП(її), {media_type:'image/jpeg', data:в}, false)).звіт));
    вих.на_результат = JSON.parse(JSON.stringify((await повернутиЛюдинуП(підготуватиПоверненняП(її), {media_type:'image/png', data:р}, false)).звіт));
    return вих; }, {в: fs.readFileSync(path.join(т,'вона_манекен.jpg')).toString('base64'), р: fs.readFileSync(path.join(т,'результат.png')).toString('base64')});
  fs.writeFileSync(path.join(т,'контроль_маски.json'), JSON.stringify(р,null,1)); console.log(JSON.stringify(р));
  await б.close();
})().catch(e => { console.error(e); process.exit(1); });
