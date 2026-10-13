const {chromium}=require('playwright'),fs=require('fs'),assert=require('assert');
const OUT='/tmp/qa5205-media'; const facts=[];
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
for(const [version,file]of [['ДО','/tmp/qa5205-before-full.html'],['ПІСЛЯ','/tmp/5205-after-full.html']]){
 const ctx=await browser.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true});const p=await ctx.newPage();let blocked=[];
 await p.route('**/*',r=>{if(r.request().url()==='http://qa.local/')return r.fulfill({body:fs.readFileSync(file),contentType:'text/html'});blocked.push(r.request().url());return r.abort()});
 await p.addInitScript(()=>{window.__recognizers=[];window.__events=[];window.SpeechRecognition=class{constructor(){window.__recognizers.push(this)}start(){this.started=true}stop(){this.stops=(this.stops||0)+1}};for(const type of ['input','pointerdown','touchstart'])document.addEventListener(type,e=>{if(e.target.tagName==='TEXTAREA')window.__events.push({type,trusted:e.isTrusted,id:e.target.id,value:e.target.value})},true)});
 await p.goto('http://qa.local/');await p.waitForFunction(()=>!!document.getElementById('чат-мікрофон')?.onclick);
 await p.evaluate(()=>{П={картки:[{рука:'1',речі:[],знахідки:[],питання:[],мітки:[],підпис:'Прогулянка',текст:'Зручний образ для прогулянки.'}]};$('картки').appendChild(рендерКартку(0));});
 let manual=0,last=0,errors=0,system=0;let detail=[];
 for(const field of ['чат-поле','ком-0']){
  const mic=field==='чат-поле'?'чат-мікрофон':'мік-ком-0',note=field==='чат-поле'?'чат-голос':'голос-ком-0';
  await p.evaluate(field=>{режим(field==='чат-поле'?'сценарій':'образи');ШІ_РОЗГОРНУТО=true;малюватиЧатП();},field);
  const el=p.locator('#'+field),button=p.locator('#'+mic);
  async function input(text){await el.tap();await el.press('ControlOrMeta+A');await p.keyboard.insertText(text);if(!text)await el.press('Backspace');}
  async function reset(){if(await button.getAttribute('aria-pressed')==='true')await button.tap();await input('');}
  async function start(){await button.tap();return p.evaluate(()=>__recognizers.length-1)}
  async function result(index,kind,final=false,partial=false){await p.evaluate(({index,kind,final,partial})=>{let texts=partial?['перші']:kind==='Android'?['перші','перші слова','перші слова далі']:kind==='Chrome'?['перші слова','далі']:['перші слова','далі','далі'];__recognizers[index].onresult({resultIndex:0,results:texts.map(transcript=>Object.assign([{transcript}],{isFinal:final}))})},{index,kind,final,partial});}
  async function callback(i,type,error){await p.evaluate(({i,type,error})=>__recognizers[i][type](error?{error}:undefined),{i,type,error})}
  async function state(){return p.evaluate(({field,mic,note})=>({value:$(field).value,state:field==='чат-поле'?$('чат-поле').value.trim():відповідь(0).коментар,marker:field==='чат-поле'?ЧАТ_ГОЛОСОМ_П:відповідь(0).коментар_голосом,pressed:$(mic).getAttribute('aria-pressed'),note:$(note).textContent,chat:ЧАТ_П.filter(x=>x.хто==='людина').length}),{field,mic,note})}
  for(const kind of ['Android','Chrome','iOS'])for(const scene of ['а','б','в','г','д']){
   await reset();const index=await start();await result(index,kind,false,scene==='д');
   if(version==='ПІСЛЯ'&&scene==='а'){const s=await state();assert.equal(s.marker,false,'до Stop позначка false');assert.equal(s.pressed,'true','власний input не гасить');await el.evaluate(e=>e.focus());assert.equal((await state()).pressed,'true','програмний focus не гасить');}
   if(['б','в','д'].includes(scene))await button.tap();if(scene==='г')await callback(index,'onend');
   if(scene!=='д'){
    await el.tap();if(version==='ПІСЛЯ'&&scene==='а')assert.equal((await state()).pressed,'false','довірений дотик гасить до введення');
    await el.press('ControlOrMeta+A');await p.keyboard.insertText('Виправила рукою');
   }
   let active=index;if(scene==='г'){active=await start();await result(active,kind,true)}else await result(index,kind,true);
   if(scene==='в'||kind==='iOS')await result(active,kind,true);if(kind==='iOS')await callback(active,'onend');
   const expected=scene==='д'?'перші слова далі':scene==='г'?'Виправила рукою перші слова далі':'Виправила рукою';const s=await state(),ok=s.value===expected&&s.state===expected&&s.chat===0;
   if(scene==='д')last+=ok;else manual+=ok;detail.push({field,kind,scene,expected,ok,...s});
   if(version==='ПІСЛЯ')assert(ok,JSON.stringify(detail.at(-1)));
   if(version==='ПІСЛЯ'&&scene==='а'&&kind==='Android'){await el.scrollIntoViewIfNeeded();await p.screenshot({path:OUT+'/ПІСЛЯ_'+(field==='чат-поле'?'чат':'картка')+'.png'});}
   if(version==='ДО'&&scene==='а'&&kind==='Android'){await el.scrollIntoViewIfNeeded();await p.screenshot({path:OUT+'/ДО_'+(field==='чат-поле'?'чат':'картка')+'.png'});}
  }
  for(const error of ['not-allowed','service-not-allowed','no-speech','aborted','network','audio-capture']){
   await reset();const i=await start();await result(i,'Android');await callback(i,'onerror',error);const message=(await state()).note;await input('Правка після помилки');await result(i,'Android',true);await callback(i,'onend');const s=await state();const ok=s.value==='Правка після помилки'&&s.state===s.value&&s.pressed==='false'&&(error==='aborted'||!!message)&&s.note===message;errors+=ok;detail.push({field,error,ok,message,...s});if(version==='ПІСЛЯ')assert(ok,JSON.stringify(detail.at(-1)));
  }
  await reset();await input('Системна диктовка');await input('Виправлена системна диктовка');const ss=await state();const sysok=ss.value==='Виправлена системна диктовка'&&ss.state===ss.value;system+=sysok;
  if(version==='ПІСЛЯ'){
   await reset();const old=await start();await result(old,'Chrome');await input('Виправила рукою');const newer=await start();await result(newer,'Chrome',false);const before=await state();await result(old,'iOS',true);await callback(old,'onend');await callback(old,'onerror','network');assert.deepEqual(await state(),before,'старі callbacks не чіпають новий розпізнавач');assert.equal(before.pressed,'true');await button.tap();assert.equal((await state()).marker,true,'після Stop позначка true');await result(newer,'Chrome',true);assert.equal((await state()).value,'Виправила рукою перші слова далі');await callback(newer,'onend');
   await reset();const pending=await start();await result(pending,'Android',false,true);await button.tap();await input('Виправлення між stop і result');await result(pending,'Android',true);await callback(pending,'onerror','network');await callback(pending,'onend');assert.equal((await state()).value,'Виправлення між stop і result');assert.equal((await state()).note,'');
  }
 }
 const eventFacts=await p.evaluate(()=>({trustedInput:__events.filter(e=>e.type==='input'&&e.trusted).length,trustedPointer:__events.filter(e=>e.type==='pointerdown'&&e.trusted).length,trustedTouch:__events.filter(e=>e.type==='touchstart'&&e.trusted).length,ownInput:__events.filter(e=>e.type==='input'&&!e.trusted).length,auto:ЧАТ_П.length}));
 facts.push({version,file,manual,last,errors,system,eventFacts,detail,blocked});console.log(JSON.stringify({version,manual,last,errors,system,eventFacts}));await ctx.close();
}
fs.writeFileSync(OUT+'/факти.json',JSON.stringify(facts,null,2));
}finally{await browser.close()}})().catch(e=>{console.error(e);process.exitCode=1});
