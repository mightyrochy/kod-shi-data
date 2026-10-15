const {chromium}=require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const stage=process.argv[2],root='/workspace/scratch/4944-crop-current',out=path.join(root,'evidence',stage);
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
 const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),page=await ctx.newPage();page.setDefaultTimeout(45000);
 const errors=[],blocked=[],requests=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.route('**/*',async r=>{const u=new URL(r.request().url()),p=decodeURIComponent(u.pathname);requests.push({method:r.request().method(),host:u.hostname,path:p});let f;
  if(u.hostname==='crop.local')f=p.startsWith('/шрифти/')?path.join('/workspace/scratch/4944-next-current',p):path.join(out,p==='/'?'index.html':p);
  else if(u.href.includes('/pyodide/'))f=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(p));
  else if(u.href.includes('/Fixel@main/fonts/webfonts/'))f=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(p));
  if(f&&fs.existsSync(f))await r.fulfill({path:f});else{blocked.push(u.href);await r.abort();}
 });
 await page.goto('http://crop.local/');await page.waitForFunction(()=>typeof document.getElementById('пф-кнопка').onclick==='function');
 const fixture=await page.evaluate(async()=>{const c=document.createElement('canvas');c.width=400;c.height=600;const g=c.getContext('2d');g.fillStyle='#ded4bd';g.fillRect(0,0,400,600);g.fillStyle='#725f49';g.fillRect(0,300,400,300);g.fillStyle='#b17060';g.fillRect(120,100,160,220);g.fillStyle='#f1e9d9';g.fillRect(175,185,50,50);const b=await new Promise(r=>c.toBlob(r,'image/png'));await писатиКв(ключФото('портрет'),b);ПРОФІЛЬ_СТВОРЕНО=true;ФОТО_Є.портрет=true;режим('сценарій');return {kind:'локальний синтетичний bitmap, не фото людини',width:c.width,height:c.height,bytes:b.size,type:b.type};});
 await page.locator('#пф-кнопка').tap();await page.locator('#е-огляд [data-аркуш="др-блок"]').tap();await page.waitForSelector('#кд-м');await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(450);
 await page.addScriptTag({path:'/workspace/scratch/liusterko-4944/.qa4944/node_modules/axe-core/axe.min.js'});
 const axeResult=await page.evaluate(async()=>{const r=await axe.run(document.getElementById('др-блок'),{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});return {violations:r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>v.id)};});
 const cdp=await ctx.newCDPSession(page);await cdp.send('Accessibility.enable');const doc=await cdp.send('DOM.getDocument');const controls=[];
 for(const [id,key,name,initial,min,max] of [['кд-м','масштаб','Масштаб',100,100,320],['кд-x','x','Ліво-право',50,0,100],['кд-y','y','Вгору-вниз',35,0,100]]){
  const locator=page.locator('#'+id);await locator.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),id);
  const target=await cdp.send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#'+id});const ax=await cdp.send('Accessibility.getPartialAXTree',{nodeId:target.nodeId,fetchRelatives:false});
  const measured=await locator.evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {html:e.outerHTML,value:e.value,focusVisible:e.matches(':focus-visible'),outline:s.outline,box:{x:r.x,y:r.y,width:r.width,height:r.height},hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e};});
  await page.screenshot({path:path.join(out,id+'-focus.png')});const keys=[];
  for(const [press,expected] of [['ArrowRight',initial+1],['ArrowLeft',initial],['End',max],['Home',min]]){await page.keyboard.press(press);const data=await locator.evaluate(e=>({value:+e.value,state:{...КАДР},transforms:[...document.querySelectorAll('#др-тіло .вікно img')].map(i=>i.style.transform)}));assert.equal(data.value,expected);assert.equal(data.state[key],expected);assert(data.transforms.length>0&&new Set(data.transforms).size===1);keys.push({press,expected,...data});}
  await locator.evaluate((e,v)=>{e.value=String(v);e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));},initial);await page.keyboard.press('Tab');await page.waitForTimeout(100);const stored=await page.evaluate(()=>читатиКв('кадр'));assert.equal(stored[key],initial);
  controls.push({id,name,measured,ax:ax.nodes.map(n=>({role:n.role?.value,name:n.name?.value,value:n.value?.value,properties:n.properties})),keys,stored});
  assert(measured.focusVisible&&measured.hit);assert.equal(controls.at(-1).ax[0].name,stage==='before'?'':name);
 }
 const final=await page.evaluate(()=>({state:{...КАДР},transforms:[...document.querySelectorAll('#др-тіло .вікно img')].map(i=>i.style.transform),viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
 await page.locator('#кд-м').focus();await page.screenshot({path:path.join(out,'crop-390x844.png')});assert.equal(final.viewport,390);assert.equal(final.scrollWidth,390);assert.equal(errors.length,0);
 const label=axeResult.violations.find(v=>v.id==='label');assert.equal(label?.targets.length||0,stage==='before'?3:0);
 const facts={stage,head:process.env.SOURCE_HEAD,chromium:browser.version(),axe:'4.14.0',fixture,axeResult,controls,final,errors,blocked,requests,modelPhotoApiCalls:0};fs.writeFileSync(path.join(out,'facts.json'),JSON.stringify(facts,null,2));console.log(JSON.stringify({stage,names:controls.map(c=>c.ax[0].name),violations:axeResult.violations,errors,final}));await ctx.close();
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
