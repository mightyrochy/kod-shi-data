const fs = require('fs');
const path = require('path');
const {chromium} = require('playwright');
const source = path.resolve(process.argv[2], 'джерела');
const out = path.resolve(process.argv[3]);
const helper = require(path.join(source, 'показ_шаблон.js'));
let html = helper.підставитиШаблон(path.join(source, 'показ.html'), {
  __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'ba4e63e2', __ВІДБИТОК__: 'стенд',
  __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: helper.прочитатиДовідникJSON(source),
});
(async () => {
  const browser = await chromium.launch({headless:true,args:['--disable-gpu']});
  try {
    const page = await browser.newPage({viewport:{width:390,height:844}});
    const errors=[];
    page.on('pageerror', e=>errors.push(String(e)));
    await page.route('**/*', route => route.request().isNavigationRequest()
      ? route.fulfill({contentType:'text/html; charset=utf-8',body:html})
      : route.fulfill({contentType:'application/javascript',body:'window.loadPyodide=null;'}));
    await page.goto('http://review.local/');
    await page.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
    await page.evaluate(async () => {
      режим('старт'); екран(0);
      МІСТ_П.адреса='http://review.local'; МІСТ_П.токен='стенд';
      await писатиКв(ключФото('портрет'),new Blob(['портрет'],{type:'image/jpeg'}));
      блобВБазу=async()=>({тип:'image/jpeg',дані:'AAAA',ширина:1568,висота:1176,якість:0.85});
      window.__викликів=0;
      модельП=async()=>{window.__викликів++;return '{"photo":"usable","skin":["#f2d6c4"],"hair":["#4a4644"],"eyes":"#6b8cae"}';};
      містП=async()=>{throw new Error('контрольний збій моста');};
      await зчитатиКольориЗПортрета();
    });
    const save=async name=>{
      await page.locator('#кол-стан').scrollIntoViewIfNeeded();
      await page.screenshot({path:path.join(out,name+'.png')});
    };
    await save('01-збій');
    const recover=async()=>page.evaluate(()=>{
      містП=async()=>({стан:'готово',шкіра:['#f2d6c4'],волосся:['#4a4644'],очі:'#6b8cae',кільце:null,освітлення:null});
    });
    await recover();
    await page.locator('#кол-повтор').click();
    await page.waitForFunction(()=>document.getElementById('кол-стан').textContent.includes('Прочитано'));
    await save('02-повтор');
    await page.evaluate(async()=>{
      містП=async()=>{throw new Error('контрольний збій моста');};
      await зчитатиКольориЗПортрета();
      await створитиПрофіль();
    });
    await save('03-інший-профіль-до');
    await recover();
    await page.locator('#кол-повтор').click();
    await page.waitForFunction(()=>document.getElementById('кол-повтор').hidden);
    await save('04-інший-профіль-після');
    console.log(JSON.stringify(await page.evaluate(async()=>({
      шкіра:КОЛІР.шкіра,записанаШкіра:(await читатиКв('профіль:'+АКТИВНИЙ)).колір.шкіра,
      викликів:window.__викликів,портрет:!!(await читатиКв(ключФото('портрет'))),
      поле:document.getElementById('кол-відповідь').value,
    })),null,2));
    console.log('Помилки сторінки:',JSON.stringify(errors));
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
