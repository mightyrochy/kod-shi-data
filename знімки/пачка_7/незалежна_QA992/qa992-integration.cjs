const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert');
const OUT='/tmp/qa992-integration';fs.mkdirSync(OUT,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
 const ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true}),p=await ctx.newPage();const network=[];
 await p.route('**/*',r=>{if(r.request().url().split('#')[0]==='http://qa.local/')return r.fulfill({body:fs.readFileSync('/tmp/pachka-1310-3-full.html'),contentType:'text/html'});network.push({url:r.request().url(),method:r.request().method()});return r.abort()});
 await p.addInitScript(()=>{window.__recs=[];window.__events=[];window.SpeechRecognition=class{constructor(){__recs.push(this)}start(){}stop(){this.stops=(this.stops||0)+1}};for(const type of ['input','pointerdown','touchstart','focus'])document.addEventListener(type,e=>{if(e.target.tagName==='TEXTAREA')__events.push({type,trusted:e.isTrusted,id:e.target.id})},true)});
 await p.goto('http://qa.local/#т=синтетичний_для_локальної_проби');await p.waitForFunction(()=>!!$('чат-мікрофон').onclick);
 await p.evaluate(()=>{П={картки:[{рука:'1',речі:[],знахідки:[],питання:[],мітки:[],підпис:'Прогулянка',текст:'Зручний образ для прогулянки.'}]};$('картки').appendChild(рендерКартку(0))});
 const facts=[];
 const emit=async(i,parts,final=false)=>p.evaluate(({i,parts,final})=>__recs[i].onresult({resultIndex:0,results:parts.map(transcript=>Object.assign([{transcript}],{isFinal:final}))}),{i,parts,final});
 const callback=async(i,type,error)=>p.evaluate(({i,type,error})=>__recs[i][type](error?{error}:undefined),{i,type,error});
 for(const field of ['чат-поле','ком-0']){
  const mic=field==='чат-поле'?'чат-мікрофон':'мік-ком-0',note=field==='чат-поле'?'чат-голос':'голос-ком-0';
  await p.evaluate(field=>{режим(field==='чат-поле'?'сценарій':'образи');ШІ_РОЗГОРНУТО=true;малюватиЧатП()},field);
  const el=p.locator('#'+field),button=p.locator('#'+mic);
  const state=()=>p.evaluate(({field,mic,note})=>({value:$(field).value,stored:field==='чат-поле'?$('чат-поле').value.trim():відповідь(0).коментар,marker:field==='чат-поле'?ЧАТ_ГОЛОСОМ_П:відповідь(0).коментар_голосом,pressed:$(mic).getAttribute('aria-pressed'),note:$(note).textContent,selection:[$(field).selectionStart,$(field).selectionEnd],humans:ЧАТ_П.filter(x=>x.хто==='людина').length}),{field,mic,note});
  const input=async text=>{await el.tap();await el.press('ControlOrMeta+A');await el.press('Backspace');if(text)await p.keyboard.insertText(text)};
  const start=async()=>{await button.tap();return p.evaluate(()=>__recs.length-1)};
  await input('');const old=await start();await emit(old,['перші','перші слова','перші слова далі']);
  assert.equal((await state()).pressed,'true');assert.equal((await state()).marker,false);
  await el.evaluate(e=>e.focus());assert.equal((await state()).pressed,'true','програмний focus');
  await el.tap();assert.equal((await state()).pressed,'false','довірений дотик');
  await el.press('Home');for(let n=0;n<5;n++)await el.press('Shift+ArrowRight');await p.keyboard.insertText('виправлені');
  const edited=await state();assert.equal(edited.value,'виправлені слова далі');
  await emit(old,['старі слова','далі','далі'],true);await callback(old,'onend');await callback(old,'onerror','network');assert.deepEqual(await state(),edited,'правка і caret пережили старі callbacks');
  await el.scrollIntoViewIfNeeded();await p.screenshot({path:OUT+'/'+field+'-правка.png'});
  const newer=await start();await emit(newer,['додала','ще']);const active=await state();assert.equal(active.value,'виправлені слова далі додала ще');
  await emit(old,['давня сесія'],true);await callback(old,'onend');await callback(old,'onerror','network');assert.deepEqual(await state(),active,'стара сесія не втручається в нову');
  await button.tap();assert.equal((await state()).marker,true);await emit(newer,['додала','ще останнє'],true);assert.equal((await state()).value,'виправлені слова далі додала ще останнє');await callback(newer,'onend');
  await input('');const pending=await start();await emit(pending,['перші']);await button.tap();await input('Правка після зупинки');const stopped=await state();await emit(pending,['перші','перші слова далі'],true);await emit(pending,['перші','перші слова далі','перші слова далі'],true);await callback(pending,'onerror','network');await callback(pending,'onend');assert.deepEqual(await state(),stopped,'правка між stop і final');
  const broken=await start();await emit(broken,['проміжні']);await callback(broken,'onerror','network');assert.equal((await state()).pressed,'false');assert((await state()).note.length>0);await input('Ручна правка після помилки');const repaired=await state();await emit(broken,['пізні після помилки'],true);await callback(broken,'onend');assert.deepEqual(await state(),repaired);
  assert.equal(repaired.humans,0);assert.equal(repaired.stored,repaired.value);facts.push({field,edited,restart:active.value,lastWordsRetained:true,stopEditLatePreserved:true,errorEditPreserved:true,noAutomaticSend:true});
 }
 await p.evaluate(()=>{режим('сценарій');ШІ_РОЗГОРНУТО=true;малюватиЧатП()});const chat=p.locator('#чат-поле');await chat.tap();await chat.press('ControlOrMeta+A');await p.keyboard.insertText('Правка рукою');await p.locator('#чат-мікрофон').tap();const sendRec=await p.evaluate(()=>__recs.length-1);await emit(sendRec,['та голосом']);assert.equal(await p.evaluate(()=>ЧАТ_ГОЛОСОМ_П),false);await p.locator('#чат-мікрофон').tap();assert.equal(await p.evaluate(()=>ЧАТ_ГОЛОСОМ_П),true);assert.equal(await p.evaluate(()=>ЧАТ_П.filter(x=>x.хто==='людина').length),0);await p.locator('#чат-слати').tap();await p.waitForTimeout(200);const humans=await p.evaluate(()=>ЧАТ_П.filter(x=>x.хто==='людина'));assert.equal(humans.length,1);assert.equal(humans[0].текст,'Правка рукою та голосом');assert.equal(humans[0].голосом,true);assert.equal(await chat.inputValue(),'');assert.equal(network.filter(x=>x.method==='POST').length,0);await p.screenshot({path:OUT+'/чат-надсилання.png'});
 const events=await p.evaluate(()=>({trustedInput:__events.filter(e=>e.type==='input'&&e.trusted).length,trustedPointer:__events.filter(e=>e.type==='pointerdown'&&e.trusted).length,trustedTouch:__events.filter(e=>e.type==='touchstart'&&e.trusted).length,ownInput:__events.filter(e=>e.type==='input'&&!e.trusted).length}));assert(events.trustedInput>0&&events.trustedPointer>0&&events.trustedTouch>0&&events.ownInput>0);
 const result={head:'af1ab8c37eeb45469646e715c8640f5ab5b86c2d',chromium:browser.version(),viewport:'390×844',facts,events,humans,networkPost:0,blocked:network};fs.writeFileSync(OUT+'/факти.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));await ctx.close();
 }finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
