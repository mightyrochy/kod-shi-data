const fs=require('fs'),path=require('path'),assert=require('assert');
const {chromium}=require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const out='/workspace/scratch/qa1058-independent';
const author='/workspace/scratch/4944-aa-next-evidence';
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});try{
for(const stage of ['before','after']){
 const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const page=await context.newPage(),errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.route('**/*',route=>{const u=new URL(route.request().url()),p=decodeURIComponent(u.pathname);let file;
 if(u.hostname==='independent.local')file=p.startsWith('/шрифти/')?path.join('/workspace/scratch/4944-next-current',p):path.join(author,stage,p==='/'?'index.html':p);
 else if(u.href.includes('/pyodide/'))file=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(p));
 else if(u.href.includes('/Fixel@main/fonts/webfonts/'))file=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(p));
 if(file&&fs.existsSync(file))return route.fulfill({path:file});requests.push({url:u.href,method:route.request().method()});return route.abort();});
 await page.goto('http://independent.local');await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
 const record=JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4943/.qa4943/fixture.json')).record;
 await page.evaluate(async r=>{const c=document.createElement('canvas');c.width=300;c.height=450;const g=c.getContext('2d');g.fillStyle='#eee4cf';g.fillRect(0,0,300,450);g.fillStyle='#964b62';g.fillRect(85,65,130,250);g.fillStyle='#344e59';g.fillRect(45,330,210,70);r.П.картки[0].картинка=c.toDataURL();ПРОФІЛЬ_СТВОРЕНО=true;const db=await дб();await tx(db,'образи','readwrite',s=>s.put(r,r.ключ));режим('бібліотека');await оновитиБібліотеку();},record);
 await page.locator('.біб-образ').first().tap();const image=page.locator('.полотно img.образ').first();await image.waitFor();await image.scrollIntoViewIfNeeded();await page.evaluate(()=>document.fonts.ready);
 const cdp=await context.newCDPSession(page);await cdp.send('Accessibility.enable');
 async function ax(sel){const d=await cdp.send('DOM.getDocument');const n=await cdp.send('DOM.querySelector',{nodeId:d.root.nodeId,selector:sel});const t=await cdp.send('Accessibility.getPartialAXTree',{nodeId:n.nodeId,fetchRelatives:false});return t.nodes.map(n=>({role:n.role?.value,name:n.name?.value,ignored:n.ignored}));}
 const opener=stage==='after'?page.locator('.перегляд-відкрити').first():image;
 const baseline=await opener.evaluate(e=>{const r=e.getBoundingClientRect();return {role:e.tagName,tabIndex:e.tabIndex,name:e.getAttribute('aria-label'),rect:{x:r.x,y:r.y,width:r.width,height:r.height},width:innerWidth,scrollWidth:document.documentElement.scrollWidth};});
 const openerAX=await ax(stage==='after'?'.перегляд-відкрити':'.полотно img.образ');
 await page.screenshot({path:path.join(out,stage,'card.png')});const activations=[];
 for(const key of ['Enter','Space']){await opener.focus();await page.keyboard.press(key);const opened=await page.locator('#перегляд').isVisible();activations.push({key,opened});if(opened)await page.keyboard.press('Escape');}
 let focus=null;if(stage==='after'){await opener.focus();await page.keyboard.press('Shift+Tab');await page.keyboard.press('Tab');focus=await opener.evaluate(e=>({active:document.activeElement===e,visible:e.matches(':focus-visible'),outline:getComputedStyle(e).outline}));await page.screenshot({path:path.join(out,stage,'keyboard-focus.png')});}
 await image.tap();const dialogAX=await ax('#перегляд');const focused=await page.locator('#перегляд button').evaluate(e=>document.activeElement===e);await page.screenshot({path:path.join(out,stage,'dialog.png')});const tabs=[];
 for(const key of ['Tab','Shift+Tab','Tab','Shift+Tab','Tab']){await page.keyboard.press(key);tabs.push({key,inside:await page.evaluate(()=>!!document.activeElement.closest('#перегляд'))});}
 await page.keyboard.press('Escape');const restored=await opener.evaluate(e=>document.activeElement===e);const exits=[];
 if(stage==='after')for(const method of ['Escape','button','image','backdrop']){
 await page.evaluate(()=>{document.getElementById('бік').setAttribute('inert','qa-original');document.body.style.overflow='clip';});
 const original=await page.evaluate(()=>[...document.body.children].map(e=>[e.tagName,e.id,e.getAttribute('inert')]));
 await image.tap();const allInert=await page.evaluate(()=>[...document.body.children].filter(e=>e.id!=='перегляд'&&!['STYLE','SCRIPT'].includes(e.tagName)).every(e=>e.hasAttribute('inert')));
 if(method==='Escape')await page.keyboard.press('Escape');else if(method==='button')await page.locator('#перегляд button').tap();else if(method==='image')await page.locator('#перегляд img').tap();else await page.locator('#перегляд').tap({position:{x:4,y:4}});
 const actual=await page.evaluate(()=>({visible:!document.getElementById('перегляд').hidden,overflow:document.body.style.overflow,inert:[...document.body.children].map(e=>[e.tagName,e.id,e.getAttribute('inert')]),active:document.activeElement.className,srcRemoved:!document.querySelector('#перегляд img').hasAttribute('src')}));
 assert.deepEqual(actual.inert,original);assert.equal(actual.overflow,'clip');assert.equal(actual.visible,false);assert.equal(actual.active,'перегляд-відкрити');assert(actual.srcRemoved);assert(allInert);exits.push({method,allInert,restored:true});
 await page.evaluate(()=>{document.getElementById('бік').removeAttribute('inert');document.body.style.overflow='';});}
 await page.addScriptTag({path:'/workspace/scratch/liusterko-4944/.qa4944/node_modules/axe-core/axe.min.js'});await image.tap();
 const axe=await page.evaluate(async()=>{const r=await axe.run(document.getElementById('перегляд'),{runOnly:{type:'rule',values:['aria-dialog-name','button-name','aria-valid-attr-value','aria-allowed-attr']}});return {violations:r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>v.id)};});await page.keyboard.press('Escape');
 const facts={stage,browser:browser.version(),baseline,openerAX,dialogAX,activations,focus,focused,tabs,restored,exits,axe,errors,blocked:requests};
 fs.writeFileSync(path.join(out,stage,'facts.json'),JSON.stringify(facts,null,2));console.log(JSON.stringify({stage,activations,dialogAX,tabs,focus,restored,exits,axe,errors}));
 assert.equal(errors.length,0);assert.equal(baseline.scrollWidth,390);
 if(stage==='after'){assert(activations.every(a=>a.opened));assert(tabs.every(t=>t.inside));assert(restored&&focused&&focus.active&&focus.visible);assert.equal(axe.violations.length,0);assert.equal(dialogAX[0].role,'dialog');assert.equal(dialogAX[0].name,'Образ на весь екран');}
 else {assert(activations.every(a=>!a.opened));assert(tabs.some(t=>!t.inside));}
 await context.close();
}
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
