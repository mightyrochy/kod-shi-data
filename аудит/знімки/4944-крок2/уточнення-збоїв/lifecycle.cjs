const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert/strict'),crypto=require('crypto'),http=require('http');
const root=__dirname,stage=process.argv[2],out=path.join(root,stage);const fixture=JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4943/.qa4943/fixture.json'));
(async()=>{const server=http.createServer((q,r)=>{const url=new URL(q.url,'http://127.0.0.1');const file=url.pathname.startsWith('/pyodide/')?path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(url.pathname)):url.pathname==='/'?path.join(out,'index.html'):null;if(!file||!fs.existsSync(file)){r.statusCode=404;return r.end();}r.setHeader('Access-Control-Allow-Origin','*');r.setHeader('Content-Type',file.endsWith('.html')?'text/html; charset=utf-8':file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'application/javascript':file.endsWith('.json')?'application/json':'application/octet-stream');r.end(fs.readFileSync(file));});await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
const p=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
const errors=[];p.on('pageerror',e=>errors.push(String(e)));
await p.route('**/*',r=>{const u=new URL(r.request().url());if(u.origin===origin)return r.continue();const f=u.hostname==='lifecycle.local'?path.join(out,decodeURIComponent(u.pathname)==='/'?'index.html':decodeURIComponent(u.pathname)):u.href.includes('/pyodide/')?path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(u.pathname)):u.href.includes('/Fixel@main/fonts/webfonts/')?path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(u.pathname)):null;return f&&fs.existsSync(f)?r.fulfill(u.hostname==='lifecycle.local'?{body:fs.readFileSync(f),contentType:'text/html'}:{path:f}):r.abort();});
await p.goto(origin+'/#model_mova=off');await p.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
await p.evaluate(async origin=>{ДЗЕРКАЛА_П[0][1]=origin+'/pyodide/';await містП('помади',{});},origin);
const cdp=await p.context().newCDPSession(p);await cdp.send('Accessibility.enable');
const results={stage,chromium:browser.version(),viewport:[390,844],modelAPI:0,modelOff:await p.evaluate(()=>МОДЕЛЬ_МОВИ_П===null),artifactSha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(out,'index.html'))).digest('hex'),cases:[]};
for(const kind of ['all_failed','positive','partial','render_error','journal_error','empty_result','unknown_source']){
 const r=await p.evaluate(async({kind,fixture})=>{
  const cards=Array.from({length:4},(_,i)=>Object.assign(JSON.parse(JSON.stringify(fixture.record.П.картки[i%fixture.record.П.картки.length])),{рука:String(i+1)}));
  if(kind==='all_failed')cards.forEach(c=>{c.збій=true;c.речі=[];});if(kind==='partial')cards.slice(1).forEach(c=>{c.збій=true;c.речі=[];});if(kind==='empty_result')cards.fill(null);
  ЗБ={картки:cards,стадії:[null,null,null,null],етап:[4,4,4,4],діагноз:[],готово:false,успіх:false,ключ:null};
  П=Object.assign({},fixture.record.П,{картки:cards.filter(Boolean),прогін:'synthetic-round2-'+kind});
  if(kind==='render_error')П=null;if(kind==='unknown_source')ЗБ=null;
  const ст=$('зб-статус'),ог=$('зб-оголошення');ст.textContent='';ог.textContent=$('стани').querySelector('span:last-child').textContent;
  режим('очікування');window.round2Mutations=[];const observer=new MutationObserver(()=>round2Mutations.push(ог.textContent));observer.observe(ог,{childList:true,subtree:true,characterData:true});
  const original=зібратиОбразиП.toString(),start=original.indexOf('const секунд = Math.round'),end=original.lastIndexOf('}'),tail=original.slice(start,end);
  if(start<0||!tail.includes('const усіЗбій')||!tail.includes('рендер();'))throw new Error('exact seam missing');
  const journal=записатиЗбоїРукП;записатиЗбоїРукП=async()=>{await new Promise(r=>setTimeout(r,35));if(kind==='journal_error')throw new Error('synthetic_journal_failure');};
  // Actual renderer and actual message function remain unchanged; only journal IO is local.
  const fn=eval('(async()=>{const ст=$("зб-статус"),кн=$("зб-пуск"),далі=$("зб-зібрати"),почато=Date.now();try{'+tail+'})');await fn();await new Promise(r=>setTimeout(r,150));const first=ог.textContent;малюватиПоступП();await new Promise(r=>setTimeout(r,50));observer.disconnect();записатиЗбоїРукП=journal;
  return {kind,exactTail:tail,ready:ЗБ?.готово??null,success:ЗБ?.успіх??null,mode:РЕЖИМ,visibleStatus:ст.textContent,liveFirst:first,liveAfterRerender:ог.textContent,mutations:round2Mutations,validCards:ЗБ?.картки.filter(c=>c&&!c.збій).length??null,renderedCards:document.querySelectorAll('#картки .картка').length};
 },{kind,fixture});
 r.ax=(await cdp.send('Accessibility.getFullAXTree')).nodes.filter(n=>n.role?.value==='status').map(n=>({role:n.role,properties:n.properties}));
 await p.waitForTimeout(400);await p.screenshot({path:path.join(out,kind+'.png')});results.cases.push(r);console.log(stage,kind,r.liveAfterRerender,r.mutations);
 if(stage==='after'){const positive=['positive','partial'].includes(kind);if(positive){assert.equal(r.success,true);assert.equal(r.liveAfterRerender,'Готово');assert.ok(r.renderedCards>0);}else{assert.equal(r.liveAfterRerender,r.visibleStatus);assert.notEqual(r.liveAfterRerender,'Готово');assert.ok(!r.mutations.some(t=>t==='Готово'));assert.notEqual(r.success,true);}}
}
results.stages=await p.evaluate(()=>{const out=[];ЗБ={картки:[null,null,null,null],стадії:[null,null,null,null],етап:[0,0,0,0],діагноз:[],готово:false,успіх:false};for(const code of Object.keys(НАПИС_СТАДІЇ_П)){ЗБ.стадії[0]={код:code,раунд:1,образів:4,частин:2,спроба:1};малюватиПоступП();out.push({code,text:$('зб-оголошення').textContent,expected:написСтадіїП(ЗБ.стадії[0])});}return out;});
assert(results.stages.every(x=>x.text.includes(x.expected)&&x.expected));
for(const kind of ['missing_profile','no_token']){
 await p.evaluate(({kind,fixture})=>{ПРОФІЛЬ_СТВОРЕНО=true;КОЛІР=kind==='missing_profile'?{шкіра:null,волосся:null,очі:null}:{шкіра:'#edc4ad',волосся:'#66412f',очі:'#6f7858'};for(const [id,v]of[['мр-зріст',168],['мр-плечі',98],['мр-груди',92],['мр-талія',74],['мр-стегна',99]])$(id).value=v;ПАСПОРТ_П={джерело:'модель',нагода:'робота',місце:'офіс',джерело_полів:{}};застосуватиПаспортДоЕкрана(ПАСПОРТ_П);ЗБ={картки:[fixture.record.П.картки[0]],стадії:[null],етап:[4],діагноз:[],готово:true,успіх:true};$('зб-оголошення').textContent=$('стани').querySelector('span:last-child').textContent;режим('сценарій');}, {kind,fixture});
 await p.locator('#зб-зібрати').tap();await p.waitForTimeout(450);
 const r=await p.evaluate(kind=>{const initial=$('зб-оголошення').textContent;малюватиПоступП();return {kind,visibleStatus:$('зб-статус').textContent,liveFirst:initial,liveAfterRerender:$('зб-оголошення').textContent,success:ЗБ.успіх};},kind);results.cases.push(r);console.log(stage,kind,r);if(stage==='after'){assert.equal(r.liveFirst,r.visibleStatus);assert.equal(r.liveAfterRerender,r.visibleStatus);assert.notEqual(r.success,true);}
}
results.errors=errors;fs.writeFileSync(path.join(out,'results.json'),JSON.stringify(results,null,2)+'\n');console.log('COMPLETE',stage,results.cases.length,results.stages.length,errors);
}finally{await browser.close();await new Promise(r=>server.close(r));}})().catch(e=>{console.error(e);process.exitCode=1;});
