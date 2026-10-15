const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto'),assert=require('assert');
const {chromium}=require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const out='/dev/shm/qa5580/evidence',variant=process.argv[2],html=process.argv[3],sha=process.argv[4];
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],env:{...process.env,TMPDIR:'/dev/shm/qa5580/tmp'}});try{
const ctx=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,acceptDownloads:true});
await ctx.addInitScript(()=>{const Original=Date;window.Date=class extends Original{constructor(...args){super(...(args.length?args:['2026-10-15T12:00:00.000Z']));}static now(){return 1792065600000;}};});
const page=await ctx.newPage(),errors=[],blocked=[];page.on('pageerror',e=>errors.push(e.message));
await page.route('**/*',r=>{const u=new URL(r.request().url()),p=decodeURIComponent(u.pathname);let f;
 if(u.hostname==='qa5580.local')f=p==='/'?html:p.startsWith('/шрифти/')?path.join('/dev/shm/service5580/src',p):null;
 else if(u.href.includes('/pyodide/'))f=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(p));
 else if(u.href.includes('/Fixel@main/fonts/webfonts/'))f=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(p));
 if(f&&fs.existsSync(f))return r.fulfill({path:f});blocked.push(u.href);return r.abort();});
const card=(hand,n)=>({рука:hand,ітерацій:1,викликів:1,текст:'Образ для прогулянки',опис:'Образ для прогулянки',підпис:'Образ для прогулянки',речі:[{id:`qa-${n}@example.com`,назва:'Сукня',ціна:1500,слот:'сукня',фото:null}],мітки:[],знахідки:[],питання:[],етапи:{викликів:1,виклики:[]},свідомі:[],невиконано:null,мова:[],мова_спроб:0,мова_видано:'так',фото_не_ті:[],дібрав_код_слоти:[]});
const packet={в:'ПОКАЗ-V1',збірка:'qa5580',каталог:'каталог_стенд.xml · 639 речей',профіль:'Оля',розклад:'3142',прогін:'qa5580-independent',випадок:'Прогулянка',пул:100,картки:['3','1','4','2'].map(card)};
await page.goto('http://qa5580.local/#'+zlib.gzipSync(JSON.stringify(packet)).toString('base64url'));
await page.waitForFunction(()=>document.querySelectorAll('#картки .картка').length===4);
await page.evaluate(()=>{пристрій="qa5580-independent";СЛУЖБОВЕ=true;document.querySelector('#службове').classList.add('видно');ЗБ={картки:П.картки,стадії:[],етап:[],ключ:['3','1','4','2'],готово:true,успіх:true,діагноз:[
'hand_1 · blocks=2 · with_id=2','hand_2 · failed: HTTP 413','hand_3 · repeat_from_hand_1','hand_4.retry · layer · model=local',
'prompt · hand_1_without_format · format=OBRAZ · variants=1',
'control · hand_2_broken=temperature · drawn_from=hour,temperature',
'control · blind · breakage=temperature · brief_rows=3',
'control · trace · breakage=hour · packet_fields=x','control · no_input=a=b']};малюватиДіагнозП();});
const initial=await page.evaluate(()=>JSON.stringify({packet:П,diag:ЗБ.діагноз,assignment:ЗБ.ключ,pool:П.пул,control:ЗБ.контроль}));
await page.locator('#службове > summary').tap();await page.evaluate(()=>document.fonts.ready);

await page.locator('#службове').scrollIntoViewIfNeeded();
const box=await page.locator('#зб-діагноз').boundingBox();await page.mouse.move(box.x+60,Math.min(box.y+30,760));await page.mouse.wheel(0,700);
await page.screenshot({path:`${out}/${variant}-leak-native-scroll.png`});
console.log(await page.locator('#зб-діагноз').evaluate(e=>({text:e.innerText,rect:e.getBoundingClientRect().toJSON(),scroll:e.scrollTop,ancestors:[...function*(n){for(;n;n=n.parentElement)yield n;}(e)].map(n=>({id:n.id,scrollTop:n.scrollTop,scrollHeight:n.scrollHeight,height:n.clientHeight}))})));
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
