const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const qa=path.resolve('.qa4943'), fixture=JSON.parse(fs.readFileSync(path.join(qa,'fixture.json'),'utf8'));
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try {
  const context=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,reducedMotion:'reduce'});
  const p=await context.newPage();let stage='before',modelCalls=0;const errors=[];
  p.on('pageerror',e=>errors.push(String(e)));
  await p.route('**/*',async r=>{
   const u=new URL(r.request().url());
   if(/anthropic|openai|1234/.test(u.href))modelCalls++;
   if(u.hostname==='library.invalid')return r.fulfill({path:path.join(qa,stage,'index.html'),contentType:'text/html'});
   if(u.pathname.includes('/pyodide/'))return r.fulfill({path:path.join(qa,'pyodide',path.basename(u.pathname))});
   if(u.pathname.includes('/fonts/webfonts/')){const file=path.join(qa,'fonts',path.basename(u.pathname));return fs.existsSync(file)?r.fulfill({path:file}):r.abort();}
   if(u.pathname.includes('/шрифти/'))return r.fulfill({path:path.resolve('шрифти',path.basename(decodeURI(u.pathname)))});
   return r.abort();
  });
  const results={fixture:fixture.kind,source:fixture.source,source_sha256:fixture.source_sha256,viewport:'390x844'};
  const snapshot=async()=>p.evaluate(async()=>{
   const d=await дб();const read=async name=>new Promise((resolve,reject)=>{const r=d.transaction(name).objectStore(name).getAll();r.onsuccess=()=>resolve(r.result);r.onerror=()=>reject(r.error);});
   return {version:d.version,stores:[...d.objectStoreNames],images:(await read('образи')).map(({час,...record})=>record),choices:await read('вердикти')};
  });
  const library=async name=>{
   await p.waitForFunction(()=>document.getElementById('е-бібліотека').style.display==='block');
   await p.waitForFunction(()=>window.pendingLibrary===0);await p.evaluate(()=>document.fonts.ready);
   await p.evaluate(()=>window.scrollTo(0,0));
   const data=await p.evaluate(()=>{
    const section=document.getElementById('е-бібліотека'), intro=section.querySelector('.вступ').innerText, rows=[...section.querySelectorAll('.біб-образ')].map(e=>e.innerText), placeholder=document.getElementById('чат-поле').placeholder;
    return {intro,rows,placeholder,terms:(intro+' '+rows.join(' ')+' '+placeholder).match(/судж\S*|вердикт\S*/gi)||[],collapsedTerms:(intro+' '+rows.join(' ')).match(/судж\S*|вердикт\S*/gi)||[],report:document.getElementById('журнал').outerHTML,overflow:document.documentElement.scrollWidth>390};
   });
   assert.equal(data.overflow,false);await p.screenshot({path:path.join(qa,stage,name+'.png')});
   await p.locator('#ші-пілюля').tap();assert.equal(await p.locator('#чат-поле').isVisible(),true);
   await p.screenshot({path:path.join(qa,stage,name+'-chat.png')});
   await p.locator('#ші-згорнути').tap();return data;
  };
  for(stage of ['before','after']){
   await p.goto('https://library.invalid/?stage='+stage+'#model_mova=none');
   await p.waitForFunction(()=>typeof document.getElementById('біб-назад').onclick==='function');
   await p.evaluate(()=>{const original=window.оновитиБібліотеку;window.pendingLibrary=0;window.оновитиБібліотеку=async function(){window.pendingLibrary++;try{return await original();}finally{window.pendingLibrary--;}};});
   await p.evaluate(()=>{ПРОФІЛЬ_СТВОРЕНО=true;режим('бібліотека');});
   if(stage==='before')results.beforeEmpty=await library('empty');
   else{
    results.persistedAfterReload=await snapshot();
    assert.deepEqual(results.persistedAfterReload,results.beforeAfterNavigation);
   }
   if(stage==='before')await p.evaluate(async fixture=>{const d=await дб();await tx(d,'образи','readwrite',s=>s.put(fixture.record,fixture.record.ключ));for(const v of fixture.verdicts)await tx(d,'вердикти','readwrite',s=>s.add(v));},fixture);
   if(stage==='before')await p.evaluate(()=>оновитиБібліотеку());
   results[stage+'Filled']=await library('filled');
   assert.equal(await p.locator('.біб-образ').count(),2);
   await p.locator('.біб-образ').first().tap();
   await p.waitForFunction(()=>РЕЖИМ==='образи'&&В[0]?.верд==='вдягну як є');
   const selected=await p.evaluate(()=>({mode:РЕЖИМ,visible:[...document.querySelectorAll('.картка')].filter(e=>!e.hidden).map(e=>e.id),verdict:В[0].верд,selected:[...document.querySelectorAll('#к-0 .ряд[data-поле="верд"] .чип.вибр')].map(e=>e.textContent),cards:П.картки}));
   assert.deepEqual(selected.visible,['к-0']);assert.equal(selected.verdict,fixture.verdicts[0].вердикт_людини);assert.equal(selected.selected.length,1);
   assert.deepEqual(selected.cards,fixture.record.П.картки);
   await p.screenshot({path:path.join(qa,stage,'opened.png')});
   await p.locator('#к-0 .ряд[data-поле="верд"] .чип.вибр').scrollIntoViewIfNeeded();
   await p.screenshot({path:path.join(qa,stage,'selected.png')});
   await p.locator('#до-бібліотеки').tap();results[stage+'Return']=await library('returned');
   assert.equal(await p.locator('.біб-образ').count(),2);
   await p.locator('#біб-назад').tap();await p.waitForFunction(()=>РЕЖИМ==='образи');
   assert.equal(await p.evaluate(()=>В[0].верд),fixture.verdicts[0].вердикт_людини);
   await p.locator('#до-бібліотеки').tap();
   await p.waitForFunction(()=>window.pendingLibrary===0);
   results[stage+'AfterNavigation']=await snapshot();results[stage+'Selected']=selected;
  }
  assert.deepEqual(results.afterSelected,results.beforeSelected);
  assert.deepEqual(results.afterAfterNavigation,results.beforeAfterNavigation);
  // Snapshot timestamps may refresh when a record is opened; compare only saved payload and choices.
  assert.deepEqual(results.afterFilled.report,results.beforeFilled.report);
  await p.evaluate(async()=>{const d=await дб();await tx(d,'образи','readwrite',s=>s.clear());await tx(d,'вердикти','readwrite',s=>s.clear());П=null;режим('бібліотека');});
  results.afterEmpty=await library('empty');
  console.log('terms',results.beforeEmpty.terms,results.beforeFilled.terms,results.afterEmpty.terms,results.afterFilled.terms);
  console.log('after empty',results.afterEmpty.intro,results.afterEmpty.placeholder);
  assert.equal(results.afterEmpty.terms.length,0);assert.equal(results.afterFilled.terms.length,0);
  assert.equal(modelCalls,0);assert.deepEqual(errors,[]);results.modelCalls=modelCalls;results.errors=errors;
  fs.writeFileSync(path.join(qa,'facts.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify({empty:[results.beforeEmpty.terms.length,results.afterEmpty.terms.length],filled:[results.beforeFilled.terms.length,results.afterFilled.terms.length],cards:2,choices:1,version:results.beforeAfterNavigation.version,modelCalls,errors}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
