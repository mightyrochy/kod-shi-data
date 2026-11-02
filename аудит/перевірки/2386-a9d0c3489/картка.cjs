const fs=require('fs'),path=require('path'),zlib=require('zlib');
const {chromium}=require('playwright');
const root=process.cwd(),out=path.resolve(root,'../evidence2386-current');
const {прочитатиДовідникJSON,підставитиШаблон,зібратиШаблонПоказу}=require(path.join(root,'джерела/показ_шаблон.js'));
const code=path.join(root,'джерела');
const html=підставитиШаблон(зібратиШаблонПоказу(path.join(code,'показ.html')),{
  __МОДУЛІ_ПОКАЗУ__:'офлайн',__ЗБІРКА_ПОКАЗУ__:'a9d0c34898ac51ec8ea349b10b69ce9666c2210f',__ВІДБИТОК__:'перевірка-2386',
  __ФІД_ПОКАЗУ__:'каталог_повний.xml',__КАТАЛОГ_ПОКАЗУ__:'перевірка-2386',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(code)});
const rows=zlib.gunzipSync(fs.readFileSync(path.join(root,'каталог_записи_v1.jsonl.gz'))).toString('utf8').trim().split('\n').slice(1).map(JSON.parse);
const items=rows.filter(r=>r['ід'].startsWith('ж53-')&&r['адреса'].startsWith('https://25union.com.ua/')).slice(0,2).map(r=>({
  id:r['ід']+'@25union.com.ua',назва:r['назва'],ціна:r['ціна'],урл:r['адреса'],фото:r['кадри'][0],фото_усі:r['кадри'],
  слот:(r['параметри'].find(p=>p[0]==='слот')||[])[1]}));
(async()=>{
const b=await chromium.launch({headless:true,args:['--disable-gpu']});
try{
 const p=await b.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
 await p.route('**/*',r=>r.request().url()==='http://review.local/'?r.fulfill({contentType:'text/html; charset=utf-8',body:html}):r.request().resourceType()==='image'?r.continue():r.abort());
 await p.goto('http://review.local/');
 await p.evaluate(items=>{
  П={збірка:'перевірка-2386',каталог:'28 904 речі',профіль:'Перевірка',картки:[{рука:'1',речі:items,питання:[],як_носити:[],текст:'',опис:''}]};
  document.querySelectorAll('.екран').forEach(e=>{e.style.display='none';e.hidden=true;});
  const card=рендерКартку(0); document.body.replaceChildren(card); card.style.margin='8px';
 },items);
 await p.waitForFunction(()=>[...document.images].every(i=>i.complete),null,{timeout:30000}).catch(()=>{});
 await p.screenshot({path:path.join(out,'картка-390x844.png'),animations:'disabled'});
 fs.writeFileSync(path.join(out,'картка.json'),JSON.stringify(await p.evaluate(()=>({текст:document.body.innerText,фото:[...document.images].map(i=>({url:i.src,видно:i.naturalWidth>0}))})),null,2));
 console.log('Знімок 390×844: реальний шаблон голови, 2 записи каталогу; добір без моделі, FOTO=1 не запускався.');
}finally{await b.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
