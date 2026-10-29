const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),out=path.join(root,'аудит','живі_960');
const sources=['02_ж2_новорічна_мороз','04_ж7_мороз_без_відкритого'];
const verdicts=sources.map(s=>JSON.parse(fs.readFileSync(path.join(out,s,'вердикти.txt'),'utf8')));
const verdict=verdicts[0];
const ids=[...new Set(verdicts.flatMap(v=>v.прогони.flatMap(p=>p.вердикти.flatMap(r=>r.склад.split('+').filter(id=>id.startsWith('ж-'))))))];
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM,headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844},ignoreHTTPSErrors:true});
  await page.route('**/*',async route=>{
   const u=new URL(route.request().url());let file;
   if(u.hostname==='cdn.jsdelivr.net' && u.pathname.includes('/pyodide/')) file=path.join('C:/tmp/pyodide',u.pathname.split('/').pop());
   else if(u.origin==='http://127.0.0.1:8765') file=path.join('C:/tmp/zh960/site',decodeURIComponent(u.pathname).replace(/^\//,'')||'index.html');
   else return route.abort();
   if(!fs.existsSync(file)) return route.fulfill({status:404,body:'missing'});
   const ext=path.extname(file),type=ext==='.html'?'text/html; charset=utf-8':ext==='.wasm'?'application/wasm':ext==='.js'||ext==='.mjs'?'application/javascript':ext==='.json'?'application/json':'application/octet-stream';
   return route.fulfill({contentType:type,body:fs.readFileSync(file)});
  });
  await page.goto('http://127.0.0.1:8765/#model_mova=нема');
  const rows=await page.evaluate(async ({ids,input})=>{
   await підняти_міст_показу();
   const catalog=ФІД_П;
   const shown=await містП('показ',{...input,каталог:catalog,речі:ids});
   const expected=JSON.parse(await pyodide_показу.runPythonAsync('import json, feed\njson.dumps(feed.читати_збагачення(), ensure_ascii=False)'));
   const rows=shown.map(r=>({id:r.id,first_photo:r.фото,hex:r.hex,colour:r.колір,
     measured_hex:expected[r.id]?.колір_основний?.hex,harvest_photo:expected[r.id]?.фото,
     exact_photo_match:r.фото===expected[r.id]?.фото,exact_hex_match:r.hex===expected[r.id]?.колір_основний?.hex,
     photo_reason:r.кадр_кольору||null}));
   const matches=JSON.parse(await pyodide_показу.runPythonAsync(
     'import json\nfrom фід_фото import _файл_фото\n' +
     'json.dumps([_файл_фото(r["first_photo"]) == _файл_фото(r["harvest_photo"]) for r in json.loads(' + JSON.stringify(JSON.stringify(rows)) + ')])'));
   return rows.map((r,i)=>({...r,canonical_photo_match:matches[i]}));
  },{ids,input:verdict.спільне.вхід_прогону});
  const result={source_sha:'7c90a0093b5d7dc8587a90c541eaf11e23b9a3be',source_scenes:sources,method:'same built page, real Pyodide, saved card IDs; no models',rows};
  fs.writeFileSync(path.join(out,'page_enrichment_3781.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
