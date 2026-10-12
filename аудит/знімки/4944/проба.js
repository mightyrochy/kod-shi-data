const fs = require('fs'), path = require('path'), {chromium} = require('playwright');
const assert = require('assert/strict');
const root = process.argv[2] || '/tmp/974-evidence/after';
const суворо = !root.endsWith('before');
(async()=>{
 const b = await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']});
 const c = await b.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1});
 const p = await c.newPage(); p.setDefaultTimeout(10000); const  факти={браузер:await b.version(),розмір:'390×844',axe:{},перевірки:[],помилки:[]};
 p.on('pageerror',e=>факти.помилки.push(String(e)));
 await p.route('**/*', async r=>{
  const u = new URL(r.request().url());
  if(u.hostname==='974.test') return r.fulfill({path:path.join(root,'index.html'),contentType:'text/html'});
  if(u.href.includes('/pyodide/')) {
   const f=path.join('/tmp/974-pyodide',u.pathname.split('/').pop());
   if(fs.existsSync(f)) return r.fulfill({path:f,contentType:f.endsWith('.wasm')?'application/wasm':f.endsWith('.js')?'application/javascript':'application/octet-stream'});
  }
  return r.abort();
 });
 const active=()=>p.evaluate(()=>({id:document.activeElement.id,tag:document.activeElement.tagName,аркуш:document.getElementById('аркуш').contains(document.activeElement),ряд:document.activeElement.dataset.аркуш || document.activeElement.dataset.редактор,outline:getComputedStyle(document.activeElement).outline,видимий:document.activeElement.matches(':focus-visible')}));
 const check=(назва,умова,дані)=>{факти.перевірки.push({назва,успіх:умова,дані}); if(суворо) assert.ok(умова,назва+': '+JSON.stringify(дані));};
 const shot=назва=>p.screenshot({path:path.join(root,назва+'.png')});
 const axe=async назва=>{
  await p.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{})))); await p.addScriptTag({path:'/tmp/974-deps/node_modules/axe-core/axe.min.js'});
  факти.axe[назва]=await p.evaluate(async()=>{const r=await axe.run(document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22a','wcag22aa']}}); return {версія:r.testEngine.version,порушення:r.violations.map(v=>({id:v.id,impact:v.impact,description:v.description,nodes:v.nodes.map(n=>({target:n.target,html:n.html,failureSummary:n.failureSummary}))})),неповні:r.incomplete.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))};});
 };
 try{
 await p.goto('http://974.test/index.html');
 await p.waitForFunction(()=>typeof document.getElementById('сцн-новий').onclick==='function',{timeout:60000});
 await axe('головний-знайомство'); await shot('головний');
 await p.locator('[id="пр-імʼя"]').fill('Проба'); await p.locator('#пр-згода').check();
 for(let i=0;i<3;i++) await p.locator('#н-далі').tap();
 await p.waitForFunction(()=>РЕЖИМ==='сценарій');
 await axe('сценарій-порожній');
 await p.locator('#сц-рукою-показати').tap();
 let a=await active(); check('перший ручний дотик → фокус усередині',a.аркуш,a); await axe('аркуш-сценарій'); await shot('сценарій-аркуш');
 await p.keyboard.press('Escape'); a=await active(); check('перший ручний вхід → рядок Нагода',a.ряд==='ред-нагода',a);
 const trap=async назва=>{
  const n=await p.evaluate(()=>[...document.querySelectorAll('#аркуш button,#аркуш input,#аркуш select,#аркуш textarea,#аркуш a[href],#аркуш summary,#аркуш [tabindex]')].filter(e=>e.tabIndex>=0&&!e.matches(':disabled')&&!e.closest('[inert]')&&e.getClientRects().length&&getComputedStyle(e).visibility!=='hidden').length);
  for(const key of ['Tab','Shift+Tab']) for(let i=0;i<n+2;i++){await p.keyboard.press(key);const a=await active();check(назва+' '+key+' '+i,a.аркуш,a);check(назва+' видимий фокус '+key+' '+i,a.видимий&&!a.outline.includes('none'),a);}
  await shot(назва+'-фокус');
 };
 await p.locator('[data-редактор="ред-нагода"]').press('Enter'); a=await active();check('сценарій Enter → фокус',a.аркуш,a);await trap('сценарій');
 await p.locator('#аркуш-готово').tap();a=await active();check('сценарій Готово → відкривач',a.ряд==='ред-нагода',a);
 await p.locator('[data-редактор="ред-нагода"]').tap();await p.touchscreen.tap(10,10);a=await active();check('сценарій заслона → відкривач',a.ряд==='ред-нагода',a);
 await p.locator('[data-редактор="ред-нагода"]').tap();await p.keyboard.press('Escape');a=await active();check('сценарій Escape → відкривач',a.ряд==='ред-нагода',a);
 await p.locator('#сц-зберегти').tap();a=await active();check('збереження дотик → поле назви',a.id==='сц-назва-поле',a);await axe('аркуш-збереження');await trap('збереження');
 await p.keyboard.press('Escape');a=await active();check('збереження Escape → відкривач',a.id==='сц-зберегти',a);
 await p.locator('#сц-зберегти').press('Enter');a=await active();check('збереження Enter → поле назви',a.id==='сц-назва-поле',a);await p.touchscreen.tap(10,10);a=await active();check('збереження заслона → відкривач',a.id==='сц-зберегти',a);
 await p.locator('#сц-зберегти').tap();await p.locator('#сц-збер-скасувати').tap();a=await active();check('збереження Скасувати → відкривач',a.id==='сц-зберегти',a);
 await p.locator('#сц-зберегти').tap();await p.locator('#сц-збер-новий').tap();await p.waitForFunction(()=>!document.getElementById('аркуш').hidden===false);a=await active();check('збереження Зберегти → відкривач',a.id==='сц-зберегти',a);
 await p.locator('#пф-кнопка').tap();
 const фон=await p.evaluate(()=>{const d=document.createElement('div');d.id='974-попередній-inert';d.setAttribute('inert','попередній');document.body.appendChild(d);return [...document.body.children].filter(e=>!['SCRIPT','STYLE'].includes(e.tagName)&&!['аркуш','заслона'].includes(e.id)).map(e=>[e.id,e.getAttribute('inert')]);});
 await p.locator('[data-аркуш="проф-блок"]').tap();a=await active();check('профіль дотик → фокус',a.аркуш,a);await axe('аркуш-профіль');await trap('профіль');
 const інертний=await p.evaluate(()=>[...document.body.children].filter(e=>!['SCRIPT','STYLE'].includes(e.tagName)&&!['аркуш','заслона'].includes(e.id)).every(e=>e.hasAttribute('inert')));check('весь фон inert під аркушем',інертний,await p.evaluate(()=>[...document.body.children].map(e=>[e.tagName,e.id,e.inert])));
 await p.keyboard.press('Escape');a=await active();check('профіль Escape → відкривач',a.ряд==='проф-блок',a);
 const після=await p.evaluate(()=>[...document.body.children].filter(e=>!['SCRIPT','STYLE'].includes(e.tagName)&&!['аркуш','заслона'].includes(e.id)).map(e=>[e.id,e.getAttribute('inert')]));check('попередній inert відновлено дослівно',JSON.stringify(фон)===JSON.stringify(після),{фон,після});
 await p.locator('[data-аркуш="проф-блок"]').press('Enter');a=await active();check('профіль Enter → фокус',a.аркуш,a);await p.locator('#аркуш-готово').tap();a=await active();check('профіль Готово → відкривач',a.ряд==='проф-блок',a);
 await p.locator('[data-аркуш="проф-блок"]').tap();await p.touchscreen.tap(10,10);a=await active();check('профіль заслона → відкривач',a.ряд==='проф-блок',a);
 await p.locator('#вк-сценарій').tap();await axe('сценарій-ручний');await shot('сценарій');
 await p.locator('#пал-кнопка').tap();await p.waitForFunction(()=>РЕЖИМ==='палітра');await axe('палітра-порожня');await shot('палітра');
 await p.evaluate(()=>{П={архівна:true,картки:[{рука:'1',текст:'',опис:'Архівний образ для перевірки доступності.',як_носити:[],питання:[],неповний:'',речі:[{id:'фікстура-сукня',назва:'Сукня',слот:'сукня',ціна:1000},{id:'фікстура-пальто',назва:'Пальто',слот:'пальто',ціна:2000}]}]};рендер();режим('образи');});
 await axe('картка-архівна');await shot('картка');
 } finally {fs.writeFileSync(path.join(root,'факти.json'),JSON.stringify(факти,null,2));await b.close();}
 console.log(JSON.stringify({перевірок:факти.перевірки.length,провалів:факти.перевірки.filter(x=>!x.успіх).length,axe:Object.fromEntries(Object.entries(факти.axe).map(([k,v])=>[k,v.порушення.map(x=>x.id)])),помилки:факти.помилки}));
})().catch(e=>{console.error(e);process.exitCode=1;});
