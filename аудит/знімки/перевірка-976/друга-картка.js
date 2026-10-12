const fs=require('fs'),path=require('path'),assert=require('assert/strict'),{chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 const p=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true});
 const facts={errors:[],modelCalls:0};p.on('pageerror',e=>facts.errors.push(String(e)));
 try{
  await p.route('**/*',r=>{const u=new URL(r.request().url());if(/anthropic|openai|1234/.test(u.href))facts.modelCalls++;
   if(u.hostname==='review976.test')return r.fulfill({path:'/tmp/review976/after/index.html',contentType:'text/html'});
   if(u.pathname.includes('/pyodide/'))return r.fulfill({path:'/tmp/974-pyodide/'+path.basename(u.pathname)});return r.abort();});
  await p.goto('http://review976.test');await p.waitForFunction(()=>typeof document.getElementById('біб-назад').onclick==='function');
  const fixture=JSON.parse(fs.readFileSync('/tmp/review976/library/fixture.json'));
  await p.evaluate(async f=>{const d=await дб();await tx(d,'образи','readwrite',s=>s.put(f.record,f.record.ключ));for(const v of f.verdicts)await tx(d,'вердикти','readwrite',s=>s.add(v));ПРОФІЛЬ_СТВОРЕНО=true;режим('бібліотека');},fixture);
  await p.locator('.біб-образ').first().tap();await p.waitForFunction(()=>РЕЖИМ==='образи'&&!document.getElementById('к-0').hidden);
  await p.locator('#пейджер button[data-крок="1"]').tap();await p.waitForFunction(()=>!document.getElementById('к-1').hidden);
  facts.second=await p.evaluate(()=>({visible:[...document.querySelectorAll('.картка')].filter(e=>!e.hidden).map(e=>e.id),cards:П.картки,verdict:В[0].верд}));
  assert.deepEqual(facts.second.visible,['к-1']);assert.deepEqual(facts.second.cards,fixture.record.П.картки);assert.equal(facts.second.verdict,'вдягну як є');
  await p.screenshot({path:path.join(__dirname,'друга-картка.png')});
  await p.locator('#к-1 h2').scrollIntoViewIfNeeded();
  const text=await p.locator('#к-1').innerText();facts.secondText=text;
  const description=p.locator('#к-1 .пояснення');if(await description.count())await description.first().scrollIntoViewIfNeeded();
  await p.screenshot({path:path.join(__dirname,'друга-картка-текст.png')});
  assert.deepEqual(facts.errors,[]);assert.equal(facts.modelCalls,0);
 }finally{fs.writeFileSync(path.join(__dirname,'друга-картка-факти.json'),JSON.stringify(facts,null,2));await browser.close();}
 console.log(JSON.stringify({visible:facts.second.visible,errors:facts.errors,modelCalls:facts.modelCalls}));
})().catch(e=>{console.error(e);process.exitCode=1});
