const fs=require('fs'), path=require('path');
const root=path.resolve(__dirname,'pr2386'), out=path.resolve(__dirname,'evidence2386');
const {chromium}=require(path.join(root,'джерела/node_modules/playwright'));
const {прочитатиДовідникJSON,підставитиШаблон,зібратиШаблонПоказу}=require(path.join(root,'джерела/показ_шаблон.js'));
const photos=JSON.parse(fs.readFileSync(path.join(out,'photos.json'),'utf8'));
const code=path.join(root,'джерела');
const html=підставитиШаблон(зібратиШаблонПоказу(path.join(code,'показ.html')),{__МОДУЛІ_ПОКАЗУ__:'офлайн',__ЗБІРКА_ПОКАЗУ__:'review2386',__ВІДБИТОК__:'review2386',__ФІД_ПОКАЗУ__:'каталог_повний.xml',__КАТАЛОГ_ПОКАЗУ__:'офлайн',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(code)});
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--disable-gpu']});
 const results=[];
 try {
  for(let index=0;index<3;index++){
   const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,ignoreHTTPSErrors:true});
   const errors=[], network=[];page.on('pageerror',e=>errors.push(String(e)));
   page.on('response',r=>{if(photos.some(p=>p.фото===r.url()))network.push({адреса:r.url(),код:r.status()});});
   page.on('requestfailed',r=>{if(photos.some(p=>p.фото===r.url()))network.push({адреса:r.url(),помилка:r.failure()});});
   await page.route('**/*',route=>{
    const url=route.request().url();
    if(url==='https://review.local/')return route.fulfill({contentType:'text/html',body:html});
    const photo=photos.find(p=>p.фото===url);
    if(photo&&photo.файл)return route.fulfill({path:photo.файл,contentType:photo.тип});
    if(process.env.FOTO==='1'&&photo)return route.continue();
    return route.abort();
   });
   await page.goto('https://review.local/#model_mova=none');
   await page.waitForFunction(()=>typeof document.getElementById('оц-оцінити').onclick==='function');
   const items=photos.slice(index*4,index*4+4);
   await page.evaluate(items=>{
    const card={речі:items.map(p=>({id:p.ід,назва:p.назва,ціна:p.ціна,урл:p.адреса,фото:p.фото,кадри:[p.фото]})),опис:'',як_носити:[],питання:[],питання_жінці:[]};
    П={картки:[card],вердикти:{}};
    document.getElementById('картки').replaceChildren(рендерКартку(0));
    document.querySelectorAll('.екран').forEach(e=>e.style.display='none');
    document.getElementById('е-образи').style.display='block';
    document.querySelectorAll('img').forEach(i=>i.loading='eager');
   },items);
   await page.locator('#к-0').scrollIntoViewIfNeeded();
   await page.waitForFunction(()=>[...document.querySelectorAll('#к-0 img')].every(i=>i.complete),null,{timeout:30000});
   await page.screenshot({path:path.join(out,`card-${index}.png`)});
   await page.locator('#к-0').screenshot({path:path.join(out,`card-${index}-full.png`)});
   results.push({номер:index,ід:items.map(p=>p.ід),помилки:errors,мережа:network,...await page.evaluate(()=>({текст:document.getElementById('к-0').innerText,фото:[...document.querySelectorAll('#к-0 img')].map(i=>({url:i.currentSrc,ширина:i.naturalWidth,висота:i.naturalHeight})),горизонтальна_прокрутка:document.documentElement.scrollWidth>390}))});
   await page.close();
  }
 } finally {await browser.close();}
 fs.writeFileSync(path.join(out,'render.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
