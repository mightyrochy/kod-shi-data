// Незалежна QA композиції: власні дії/асерції. Локальна інфраструктура Pyodide і фікстура з попередніх QA.
const fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require('playwright');
const OUT=__dirname,ART='/workspace/replace4945-compose-evidence/index.html';
const HEAD='0a664f440b208a4023cbeb9a01bc4461ae37ab84';
const sha=x=>crypto.createHash('sha256').update(x).digest('hex');
const EXPECT='e3622fdfdddcbbe2d9b9f5921ce9c4d72cd64ca2604ed5713dcaadd2334d7864';
assert.equal(sha(fs.readFileSync(ART)),EXPECT);
const fixture=JSON.parse(fs.readFileSync('/workspace/replace4945-compose-evidence/fixture.json'));
const profile=JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4942/.qa4942/after/full.json'));
const result={head:HEAD,artifact:ART,artifactSHA256:EXPECT,viewport:[390,844],scope:'Лише технічна композиція: справжні Chromium/Pyodide/міст/IndexedDB, синтетичні відповіді моделі. Завершення повного збору — фактичний suffix, синтетичні контейнери рук, journal stub. Не живий добір і не фізичний телефон.',focus:[],targets:[],statuses:[],replacements:[],blocked:[],errors:[]};
const server=require('http').createServer((req,res)=>{
 const f=req.url==='/'?ART:req.url.startsWith('/pyodide/')?path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(req.url)):null;
 if(!f||!fs.existsSync(f)){res.writeHead(404);return res.end();}
 res.setHeader('Access-Control-Allow-Origin','*');
 res.setHeader('Content-Type',req.url==='/'?'text/html; charset=utf-8':req.url.endsWith('.wasm')?'application/wasm':req.url.endsWith('.js')?'application/javascript':'application/octet-stream');
 fs.createReadStream(f).pipe(res);
});
let browser,p,origin,ctx;
async function tabTo(selector,n=0){
 await p.evaluate(()=>{document.activeElement.blur();document.body.tabIndex=-1;document.body.focus();});
 let reached=false,steps=0;
 for(;steps<150;steps++){
  await p.keyboard.press('Tab');
  reached=await p.locator(selector).nth(n).evaluate(e=>e===document.activeElement);
  if(reached)break;
 }
 assert(reached,'Фактичний Tab не досяг '+selector);
 const m=await p.locator(selector).nth(n).evaluate(e=>{
  const box=e.getBoundingClientRect();
  const visual=getComputedStyle(e).opacity==='0'||box.width<=1?e.closest('label,.слот')||e:e;
  const s=getComputedStyle(visual),r=visual.getBoundingClientRect();
  return{id:e.id,tag:e.tagName,focusVisible:e.matches(':focus-visible'),active:e===document.activeElement,
   outline:s.outline,outlineStyle:s.outlineStyle,outlineWidth:s.outlineWidth,outlineColor:s.outlineColor,offset:s.outlineOffset,
   visibleRect:{x:r.x,y:r.y,width:r.width,height:r.height},visualTag:visual.tagName,visualClass:visual.className};
 });
 assert(m.focusVisible&&m.active,'Нема keyboard focus '+selector);
 assert(m.outlineStyle!=='none'&&parseFloat(m.outlineWidth)>=2,'Нема видимого outline '+selector);
 assert(m.visibleRect.width>1&&m.visibleRect.height>1,'Контур невидимого input '+selector);
 result.focus.push({selector,index:n,tabPresses:steps+1,...m});
 await p.evaluate(()=>document.body.removeAttribute('tabindex'));
 return m;
}
async function target(selector,n=0){
 const l=p.locator(selector).nth(n);await l.scrollIntoViewIfNeeded();
 const m=await l.evaluate(e=>{
  if(e.type==='file'&&getComputedStyle(e).opacity==='0')e=e.closest('label')||e;
  const r=e.getBoundingClientRect();
  return{width:r.width,height:r.height,points:[[-11,-11],[11,-11],[-11,11],[11,11],[0,0]].map(([x,y])=>{const hit=document.elementFromPoint(r.x+r.width/2+x,r.y+r.height/2+y);return hit===e||e.contains(hit);})};
 });
 assert(m.width>=24&&m.height>=24&&m.points.every(Boolean),'Недоступна зона дотику '+selector);
 result.targets.push({selector,index:n,...m});
}
async function aria(){
 const m=await p.evaluate(()=>({chips:[...document.querySelectorAll('#картки .чип')].map(e=>({selected:e.classList.contains('вибр'),pressed:e.getAttribute('aria-pressed')})),
  statuses:['зб-статус','зб-оголошення'].map(id=>{const e=$(id);return{id,role:e.getAttribute('role'),live:e.getAttribute('aria-live'),atomic:e.getAttribute('aria-atomic')};})}));
 assert(m.chips.every(x=>x.pressed===String(x.selected)),'ARIA чипів відрізняється від вибору');
 assert(m.statuses.every(x=>x.role==='status'&&x.live==='polite'&&x.atomic==='true'),'ARIA статусів');
 return m;
}
async function install(pos,mode){
 await p.evaluate(async({fixture,pos,mode})=>{
  П=structuredClone(fixture);Object.keys(В).forEach(k=>delete В[k]);НЕ_ЦЯ_П.clear();
  ЗАМІНУ_ВЖЕ_РОЗУМІЄ_П=false;
  ЗБ={картки:П.картки,діагноз:[],готово:true,успіх:true,стадії:[],етап:[]};
  const v=відповідь(pos);v.коментар='SYNTHETIC: мої слова залишаються';v.для_мене='mine';
  рендер();window.показатиОбраз(pos,true);await window.зберегтиОбраз();
  window.qaCalls=[];window.qaRelease=null;
  модельП=async prompt=>{
   const body=JSON.parse(prompt),call={prompt:body};qaCalls.push(call);
   if(mode==='error')throw Error('SYNTHETIC відмова транспорту');
   if(mode==='delay')await new Promise(resolve=>{window.qaRelease=resolve;});
   const response=body.pool?{version:'1',outfits:[{id:'o1',items:[body.pool.at(-1).n]}]}:
    {items:[{name:'Ботильйони',details:'Гладка шкіра',slot:'shoes',color_hex:'#553322',own:null,worn:true}]};
   call.response=response;return JSON.stringify(response);
  };
 },{fixture,pos,mode});
 await p.waitForFunction(()=>[...document.querySelectorAll('.картка:not([hidden]) img')].every(i=>i.complete||i.loading==='lazy'));
 await p.waitForTimeout(350);
 await p.evaluate(async pos=>{
  window.qaNodes=П.картки.map((_,i)=>$('к-'+i));
  window.qaBefore={cards:П.картки.map(x=>JSON.stringify(x)),dom:П.картки.map((_,i)=>$('к-'+i).innerHTML),snapshot:JSON.stringify(П.знімок),choices:JSON.stringify(В),pager:$('пейджер').innerHTML,
   saved:(await tx(await дб(),'образи','readonly',s=>s.get(П.прогін))).П,verdicts:(await усіВердикти()).length};
 },pos);
}
async function replace(name,pos,mode,keyboard){
 await install(pos,mode);const index=pos<2?2:0,selector='#к-'+pos+' button.замін';
 await target(selector,index);
 const beforeAria=await aria();
 if(keyboard){await tabTo(selector,index);await p.screenshot({path:OUT+'/replacement-keyboard-focus.png'});}
 const preAction=await p.evaluate(()=>({cards:П.картки.map(x=>JSON.stringify(x)),dom:П.картки.map((_,i)=>$('к-'+i).innerHTML)}));
 if(keyboard)await p.keyboard.press('Enter');else await p.locator(selector).nth(index).tap();
 let pending=null;
 if(mode==='delay'){
  await p.waitForFunction(()=>typeof qaRelease==='function');
  pending=await p.evaluate(pos=>({buttons:[...$('к-'+pos).querySelectorAll('button.замін')].map(x=>({disabled:x.disabled,pressed:x.getAttribute('aria-pressed')})),oldNodes:$('к-'+pos).querySelectorAll('.відп-заміни').length,text:$('к-'+pos).textContent,header:$('обр-не-ця').textContent,headerVisible:getComputedStyle($('обр-не-ця')).display!=='none',calls:qaCalls.length}),pos);
  assert(pending.buttons.every(x=>x.disabled));assert.equal(pending.calls,1);assert.equal(pending.oldNodes,0);
  assert(!pending.text.includes('коли збиратиму образи знову'));assert(pending.headerVisible&&pending.header.includes('Повернути всі'));
  await p.screenshot({path:OUT+'/replacement-pending.png'});
  await p.evaluate(()=>qaRelease());
 }
 await p.waitForFunction(pos=>!ЗАМІНИ_П.has(П.картки[pos]),pos);
 const r=await p.evaluate(async pos=>{
  const saved=(await tx(await дб(),'образи','readonly',s=>s.get(П.прогін))).П;
  return{before:qaBefore,cards:П.картки.map(x=>JSON.stringify(x)),dom:П.картки.map((_,i)=>$('к-'+i).innerHTML),nodesSame:П.картки.map((_,i)=>qaNodes[i]===$('к-'+i)),
   saved,calls:qaCalls,snapshot:JSON.stringify(П.знімок),choices:JSON.parse(JSON.stringify(В)),pager:$('пейджер').innerHTML,
   stage:П.картки[pos].етапи?.заміни?.at(-1),verdicts:(await усіВердикти()).length,marks:[...НЕ_ЦЯ_П],
   text:$('к-'+pos).textContent,oldNodes:$('к-'+pos).querySelectorAll('.відп-заміни').length,
   status:$('к-'+pos).querySelector('.не-ця-рядок')?.textContent,statusHidden:$('к-'+pos).querySelector('.не-ця-рядок')?.hidden,
   focus:{tag:document.activeElement.tagName,id:document.activeElement.id},buttons:[...$('к-'+pos).querySelectorAll('button.замін')].map(x=>x.disabled)};
 },pos);
 const before=JSON.parse(r.before.cards[pos]),after=JSON.parse(r.cards[pos]);
 r.checks={otherCards:r.cards.every((x,i)=>i===pos||x===r.before.cards[i]),otherDOM:r.dom.every((x,i)=>i===pos||x===preAction.dom[i]),
  otherIDB:r.saved.картки.every((x,i)=>i===pos||JSON.stringify(x)===r.before.cards[i]),
  fixedItems:after.речі.every((x,i)=>i===index||JSON.stringify(x)===JSON.stringify(before.речі[i])),
  stageSaved:JSON.stringify(r.saved.картки[pos].етапи.заміни.at(-1))===JSON.stringify(r.stage),
  snapshot:r.snapshot===r.before.snapshot,saveSnapshot:JSON.stringify(r.saved.знімок)===r.before.snapshot,pager:r.pager===r.before.pager,
  sameNodes:r.nodesSame.every(Boolean),noAutoVerdict:r.verdicts===r.before.verdicts,buttons:r.buttons.every(x=>!x)};
 r.preAction=preAction; r.preActionNotes='Порівняння DOM починається після фактичного Tab і ДО Enter/tap. У попередній спробі Tab додав порожній style до полів інших карток; жодної зміни після Enter не було.';r.name=name;result.replacements.push(r);
 if(!r.checks.otherDOM){fs.writeFileSync(OUT+'/dom-difference.json',JSON.stringify({name,pos,before:r.before.dom,preAction:preAction.dom,after:r.dom},null,2)+'\n');}
 assert(Object.values(r.checks).every(Boolean),name+': '+JSON.stringify(r.checks));
 assert.equal(r.calls.length,1);assert.equal(r.oldNodes,0);assert(!r.text.includes('коли збиратиму образи знову'));
 assert.equal(after.речі[index].слот,before.речі[index].слот);
 for(const call of r.calls){assert.equal(call.prompt.replacement.slot,'shoes');assert.deepEqual(call.prompt.replacement.fixed_outfit.map(x=>x.name),before.речі.filter((_,i)=>i!==index).map(x=>x.назва));}
 assert.equal(after.речі[index].id!==before.речі[index].id,mode!=='error');
 assert(r.stage.закінчено>=r.stage.почато&&r.stage.застаріло===false);
 if(mode==='error'){assert(r.status.trim()&&!r.statusHidden);}
 for(const[k,v]of Object.entries(JSON.parse(r.before.choices)[pos]))if(!['замінити','зміна'].includes(k))assert.deepEqual(r.choices[pos][k],v);
 r.ariaBefore=beforeAria;r.ariaAfter=await aria();r.pending=pending;r.name=name;r.pos=pos;r.keyboard=keyboard;
 r.beforeDOMHashes=r.before.dom.map(sha);r.preActionDOMHashes=preAction.dom.map(sha);r.afterDOMHashes=r.dom.map(sha);delete r.preAction.dom;delete r.before.dom;delete r.dom;
 if(keyboard){await p.keyboard.press('Tab');r.nextTab=await p.evaluate(()=>({tag:document.activeElement.tagName,id:document.activeElement.id,text:document.activeElement.textContent.slice(0,100)}));}
 await p.locator('#к-'+pos).scrollIntoViewIfNeeded();await p.screenshot({path:OUT+'/'+name+'.png'});
 console.log('PASS',name,JSON.stringify(r.checks));
}
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));origin='http://127.0.0.1:'+server.address().port;
 browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});result.chromium=browser.version();
 ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});p=await ctx.newPage();p.setDefaultTimeout(45000);
 p.on('pageerror',e=>result.errors.push(String(e)));
 await p.route('**/*',r=>{
  const u=new URL(r.request().url());if(u.origin===origin)return r.continue();
  if(u.href.includes('/pyodide/'))return r.fulfill({status:302,headers:{location:origin+'/pyodide/'+path.basename(u.pathname),'access-control-allow-origin':'*'}});
  const font=u.href.includes('/Fixel@main/fonts/webfonts/')?path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(u.pathname)):null;
  if(font&&fs.existsSync(font))return r.fulfill({path:font});
  result.blocked.push({method:r.request().method(),url:u.href});return r.abort();
 });
 await p.goto(origin+'/#model_mova=off&vybir=list');await p.waitForFunction(()=>typeof $('сц-рукою-показати').onclick==='function');
 result.pyodide=await p.evaluate(async origin=>{ДЗЕРКАЛА_П[0][1]=origin+'/pyodide/';await підняти_міст_показу();return pyodide_показу.version},origin);
 await p.evaluate(profile=>{
  window.qaUnhandled=[];addEventListener('unhandledrejection',e=>qaUnhandled.push(String(e.reason)));
  КОЛІР=profile.colors;for(const[id,v]of[['мр-зріст',168],['мр-плечі',98],['мр-груди',92],['мр-талія',74],['мр-стегна',99]])$(id).value=v;
  ПАСПОРТ_П={джерело:'модель',нагода:'робота',місце:'офіс',джерело_полів:{}};застосуватиПаспортДоЕкрана(ПАСПОРТ_П);ПРОФІЛЬ_СТВОРЕНО=true;режим('сценарій');ШІ_РОЗГОРНУТО=true;малюватиЧатП();
 },profile);
 if(!process.env.QA_ONLY_REPLACEMENT){
 await p.evaluate(()=>document.fonts.ready);
 await p.evaluate(f=>{П=structuredClone(f);Object.keys(В).forEach(k=>delete В[k]);НЕ_ЦЯ_П.clear();рендер();},fixture);await p.waitForTimeout(700);const raw=await p.evaluate(()=>П.картки.map((_,i)=>$('к-'+i).innerHTML));
 await p.screenshot({path:OUT+'/instrumentation-default-caret.png'});
 const after=await p.evaluate(()=>П.картки.map((_,i)=>$('к-'+i).innerHTML));
 result.screenshotEffect={raw,after,onlyEmptyStyle:after.every((x,i)=>x.replaceAll(' style=""','')===raw[i].replaceAll(' style=""',''))};
 assert(result.screenshotEffect.onlyEmptyStyle);assert(after.some((x,i)=>x!==raw[i]));
 result.completionSuffix=await p.evaluate(()=>{const s=зібратиОбразиП.toString(),i=s.indexOf('const секунд = Math.round((Date.now()-почато)/1000);');return s.slice(i,s.lastIndexOf('}'));});
 const failure=await p.evaluate(async suffix=>{
  ЗБ={картки:Array.from({length:4},(_,i)=>({рука:String(i+1),збій:true,речі:[]})),стадії:[null,null,null,null],етап:[4,4,4,4],діагноз:['SYNTHETIC all-four-failed visual capture'],готово:false,успіх:false};П.картки=ЗБ.картки;
  записатиЗбоїРукП=async()=>{};режим('очікування');малюватиПоступП();
  const finish=eval('(async()=>{const ст=$("зб-статус"),кн=$("зб-пуск"),далі=$("зб-зібрати"),почато=Date.now();try{'+suffix+'})');await finish();
  return{field:$('зб-статус').textContent,live:$('зб-оголошення').textContent,ready:ЗБ.готово,success:ЗБ.успіх};
 },result.completionSuffix);
 assert(failure.field.trim()&&failure.field===failure.live&&!failure.success&&failure.ready);
 await p.waitForTimeout(700);
 result.visualFailure={...failure,...await p.locator('#зб-статус').evaluate(e=>{let opacity=1;for(let a=e;a;a=a.parentElement)opacity*=Number(getComputedStyle(a).opacity);const r=e.getBoundingClientRect();return{opacity,display:getComputedStyle(e).display,rect:{width:r.width,height:r.height}};})};
 assert(result.visualFailure.opacity===1&&result.visualFailure.rect.width>0);
 await p.screenshot({path:OUT+'/all-four-failed-settled.png',caret:'initial'});
 }
 result.unhandled=await p.evaluate(()=>qaUnhandled);result.modelPOST=result.blocked.filter(x=>x.method==='POST').length;
 assert.equal(result.errors.length,0);assert.equal(result.unhandled.length,0);assert.equal(result.modelPOST,0);
 assert.equal(sha(fs.readFileSync(ART)),EXPECT);result.pass=true;
})().catch(e=>{result.failure=String(e.stack||e);console.error(e);process.exitCode=1;}).finally(async()=>{
 fs.writeFileSync(OUT+'/visual-status.json',JSON.stringify(result,null,2)+'\n');if(browser)await browser.close();await new Promise(r=>server.close(r));
});
