const zlib=require('zlib'),fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{chromium}=require('playwright');
const qa=path.resolve('.qa5080'),stage=process.argv[2],fixture=JSON.parse(zlib.gunzipSync(fs.readFileSync(qa+'/fixture.json.gz')));
(async()=>{const context=await chromium.launchPersistentContext(qa+'/profile',{executablePath:'/usr/bin/chromium',args:['--no-sandbox'],viewport:{width:390,height:844},isMobile:true,hasTouch:true,reducedMotion:'reduce'});
try{const page=await context.newPage(),errors=[],requests=[];page.on('pageerror',e=>errors.push(String(e)));
await page.route('**/*',route=>{const u=new URL(route.request().url());if(/anthropic|openai|1234/.test(u.href))requests.push(u.href);if(u.hostname==='qa5080.invalid')return route.fulfill({path:qa+'/'+stage+'/index.html',contentType:'text/html'});if(u.pathname.includes('/pyodide/'))return route.fulfill({path:qa+'/pyodide/'+path.basename(u.pathname)});if(u.pathname.includes('/шрифти/'))return route.fulfill({path:path.resolve('шрифти',path.basename(decodeURI(u.pathname)))});return route.abort();});
await page.goto('https://qa5080.invalid/#model_mova=none');await page.waitForFunction(()=>typeof document.getElementById('вк-образи').onclick==='function');
await page.evaluate(()=>{const original=window.оновитиБібліотеку;window.pending=0;window.оновитиБібліотеку=async()=>{pending++;try{return await original();}finally{pending--;}};ПРОФІЛЬ_СТВОРЕНО=true;режим('сценарій');});
const library=async()=>{await page.waitForFunction(()=>РЕЖИМ==='бібліотека'&&pending===0);await page.evaluate(()=>document.fonts.ready);assert.equal(await page.locator('.біб-образ').count(),2);};
const storage=()=>page.evaluate(async()=>{const db=await дб();const get=n=>new Promise((res,rej)=>{const r=db.transaction(n).objectStore(n).getAll();r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error);});return{version:db.version,stores:[...db.objectStoreNames],images:(await get('образи')).map(({час,...v})=>v),choices:await get('вердикти')};});
await page.locator('#вк-образи').tap();await page.waitForFunction(()=>pending===0);
if(stage==='before')await page.evaluate(async f=>{const db=await дб();await tx(db,'образи','readwrite',s=>s.clear());await tx(db,'вердикти','readwrite',s=>s.clear());await tx(db,'образи','readwrite',s=>s.put(f.record,f.record.ключ));for(const v of f.verdicts)await tx(db,'вердикти','readwrite',s=>s.add(v));await оновитиБібліотеку();},fixture);
await library();const result={stage,source:fixture.source,kind:fixture.kind,viewport:'390x844',initialStorage:await storage(),activations:[]};
if(stage==='after')assert.deepEqual(result.initialStorage,JSON.parse(zlib.gunzipSync(fs.readFileSync(qa+'/before/facts.json.gz'))).finalStorage);
await page.screenshot({path:qa+'/'+stage+'/library.png'});
const visible=()=>page.evaluate(()=>[...document.querySelectorAll('#картки > .картка')].filter(x=>!x.hidden).map(x=>x.id));
for(const method of ['tap','Enter'])for(const i of [0,1]){
const tile=page.locator('.біб-образ').nth(i);if(method==='tap')await tile.tap();else{await tile.focus();await page.keyboard.press('Enter');}
await page.waitForFunction(()=>РЕЖИМ==='образи'&&В[0]?.верд==='вдягну як є');await page.waitForTimeout(200);
const state=await page.evaluate(()=>({visible:[...document.querySelectorAll('#картки > .картка')].filter(x=>!x.hidden).map(x=>x.id),cards:П.картки,choice:В[0].верд,chip:[...document.querySelectorAll('#к-0 .ряд[data-поле="верд"] .чип.вибр')].map(x=>x.textContent)}));
assert.deepEqual(state.cards,fixture.record.П.картки);assert.equal(state.choice,fixture.verdicts[0].вердикт_людини);assert.equal(state.chip.length,1);
result.activations.push({method,tile:i,...state});if(stage==='after')assert.deepEqual(state.visible,['к-'+i]);
await page.screenshot({path:qa+'/'+stage+'/'+method+'-'+i+'.png'});
const current=Number(state.visible[0].slice(2)),next=1-current;await page.locator('#пейджер button[data-крок="'+(next-current)+'"]').tap();assert.deepEqual(await visible(),['к-'+next]);await page.locator('#пейджер-низ button[data-крок="'+(current-next)+'"]').tap();assert.deepEqual(await visible(),['к-'+current]);
await page.locator('#до-бібліотеки').tap();await library();await page.locator('#біб-назад').tap();await page.waitForFunction(()=>РЕЖИМ==='образи');assert.deepEqual(await visible(),['к-'+current]);await page.locator('#до-бібліотеки').tap();await library();
}
await page.locator('.біб-образ').first().tap();await page.waitForFunction(()=>РЕЖИМ==='образи'&&В[0]?.верд);await page.locator('#к-0 .ряд[data-поле="верд"] .чип.вибр').scrollIntoViewIfNeeded();await page.screenshot({path:qa+'/'+stage+'/choice.png'});
await page.locator('#до-бібліотеки').tap();await library();await page.screenshot({path:qa+'/'+stage+'/returned.png'});
if(stage==='after'){await page.locator('.біб-образ').nth(1).tap();await page.waitForFunction(()=>РЕЖИМ==='образи'&&В[0]?.верд);await page.evaluate(()=>рендер());await page.waitForTimeout(200);assert.deepEqual(await visible(),['к-0']);result.freshRenderResets=true;await page.locator('#до-бібліотеки').tap();await library();}
result.finalStorage=await storage();assert.deepEqual(result.finalStorage,result.initialStorage);assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);result.pageerrors=errors;result.modelRequests=requests;fs.writeFileSync(qa+'/'+stage+'/facts.json.gz',zlib.gzipSync(JSON.stringify(result,null,2)));console.log(JSON.stringify({stage,activations:result.activations.map(({method,tile,visible})=>({method,tile,visible})),dataPreserved:true,pagerBoth:true,lastReturn:true,errors,requests}));
}finally{await context.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
