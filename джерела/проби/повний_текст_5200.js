/* 5200: запис Ж12 Б/08 без змін → зібрана сторінка, Chromium 390×844.
   Із джерела: node проби/повний_текст_5200.js <html> <тека доказів> <ДО|ПІСЛЯ|ДО955>. */
const fs=require('fs'),path=require('path'),os=require('os'),assert=require('assert'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'../..'),dir=process.argv[3],stage=process.argv[4];
const scene='аудит/живі_12/Б/08_ж1_оціни_образ_6б/вердикти.txt';
const data=JSON.parse(fs.readFileSync(path.join(root,scene),'utf8'));
const raw=data.прогони.flatMap(r=>r.вердикти).map(v=>v.етапи).find(e=>e&&e.картка);
const html=fs.readFileSync(process.argv[2],'utf8');
fs.mkdirSync(dir,{recursive:true});
(async()=>{const browser=await chromium.launch({executablePath:process.env.CHROMIUM||'/usr/bin/chromium',args:['--no-sandbox']});
try{const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,reducedMotion:'reduce'});
 await page.route('**/*',r=>{const u=new URL(r.request().url());
  if(u.hostname==='probe.invalid'&&u.pathname==='/')return r.fulfill({contentType:'text/html',body:html});
  const f=u.pathname.includes('/шрифти/')?path.join(root,'шрифти',path.basename(decodeURI(u.pathname))):
   u.hostname==='cdn.jsdelivr.net'&&u.pathname.endsWith('.woff2')?path.join(os.tmpdir(),'956-fonts',path.basename(u.pathname)):'';
  return f&&fs.existsSync(f)?r.fulfill({path:f}):r.abort();});
 await page.goto('https://probe.invalid/#model_mova=none');
 await page.waitForFunction(()=>typeof document.getElementById('оц-оцінити').onclick==='function');
 await page.evaluate(raw=>{ОЦ.перелік={так:true}; ОЦ.результат={картка:raw.картка,суд:raw.суд,сценарій:raw.сценарій_екрана};
  ОЦ.фото=[];ОЦ.етапи=raw;режим('оцінка');малюватиКарткуОцінкиП();},raw);
 await page.evaluate(()=>document.fonts.ready);
 const changes=page.locator('.оц-зміни .оц-чому');
 assert.deepStrictEqual(await changes.allTextContents(),raw.картка.змінити.map(x=>x.текст));
 await page.locator('.оц-не-знаю summary').tap();
 assert.deepStrictEqual(await page.locator('.оц-не-знаю .задум > div').allTextContents(),raw.картка.не_знаю.map(x=>x.текст));
 const selector='.оц-зміни .н .назва,.оц-зміни .н a,.оц-не-знаю .задум > div';
 const rows=await page.locator(selector).evaluateAll(nodes=>nodes.map(n=>{const b=n.getBoundingClientRect(),s=getComputedStyle(n);
  return {text:n.textContent,x:b.x,y:b.y,width:b.width,height:b.height,scrollHeight:n.scrollHeight,clientHeight:n.clientHeight,
   scrollWidth:n.scrollWidth,clientWidth:n.clientWidth,clamp:s.webkitLineClamp,overflow:s.overflow,
   clipped:n.scrollHeight>n.clientHeight+1||n.scrollWidth>n.clientWidth+1};}));
 const clipped=rows.filter(x=>x.clipped).length;
 if(stage==='ПІСЛЯ')assert.strictEqual(clipped,0,JSON.stringify(rows));
 // Реальні дотики до розкривача; дочитування кожного рядка через прокручування його кінця.
 for(let i=0;i<rows.length;i++){
  const row=page.locator(selector).nth(i);await row.scrollIntoViewIfNeeded();
  const delta=await row.evaluate(n=>{const r=document.createRange();r.selectNodeContents(n);r.setStart(n.firstChild,Math.max(0,n.textContent.length-1));
   return r.getBoundingClientRect().bottom-innerHeight+180;});
  await page.mouse.wheel(0,delta);await page.waitForTimeout(100);
  const last=await row.evaluate(n=>{const r=document.createRange();r.selectNodeContents(n);r.setStart(n.firstChild,Math.max(0,n.textContent.length-1));
   const b=r.getBoundingClientRect(),p=n.getBoundingClientRect();return {x:b.x,y:b.y,bottom:b.bottom,visible:b.x>=0&&b.right<=innerWidth&&b.y>=0&&b.bottom<innerHeight-90&&b.bottom<=p.bottom+1};});
  rows[i].last=last;if(stage==='ПІСЛЯ')assert(last.visible,'кінець рядка недоступний: '+i);
  await page.screenshot({path:path.join(dir,stage+'_'+i+'.png')});
 }
 await page.locator('#оц-картка').screenshot({path:path.join(dir,stage+'_картка.png')});
 const result={stage,scene,viewport:'390×844',clipped,rows,photoLimit:'Фото з запису не збережені; фото крамниць у хмарі не оцінювались. Без підміни.',modelCalls:0};
 fs.writeFileSync(path.join(dir,stage+'.json'),JSON.stringify(result,null,2));console.log(stage+': clipped='+clipped+', rows='+rows.length+', unchanged recorded texts, real tap');
}finally{await browser.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
