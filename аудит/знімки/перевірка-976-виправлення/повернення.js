const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
const dir=__dirname,head='78700cad184c76f133e20472eb31267ff5a01674',facts={head,viewport:{width:390,height:844},cases:[],errors:[],modelRequests:0,checks:[]};
const check=(name,ok,data)=>{facts.checks.push({name,ok:!!ok,data});assert.ok(ok,name+' '+JSON.stringify(data));};
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});facts.browser=await browser.version();
 try{
  for(const dark of [false,true])for(const change of [false,true])for(const close of ['Escape','Готово','заслона']){
   const name=(dark?'темна':'світла')+'-'+(change?'зміна':'порожня')+'-'+close;
   const context=await browser.newContext({viewport:facts.viewport,isMobile:true,hasTouch:true,reducedMotion:'reduce'});
   const page=await context.newPage();page.setDefaultTimeout(90000);page.on('pageerror',e=>facts.errors.push({name,error:String(e)}));
   await page.route('**/*',r=>{const u=new URL(r.request().url());if(/anthropic|openai|1234|\/v1\/(chat|responses)/.test(u.href))facts.modelRequests++;
    if(u.hostname==='return976.test')return r.fulfill({path:'/tmp/review976-fix/after/index.html',contentType:'text/html'});
    if(u.pathname.includes('/pyodide/')){const f='/tmp/974-pyodide/'+path.basename(u.pathname);if(fs.existsSync(f))return r.fulfill({path:f,contentType:f.endsWith('.wasm')?'application/wasm':f.endsWith('.js')?'application/javascript':'application/octet-stream'});}return r.abort();});
   const q=id=>page.locator('[id="'+id+'"]');
   const state=()=>page.evaluate(()=>{const active=document.activeElement,row=document.querySelector('#е-огляд [data-аркуш="кол-блок"]'),r=active.getBoundingClientRect();return {mode:РЕЖИМ,active:active.id||active.tagName,logical:active.dataset.аркуш,currentRow:active===row,connected:active.isConnected,visible:!!active.getClientRects().length&&getComputedStyle(active).visibility==='visible',outside:!document.querySelector('#аркуш').contains(active),inert:!!active.closest('[inert]'),rect:{x:r.x,y:r.y,w:r.width,h:r.height},sheetHidden:document.querySelector('#аркуш').hidden,colors:КОЛІР,oldRowConnected:window.__рядДоЗміни?.isConnected,oldRowIsCurrent:window.__рядДоЗміни===row};});
   const inert=()=>page.evaluate(()=>[...document.body.children].filter(e=>!['SCRIPT','STYLE'].includes(e.tagName)&&!['аркуш','заслона'].includes(e.id)).map(e=>[e.id,e.getAttribute('inert')]));
   try{
    await page.goto('http://return976.test/index.html');await page.waitForFunction(()=>typeof document.getElementById('сцн-новий').onclick==='function');
    await q('пр-імʼя').fill('Незалежна перевірка повернення');await q('пр-згода').check();for(let i=0;i<3;i++)await q('н-далі').tap();
    await page.waitForFunction(()=>РЕЖИМ==='сценарій');if(dark)await q('тема-кнопка').tap();
    await q('сц-рукою-показати').tap();await page.keyboard.press('Escape');await q('пал-кнопка').tap();await q('пал-кольори').waitFor({state:'visible'});
    check(name+' порожня палітра',await q('пал-стан').textContent()==='Кольорів шкіри, волосся й очей у профілі ще нема — від них рахується палітра.');
    const before=await inert();await q('пал-кольори').tap();await q('аркуш').waitFor({state:'visible'});
    check(name+' фокус увійшов',await page.evaluate(()=>document.getElementById('аркуш').contains(document.activeElement)));
    check(name+' фон inert',(await inert()).every(x=>x[1]!==null));
    for(let i=0;i<5;i++){await page.keyboard.press('Tab');check(name+' Tab '+i,await page.evaluate(()=>document.getElementById('аркуш').contains(document.activeElement)));}
    for(let i=0;i<5;i++){await page.keyboard.press('Shift+Tab');check(name+' ShiftTab '+i,await page.evaluate(()=>document.getElementById('аркуш').contains(document.activeElement)));}
    await page.evaluate(()=>window.__рядДоЗміни=document.querySelector('#е-огляд [data-аркуш="кол-блок"]'));
    if(change){
     await page.locator('#кол-блок details > summary').tap();await q('кол-відповідь').fill('шкіра #f0d5c8 волосся #4a4644 очі #6b8cae');await q('кол-читати').tap();
     await page.waitForFunction(()=>КОЛІР.шкіра==='#f0d5c8'&&КОЛІР.волосся==='#4a4644'&&КОЛІР.очі==='#6b8cae'&&document.getElementById('кол-стан').textContent.startsWith('Прочитано:'));
     check(name+' поле справді застосоване',(await state()).colors.очі==='#6b8cae');
    }
    await page.screenshot({path:path.join(dir,name+'-аркуш.png'),animations:'disabled'});
    if(close==='Escape')await page.keyboard.press('Escape');else if(close==='Готово')await q('аркуш-готово').tap();else await page.touchscreen.tap(8,8);
    await q('аркуш').waitFor({state:'hidden'});const after=await state();
    check(name+' повернення на поточний видимий рядок',after.mode==='профіль'&&after.currentRow&&after.logical==='кол-блок'&&after.connected&&after.visible&&after.outside&&!after.inert&&after.sheetHidden,after);
    check(name+' рядок у viewport',after.rect.y>=0&&after.rect.y<844&&after.rect.h>0,after.rect);
    check(name+' inert дослівно відновлено',JSON.stringify(before)===JSON.stringify(await inert()));
    if(change)check(name+' зміна збережена після закриття',after.colors.шкіра==='#f0d5c8'&&after.colors.волосся==='#4a4644'&&after.colors.очі==='#6b8cae',after.colors);
    await page.screenshot({path:path.join(dir,name+'-закрито.png'),animations:'disabled'});facts.cases.push({name,close,change,dark,after});
    await page.keyboard.press('Enter');check(name+' Enter повторно відкриває правильний аркуш',await page.evaluate(()=>!document.getElementById('аркуш').hidden&&document.getElementById('аркуш-назва').textContent==='Твої кольори'));
   }finally{await context.close();}
  }
  check('помилок сторінки 0',facts.errors.length===0,facts.errors);check('модельних запитів 0',facts.modelRequests===0,facts.modelRequests);
 }finally{fs.writeFileSync(path.join(dir,'повернення-факти.json'),JSON.stringify(facts,null,2));await browser.close();}
 console.log(JSON.stringify({head,cases:facts.cases.length,checks:facts.checks.length,fails:facts.checks.filter(x=>!x.ok).length,errors:facts.errors,modelRequests:facts.modelRequests}));
})().catch(e=>{console.error(e);process.exitCode=1});
