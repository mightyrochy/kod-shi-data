// Мобільний дим показу голови на даних справжнього Python-моста, без виклику моделі.
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const [html, dataFile, out] = process.argv.slice(2);
(async () => {
  const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
    const errors=[]; page.on('pageerror',e=>errors.push(String(e)));
    await page.route('**/*',route=>route.request().url()==='http://127.0.0.1:8765/'
      ? route.fulfill({contentType:'text/html; charset=utf-8',body:fs.readFileSync(html)}) : route.abort());
    await page.goto('http://127.0.0.1:8765/');
    await page.waitForFunction(()=>typeof (document.getElementById('сцн-новий')||{}).onclick==='function');
    await page.evaluate(async d=>{
      КОЛІР.шкіра=d.вхід.шкіра[0]; КОЛІР.волосся=d.вхід.волосся[0]; КОЛІР.очі=d.вхід.очі;
      КОЛІР.точки={шкіра:d.вхід.шкіра,волосся:d.вхід.волосся};
      $('мр-зріст').value=d.вхід.зріст;
      ПАСПОРТ_П=null; закріпитиПоказануП(d.вибір);
      містП=async name=> name==='палітри' ? d.палітра : {повідомлення:{}};
      поколінняМістуП=()=>1; чиннеМістуП=()=>true;
      режим('палітра'); await оновитиПалітруП();
    },data);
    await page.locator('#пал-основа .чип').first().waitFor();
    await page.screenshot({path:path.join(out,'палітра-390x844.png'),animations:'disabled'});
    await page.locator('#пал-вибір').screenshot({path:path.join(out,'палітра-повна.png'),animations:'disabled'});
    const body=await page.locator('body').innerText();
    fs.writeFileSync(path.join(out,'огляд.json'),JSON.stringify({viewport:{width:390,height:844},errors,body},null,2));
    console.log(JSON.stringify({errors,baseChips:await page.locator('#пал-основа .чип').count()}));
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exit(1)});
