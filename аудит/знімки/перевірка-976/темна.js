const fs=require('fs'), path=require('path'), assert=require('assert/strict');
const {chromium}=require('playwright');
const dir=__dirname, facts={перевірки:[],axe:{},помилки:[]};
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 facts.браузер=await browser.version(); facts.розмір='390×844';
 const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
 page.on('pageerror',e=>facts.помилки.push(String(e)));
 const q=id=>page.locator('[id="'+id+'"]');
 await page.route('**/*',r=>{
  const u=new URL(r.request().url());
  if(u.hostname===new URL('http://перевірка.test').hostname) return r.fulfill({path:'/tmp/review976/after/index.html',contentType:'text/html'});
  if(u.pathname.includes('/pyodide/')){const f='/tmp/974-pyodide/'+u.pathname.split('/').pop();if(fs.existsSync(f)) return r.fulfill({path:f,contentType:f.endsWith('.wasm')?'application/wasm':f.endsWith('.js')?'application/javascript':'application/octet-stream'});}
  return r.abort();
 });
 const active=()=>page.evaluate(()=>{const e=document.activeElement,s=getComputedStyle(e),r=e.getBoundingClientRect();return {id:e.id,текст:e.textContent.trim().slice(0,55),редактор:e.dataset.редактор,профіль:e.dataset.аркуш,усередині:document.querySelector('#аркуш').contains(e),видимий:e.matches(':focus-visible'),outline:s.outline,прямокутник:{x:r.x,y:r.y,w:r.width,h:r.height},доступний:!!e.getClientRects().length&&!e.closest('[inert]')};});
 const check=(назва,ok,data)=>{facts.перевірки.push({назва,успіх:!!ok,дані:data});assert.ok(ok,назва+' '+JSON.stringify(data));};
 const inside=async label=>{const a=await active();check(label,a.усередині,a);};
 const opener=async(label,key,value)=>{const a=await active();check(label,a[key]===value&&a.доступний&&!a.усередині,a);};
 const inert=()=>page.evaluate(()=>[...document.body.children].filter(e=>!['SCRIPT','STYLE'].includes(e.tagName)&&!['аркуш','заслона'].includes(e.id)).map(e=>[e.id,e.getAttribute('inert')]));
 const axe=async label=>{
  await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));
  await page.addScriptTag({path:'/tmp/974-deps/node_modules/axe-core/axe.min.js'});
  facts.axe[label]=await page.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22a','wcag22aa']}});return {версія:r.testEngine.version,порушення:r.violations.map(v=>({id:v.id,вузли:v.nodes.map(n=>({target:n.target,html:n.html}))})),неповні:r.incomplete.map(v=>({id:v.id,вузли:v.nodes.map(n=>n.target)}))};});
 };
 const trap=async label=>{
  const first=await active();let forward=[],back=[];
  for(let i=0;i<15;i++){await page.keyboard.press('Tab');const a=await active();forward.push(a.id||a.текст);check(label+' Tab '+i,a.усередині&&a.видимий&&a.outline.includes('solid 2px'),a);}
  for(let i=0;i<15;i++){await page.keyboard.press('Shift+Tab');const a=await active();back.push(a.id||a.текст);check(label+' ShiftTab '+i,a.усередині&&a.видимий&&a.outline.includes('solid 2px'),a);}
  check(label+' повернення після симетричного обходу',(await active()).id===first.id&&(await active()).текст===first.текст,{first,after:await active(),forward,back});
  await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await page.screenshot({path:path.join(dir,label+'-фокус.png')});
 };
 try{
  await page.goto('http://перевірка.test/index.html');
  await page.waitForFunction(()=>typeof document.querySelector('#сцн-новий').onclick==='function',{timeout:60000});
  await q('пр-імʼя').fill('Перевірка');await q('пр-згода').check();for(let i=0;i<3;i++)await q('н-далі').tap();
  await page.waitForFunction(()=>РЕЖИМ==='сценарій');await q('тема-кнопка').tap();
  check('Перемикання на темну тему',await page.evaluate(()=>document.documentElement.dataset.тема==='темна'));
  await q('сц-рукою-показати').tap();await page.keyboard.press('Tab');let a=await active();check('Темна сценарій: видимий фокус',a.усередині&&a.видимий&&a.outline.includes('solid 2px'),a);await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await page.screenshot({path:path.join(dir,'сценарій-темна.png')});await page.keyboard.press('Escape');await opener('Темна сценарій: повернення','редактор','ред-нагода');
  await q('сц-зберегти').press('Enter');a=await active();check('Темна збереження: видимий фокус',a.усередині&&a.видимий&&a.outline.includes('solid 2px'),a);await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await page.screenshot({path:path.join(dir,'збереження-темна.png')});await page.keyboard.press('Escape');await opener('Темна збереження: повернення','id','сц-зберегти');
  await q('пф-кнопка').tap();await page.locator('[data-аркуш="проф-блок"]').press('Enter');await page.keyboard.press('Tab');a=await active();check('Темна профіль: видимий фокус',a.усередині&&a.видимий&&a.outline.includes('solid 2px'),a);await page.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await page.screenshot({path:path.join(dir,'профіль-темна.png')});await page.keyboard.press('Escape');await opener('Темна профіль: повернення','профіль','проф-блок');
 }finally{fs.writeFileSync(path.join(dir,'темна-факти.json'),JSON.stringify(facts,null,2));await browser.close();}
 console.log(JSON.stringify({перевірок:facts.перевірки.length,провалів:facts.перевірки.filter(x=>!x.успіх).length,помилки:facts.помилки}));
})().catch(e=>{console.error(e);process.exitCode=1;});
