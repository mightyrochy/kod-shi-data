const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
(async()=>{
 const root=process.argv[2], b=await chromium.launch({executablePath:'/usr/bin/chromium',headless:true,args:['--no-sandbox']}), c=await b.newContext({viewport:{width:390,height:844},hasTouch:true,isMobile:true,deviceScaleFactor:1,reducedMotion:'reduce'}), p=await c.newPage();
 p.setDefaultTimeout(180000);
 const facts={браузер:await b.version(),розмір:'390×844',модельних_запитів:0,помилки:[],заблоковані:[]};
 p.on('pageerror',e=>facts.помилки.push(String(e)));
 await p.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='975.test')return r.fulfill({path:path.join(root,'index.html'),contentType:'text/html'});if(u.href.includes('/pyodide/')){const f=path.join('/tmp/974-pyodide',u.pathname.split('/').pop());if(fs.existsSync(f))return r.fulfill({path:f,contentType:f.endsWith('.wasm')?'application/wasm':f.endsWith('.js')?'application/javascript':'application/octet-stream'});}facts.заблоковані.push(u.href);return r.abort();});
 try{
 await p.goto('http://975.test/index.html');await p.waitForFunction(()=>typeof document.getElementById('сцн-новий').onclick==='function',null,{timeout:60000});
 await p.locator('[id="пр-імʼя"]').fill('Проба');await p.locator('#пр-згода').check();for(let i=0;i<3;i++)await p.locator('#н-далі').tap();await p.waitForFunction(()=>РЕЖИМ==='сценарій');
 await p.evaluate(()=>режим('палітра'));await p.waitForFunction(()=>РЕЖИМ==='палітра');await p.locator('#пал-кольори').waitFor({state:'visible'});
 facts.порожня=await p.evaluate(()=>({текст:document.getElementById('пал-стан').textContent,кнопка:document.getElementById('пал-кольори').textContent,кольори:КОЛІР,режим:РЕЖИМ}));await p.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await p.screenshot({animations:'disabled',path:path.join(root,'empty.png')});
 await p.locator('#пал-кольори').tap();await p.locator('#аркуш').waitFor({state:'visible'});facts.дотик=await p.evaluate(()=>({заголовок:document.getElementById('аркуш').innerText,режим:РЕЖИМ}));await p.evaluate(()=>Promise.all(document.getAnimations().map(a=>a.finished.catch(()=>{}))));await p.screenshot({animations:'disabled',path:path.join(root,'tap.png')});

 await p.locator('#аркуш-готово').tap();
 const стан=()=>p.evaluate(()=>({текст:document.getElementById('пал-стан').textContent,вступ:document.getElementById('пал-вступ').hidden,вибір:document.getElementById('пал-вибір').hidden,порожній:document.getElementById('пал-порожньо').hidden,html:document.getElementById('пал-вибір').innerHTML,палітра:ПАЛІТРА}));
 facts.інші_стани={};
 await p.evaluate(async()=>{КОЛІР={шкіра:'#f0d5c8',волосся:null,очі:null,кільце:null,точки:null};режим('палітра');await оновитиПалітруП();});facts.інші_стани.частковий=await стан();
 await p.evaluate(async()=>{КОЛІР={шкіра:'#f0d5c8',волосся:'#4a4644',очі:'#6b8cae',кільце:null,точки:null};document.getElementById('мр-зріст').value=167; for(const [id,key] of ПОЛЯ_ОБХВАТІВ){const v={плечі:96,груди:92,талія:74,стегна:100}[key];if(v)document.getElementById(id).value=v;} await оновитиПалітруП();});facts.інші_стани.повний=await стан();
 }finally{fs.writeFileSync(path.join(root,'facts.json'),JSON.stringify(facts,null,2));await b.close();}console.log(JSON.stringify({порожня:facts.порожня,дотик:facts.дотик,моделі:facts.модельних_запитів,помилки:facts.помилки,інші:Object.fromEntries(Object.entries(facts.інші_стани||{}).map(([k,v])=>[k,{текст:v.текст,порожній:v.порожній,гілки:v.палітра?.гілки?.length}]))}));
})().catch(e=>{console.error(e);process.exitCode=1});
