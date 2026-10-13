const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict');
(async()=>{
 const root=process.cwd(),stage=process.argv[2],out=path.join(root,'.qa5090',stage),res={stage,scenes:[],errors:[],modelApiCalls:0};
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});res.chromium=browser.version();
 try{
  for(const scene of ['сценарій','порожня-палітра','архівна-картка']){
   const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true,reducedMotion:'reduce'});
   page.on('pageerror',e=>res.errors.push(String(e)));
   await page.route('**/*',r=>{const u=new URL(r.request().url()),name=decodeURIComponent(u.pathname).replace(/^\//,'');let file;
    if(u.hostname==='probe.invalid')file=path.join(name.startsWith('шрифти/')?root:out,name||'index.html');
    else if(u.href.includes('/pyodide/'))file=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(name));
    else if(u.href.includes('/Fixel@main/fonts/webfonts/'))file=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(name));
    else if(r.request().method()==='POST')res.modelApiCalls++;
    return file&&fs.existsSync(file)?r.fulfill({path:file}):r.abort();});
   await page.goto('https://probe.invalid/');await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
   await page.evaluate(()=>{ПРОФІЛЬ_СТВОРЕНО=true;режим('сценарій')});
   if(scene==='порожня-палітра')await page.evaluate(()=>{КОЛІР={шкіра:null,волосся:null,очі:null};режим('палітра')});
   if(scene==='архівна-картка'){
    const fixture=JSON.parse(fs.readFileSync(path.join(root,'.qa5090/media/архівна_фікстура.json')));res.fixture={kind:fixture.kind,source:fixture.source,source_sha256:fixture.source_sha256};
    await page.evaluate(async f=>{const d=await дб();await tx(d,'образи','readwrite',s=>s.put(f.record,f.record.ключ));режим('бібліотека');await оновитиБібліотеку()},fixture);
    await page.locator('.біб-образ').first().tap();await page.waitForFunction(()=>РЕЖИМ==='образи'&&!!П?.картки?.length);
   }
   await page.evaluate(()=>document.fonts.ready);await page.waitForTimeout(350);
   const cdp=await page.context().newCDPSession(page);await cdp.send('Accessibility.enable');const doc=await cdp.send('DOM.getDocument'),node=await cdp.send('DOM.querySelector',{nodeId:doc.root.nodeId,selector:'#вк-оцінка'}),ax=await cdp.send('Accessibility.getPartialAXTree',{nodeId:node.nodeId,fetchRelatives:false});
   const facts={scene,accessibleName:ax.nodes[0].name.value,role:ax.nodes[0].role.value,dom:await page.locator('#вк-оцінка').evaluate(e=>({visible:e.innerText,title:e.title,aria:e.getAttribute('aria-label'),rect:e.getBoundingClientRect().toJSON()}))};
   await page.addScriptTag({path:'/workspace/scratch/liusterko-4944/.qa4944/node_modules/axe-core/axe.min.js'});
   facts.axe=await page.evaluate(async()=>{const a=await axe.run(document,{runOnly:{type:'rule',values:['label-content-name-mismatch']}});return {version:axe.version,violations:a.violations.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)})),incomplete:a.incomplete.map(v=>({id:v.id,targets:v.nodes.map(n=>n.target)}))}});
   await page.screenshot({path:path.join(out,scene+'.png')});
   await page.evaluate(()=>{window.trusted5090=[];$('вк-оцінка').addEventListener('click',e=>trusted5090.push({trusted:e.isTrusted,type:e.pointerType||'keyboard'}))});
   facts.keyboard=[];
   for(let i=0;i<120;i++){await page.keyboard.press('Tab');const id=await page.evaluate(()=>document.activeElement.id);facts.keyboard.push(id);if(id==='вк-оцінка')break;}
   assert.equal(facts.keyboard.at(-1),'вк-оцінка');await page.keyboard.press('Enter');facts.enter=await page.evaluate(()=>({mode:РЕЖИМ,events:trusted5090.slice()}));assert.equal(facts.enter.mode,'оцінка');assert(facts.enter.events.at(-1).trusted);
   await page.evaluate(scene=>режим(scene==='порожня-палітра'?'палітра':scene==='архівна-картка'?'образи':'сценарій'),scene);facts.preTouchMode=await page.evaluate(()=>РЕЖИМ);await page.locator('#вк-оцінка').tap();facts.touch=await page.evaluate(()=>({mode:РЕЖИМ,events:trusted5090.slice()}));assert.equal(facts.touch.mode,'оцінка');assert(facts.touch.events.at(-1).trusted);
   if(scene==='сценарій'){
    await page.locator('#вк-сценарій').tap();await page.locator('#сц-рукою-показати').tap();await page.keyboard.press('Escape');
    const opener=page.locator('.ряд-паспорта[data-редактор="ред-нагода"]');await opener.tap();
    facts.modal=await page.evaluate(()=>({inside:$('аркуш').contains(document.activeElement),inert:[...document.body.children].filter(e=>e.id&&e.inert).map(e=>e.id)}));assert(facts.modal.inside);
    await page.locator('#аркуш-готово').focus();await page.keyboard.press('Tab');facts.modal.tabInside=await page.evaluate(()=>$('аркуш').contains(document.activeElement));assert(facts.modal.tabInside);await page.keyboard.press('Shift+Tab');assert.equal(await page.evaluate(()=>document.activeElement.id),'аркуш-готово');
    await page.keyboard.press('Escape');facts.modal.closed=await page.evaluate(()=>({hidden:$('аркуш').hidden,editor:document.activeElement.dataset.редактор,inert:[...document.body.children].filter(e=>e.id&&e.inert).map(e=>e.id)}));assert(facts.modal.closed.hidden);assert.equal(facts.modal.closed.editor,'ред-нагода');assert.deepEqual(facts.modal.closed.inert,[]);
   }
   assert.equal(facts.dom.visible,'Оцінити');assert.equal(facts.dom.title,'Оціни мій образ');assert.equal(facts.accessibleName,stage==='before'?'Оціни мій образ':'Оцінити');assert.equal(facts.axe.violations.length,stage==='before'?1:0);
   res.scenes.push(facts);await page.close();
  }
  assert.deepEqual(res.errors,[]);assert.equal(res.modelApiCalls,0);
 }finally{await browser.close();fs.writeFileSync(path.join(out,'факти.json'),JSON.stringify(res,null,2))}
 console.log(JSON.stringify(res,null,2));
})().catch(e=>{console.error(e);process.exitCode=1});
