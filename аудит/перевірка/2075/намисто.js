/* Звичайне відкриття публічної картки товару в Chromium; без повторів відмови. */
const {chromium}=require('playwright');
const path=require('path'),fs=require('fs');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM});
 try {
  const page=await browser.newPage({viewport:{width:1200,height:1000}});
  const url='https://theoriginals.com.ua/zhinkam/aksesuary/prykrasy-1/bizhuteriya/namysta-1/zolotyste-namysto-z-pidvisamy';
  const response=await page.goto(url,{waitUntil:'domcontentloaded',timeout:45000});
  const status=response.status();
  console.log(JSON.stringify({url,status}));
  if(status!==200)return;
  await page.waitForLoadState('networkidle',{timeout:15000}).catch(()=>{});
  const images=await page.locator('img').evaluateAll(xs=>xs.filter(x=>x.naturalWidth>200).map(x=>({src:x.currentSrc,width:x.naturalWidth,height:x.naturalHeight})));
  fs.writeFileSync(path.join(__dirname,'намисто-браузер.json'),JSON.stringify({url,status,images},null,2));
  await page.screenshot({path:path.join(__dirname,'намисто-браузер.png')});
  console.log(JSON.stringify(images));
 }finally{await browser.close();}
})().catch(e=>{console.error(String(e));process.exitCode=1;});
