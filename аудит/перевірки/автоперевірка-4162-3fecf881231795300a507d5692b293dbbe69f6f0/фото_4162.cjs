const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
(async()=>{
 const base=__dirname, data=JSON.parse(fs.readFileSync(path.join(base,'4162-фото.json'),'utf8'));
 const browser=await chromium.launch({headless:true});
 try{
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('"','&quot;');
  const body='<!doctype html><meta charset="utf-8"><style>body{font:14px Arial;margin:12px}article{break-inside:avoid;margin-bottom:20px}img{width:350px;height:260px;object-fit:contain;background:#eee}h3{margin:5px 0}</style>'+data.map(r=>`<article><h3>${esc(r.пара)} ${esc(r.id)}</h3><img src="${esc(r.фото)}"><p>${esc(r.назва)}</p><p>${esc(JSON.stringify(r.рядок))}</p></article>`).join('');
  await page.setContent(body,{waitUntil:'domcontentloaded'});
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete),null,{timeout:30000}).catch(()=>{});
  const results=await page.evaluate(()=>[...document.images].map(i=>({url:i.src,завантажено:i.naturalWidth>0})));
  fs.writeFileSync(path.join(base,'4162-фото-завантаження.json'),JSON.stringify(results,null,2));
  for(let i=0;i<data.length;i++) await page.locator('article').nth(i).screenshot({path:path.join(base,`4162-фото-${i+1}.png`)});
  console.log(JSON.stringify(results));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
