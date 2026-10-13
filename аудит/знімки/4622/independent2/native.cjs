const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
const out='/workspace/scratch2/review4622-round2', artifact='/workspace/scratch/4622-proof/round2-native/index.html';
const fixtures=JSON.parse(fs.readFileSync(path.join(out,'fixtures.json'))),missing=JSON.parse(fs.readFileSync(path.join(out,'missing.json')));
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});const errors=[],blocked=[],requests=[];
page.on('pageerror',e=>errors.push(String(e)));
await page.route('**/*',async route=>{const request=route.request(),u=new URL(request.url());
if(u.hostname==='localhost'&&request.method()==='POST') {const data=request.postDataJSON();requests.push(data);const promptText=data.messages.flatMap(m=>m.content||[]).filter(b=>b.type==='text').map(b=>b.text).join('');let prompt={};try{prompt=JSON.parse(promptText)}catch{};const answer=prompt.task&&prompt.task.codes?fixtures[0].response:{text:'Синтетична відповідь для перевірки шва.',invite_topics:[],invite:''};return route.fulfill({contentType:'application/json',body:JSON.stringify({content:[{type:'text',text:JSON.stringify(answer)}],stop_reason:'end_turn'})});}
const file=u.hostname==='localhost'?artifact:u.href.includes('/pyodide/')?path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(u.pathname)):u.href.includes('/Fixel@main/fonts/webfonts/')?path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(u.pathname)):null;
if(file&&fs.existsSync(file))return route.fulfill({path:file});blocked.push(u.origin+u.pathname);return route.abort();});
await page.goto('http://localhost:8787/index.html#bridge=http%3A%2F%2Flocalhost%3A8787&t=synthetic&model=synthetic&model_mova=synthetic');
await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
const result=await page.evaluate(async ({fixtures,missing})=>{
const words='йога зранку, потім кава з подругою',rows=[];
function display(q,prior){document.getElementById('сц-нагода').value=prior;ПАСПОРТ_П=q.паспорт;застосуватиПаспортДоЕкрана(q.паспорт);режим('сценарій');малюватиКарткуСценарію();return {metric:q.паспорт.виміри.occasion,dom:document.getElementById('сц-нагода').value,card:document.getElementById('зн-нагода').textContent,nextInput:зібратиВхід().сценарій.нагода,passport:q.паспорт,notRecorded:q.не_записано};}
const base=fixtures.find(f=>f.name==='absent').result.паспорт;
const producer=await містП('мова',{розмова:{нове:words,історія:[]},сценарій:{нагода:'спорт'},паспорт:base});
for(const f of fixtures){const parsed=await містП('мова',{розмова:{нове:words,історія:[]},відповідь_моделі:JSON.stringify(f.response)});const q=await містП('мова',{паспорт_з:parsed.внутрішня,сценарій:{нагода:'спорт'},паспорт:base,слова_розмови:[words],частини:parsed.частини});rows.push({name:f.name,...display(q,'спорт')});}
document.getElementById('сц-місце').value='офіс';document.getElementById('сц-темп').value='23';const manual=display(missing,'робота');manual.place=document.getElementById('сц-місце').value;manual.temperature=document.getElementById('сц-темп').value;
// Увесь штатний клієнтський хід; лише транспорт до моделі віддає явно синтетичні fixtures.
ПАСПОРТ_П=base;document.getElementById('сц-місце').value='';document.getElementById('сц-темп').value='';document.getElementById('сц-нагода').value='спорт';ЧАТ_П=[{хто:'людина',текст:words}];режим('сценарій');
const workflow=await розмоваШаромП(words,[],null,false,null);малюватиКарткуСценарію();
const nextProducer=await містП('мова',{розмова:{нове:words,історія:[]},сценарій:зібратиВхід().сценарій,паспорт:ПАСПОРТ_П});return {producer,rows,manual,workflow,nextProducer,workflowPassport:ПАСПОРТ_П,workflowDom:document.getElementById('сц-нагода').value,workflowCard:document.getElementById('зн-нагода').textContent,workflowNextInput:зібратиВхід().сценарій.нагода,chat:ЧАТ_П,viewport:{width:innerWidth,height:innerHeight}};
},{fixtures,missing});
for(const row of result.rows){assert.equal(row.metric,fixtures.find(f=>f.name===row.name).result.паспорт.виміри.occasion);assert.equal(row.nextInput,row.name==='quoted_other'?null:row.passport.нагода);assert.equal(row.dom,row.name==='quoted_other'?'':row.passport.нагода);}
assert.equal(result.rows[0].card,'не обрано');assert.equal(result.manual.dom,'робота');assert.equal(result.manual.place,'офіс');assert.equal(result.manual.temperature,'23');
assert.equal(result.workflow.відмова,false);assert.equal(result.workflowPassport.виміри.occasion,'unknown');assert.equal(result.workflowDom,'');assert.equal(result.workflowCard,'не обрано');assert.equal(result.workflowNextInput,null);assert.equal(errors.length,0);
await page.evaluate(base=>{ПАСПОРТ_П=base;ЧАТ_П=[];document.getElementById('сц-нагода').value='спорт';document.getElementById('сц-місце').value='';малюватиЧатП();малюватиКарткуСценарію();},fixtures.find(f=>f.name==='absent').result.паспорт);
await page.locator('#чат-поле').fill('йога зранку, потім кава з подругою');
const hit=await page.locator('#чат-слати').boundingBox();await page.locator('#чат-слати').click();
await page.waitForFunction(()=>ПАСПОРТ_П&&ПАСПОРТ_П.виміри.occasion==='unknown'&&document.getElementById('чат-слати').disabled===false,{},{timeout:60000});
result.actualClick=await page.evaluate(()=>({metric:ПАСПОРТ_П.виміри.occasion,place:ПАСПОРТ_П.виміри.place,movement:ПАСПОРТ_П.виміри.movement,dom:document.getElementById('сц-нагода').value,card:document.getElementById('зн-нагода').textContent,nextInput:зібратиВхід().сценарій.нагода,chat:ЧАТ_П}));result.actualClick.hit=hit;assert.equal(result.actualClick.nextInput,null);assert.equal(result.actualClick.card,'не обрано');
result.requests=requests;result.errors=errors;result.blocked=blocked;result.chromium=browser.version();result.actualModelCalls=0;result.sourceSHA='03759fd671272d6353dedd671dd528ea049a0003';result.artifact=artifact;result.kind='Явно синтетичні fixtures; справжня повна збірка, Pyodide й штатні функції; якість нової моделі не оцінено';
fs.writeFileSync(path.join(out,'native.json'),JSON.stringify(result,null,2));await page.screenshot({path:path.join(out,'native.png')});console.log(JSON.stringify({rows:result.rows.map(({passport,...r})=>r),manual:result.manual.dom,workflow:result.workflow,workflowNextInput:result.workflowNextInput,viewport:result.viewport,chromium:result.chromium,errors,syntheticTransport:requests.length}));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1});
