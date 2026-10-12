const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const html=process.argv[2],dir=process.argv[3],strict=process.argv[4]==='strict';
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
 const facts={браузер:await browser.version(),розмір:'390×844',перевірки:[],закриття:[],помилки:[],модельних_запитів:0};
 const q=id=>page.locator('[id="'+id+'"]');
 const state=()=>page.evaluate(()=>{const a=document.activeElement;return {tag:a.tagName,id:a.id,рядок:a.dataset.аркуш,режим:РЕЖИМ,аркуш:document.getElementById('аркуш').contains(a),видимий:!!a.getClientRects().length&&getComputedStyle(a).visibility!=='hidden',inert:!!a.closest('[inert]'),opener:АРКУШ&&АРКУШ.відкривач.id,opener_видимий:АРКУШ&&!!АРКУШ.відкривач.getClientRects().length,рядок_видимий:!!document.querySelector('[data-аркуш="кол-блок"]').getClientRects().length};});
 const inert=()=>page.evaluate(()=>[...document.body.children].filter(e=>!['SCRIPT','STYLE'].includes(e.tagName)&&!['аркуш','заслона'].includes(e.id)).map(e=>[e.id,e.getAttribute('inert')]));
 const check=(назва,ok,дані)=>{facts.перевірки.push({назва,успіх:!!ok,дані});if(strict)assert.ok(ok,назва+' '+JSON.stringify(дані));};
 const shot=async name=>{await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await page.screenshot({path:path.join(dir,name+'.png')});};
 fs.mkdirSync(dir,{recursive:true});page.on('pageerror',e=>facts.помилки.push(String(e)));
 await page.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='974.test')return r.fulfill({path:html,contentType:'text/html'});if(u.pathname.includes('/pyodide/')){const f=path.join('/tmp/974-pyodide',u.pathname.split('/').pop());if(fs.existsSync(f))return r.fulfill({path:f,contentType:f.endsWith('.wasm')?'application/wasm':f.endsWith('.js')?'application/javascript':'application/octet-stream'});}if(/api|міст/.test(u.href))facts.модельних_запитів++;return r.abort();});
 try{
  await page.goto('http://974.test/index.html');await page.waitForFunction(()=>typeof document.getElementById('сцн-новий').onclick==='function');
  await q('пр-імʼя').fill('Проба');await q('пр-згода').check();for(let i=0;i<3;i++)await q('н-далі').tap();await page.waitForFunction(()=>РЕЖИМ==='сценарій');
  await q('сц-рукою-показати').tap();await page.keyboard.press('Escape');
  for(const how of ['Escape','Готово','заслона']){
   await q('пал-кнопка').tap();await page.waitForFunction(()=>РЕЖИМ==='палітра');const before=await inert();await shot(how+'-палітра');
   await q('пал-кольори').tap();let s=await state();check(how+' вхід у Твої кольори',s.аркуш&&s.режим==='профіль',s);check(how+' початковий відкривач прихований, рядок видимий',s.opener==='пал-кольори'&&!s.opener_видимий&&s.рядок_видимий,s);check(how+' фон inert',(await inert()).every(x=>x[1]!==null),await inert());
   await shot(how+'-аркуш');await page.keyboard.press('Tab');s=await state();check(how+' Tab усередині',s.аркуш,s);await page.keyboard.press('Shift+Tab');s=await state();check(how+' ShiftTab усередині',s.аркуш,s);
   if(how==='Escape')await page.keyboard.press('Escape');else if(how==='Готово')await q('аркуш-готово').tap();else await page.touchscreen.tap(8,8);
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));s=await state();facts.закриття.push({спосіб:how,після:s});check(how+' повертає видимий рядок Твої кольори',s.tag==='BUTTON'&&s.рядок==='кол-блок'&&s.видимий&&!s.inert&&!s.аркуш,s);check(how+' відновлює inert',JSON.stringify(before)===JSON.stringify(await inert()),{before,after:await inert()});await shot(how+'-закрито');
   await q('вк-сценарій').tap();
  }
  await q('пал-кнопка').tap();await q('пал-кольори').tap();
  await page.evaluate(()=>{window._974_попередній_превью=document.getElementById('ог-кольори').firstChild;});
  await page.locator('#кол-блок details.розкривач > summary').tap();await q('кол-відповідь').fill('шкіра #d0a48a\nволосся #523c2d\nочі #64785e');await q('кол-читати').tap();await page.waitForFunction(()=>document.getElementById('кол-стан').textContent.startsWith('Прочитано'));
  check('Реальна зміна поля кольорів застосована',await page.evaluate(()=>КОЛІР.шкіра==='#d0a48a'&&КОЛІР.волосся==='#523c2d'&&КОЛІР.очі==='#64785e'));
  await q('аркуш-готово').tap();await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const changed=await page.evaluate(()=>({огляд_перерендерено:window._974_попередній_превью!==document.getElementById('ог-кольори').firstChild,зразків:document.querySelectorAll('#ог-кольори .зразки i').length,поточний_рядок:document.activeElement===document.querySelector('#е-огляд [data-аркуш="кол-блок"]'),connected:document.activeElement.isConnected,видимий:!!document.activeElement.getClientRects().length,inert:!!document.activeElement.closest('[inert]')}));facts.зміна_профілю=changed;
  check('Після зміни поля огляд перерендерив зразки',changed.огляд_перерендерено&&changed.зразків===3,changed);
  check('Після зміни поля фокус на поточному видимому рядку',changed.поточний_рядок&&changed.connected&&changed.видимий&&!changed.inert,changed);await shot('після-зміни-поля');
  check('Нема помилок сторінки',facts.помилки.length===0,facts.помилки);check('Нема модельних запитів',facts.модельних_запитів===0,facts.модельних_запитів);
 }finally{fs.writeFileSync(path.join(dir,'факти.json'),JSON.stringify(facts,null,2));await browser.close();}
 console.log(JSON.stringify({перевірок:facts.перевірки.length,провалів:facts.перевірки.filter(x=>!x.успіх).length,закриття:facts.закриття,помилки:facts.помилки,модельних_запитів:facts.модельних_запитів}));
})().catch(e=>{console.error(e);process.exitCode=1;});
