const {chromium}=require('playwright');
const fs=require('fs'),path=require('path');
(async()=>{
 const root=process.cwd(),stage=process.argv[2],out=path.join(root,'.qa4944',stage);
 if(!fs.existsSync(path.join(out,'index.html')))throw new Error('Missing built '+stage+' index.html');
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true,reducedMotion:'reduce'});
 const errors=[];page.on('pageerror',e=>errors.push(String(e)));
 await page.route('**/*',r=>{
  const u=new URL(r.request().url());
  const name=decodeURIComponent(u.pathname).replace(/^\//,'')||'index.html';
  let file=u.hostname==='focus.local'?path.join(out,name):u.href.includes('/pyodide/')?path.join(root,'.qa4944/pyodide',path.basename(u.pathname)):u.href.includes('/Fixel@main/fonts/webfonts/')?path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(u.pathname)):null;
  if(file&&!fs.existsSync(file)&&u.hostname==='focus.local')file=path.join(root,name);
  return file&&fs.existsSync(file)?r.fulfill({path:file}):r.abort();
 });
 await page.goto('http://focus.local/');
 await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
 await page.addScriptTag({path:path.join(root,'.qa4944/node_modules/axe-core/axe.min.js')});
 const result={stage,base:'286b310328eb3f981e403ae9b4ddcabd667b2f97',chromium:browser.version(),axeVersion:require('./node_modules/axe-core/package.json').version,scenes:[],axe:{}};
 const focus=()=>page.evaluate(()=>({id:document.activeElement.id,tag:document.activeElement.tagName,editor:document.activeElement.dataset.редактор||document.activeElement.dataset.аркуш||null,inSheet:document.getElementById('аркуш').contains(document.activeElement),sheetHidden:document.getElementById('аркуш').hidden,outline:getComputedStyle(document.activeElement).outline}));
 const closed=async()=>{await page.locator('#аркуш').waitFor({state:'hidden'});return focus();};
 const axe=async(name,context)=>{
  result.axe[name]=await page.evaluate(async context=>{
   const a=await axe.run(context||document,{runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']}});
   return a.violations.map(v=>({id:v.id,impact:v.impact,nodes:v.nodes.map(n=>({target:n.target,summary:n.failureSummary}))}));
  },context);
 };
 await axe('home');
 await page.evaluate(()=>{ПРОФІЛЬ_СТВОРЕНО=true;режим('сценарій');});
 await page.locator('#сц-рукою-показати').tap();
 const manual={name:'manual',opened:await focus()};
 await page.screenshot({path:path.join(out,'manual.png')});
 await page.keyboard.press('Escape');manual.closed=await closed();result.scenes.push(manual);
 await axe('scenario');
 await page.locator('.ряд-паспорта[data-редактор="ред-нагода"]').tap();
 const scenario={name:'scenario',opened:await focus()};
 await page.locator('#аркуш-готово').focus();await page.keyboard.press('Tab');scenario.tabFromLast=await focus();
 await page.keyboard.press('Shift+Tab');scenario.shiftTab=await focus();
 await axe('scenario-sheet','#аркуш');
 await page.locator('#аркуш-готово').tap();scenario.closed=await closed();result.scenes.push(scenario);
 await page.screenshot({path:path.join(out,'scenario-return.png')});
 await page.locator('.ряд-паспорта[data-редактор="ред-нагода"]').focus();await page.keyboard.press('Enter');
 const keyboard={name:'keyboard-open',opened:await focus()};await page.keyboard.press('Escape');keyboard.closed=await closed();result.scenes.push(keyboard);
 await page.locator('#сц-зберегти').tap();
 const save={name:'save',opened:await focus()};
 await page.keyboard.press('Escape');save.closed=await closed();result.scenes.push(save);
 await page.locator('#пф-кнопка').tap();
 await page.evaluate(()=>document.getElementById('правий').setAttribute('inert',''));
 await page.locator('button[data-аркуш="проф-блок"]').tap();
 const profile={name:'profile',opened:await focus()};
 await page.locator('#пр-імʼя').focus();await page.keyboard.press('Tab');profile.fieldKeyboard=await focus();
 await page.locator('#аркуш-готово').focus();await page.keyboard.press('Tab');profile.tabFromLast=await focus();
 await page.keyboard.press('Shift+Tab');profile.shiftTab=await focus();
 profile.background=await page.evaluate(()=>[...document.body.children].filter(x=>x.id!=='аркуш'&&x.id!=='заслона'&&x.tagName!=='SCRIPT').map(x=>({id:x.id,tag:x.tagName,inert:x.inert})).filter(x=>x.id));
 profile.done=await page.locator('#аркуш-готово').evaluate(e=>({width:e.getBoundingClientRect().width,height:e.getBoundingClientRect().height,color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor,outline:getComputedStyle(e).outline}));
 await page.screenshot({path:path.join(out,'profile.png')});
 await axe('profile-sheet','#аркуш');
 await page.locator('#аркуш-готово').tap();profile.closed=await closed();
 profile.restored=await page.evaluate(()=>[...document.body.children].filter(x=>x.inert).map(x=>x.id));result.scenes.push(profile);
 await page.evaluate(()=>document.getElementById('правий').removeAttribute('inert'));
 await page.locator('button[data-аркуш="мір-блок"]').tap();
 const measurements={name:'measurements',opened:await focus()};
 await page.locator('#мр-зріст').focus();measurements.field=await focus();
 await page.screenshot({path:path.join(out,'measurements.png')});
 const rect=await page.locator('#аркуш').boundingBox();await page.touchscreen.tap(10,Math.max(2,rect.y-15));measurements.closed=await closed();result.scenes.push(measurements);
 await page.evaluate(()=>document.documentElement.setAttribute('data-тема','темна'));
 await page.locator('button[data-аркуш="проф-блок"]').focus();await page.keyboard.press('Enter');
 const dark={name:'dark-profile',opened:await focus()};
 dark.done=await page.locator('#аркуш-готово').evaluate(e=>({height:e.getBoundingClientRect().height,color:getComputedStyle(e).color,background:getComputedStyle(e).backgroundColor,backgroundImage:getComputedStyle(e).backgroundImage,outline:getComputedStyle(e).outline}));
 await axe('dark-profile-sheet','#аркуш');
 await page.keyboard.press('Escape');dark.closed=await closed();result.scenes.push(dark);
 await page.evaluate(()=>document.documentElement.setAttribute('data-тема','світла'));
 await page.evaluate(()=>{КОЛІР={шкіра:null,волосся:null,очі:null,кільце:null,точки:null};режим('палітра');});
 await axe('palette-empty');
 const fixture=JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4943/.qa4943/fixture.json','utf8'));
 result.cardFixture={kind:fixture.kind,source:fixture.source,source_sha256:fixture.source_sha256};
 await page.evaluate(async fixture=>{const d=await дб();await tx(d,'образи','readwrite',s=>s.put(fixture.record,fixture.record.ключ));режим('бібліотека');await оновитиБібліотеку();},fixture);
 await page.locator('.біб-образ').first().tap();await page.waitForFunction(()=>РЕЖИМ==='образи'&&!!П?.картки?.length);
 await axe('card');
 result.errors=errors;fs.writeFileSync(path.join(out,'measurements.json'),JSON.stringify(result,null,2));
 if(stage==='after'){
  const assert=require('assert/strict');
  for(const s of result.scenes){assert.equal(s.opened.inSheet,true,s.name+' opens in sheet');assert.equal(s.closed.sheetHidden,true);assert.equal(s.closed.inSheet,false);assert.notEqual(s.closed.tag,'BODY',s.name+' returns to control');}
  for(const s of result.scenes.filter(s=>s.tabFromLast)){assert.equal(s.tabFromLast.inSheet,true);assert.equal(s.shiftTab.id,'аркуш-готово');}
  assert.equal(result.scenes.find(s=>s.name==='manual').closed.editor,'ред-нагода');
  assert.equal(result.scenes.find(s=>s.name==='save').closed.id,'сц-зберегти');
  const profile=result.scenes.find(s=>s.name==='profile');assert.deepEqual(profile.restored,['правий']);
  assert.ok(profile.done.height>=44);assert.equal(result.axe['scenario-sheet'].length,0);assert.equal(result.axe['profile-sheet'].length,0);assert.deepEqual(errors,[]);
 }
 console.log(JSON.stringify(result.scenes,null,2));console.log('axe',Object.fromEntries(Object.entries(result.axe).map(([k,v])=>[k,v.map(x=>x.id)])));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
