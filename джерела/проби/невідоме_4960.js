/* 4960: справжній Chromium 390×844, мовний ендпойнт і запис Ж26, без мережі/живої моделі.
   cd джерела; NODE_PATH=node_modules node проби/невідоме_4960.js /tmp/4960-after.html /tmp/4960-evidence */
const fs=require('fs'),path=require('path'),cp=require('child_process'),{chromium}=require('playwright');
const dir=process.argv[3]||'/tmp/4960-evidence', root=process.cwd();
const card=JSON.parse(fs.readFileSync(path.join(dir,'картка.json'),'utf8'));
const old=JSON.parse(fs.readFileSync(path.join(dir,'записаний_вихід.json'),'utf8'));
const raw=JSON.parse(cp.execFileSync('git',['show','origin/claude/zhyvi-26:аудит/живі_26/А/05_ж1_оціни_образ_6б/вердикти.txt'],{encoding:'utf8',maxBuffer:2e7})).прогони[0].вердикти[0].етапи;
const source=cp.execFileSync('git',['show','d4431417f93f347f9b105ad941f08b7406bbba07:джерела/показ.html'],{encoding:'utf8',maxBuffer:2e7});
const before=source.split('\n').find(x=>x.includes("= 'unknown: ' + String(х.код)"));
const base=fs.readFileSync(process.argv[2],'utf8').replace(/<script[^>]*src="https:[^>]*><\/script>/g,'');
const py="import sys,json,мовний_шар as М;print(М.мова(sys.stdin.read()))";
const bridge=d=>JSON.parse(cp.execFileSync('python3',['-c',py],{input:JSON.stringify(d),encoding:'utf8',maxBuffer:2e7}));
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
try{for(const stage of ['ДО','ПІСЛЯ_запис']){
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});let marked,requests=[];
 await page.exposeFunction('bridge4960',d=>{if(d.тексти){requests.push(d.тексти);marked=bridge(d).розмітка;}return bridge(d);});
 await page.exposeFunction('model4960',()=>JSON.stringify(Object.fromEntries(marked.map(r=>[String(r.н),old[r.ключ]]))));
 const html=stage==='ДО'?base.replace(/^  if \(невідоме\).*review_unknown.*$/m,before):base;
 await page.route('**/*',r=>{const u=new URL(r.request().url());if(u.hostname==='probe.invalid'&&u.pathname==='/')return r.fulfill({contentType:'text/html',body:html});
  const f=u.pathname.startsWith('/шрифти/')?path.join(root,'..',decodeURI(u.pathname)):u.hostname==='cdn.jsdelivr.net'?path.join('/tmp/956-fonts',path.basename(u.pathname)):'';
  return f&&fs.existsSync(f)?r.fulfill({path:f}):r.abort();});
 await page.goto('https://probe.invalid/#model_mova=recorded');
 await page.evaluate(({card,raw})=>{містП=async(вид,d)=>{if(вид!=='мова')throw Error('live bridge blocked');return window.bridge4960(d);};модельМовиП=async()=>window.model4960();
  ОЦ.результат={картка:{...raw.картка,не_знаю:card.не_знаю,мова_шару:[]},сценарій:raw.сценарій_екрана};ОЦ.фото=[];ОЦ.етапи={мова_шару:[]};
  document.querySelectorAll('.екран').forEach(x=>x.style.display='none');document.getElementById('е-оцінка').style.display='block';малюватиКарткуОцінкиП();}, {card,raw});
 await page.locator('.оц-не-знаю summary').click();
 await page.waitForFunction(()=>document.querySelectorAll('.оц-не-знаю .задум > div').length===57);await page.evaluate(()=>document.querySelector('.оц-не-знаю').scrollIntoView());
 const texts=await page.locator('.оц-не-знаю .задум > div').allTextContents();if(JSON.stringify(texts)!==JSON.stringify(Object.values(old)))throw Error('recorded text changed');
 if(stage!=='ДО'){const payload=Object.values(requests[0]).map(x=>JSON.parse(x).review_unknown);if(JSON.stringify(payload)!==JSON.stringify(card.не_знаю.map(x=>x.контекст)))throw Error('context lost');}
 await page.screenshot({path:path.join(dir,'4960_'+stage+'.png')});fs.writeFileSync(path.join(dir,stage+'_запит.json'),JSON.stringify(requests,null,2));
 console.log(stage+': rows=57, recorded text unchanged, language calls='+requests.length);await page.close();
}}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
