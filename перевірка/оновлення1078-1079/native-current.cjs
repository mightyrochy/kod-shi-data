const fs = require('fs'), path = require('path'), assert = require('assert/strict'), crypto = require('crypto'), zlib = require('zlib'), http=require('http');
const {chromium} = require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const root='/dev/shm/qa-updates-1078-1079', out=root+'/native', html=root+'/current1094.html';
let server;const network=[],failures=[],consoleErrors=[];
const sha256=x=>crypto.createHash('sha256').update(x).digest('hex');
const diagnostics=[
  'hand_1 · blocks=2 · with_id=2',
  'prompt · hand_1_without_format · format=OBRAZ · variants=1',
  'hand_2 · failed: HTTP 413',
  'hand_3 · repeat_from_hand_1',
  'hand_4.retry · layer · failed: HTTP 503',
  'prompt · hand_1_no_K-KOH-05 · variants=1',
  'prompt · hand_2_no_K-COL-06-M · failed: HTTP 429',
  'control · hand_2_broken=temperature · drawn_from=hour,temperature',
  'control · blind · breakage=temperature · brief_rows=3',
  'control · trace · breakage=hour · packet_fields=x',
  'control · no_input=a=b',
  'verdict · edges_not_counted: Error: test_diagnostic'
];
const spoiler=/hand_\d+|without_format|_no_K-|K-KOH-05|K-COL-06-M|temperature|\bhour\b|breakage=/;
const card=(hand,n)=>({рука:hand,ітерацій:1,викликів:1,текст:'Образ для прогулянки',опис:'Образ для прогулянки',підпис:'Образ для прогулянки',речі:[{id:`r3-${n}@example.com`,назва:'Сукня',ціна:1500,слот:'сукня',фото:null}],мітки:[],знахідки:[],питання:[],етапи:{викликів:1,виклики:[]},свідомі:[],невиконано:null,мова:[],мова_спроб:0,мова_видано:'так',фото_не_ті:[],дібрав_код_слоти:[]});
const packet={в:'ПОКАЗ-V1',збірка:'незалежна-проба-5580-r3',каталог:'каталог_стенд.xml · 639 речей',профіль:'Оля',розклад:'3142',прогін:'qa5580-r3',випадок:'Прогулянка',пул:100,картки:['3','1','4','2'].map(card)};

(async()=>{
 let browser,context;const pageErrors=[],facts={};
 try{
 server=http.createServer((q,r)=>{const u=decodeURIComponent(new URL(q.url,'http://localhost').pathname);if(u==='/build.txt'){r.writeHead(404);return r.end('');}const f=u==='/'?html:path.join(root,'current',u);fs.readFile(f,(e,b)=>{r.writeHead(e?404:200,{'Content-Type':u.endsWith('.ttf')?'font/ttf':'text/html; charset=utf-8'});r.end(e?'':b);});});
 await new Promise(r=>server.listen(0,'127.0.0.1',r));
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],proxy:{server:process.env.HTTPS_PROXY,bypass:'127.0.0.1,localhost'},env:{...process.env,TMPDIR:root+'/tmp'}});
 context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 await context.addInitScript(()=>{const D=Date;window.Date=class extends D{constructor(...a){super(...(a.length?a:['2026-10-15T12:00:00Z']));}static now(){return new D('2026-10-15T12:00:00Z').getTime();}};});
 const page=await context.newPage();page.on('pageerror',e=>pageErrors.push(e.message));page.on('console',m=>{if(m.type()==='error')consoleErrors.push(m.text());});page.on('requestfailed',q=>failures.push({url:q.url(),failure:q.failure()}));
 page.on('response',async r=>{if(r.url().includes('cdn.jsdelivr.net')){const rec={url:r.url(),status:r.status(),type:r.request().resourceType()};network.push(rec);if(r.url().endsWith('/pyodide.js')){try{const b=await r.body();rec.bytes=b.length;rec.sha384=crypto.createHash('sha384').update(b).digest('base64');}catch(e){rec.error=String(e);}}}});
 await page.goto('http://127.0.0.1:'+server.address().port+'/#'+zlib.gzipSync(JSON.stringify(packet)).toString('base64url'));
 await page.waitForFunction(()=>document.querySelectorAll('#картки .картка').length===4);
 await page.evaluate(diagnostics=>{пристрій='qa5580-r3';СЛУЖБОВЕ=true;document.querySelector('#службове').classList.add('видно');ЗБ={картки:П.картки,стадії:[],етап:[],ключ:['3','1','4','2'],готово:true,успіх:true,діагноз:diagnostics};малюватиДіагнозП();const c=document.createElement('canvas');c.width=360;c.height=640;const x=c.getContext('2d');x.fillStyle='#d7b8a4';x.fillRect(0,0,360,640);x.fillStyle='#305955';x.fillRect(75,160,210,400);x.fillStyle='#f3d0b1';x.beginPath();x.arc(180,100,58,0,Math.PI*2);x.fill();П.картки[0].картинка=c.toDataURL('image/png');полотно(0);},diagnostics);
 const baseline=await page.evaluate(()=>JSON.stringify({P:П,raw:ЗБ.діагноз,assignment:ЗБ.ключ,pool:П.пул}));
 await page.locator('#к-0 .ряд[data-поле="верд"] .чип[data-код="as_is"]').tap();await page.waitForFunction(()=>В[0]?.записано);
 await page.locator('#службове > summary').tap();await page.locator('#службове').scrollIntoViewIfNeeded();
 const cdp=await context.newCDPSession(page);async function names(){return (await cdp.send('Accessibility.getFullAXTree')).nodes.filter(x=>!x.ignored&&typeof x.name?.value==='string').map(x=>x.name.value);}
 const text=await page.locator('#службове').innerText(),ax=await names();assert(!spoiler.test(text));assert(!ax.some(x=>spoiler.test(x)));for(const x of ['HTTP 413','HTTP 503','HTTP 429','control · no_input=a=b','Error: test_diagnostic']){assert(text.includes(x));assert(ax.some(t=>t.includes(x)));}
 assert.equal(await page.evaluate(()=>JSON.stringify({P:П,raw:ЗБ.діагноз,assignment:ЗБ.ключ,pool:П.пул})),baseline);
 facts.blind={oneSaved:true,spoilersText:false,spoilersAX:false,errorsVisible:true,rawAssignmentPoolPacketUnchanged:true,text,ax:ax.filter(x=>/HTTP|no_input|Error:|hand_|breakage=/.test(x))};
 await page.screenshot({path:out+'/current-service-blind-390.png',animations:'disabled'});
 const opener=page.locator('#к-0 .перегляд-відкрити');await opener.focus();const before=await page.evaluate(()=>({overflow:document.body.style.overflow,inert:Array.from(document.body.children).map(x=>x.getAttribute('inert'))}));await page.keyboard.press('Enter');
 await page.getByRole('dialog',{name:'Образ на весь екран'}).waitFor({state:'visible'});assert(await page.locator('#службове').evaluate(x=>!!x.closest('[inert]')));assert.equal(await page.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Закрити');await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'Закрити');assert(!(await names()).some(x=>spoiler.test(x)));
 await page.screenshot({path:out+'/current-modal-390.png',animations:'disabled'});await page.keyboard.press('Escape');assert(await opener.evaluate(x=>x===document.activeElement));assert.deepEqual(await page.evaluate(()=>({overflow:document.body.style.overflow,inert:Array.from(document.body.children).map(x=>x.getAttribute('inert'))})),before);
 facts.modal={namedDialog:true,nativeEnterEscapeTab:true,backgroundInert:true,focusRestored:true,priorInertOverflowRestored:true,spoilerAX:false};
 await page.evaluate(async()=>{const c=document.createElement('canvas');c.width=360;c.height=640;const x=c.getContext('2d');x.fillStyle='#d7b8a4';x.fillRect(0,0,360,640);x.fillStyle='#f3d0b1';x.beginPath();x.arc(180,100,58,0,Math.PI*2);x.fill();await писатиКв(ключФото('портрет'),await new Promise(r=>c.toBlob(r,'image/png')));ФОТО_Є.портрет=true;режим('сценарій');});
 await page.locator('#пф-кнопка').tap();await page.locator('#е-огляд [data-аркуш="др-блок"]').tap();await page.locator('#кд-м').waitFor({state:'visible'});
 const sliders=[];for(const name of ['Масштаб','Ліво-право','Вгору-вниз']){const l=page.getByRole('slider',{name,exact:true});assert.equal(await l.count(),1);const old=+await l.inputValue();await l.focus();await page.keyboard.press('ArrowRight');assert.equal(+await l.inputValue(),old+1);sliders.push({name,before:old,after:+await l.inputValue()});}
 await page.evaluate(async()=>{await Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{})));});await page.screenshot({path:out+'/current-crop-390.png',animations:'disabled'});facts.crop={sliders,nativeArrowRight:true,settledAnimations:true,syntheticPortrait:true};
 const resources=await page.evaluate(async()=>{await document.fonts.ready;const e=document.querySelector('script[src*="pyodide.js"]');return {script:{url:e.src,integrity:e.integrity,crossOrigin:e.crossOrigin},loader:typeof loadPyodide,fonts:await Promise.all(['400 16px "Fixel Text"','500 16px "Fixel Text"','600 16px "Fixel Text"','600 16px "Fixel Display"'].map(async s=>({spec:s,count:(await document.fonts.load(s)).length,loaded:document.fonts.check(s)}))),width:innerWidth,scrollWidth:document.documentElement.scrollWidth};});
 assert.equal(resources.loader,'function');assert.equal(resources.script.crossOrigin,'anonymous');assert(resources.fonts.every(x=>x.count>0&&x.loaded));const py=network.find(x=>x.url.endsWith('/pyodide.js'));assert(py&&py.status===200&&py.bytes===14761);assert.equal('sha384-'+py.sha384,resources.script.integrity);assert.equal(new Set(network.filter(x=>x.type==='font'&&x.status===200&&x.url.includes('Fixel@514fd02ea7d70668ed3dd09fb2674ba6f70d61ee/')).map(x=>x.url)).size,4);assert.equal(failures.filter(x=>x.url.includes('cdn.jsdelivr.net')).length,0);assert.equal(pageErrors.length,0);assert.equal(consoleErrors.filter(x=>/integrity|valid digest|CORS|crossorigin/i.test(x)).length,0);assert.equal(resources.width,390);assert.equal(resources.scrollWidth,390);
 const report={head:'0ffb624821c5972d7361c60f73dabcd52e61d9ee',main:'7f9e9f8d51c7ea135b68eb3c12aa94c456de324f',actualCDN:true,stubs:0,pyodideInstantiations:0,paidCalls:0,models:0,syntheticImages:true,browser:browser.version(),builtSha256:sha256(fs.readFileSync(html)),resources,facts,network,failures,consoleErrors,pageErrors,scope:'ONE meaningful current combined scenario; no old 0/1/3/4 matrix or full export repeat; jsdom auto display stage skipped by builder'};fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));console.log(JSON.stringify({PASS:true,head:report.head,facts,resources,pageErrors}));
 }catch(e){fs.writeFileSync(out+'/failure.json',JSON.stringify({error:String(e),stack:e.stack,facts,network,failures,consoleErrors,pageErrors},null,2));throw e;}finally{if(context)await context.close();if(browser)await browser.close();if(server)await new Promise(r=>server.close(r));}
})().catch(e=>{console.error(e);process.exitCode=1;});
