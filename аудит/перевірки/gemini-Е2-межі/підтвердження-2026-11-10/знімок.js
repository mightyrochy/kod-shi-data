/* Показ фактичної прийнятої репліки та картки; мережевих викликів немає. */
const fs = require('fs'), path = require('path'), Module = require('module');
const root = path.resolve(__dirname, '../../../..'), source = path.join(root, 'джерела');
const file = path.join(source, 'тест_показу.js'), code = fs.readFileSync(file, 'utf8');
const mod = new Module(file); mod.filename = file; mod.paths = Module._nodeModulePaths(source);
mod._compile(code.slice(0, code.indexOf('(async () => {')) + '\nmodule.exports={сторінка};', file);
const {дом, w, d} = mod.exports.сторінка({url:'https://example.test/'});
const passport = JSON.parse(fs.readFileSync(path.join(__dirname, '../складені-2026-11-05/приклад.json'), 'utf8'));
const lines = fs.readFileSync(path.join(__dirname, 'підтвердження-після.txt'), 'utf8').split(/\r?\n/);
const reply = JSON.parse(lines.find(line => line.startsWith('{'))).прийнято;
w.eval('ПРОФІЛЬ_СТВОРЕНО=true; режим("сценарій"); застосуватиПаспортДоЕкрана(' + JSON.stringify(passport)
  + '); ПАСПОРТ_П=' + JSON.stringify(passport) + '; ВИПАДОК_ЗМІНЕНО_П=false; малюватиКарткуСценарію();'
  + 'ЧАТ_П=[{хто:"людина",текст:"не хочу виділятись",тема:"сценарій"},{хто:"ші",текст:'
  + JSON.stringify(reply) + ',тема:"сценарій"}]; малюватиЧатП();');
for (const screen of d.querySelectorAll('.екран')) screen.style.display = 'none';
d.getElementById('е-випадок').style.display = 'block';
for (const script of d.querySelectorAll('script')) script.remove();
const html = дом.serialize(); w.close();
(async () => {
  const {chromium} = require(path.join(source, 'node_modules/playwright'));
  const browser = await chromium.launch({headless:true, executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
    await page.route('**/*', route => route.abort());
    await page.setContent(html);
    await page.locator('#зн-місце').scrollIntoViewIfNeeded();
    await page.screenshot({path:path.join(__dirname, '390x844.png'),animations:'disabled'});
    console.log(JSON.stringify({ширина:await page.evaluate(()=>document.documentElement.scrollWidth),viewport:390,
      репліка:reply, текст:await page.locator('#е-випадок').innerText()}));
  } finally { await browser.close(); }
})().catch(error => { console.error(error);process.exitCode=1; });
