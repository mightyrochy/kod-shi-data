/* Однаковий вхід у справжній рендер зібраного HTML; без відбору й викликів моделей.
   node картки_очі.cjs <index.html> <фікстура-карток.json> <тека знімків> */
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
(async()=>{
  const [htmlFile,fixtureFile,dest]=process.argv.slice(2);
  fs.mkdirSync(dest,{recursive:true});
  const fixture=JSON.parse(fs.readFileSync(fixtureFile,'utf8'));
  const browser=await chromium.launch({headless:true,
    proxy:process.env.HTTPS_PROXY?{server:process.env.HTTPS_PROXY,bypass:'localhost,127.0.0.1'}:undefined});
  try{
    const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,ignoreHTTPSErrors:true});
    await page.route('**/*',route=>{
      if(route.request().url()==='http://127.0.0.1:8799/')return route.fulfill({contentType:'text/html',body:fs.readFileSync(htmlFile)});
      if(route.request().resourceType()==='image')return route.continue();
      return route.abort();
    });
    await page.goto('http://127.0.0.1:8799/',{waitUntil:'domcontentloaded'});
    await page.waitForFunction(()=>typeof рендерКартку==='function');
    await page.waitForFunction(()=>typeof(document.getElementById('сцн-новий')||{}).onclick==='function');
    await page.evaluate(data=>{
      П=data;рендер();
      document.querySelectorAll('img').forEach(im=>im.loading='eager');
    },fixture);
    await page.waitForFunction(()=>Array.from(document.querySelectorAll('#картки img')).every(im=>im.complete),null,{timeout:20000}).catch(()=>{});
    const texts=[];
    for(let i=0;i<fixture.картки.length;i++){
      await page.evaluate(i=>new Promise(done=>{window.показатиОбраз(i,true);window.scrollTo(0,0);
        requestAnimationFrame(()=>requestAnimationFrame(done));}),i);
      const card=page.locator('#к-'+i);await card.waitFor({state:'visible'});
      await page.screenshot({path:path.join(dest,'картка-'+(i+1)+'-390x844.png'),animations:'disabled'});
      await card.screenshot({path:path.join(dest,'картка-'+(i+1)+'-ціла.png'),animations:'disabled'});
      texts.push(await card.innerText());
    }
    fs.writeFileSync(path.join(dest,'текст-карток.txt'),texts.join('\n\n===\n\n'));
    const evidence=await page.evaluate(()=>({карток:document.querySelectorAll('#картки .картка').length,
      фото:Array.from(document.querySelectorAll('#картки img')).map(im=>({url:im.currentSrc,видно:im.naturalWidth>0}))}));
    fs.writeFileSync(path.join(dest,'доказ.json'),JSON.stringify(evidence,null,2));
    console.log('Карток '+evidence.карток+'; зображень '+evidence.фото.length+'; завантажено '+evidence.фото.filter(p=>p.видно).length);
  }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exit(1)});
