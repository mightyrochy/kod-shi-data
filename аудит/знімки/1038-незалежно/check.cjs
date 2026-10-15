const {chromium}=require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const fs=require('fs'),path=require('path'),assert=require('assert');
const root='/workspace/scratch/qa1038-independent';
const fixture=JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4943/.qa4943/fixture.json'));
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try {for(const stage of ['before','after']){
  const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const page=await ctx.newPage();page.setDefaultTimeout(60000);
  const errors=[],blocked=[];let chooserCount=0;page.on('pageerror',e=>errors.push(String(e)));page.on('filechooser',()=>chooserCount++);
  await page.route('**/*',async route=>{
   const url=new URL(route.request().url()),p=decodeURIComponent(url.pathname);let file;
   if(url.hostname==='independent.local')file=p.startsWith('/шрифти/')?path.join('/workspace/scratch/4944-next-current',p):path.join(root,stage,p==='/'?'index.html':p);
   else if(url.href.includes('/pyodide/'))file=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(p));
   else if(url.href.includes('/Fixel@main/fonts/webfonts/'))file=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(p));
   if(file&&fs.existsSync(file))await route.fulfill({path:file});else {blocked.push(url.href);await route.abort();}
  });
  await page.goto('http://independent.local/');
  await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
  await page.evaluate(async f=>{ПРОФІЛЬ_СТВОРЕНО=true;const db=await дб();await tx(db,'образи','readwrite',s=>s.put(f.record,f.record.ключ));режим('бібліотека');await оновитиБібліотеку();},fixture);
  await page.locator('.біб-образ').first().tap();await page.waitForFunction(()=>РЕЖИМ==='образи'&&П.картки.length>0);
  const summary=page.locator('#к-0 details summary').filter({hasText:'Або додати картинку вручну'});
  await summary.tap();await page.locator('#кф-0').scrollIntoViewIfNeeded();await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(650);
  await summary.focus();await page.keyboard.press('Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'кф-0');
  await page.screenshot({path:path.join(root,stage,'focus-390x844.png')});
  const measured=await page.locator('#кф-0').evaluate(e=>{const r=e.getBoundingClientRect(),c=getComputedStyle(e);return {html:e.outerHTML,active:document.activeElement.id,label:e.getAttribute('aria-label'),outline:c.outline,focusVisible:e.matches(':focus-visible'),box:{x:r.x,y:r.y,width:r.width,height:r.height},viewport:innerWidth,scrollWidth:document.documentElement.scrollWidth,hit:document.elementFromPoint(r.x+r.width/2,r.y+r.height/2)===e};});
  await page.addScriptTag({path:'/workspace/scratch/liusterko-4944/.qa4944/node_modules/axe-core/axe.min.js'});
  const axeResult=await page.evaluate(async()=>{const r=await axe.run(document.getElementById('кф-0'),{runOnly:{type:'rule',values:['label']}});return {violations:r.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),incomplete:r.incomplete.map(v=>v.id)};});
  const cdp=await ctx.newCDPSession(page);await cdp.send('Accessibility.enable');const dom=await cdp.send('DOM.getDocument');const node=await cdp.send('DOM.querySelector',{nodeId:dom.root.nodeId,selector:'#кф-0'});const ax=await cdp.send('Accessibility.getPartialAXTree',{nodeId:node.nodeId,fetchRelatives:false});
  await page.keyboard.press('Shift+Tab');const backward=await summary.evaluate(e=>document.activeElement===e);await page.keyboard.press('Tab');
  const chooserPromise=page.waitForEvent('filechooser');await page.keyboard.press('Enter');const chooser=await chooserPromise;const multiple=chooser.isMultiple();await chooser.setFiles([]);
  const final={stage,chromium:browser.version(),measured,axe:axeResult,ax:ax.nodes.map(n=>({role:n.role?.value,name:n.name?.value,ignored:n.ignored,sources:n.name?.sources})),shiftTabSummary:backward,chooserCount,multiple,errors,blocked,modelPhotoApiCalls:0,fixture:{kind:fixture.kind,source:fixture.source,sha256:fixture.source_sha256}};
  assert(measured.focusVisible&&measured.hit&&measured.box.width>=24&&measured.box.height>=24&&measured.viewport===390&&measured.scrollWidth===390&&backward&&chooserCount===1&&!multiple&&!errors.length);
  assert.equal(axeResult.violations.length,stage==='before'?1:0);
  if(stage==='after')assert(ax.nodes.some(n=>n.name?.value==='Картинка образу з телефона'));
  fs.writeFileSync(path.join(root,stage,'facts.json'),JSON.stringify(final,null,2));console.log(JSON.stringify(final));await ctx.close();
 }} finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
