/* Повтор записаних входів через незмінений транспорт і сторож сторінки PR #3707.
   node воркер3707.js <index.html> <кеш Pyodide> <входи.jsonl.gz> <вихід.json> */
const fs=require('fs'),path=require('path'),zlib=require('zlib'),crypto=require('crypto');
const {chromium}=require('playwright');
const [html,cache,input,output]=process.argv.slice(2);
const calls=zlib.gunzipSync(fs.readFileSync(input)).toString('utf8').trim().split('\n').map(JSON.parse);
const base='http://127.0.0.1:8765';
(async()=>{
  const browser=await chromium.launch({headless:true,executablePath:process.env.CHROMIUM||undefined});
  const context=await browser.newContext({viewport:{width:390,height:844},ignoreHTTPSErrors:true});
  await context.route('**/*',async route=>{
    const url=new URL(route.request().url());
    if(url.origin===base){
      if(url.pathname==='/index.html') return route.fulfill({status:200,contentType:'text/html; charset=utf-8',body:fs.readFileSync(html)});
      return route.fulfill({status:404,body:'нема файла'});
    }
    if(url.href.startsWith('https://cdn.jsdelivr.net/pyodide/')){
      const name=url.pathname.split('/').pop(),file=path.join(cache,name);
      if(!fs.existsSync(file)) return route.fulfill({status:404,body:'нема файла'});
      const type=name.endsWith('.wasm')?'application/wasm':name.endsWith('.js')?'application/javascript':name.endsWith('.json')?'application/json':'application/octet-stream';
      return route.fulfill({status:200,contentType:type,headers:{'Access-Control-Allow-Origin':'*'},body:fs.readFileSync(file)});
    }
    return route.abort();
  });
  const page=await context.newPage();
  await page.goto(base+'/index.html',{waitUntil:'load',timeout:180000});
  await page.waitForFunction(()=>typeof транспортМостуП==='function'&&!!(document.getElementById('н-далі')||{}).onclick,null,{timeout:180000});
  const limit=await page.evaluate(()=>СТОРОЖ_ВИКЛИКУ_П);
  if(limit!==300000) throw new Error('Не штатний сторож: '+limit);
  const report={сторінка_sha256:crypto.createHash('sha256').update(fs.readFileSync(html)).digest('hex'),входи_sha256:crypto.createHash('sha256').update(fs.readFileSync(input)).digest('hex'),сторож_мс:limit,браузер:browser.version(),виклики:[]};
  const save=()=>fs.writeFileSync(output,JSON.stringify(report,null,1));
  save();
  for(let i=0;i<calls.length;i++){
    const call=calls[i],t=Date.now();
    if(call.ім==='запити') console.log('ПОЧАТОК запити · виклик '+i+' · сторож '+limit+' мс');
    try{
      const raw=await page.evaluate(async c=>await транспортМостуП(c.ім,c.вхід,!!c.async),call);
      const result=typeof raw==='string'?JSON.parse(raw):raw;
      if(result&&result.помилка) throw new Error(result.помилка);
      report.виклики.push({н:i,ім:call.ім,секунд:(Date.now()-t)/1000,помилка:null});
      if(call.ім==='запити'){
        fs.writeFileSync(output+'.відповідь.json.gz',zlib.gzipSync(typeof raw==='string'?raw:JSON.stringify(raw)));
        report.пул_речей=result.пул_речей;
        report.таблиця=(result.мета||{}).таблиця_каталогу;
      }
    }catch(e){
      report.виклики.push({н:i,ім:call.ім,секунд:(Date.now()-t)/1000,помилка:String(e)});
      report.перезапусків=await page.evaluate(()=>ПЕРЕЗАПУСКІВ_ВОРКЕРА_П);
      save();
      console.log(JSON.stringify(report.виклики[report.виклики.length-1]));
      await browser.close();
      process.exitCode=2;
      return;
    }
    save();
  }
  console.log(JSON.stringify(report.виклики[report.виклики.length-1]));
  await browser.close();
})().catch(e=>{console.error(e);process.exit(1);});
