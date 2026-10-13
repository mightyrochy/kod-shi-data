const {chromium}=require('playwright'),fs=require('fs'),path=require('path'),assert=require('assert');
const out='/workspace/scratch/4622-proof/round2-native';
(async()=>{const b=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});try{
const page=await b.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true}); const errors=[],blocked=[];
page.on('pageerror',e=>errors.push(String(e)));
await page.route('**/*',r=>{const u=new URL(r.request().url());const f=u.hostname==='qa4622.local'?path.join(out,'index.html'):u.href.includes('/pyodide/')?path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(u.pathname)):u.href.includes('/Fixel@main/fonts/webfonts/')?path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(u.pathname)):null;if(f&&fs.existsSync(f))return r.fulfill({path:f});blocked.push(u.origin+u.pathname);return r.abort();});
await page.goto('http://qa4622.local');await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
const fixture=JSON.parse(fs.readFileSync(path.join(out,'fixture.json')));
const facts=await page.evaluate(async f=>{const rows=[];const old=await містП('мова',{розмова:{},відповідь_моделі:JSON.stringify(f.recorded)});const prior=await містП('мова',{паспорт_з:old.внутрішня,сценарій:{нагода:'спорт'},слова_розмови:[f.words],частини:old.частини});
for(const [id,intent,quote,place] of [['conflict','other',f.recorded.update.place.quote,'cafe'],['sport_park','sport',f.recorded.update.movement.quote,'park'],['missing',null,null,'cafe'],['unknown','unknown',f.words,'cafe'],['no_quote','other',null,'cafe']]){
const model=structuredClone(f.recorded);model.update.place.value=place;if(intent)model.update.occasion_part={value:intent,...(quote?{quote}: {})};
const parsed=await містП('мова',{розмова:{},відповідь_моделі:JSON.stringify(model)});const q=await містП('мова',{паспорт_з:parsed.внутрішня,сценарій:{нагода:'спорт'},паспорт:prior.паспорт,слова_розмови:[f.words],частини:parsed.частини});
if(!q.паспорт)throw new Error(JSON.stringify(q)); const e=document.getElementById('сц-нагода');e.value='спорт';ПАСПОРТ_П=q.паспорт;застосуватиПаспортДоЕкрана(q.паспорт);режим('сценарій');малюватиКарткуСценарію();
rows.push({id,passport:q.паспорт.нагода,metric:q.паспорт.виміри.occasion,source:q.паспорт.джерело_полів.нагода,notRecorded:q.не_записано,dom:e.value,card:document.getElementById('зн-нагода').textContent,nextInput:зібратиВхід().сценарій.нагода,place:q.паспорт.виміри.place,movement:q.паспорт.виміри.movement,parsed,q});}
return {rows,viewport:innerWidth};},fixture);
for(const r of facts.rows){assert.equal(r.dom,r.id==='conflict'?'':'спорт');assert.equal(r.nextInput,r.id==='conflict'?null:'спорт');assert.equal(r.metric,r.id==='conflict'?'unknown':'sport');assert.equal(r.place,r.id==='sport_park'?'park':'cafe');assert.equal(r.movement,'sport');}assert.equal(errors.length,0);
facts.chromium=b.version();facts.errors=errors;facts.blocked=blocked;facts.modelCalls=0;facts.buildSource='03759fd671272d6353dedd671dd528ea049a0003';facts.kind='SYNTHETIC contract fixtures via actual bridge and exact full build; NOT LIVE model grade';fs.writeFileSync(path.join(out,'native.json'),JSON.stringify(facts,null,2));
await page.evaluate(q=>{document.getElementById('сц-нагода').value='спорт';ПАСПОРТ_П=q.паспорт;застосуватиПаспортДоЕкрана(q.паспорт);режим('сценарій');малюватиКарткуСценарію();},facts.rows[0].q);await page.screenshot({path:path.join(out,'conflict.png')});console.log(JSON.stringify({rows:facts.rows.map(({parsed,q,...r})=>r),errors,blocked,modelCalls:0}));
}finally{await b.close();}})().catch(e=>{console.error(e);process.exitCode=1});
