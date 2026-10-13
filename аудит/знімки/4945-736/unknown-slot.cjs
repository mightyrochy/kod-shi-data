const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert'),crypto=require('crypto');
const [ART,HEAD,CHOICE='list']=process.argv.slice(2),OUT=__dirname;
const server=require('http').createServer((req,res)=>{const f=req.url==='/'?ART:req.url.startsWith('/pyodide/')?path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(req.url)):null;if(f&&fs.existsSync(f)){res.setHeader('Access-Control-Allow-Origin','*');res.setHeader('Content-Type',req.url==='/'?'text/html; charset=utf-8':req.url.endsWith('.wasm')?'application/wasm':req.url.endsWith('.js')?'application/javascript':'application/octet-stream');fs.createReadStream(f).pipe(res)}else{res.writeHead(404);res.end()}});
const fixture=JSON.parse(fs.readFileSync(OUT+'/fixture.json'));
const profile=JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4942/.qa4942/after/full.json'));
(async()=>{await new Promise(r=>server.listen(0,'127.0.0.1',r));const origin='http://127.0.0.1:'+server.address().port;const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox','--disable-dev-shm-usage']});const errors=[],blocked=[],result={head:HEAD,artifact:ART,sha256:crypto.createHash('sha256').update(fs.readFileSync(ART)).digest('hex'),chromium:browser.version(),viewport:'390x844',modelAPI:0,scope:'SYNTHETIC model responses only; actual full artifact, Pyodide, bridge and DOM button. Real catalogue rows; no new model or photo quality claim.',cases:[]};try{
const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const p=await ctx.newPage();p.on('pageerror',e=>errors.push(String(e)));p.setDefaultTimeout(120000);
await p.route('**/*',r=>{const u=new URL(r.request().url());if(u.origin===origin)return r.continue();if(u.href.includes('/pyodide/'))return r.fulfill({status:302,headers:{location:origin+'/pyodide/'+path.basename(u.pathname),'access-control-allow-origin':'*'}});let f=u.href.includes('/Fixel@main/fonts/webfonts/')?path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(u.pathname)):null;if(f&&fs.existsSync(f))return r.fulfill({path:f});blocked.push({method:r.request().method(),url:u.href});return r.abort()});
await p.goto(origin+'/#model_mova=off&vybir='+CHOICE);await p.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');

result.pyodide=await p.evaluate(async origin=>{ДЗЕРКАЛА_П[0][1]=origin+'/pyodide/';await підняти_міст_показу();return {version:pyodide_показу.version,bridge:pyodide_показу.runPython('"bridge" in __import__("sys").modules')}},origin);assert(result.pyodide.bridge);
await p.evaluate(()=>{window.qaUnhandled=[];addEventListener('unhandledrejection',e=>qaUnhandled.push(String(e.reason)));window.qaNativeModel=модельП;window.qaCalls=[];window.qaDone=false;window.qaFailure='';});
for(const [name,pos,mode] of [['unknown-slot',0,'unknownslot']]){
console.log('START',name);
await p.evaluate(async({fixture,pos,mode})=>{
П=structuredClone(fixture);Object.keys(В).forEach(k=>delete В[k]);НЕ_ЦЯ_П.clear();ЗАМІНУ_ВЖЕ_РОЗУМІЄ_П=false;ЗБ={картки:П.картки,діагноз:[],готово:true,стадії:[],етап:[]};
if(mode==='unknown')delete П.знімок;if(mode==='unknownslot')П.картки[pos].речі[2].слот=null;
if(mode==='notfound')П.картки[pos].речі[2].id='ж-not-found@fixture.invalid';
if(mode==='noeligible'){const x=JSON.parse(pyodide_показу.runPython('import json, bridge\njson.dumps([str(r["id"]) for p in bridge._КЕШ_ПАКЕТА.values() for r in p["_каталог"]])'));x.forEach(i=>НЕ_ЦЯ_П.add(i));}
const choice=відповідь(pos);choice.коментар='SYNTHETIC збережені слова';choice.для_мене='mine';рендер();await new Promise(r=>setTimeout(r,10));window.показатиОбраз(pos,true);
window.qaCalls=[];window.qaRelease=null;window.qaMode=mode;window.qaBefore={cards:П.картки.map(x=>JSON.stringify(x)),dom:П.картки.map((x,i)=>$('к-'+i).innerHTML),snapshot:JSON.stringify(П.знімок),pager:$('пейджер').innerHTML,verdicts:JSON.stringify(В),old:П.картки[pos].речі[pos<2?2:0],pos};
модельП=async function(prompt){const body=JSON.parse(prompt),pool=body.pool||[],entry={prompt:body,mode:qaMode};qaCalls.push(entry);if(qaMode==='error')throw Error('SYNTHETIC_model_transport_failure');if(qaMode==='delay')await new Promise(r=>{window.qaRelease=r});
let answer;if(body.items){answer={version:'1',ratings:Object.fromEntries(Object.values(body.items).flat().map(x=>[x.n,'fits']))};}else if(body.groups){answer={version:'1',winners:Object.fromEntries(Object.entries(body.groups).map(([g,xs])=>[g,xs.slice(0,2).map(x=>x.n)]))};}else if(body.replacement && !body.pool){answer={items:[{name:'Ботильйони',details:'Гладка шкіра',slot:'shoes',color_hex:'#553322',own:null,worn:true}]};}
else if(qaMode==='same'){answer={version:'1',outfits:[{id:'o1',items:[qaBefore.old.id]}]};}
else {answer={version:'1',outfits:[{id:'o1',items:qaMode==='none'?[]:[pool[0]?.n]}]};}
entry.answer=answer;return JSON.stringify(answer);};
},{fixture,pos,mode});
const index=pos<2?2:0,button=p.locator('#к-'+pos+' button.замін').nth(index);
await button.tap();
if(mode==='delay'){
await p.waitForFunction(()=>typeof qaRelease==='function',{timeout:120000});
if(name==='rapid')await p.evaluate(({pos,index})=>{$('к-'+pos).querySelectorAll('button.замін')[index].click()}, {pos,index});
if(name==='stale-outfit')await p.evaluate(()=>window.показатиОбраз(1,true));
if(name==='navigation')await p.evaluate(()=>режим('сценарій'));
await p.evaluate(()=>qaRelease());
}
await p.waitForFunction(pos=>!ЗАМІНИ_П.has(П.картки[pos]),pos,{timeout:120000});
await p.waitForTimeout(50);
const actual=await p.evaluate(async pos=>{const b=qaBefore,k=П.картки[pos],i=pos<2?2:0;return {name:'',pos,old:b.old,new:k.речі[i],changed:k.речі[i].id!==b.old.id,otherCards:П.картки.every((x,j)=>j===pos||JSON.stringify(x)===b.cards[j]),otherDOM:П.картки.every((x,j)=>j===pos||$('к-'+j).innerHTML===b.dom[j]),sameSlot:k.речі[i].слот===b.old.слот,fixedItems:k.речі.every((x,j)=>j===i||JSON.stringify(x)===JSON.stringify(JSON.parse(b.cards[pos]).речі[j])),calls:qaCalls,stage:k.етапи?.заміни?.at(-1),pagerBefore:b.pager,pagerAfter:$('пейджер').innerHTML,snapshotSame:JSON.stringify(П.знімок)===b.snapshot,status:$('к-'+pos).querySelector('.не-ця-рядок')?.textContent,visibleFuture:[...$('к-'+pos).querySelectorAll('.відп-заміни,.не-ця-рядок')].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none').map(e=>e.textContent),library:await tx(await дб(),'образи','readonly',s=>s.get('synthetic4945')),verdictCount:(await усіВердикти()).length,choices:JSON.parse(JSON.stringify(В))}},pos).catch(async e=>{return await p.evaluate(pos=>{const b=qaBefore,k=П.картки[pos],i=pos<2?2:0;return{pos,old:b.old,new:k.речі[i],changed:k.речі[i].id!==b.old.id,otherCards:П.картки.every((x,j)=>j===pos||JSON.stringify(x)===b.cards[j]),otherDOM:П.картки.every((x,j)=>j===pos||$('к-'+j).innerHTML===b.dom[j]),sameSlot:k.речі[i].слот===b.old.слот,fixedItems:k.речі.every((x,j)=>j===i||JSON.stringify(x)===JSON.stringify(JSON.parse(b.cards[pos]).речі[j])),calls:qaCalls,stage:k.етапи?.заміни?.at(-1),pagerBefore:b.pager,pagerAfter:$('пейджер').innerHTML,snapshotSame:JSON.stringify(П.знімок)===b.snapshot,status:$('к-'+pos).querySelector('.не-ця-рядок')?.textContent,visibleFuture:[...$('к-'+pos).querySelectorAll('.відп-заміни,.не-ця-рядок')].filter(e=>!e.hidden&&getComputedStyle(e).display!=='none').map(e=>e.textContent)}},pos)});
actual.name=name;actual.choice=CHOICE;result.cases.push(actual);if(actual.changed){const saved=actual.library?.П?.картки?.[pos];assert(saved,name+' no saved card');assert.deepEqual(saved,await p.evaluate(pos=>JSON.parse(JSON.stringify(П.картки[pos])),pos),name+' saved stage differs');assert.equal(actual.verdictCount,0,name+' autosend');}if(CHOICE!=='list')assert(actual.calls.every(c=>c.prompt.replacement?.fixed_outfit?.length===3&&!JSON.stringify(c.prompt.task).includes('not as part of an outfit')),name+' context');
assert(actual.otherCards&&actual.sameSlot&&actual.fixedItems&&actual.snapshotSame,name+' preservation');
if(['hand1','hand2','hand3','hand4','rapid'].includes(name)){assert(actual.changed,name+' no change '+JSON.stringify(actual.stage));assert.equal(actual.calls.length,CHOICE==='tournament'?2:1,name+' calls');assert.equal(actual.pagerAfter,actual.pagerBefore,name+' pager');assert(actual.visibleFuture.every(x=>!x.includes('коли збиратиму образи знову')),name+' future promise');}
else {assert(!actual.changed,name+' changed');if(['unknown-source','not-found','no-eligible','unknown-slot'].includes(name))assert.equal(actual.calls.length,0,name+' calls');}
await p.screenshot({path:OUT+'/'+CHOICE+'-'+name+'.png'});console.log('PASS',name,actual.changed,actual.calls.length);
}
result.errors=errors;result.unhandled=await p.evaluate(()=>qaUnhandled);result.blockedNetwork=blocked;result.modelPOST=blocked.filter(x=>x.method==='POST').length;assert.equal(errors.length,0);assert.equal(result.unhandled.length,0);assert.equal(result.modelPOST,0);
}finally{fs.writeFileSync(OUT+'/native-unknown-slot.json',JSON.stringify(result,null,2)+'\n');await browser.close();await new Promise(r=>server.close(r))}})().catch(e=>{server.close();console.error(e);process.exitCode=1});
