const {chromium}=require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root='/workspace/scratch/review-1049-current',built='/workspace/scratch/4944-crop-current/evidence';
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
for(const stage of ['before','after']){
 const out=path.join(root,'evidence',stage),ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true}),p=await ctx.newPage(),errors=[],denied=[],requests=[];
 p.on('pageerror',e=>errors.push(String(e)));p.setDefaultTimeout(45000);
 await p.route('**/*',async r=>{const u=new URL(r.request().url()),s=decodeURIComponent(u.pathname);requests.push({method:r.request().method(),url:u.href});let f;
 if(u.hostname==='qa.local')f=s.startsWith('/шрифти/')?path.join('/workspace/scratch/4944-next-current',s):path.join(built,stage,s==='/'?'index.html':s);
 else if(u.href.includes('/pyodide/'))f=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(s));
 else if(u.href.includes('/Fixel@main/fonts/webfonts/'))f=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(s));
 if(f&&fs.existsSync(f))await r.fulfill({path:f});else{denied.push(u.href);await r.abort();}});
 await p.goto('http://qa.local/');await p.waitForFunction(()=>typeof document.getElementById('пф-кнопка').onclick==='function');
 await p.evaluate(async()=>{const c=document.createElement('canvas');c.width=300;c.height=500;const g=c.getContext('2d');g.fillStyle='#ded4bd';g.fillRect(0,0,300,500);g.fillStyle='#83635b';g.fillRect(80,80,140,160);g.fillStyle='#5b6768';g.fillRect(20,300,260,200);const blob=await new Promise(r=>c.toBlob(r));await писатиКв(ключФото('портрет'),blob);ПРОФІЛЬ_СТВОРЕНО=true;ФОТО_Є.портрет=true;режим('сценарій');});
 const opener=p.locator('#е-огляд [data-аркуш="др-блок"]');await p.locator('#пф-кнопка').tap();await opener.tap();await p.locator('#кд-м').waitFor();await p.evaluate(()=>document.fonts.ready);await p.waitForTimeout(400);
 const cdp=await ctx.newCDPSession(p);await cdp.send('Accessibility.enable');const doc=await cdp.send('DOM.getDocument'),controls=[];
 for(const [id,key,name,initial,min,max] of [['кд-м','масштаб','Масштаб',100,100,320],['кд-x','x','Ліво-право',50,0,100],['кд-y','y','Вгору-вниз',35,0,100]]){
  const l=p.locator('#'+id);await l.focus();await p.keyboard.press('Shift+Tab');await p.keyboard.press('Tab');assert.equal(await p.evaluate(()=>document.activeElement.id),id);
  const node=await cdp.send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#'+id}),tree=await cdp.send('Accessibility.getPartialAXTree',{nodeId:node.nodeId,fetchRelatives:false}),a=tree.nodes[0];
  assert.equal(a.role.value,'slider');assert.equal(a.name.value,stage==='after'?name:'');assert.equal(a.value.value,initial);
  const m=await l.evaluate(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return {value:+e.value,visible:e.matches(':focus-visible'),outline:s.outline,rect:{x:r.x,y:r.y,width:r.width,height:r.height},hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e,labelledby:e.getAttribute('aria-labelledby')};});assert(m.visible&&m.hit);await p.screenshot({path:path.join(out,id+'.png')});
  const keys=[];for(const [press,value] of [['ArrowRight',initial+1],['ArrowLeft',initial],['End',max],['Home',min]]){await p.keyboard.press(press);const state=await l.evaluate(e=>({value:+e.value,crop:{...КАДР},transforms:[...document.querySelectorAll('#др-тіло .вікно img')].map(x=>x.style.transform)}));assert.equal(state.value,value);assert.equal(state.crop[key],value);assert.equal(state.transforms.length,6);assert.equal(new Set(state.transforms).size,1);keys.push({press,...state});}
  await p.keyboard.press('ArrowRight');await p.keyboard.press('Tab');await p.waitForTimeout(100);assert.equal((await p.evaluate(()=>читатиКв('кадр')))[key],min+1);controls.push({id,role:a.role.value,name:a.name.value,value:a.value.value,properties:a.properties,measured:m,keys});
 }
 await p.addScriptTag({path:'/workspace/scratch/liusterko-4944/.qa4944/node_modules/axe-core/axe.min.js'});const axe=await p.evaluate(async()=>{const r=await axe.run(document.getElementById('др-блок'),{runOnly:{type:'rule',values:['label']}});return r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}));});assert.equal(axe.length,stage==='after'?0:1);if(stage==='before')assert.equal(axe[0].targets.length,3);
 const stored=await p.evaluate(()=>читатиКв('кадр'));await p.keyboard.press('Escape');await p.waitForTimeout(400);const returnFocus=await opener.evaluate(e=>({active:document.activeElement===e,visible:!!e.getClientRects().length}));assert(returnFocus.active&&returnFocus.visible);await opener.press('Enter');await p.locator('#кд-м').waitFor();await p.waitForTimeout(400);
 const reopened=await p.evaluate(()=>({values:['кд-м','кд-x','кд-y'].map(id=>+document.getElementById(id).value),crop:{...КАДР},viewport:innerWidth,width:document.documentElement.scrollWidth}));assert.deepEqual(reopened.values,[101,1,1]);assert.deepEqual(reopened.crop,stored);assert.equal(reopened.viewport,390);assert.equal(reopened.width,390);assert.equal(errors.length,0);
 await p.locator('#кд-м').focus();await p.screenshot({path:path.join(out,'reopened-390x844.png')});const facts={stage,chromium:browser.version(),controls,axe,stored,reopened,returnFocus,errors,denied,requests,modelPhotoApiCalls:0};fs.writeFileSync(path.join(out,'facts.json'),JSON.stringify(facts,null,2));console.log(JSON.stringify({stage,names:controls.map(c=>c.name),axe,reopened,returnFocus,errors}));await ctx.close();
}
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
