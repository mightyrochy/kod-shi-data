const fs = require('fs'), path = require('path');
const root = process.cwd(), src=path.join(root,'джерела');
const {chromium}=require(path.join(src,'node_modules/playwright'));
const {зібратиШаблонПоказу,підставитиШаблон,прочитатиДовідникJSON}=require(path.join(src,'показ_шаблон.js'));
(async()=>{
 const html=підставитиШаблон(зібратиШаблонПоказу(path.join(src,'показ.html')),{
 __МОДУЛІ_ПОКАЗУ__:'офлайн',__ЗБІРКА_ПОКАЗУ__:'перевірка-2306',__ВІДБИТОК__:'a8c07b72',__ФІД_ПОКАЗУ__:'каталог_brief.xml',__КАТАЛОГ_ПОКАЗУ__:'офлайн',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(src)});
 const browser=await chromium.launch({headless:true,executablePath:process.env.CHROME_PATH||'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',args:['--disable-gpu']});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.route('**/*',r=>r.request().url()==='http://review.local/'?r.fulfill({contentType:'text/html',body:html}):r.abort());
  await page.goto('http://review.local/');
  await page.waitForFunction(()=>typeof рендер==='function');
  const result=await page.evaluate(()=>{
   П={в:'ПОКАЗ-V1',збірка:'перевірка-2306',каталог:'офлайн-фікстура',профіль:'Оля',розклад:'1',картки:[{рука:'1',текст:'Образ на прогулянку.',речі:[{id:'її-с1',назва:'Світлі джинси кльош',слот:'низ',власна:true,чия:'моя'},{id:'ж-00010@gepur.com',назва:'Підвіска',ціна:499,слот:'прикраса',колір:'срібний',код_кольору:'silvery'}],мітки:[],знахідки:[]}]};
   рендер(); document.getElementById('картки').scrollIntoView({block:'start'});
   return {карток:document.getElementById('картки').children.length,текст:document.getElementById('картки').textContent};
  });
  await page.screenshot({path:path.resolve(process.argv[2]||path.join(__dirname,'картка-390x844.png')),animations:'disabled'});
  console.log(JSON.stringify({viewport:[390,844],...result,помилки:errors},null,2));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
