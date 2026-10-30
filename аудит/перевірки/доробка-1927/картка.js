const fs=require('fs'),path=require('path');
// Лише рендер картки з каталогом, без моделі й Python-моста.
// NODE_PATH=<node_modules> FOTO=1 node картка.js <дерево git> <голова.json> [тека знімків]
const root=path.resolve(process.argv[2]);
const {chromium}=require('playwright');
const {підставитиШаблон,зібратиШаблонПоказу}=require(root+'/джерела/показ_шаблон.js');
const cat=JSON.parse(fs.readFileSync(process.argv[3],'utf8')).каталог;
const out=path.resolve(process.argv[4]||__dirname);
const html=підставитиШаблон(зібратиШаблонПоказу(root+'/джерела/показ.html'),{
  __МОДУЛІ_ПОКАЗУ__:'офлайн',__ЗБІРКА_ПОКАЗУ__:'перевірка-1927',__ВІДБИТОК__:'перевірка-1927',
  __ФІД_ПОКАЗУ__:'',__КАТАЛОГ_ПОКАЗУ__:'',__ДОВІДНИК_ПОКАЗУ__:require('child_process').execFileSync('python',['-c','import json,pipeline; print(json.dumps(pipeline.довідник(),ensure_ascii=False))'],{cwd:root+'/джерела',encoding:'utf8',env:{...process.env,PYTHONUTF8:'1'}}).trim()
});
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'chrome'});
 try{
  for(const id of ['ж-00378@vilni.store','ж-00260@25union.com.ua']){
   const page=await browser.newPage({viewport:{width:390,height:844}});
   page.on('pageerror',e=>console.log('Помилка сторінки:',String(e)));
   await page.route('**/*',r=>r.request().url()==='http://review.local/'?r.fulfill({contentType:'text/html',body:html}):r.request().resourceType()==='image'?r.continue():r.abort());
   await page.goto('http://review.local/',{waitUntil:'domcontentloaded'});
   await page.waitForFunction(()=>!!document.getElementById('вк-сценарій').onclick);
   const r=cat.find(r=>r.id===id);
   const card={речі:[{id:r.id,слот:r.слот,назва:r.назва,ціна:r.ціна,фото:r.фото[0],фото_всі:r.фото,урл:r.урл}],знахідки:[]};
   await page.evaluate(card=>{П={картки:[card]};[...document.body.children].forEach(x=>x.style.display='none');document.body.appendChild(рендерКартку(0));},card);
   await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.complete?Promise.resolve():new Promise(res=>{i.onload=i.onerror=res;setTimeout(res,12000)})))});
   console.log(id,await page.evaluate(()=>({фото:[...document.images].map(i=>({url:i.src,ширина:i.naturalWidth})),текст:document.body.innerText})));
   await page.screenshot({path:path.join(out,id.split('@')[0]+'.png'),fullPage:true});
   await page.close();
  }
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
