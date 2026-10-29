/* FOTO=1: штатний рендер каталожних речей на повній збірці, без відповіді моделі. */
const fs=require('fs'),path=require('path'),{chromium}=require('playwright');
const here=__dirname,root=path.resolve(here,'../../..');
const html=fs.readFileSync(process.argv[2],'utf8');
const items=JSON.parse(fs.readFileSync(path.join(here,'речі-для-очей.json'),'utf8'));
if(items.length!==5)throw new Error('Потрібні п’ять справжніх записів каталогу');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM});
 const results=[];
 try{
  for(const item of items){
   const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true});
   await page.route('**/*',r=>{
    const u=new URL(r.request().url());
    if(u.hostname==='probe.invalid'&&u.pathname==='/')return r.fulfill({contentType:'text/html',body:html});
    if(u.pathname.includes('/шрифти/'))return r.fulfill({path:path.join(root,'шрифти',path.basename(decodeURI(u.pathname)))});
    return r.request().resourceType()==='image'?r.continue():r.abort();
   });
   await page.goto('https://probe.invalid/#model_mova=none');
   await page.waitForFunction(()=>typeof document.getElementById('оц-оцінити').onclick==='function');
   await page.evaluate(item=>{
    П={картки:[{речі:[item],знахідки:[]}]};
    [...document.body.children].forEach(e=>e.style.display='none');
    document.body.appendChild(рендерКартку(0));
   },item);
   await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(resolve=>{i.onload=i.onerror=resolve;setTimeout(resolve,15000)})))});
   results.push(await page.evaluate(id=>({id,текст:document.body.innerText,фото:[...document.images].map(i=>({url:i.src,width:i.naturalWidth}))}),item.id));
   await page.screenshot({path:path.join(here,'екран',item.id.split('@')[0]+'.png'),fullPage:true});
   await page.close();
  }
 }finally{await browser.close();}
 fs.writeFileSync(path.join(here,'картки-фото.json'),JSON.stringify(results,null,2));
 console.log(JSON.stringify(results));
})().catch(e=>{console.error(e);process.exitCode=1;});
