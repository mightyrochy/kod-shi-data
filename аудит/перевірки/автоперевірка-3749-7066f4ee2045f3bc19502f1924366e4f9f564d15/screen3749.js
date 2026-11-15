const fs=require('fs'),path=require('path');
const root=path.resolve(process.argv[3]||__dirname);
const {chromium}=require(path.join(root,'review3749/джерела/node_modules/playwright'));
const dir=path.join(root,'screen3749');fs.mkdirSync(dir,{recursive:true});
const data=JSON.parse(fs.readFileSync(path.join(root,'склад3749.json'),'utf8'));
const itemMap=Object.fromEntries(data.каталог_картки.map(i=>[i.id,i]));
const card={рука:'1',ітерацій:1,викликів:0,текст:null,опис:null,підпис:null,
 речі:data.вибір.ід.map(id=>{const i=itemMap[id];return {...i,фото:i.фото[0],фото_усі:i.фото};}),
 мітки:[],знахідки:[],питання:[],етапи:{викликів:0,виклики:[]},свідомі:[],невиконано:null,
 різноманітність:null,мова:[],мова_спроб:0,мова_видано:'так',фото_не_ті:[],дібрав_код_слоти:[]};
const pack={в:'ПОКАЗ-V1',збірка:'перевірка-3749',каталог:'каталог · 6 речей',профіль:'Оля',розклад:'1234',прогін:'пр-3749',
 випадок_рядок:'Робота · офіс',пул:6,картки:[card]};
(async()=>{const browser=await chromium.launch({executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe',headless:true,args:['--disable-gpu']});
const result=[];
try{for(const [stage,file] of [['до','base3749/index.html'],['після','3749-head.html']].filter(x=>!process.argv[2]||x[0]===process.argv[2])){
 const page=await browser.newPage({viewport:{width:390,height:844},reducedMotion:'reduce'});
 const html=fs.readFileSync(path.join(root,file));let requests=0;
 await page.route('**/*',async r=>{const u=r.request().url();
  if(u==='http://127.0.0.1:8765/')return r.fulfill({contentType:'text/html; charset=utf-8',body:html});
  if(process.env.FOTO==='1'&&r.request().resourceType()==='image'){
   try{return await r.fulfill({response:await r.fetch({timeout:12000})});}catch(e){console.log('КАДР',new URL(u).hostname,e.message.split('\n')[0]);return r.abort();}}
  if(/api.*(openai|google|anthropic)|\/chat\/completions/.test(u))requests++;
  return r.abort();});
 await page.goto('http://127.0.0.1:8765/',{waitUntil:'domcontentloaded'});
 await page.waitForFunction(()=>typeof (document.getElementById('сцн-новий')||{}).onclick==='function');
 await page.evaluate(pack=>{П=pack;рендер();},pack);
 await page.waitForFunction(()=>document.querySelectorAll('#картки .картка .список .річ').length===6);
 await page.waitForFunction(()=>[...document.querySelectorAll('#картки img')].every(i=>i.complete),{},{timeout:25000}).catch(()=>{});
 const info=await page.evaluate(()=>({текст:document.querySelector('#картки .картка').innerText,
  фото:[...document.querySelectorAll('#картки .список img')].map(i=>({src:i.src,завантажено:i.complete&&i.naturalWidth>0})),
  ширина:document.documentElement.scrollWidth}));
 await page.locator('#картки .картка').screenshot({path:path.join(dir,stage+'-картка.png')});
 await page.screenshot({path:path.join(dir,stage+'-390x844.png')});
 result.push({stage,viewport:'390x844',FOTO:process.env.FOTO,запитів_моделі:requests,...info});await page.close();
}}finally{await browser.close();}
fs.writeFileSync(path.join(dir,'дані-'+(process.argv[2]||'разом')+'.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
