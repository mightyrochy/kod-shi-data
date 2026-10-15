const fs = require('fs'), path = require('path'), assert = require('assert/strict'), crypto = require('crypto'), zlib = require('zlib');
const {chromium} = require('/workspace/kod-shi-data/джерела/node_modules/playwright');
const root='/dev/shm/qa5580-r3', out=root+'/proof', html='/dev/shm/service5580/proof/after-r3.html';
const sha256=x=>crypto.createHash('sha256').update(x).digest('hex');
const diagnostics=[
  'hand_1 · blocks=2 · with_id=2',
  'prompt · hand_1_without_format · format=OBRAZ · variants=1',
  'hand_2 · failed: HTTP 413',
  'hand_3 · repeat_from_hand_1',
  'hand_4.retry · layer · failed: HTTP 503',
  'prompt · hand_1_no_K-KOH-05 · variants=1',
  'prompt · hand_2_no_K-COL-06-M · failed: HTTP 429',
  'control · hand_2_broken=temperature · drawn_from=hour,temperature',
  'control · blind · breakage=temperature · brief_rows=3',
  'control · trace · breakage=hour · packet_fields=x',
  'control · no_input=a=b',
  'verdict · edges_not_counted: Error: test_diagnostic'
];
const spoiler=/hand_\d+|without_format|_no_K-|K-KOH-05|K-COL-06-M|temperature|\bhour\b|breakage=/;
const card=(hand,n)=>({рука:hand,ітерацій:1,викликів:1,текст:'Образ для прогулянки',опис:'Образ для прогулянки',підпис:'Образ для прогулянки',речі:[{id:`r3-${n}@example.com`,назва:'Сукня',ціна:1500,слот:'сукня',фото:null}],мітки:[],знахідки:[],питання:[],етапи:{викликів:1,виклики:[]},свідомі:[],невиконано:null,мова:[],мова_спроб:0,мова_видано:'так',фото_не_ті:[],дібрав_код_слоти:[]});
const packet={в:'ПОКАЗ-V1',збірка:'незалежна-проба-5580-r3',каталог:'каталог_стенд.xml · 639 речей',профіль:'Оля',розклад:'3142',прогін:'qa5580-r3',випадок:'Прогулянка',пул:100,картки:['3','1','4','2'].map(card)};
async function route(page, documentPath){
  await page.route('**/*',r=>{
    const u=new URL(r.request().url()), pathname=decodeURIComponent(u.pathname); let file;
    if(u.hostname==='qa5580-r3.local') file=pathname==='/'?documentPath:pathname.startsWith('/шрифти/')?path.join('/dev/shm/service5580/src',pathname):null;
    else if(u.href.includes('/pyodide/')) file=path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide',path.basename(pathname));
    else if(u.href.includes('/Fixel@main/fonts/webfonts/')) file=path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts',path.basename(pathname));
    return file&&fs.existsSync(file)?r.fulfill({path:file}):r.abort();
  });
}
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox'],env:{...process.env,TMPDIR:root+'/tmp'}});
 try {
  const context=await browser.newContext({viewport:{width:390,height:844},isMobile:true,hasTouch:true,acceptDownloads:true});
  await context.addInitScript(()=>{const NativeDate=Date;window.Date=class extends NativeDate {constructor(...args){super(...(args.length?args:['2026-10-15T12:00:00Z']));}static now(){return new NativeDate('2026-10-15T12:00:00Z').getTime();}};});
  const page=await context.newPage(), pageErrors=[]; page.on('pageerror',e=>pageErrors.push(e.message));
  await route(page,html);
  await page.goto('http://qa5580-r3.local/#'+zlib.gzipSync(JSON.stringify(packet)).toString('base64url'));
  await page.waitForFunction(()=>document.querySelectorAll('#картки .картка').length===4);
  await page.evaluate(diagnostics=>{пристрій='qa5580-r3';СЛУЖБОВЕ=true;document.querySelector('#службове').classList.add('видно');ЗБ={картки:П.картки,стадії:[],етап:[],ключ:['3','1','4','2'],готово:true,успіх:true,діагноз:diagnostics};малюватиДіагнозП();},diagnostics);
  await page.locator('#службове > summary').tap();
  await page.evaluate(()=>document.fonts.ready);
  const cdp=await context.newCDPSession(page), facts=[];
  const baseline=await page.evaluate(()=>JSON.stringify({P:П,raw:ЗБ.діагноз,assignment:ЗБ.ключ,pool:П.пул,control:ЗБ.контроль}));
  for(let n=0;n<=4;n++){
   if(n){if(n>1)await page.locator('#пейджер button[data-крок="1"]').tap();await page.locator(`#к-${n-1} .ряд[data-поле="верд"] .чип[data-код="as_is"]`).tap();await page.waitForFunction(n=>В[n-1]?.записано,n);}
   if(![0,1,3,4].includes(n))continue;
   const state=await page.evaluate(async()=>({saved:Object.values(В).filter(x=>x?.записано).length,gate:прогінОціненийП(),invariant:JSON.stringify({P:П,raw:ЗБ.діагноз,assignment:ЗБ.ключ,pool:П.пул,control:ЗБ.контроль}),owner:await усіВердикти(),width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
   assert.equal(state.saved,n);assert.equal(state.gate,n===4);assert.equal(state.invariant,baseline);assert.equal(state.width,390);assert.equal(state.scrollWidth,390);
   await page.locator('#службове').scrollIntoViewIfNeeded();
   const text=await page.locator('#службове').innerText();
   const ax=await cdp.send('Accessibility.getFullAXTree');
   const names=ax.nodes.filter(x=>!x.ignored&&typeof x.name?.value==='string').map(x=>x.name.value);
   assert.equal(spoiler.test(text),n===4);assert.equal(names.some(x=>spoiler.test(x)),n===4);
   for(const truth of ['HTTP 413','HTTP 503','HTTP 429','control · no_input=a=b','Error: test_diagnostic']) {assert(text.includes(truth));assert(names.some(x=>x.includes(truth)));}
   if(n===4)for(const raw of diagnostics)assert(text.includes(raw));
   await page.screenshot({path:`${out}/after-${n}.png`});
   const box=await page.locator('#зб-діагноз').boundingBox();await page.mouse.move(box.x+90,Math.min(box.y+45,790));await page.mouse.wheel(0,800);
   await page.screenshot({path:`${out}/after-${n}-scroll.png`});
   facts.push({count:n,saved:state.saved,gate:state.gate,visible:text,ax:names.filter(x=>/hand_|образ|HTTP|no_input|Error:|breakage=/.test(x)),spoilerInVisible:spoiler.test(text),spoilerInAX:names.some(x=>spoiler.test(x)),width:state.width,scrollWidth:state.scrollWidth,invariant:true,owner:state.owner});
  }
  const rows=await page.evaluate(async()=>await усіВердикти());
  fs.writeFileSync(out+'/rows.json',JSON.stringify(rows,null,2));
  const beforeExportRows=await page.evaluate(async()=>JSON.stringify(await усіВердикти()));
  const downloadEvent=page.waitForEvent('download');
  await page.evaluate(async()=>{const rows=await усіВердикти();await вивантажитиФайломП(rows,[]);});
  const download=await downloadEvent;await download.saveAs(out+'/after-owner.json');
  assert.equal(await page.evaluate(async()=>JSON.stringify(await усіВердикти())),beforeExportRows);
  const beforeContext=await browser.newContext({viewport:{width:390,height:844},acceptDownloads:true});
  await beforeContext.addInitScript(()=>{const NativeDate=Date;window.Date=class extends NativeDate {constructor(...args){super(...(args.length?args:['2026-10-15T12:00:00Z']));}static now(){return new NativeDate('2026-10-15T12:00:00Z').getTime();}};});
  const beforePage=await beforeContext.newPage();await route(beforePage,'/dev/shm/service5580/proof/before.html');await beforePage.goto('http://qa5580-r3.local/');await beforePage.waitForFunction(()=>typeof вивантажитиФайломП==='function');
  const beforeEvent=beforePage.waitForEvent('download');await beforePage.evaluate(async rows=>{пристрій='qa5580-r3';await вивантажитиФайломП(rows,[]);},rows);
  const beforeDownload=await beforeEvent;await beforeDownload.saveAs(out+'/before-owner.json');
  const afterBytes=fs.readFileSync(out+'/after-owner.json'),beforeBytes=fs.readFileSync(out+'/before-owner.json');assert.deepEqual(afterBytes,beforeBytes);
  const report={head:'b1156780ef75aa131828401041810b2895dd1bb5',browser:browser.version(),builtSha256:sha256(fs.readFileSync(html)),viewport:{width:390,height:844},facts,pageErrors,ownerExport:{sameBytes:true,bytes:afterBytes.length,sha256:sha256(afterBytes),filename:download.suggestedFilename(),sameFilename:download.suggestedFilename()===beforeDownload.suggestedFilename(),sameInputs:'Фактичні чотири записи IndexedDB після дотиків; ті самі записи подано штатному вивантаженню ДО/ПІСЛЯ. Дата та пристрій зафіксовані.'}};
  fs.writeFileSync(out+'/report.json',JSON.stringify(report,null,2));
  console.log(JSON.stringify({...report,facts:facts.map(({owner,ax,visible,...rest})=>rest)}));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
