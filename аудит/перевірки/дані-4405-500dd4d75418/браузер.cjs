const fs = require('fs'), path = require('path'), cp = require('child_process');
const root = path.resolve(process.argv[2] || path.join(process.env.TEMP, 'review4405-head', 'джерела'));
const out = path.resolve(process.argv[3] || process.env.TEMP); fs.mkdirSync(out, {recursive:true});
const {chromium} = require(path.join(root,'node_modules/playwright'));
const helper = require(path.join(root,'показ_шаблон.js'));
let raw = fs.readFileSync(path.join(root,'показ.html'),'utf8');
const measured = {стан:'вимір', причини:[], джерело:'uncontrolled',
 шкіра:{lab:[65.37,18.59,26.02],hex:'#cd9171',n:900,se_L:1,se_ab:.2,точки:[[63.8,19.54,26.86],[65.37,18.59,26.02],[77.56,17.18,23.93]],шум_зон:1.1},
 волосся:{lab:[28.93,10.23,19.22],hex:'#5c3e27',n:900,se_L:1,se_ab:.2},
 очі:{lab:[79.03,17.19,24.78],hex:'#f2b797',n:900,se_L:1,se_ab:.2}};
const model = {стан:'готово',шкіра:['#e5b79b'],волосся:['#734525'],очі:'#6e512c',кільце:'#312014',освітлення:{cast:'none',correction:'none'},зони:{}};
(async()=>{
 const browser = await chromium.launch({headless:true});
 const results = [];
 for(const mode of ['до','після','поза_воротами']){
  let html = helper.зібратиШаблонПоказу(raw,root);
  if(mode==='до') for(const name of ['кольори.js','палітра.js','оцінка.js']){
   const head = fs.readFileSync(path.join(root,'показ',name),'utf8');
   const base = cp.execFileSync('git',['show','e9a55cfadc87b8752ed94f88824d4806aed554dc:джерела/показ/'+name],{encoding:'utf8',maxBuffer:1000000});
   if(!html.includes(head)) throw Error('Модуль не знайдено: '+name);
   html=html.replace(head,()=>base);
  }
  html=helper.підставитиШаблон(html,{
   __МОДУЛІ_ПОКАЗУ__:'ЗАГЛУШКА',__ЗБІРКА_ПОКАЗУ__:'500dd4d75418',__ВІДБИТОК__:'500dd4d75418',
   __ФІД_ПОКАЗУ__:'каталог_brief.xml',__КАТАЛОГ_ПОКАЗУ__:'каталог',
   __ДОВІДНИК_ПОКАЗУ__:helper.прочитатиДовідникJSON(root)
  });
  const page = await browser.newPage({viewport:{width:390,height:844}});
  await page.route('**/*',r=>r.request().url()==='https://review.local/'?r.fulfill({contentType:'text/html',body:html}):r.abort());
  await page.goto('https://review.local/');
  await page.waitForFunction(()=>typeof Екран!=='undefined' && Екран.стан.запущено===true);
  await page.evaluate(({model,measured,mode})=>{
   window.__model=model;window.__measured=measured;
   вимірПортретаП=async()=>mode==='поза_воротами'?{стан:'поза_воротами',причини:['portrait_uneven_light']}:measured;
   повідомленнямП=async()=>({тексти:{портрет:'Потрібне фото зі світлом рівномірно на обидві щоки.'}});
   показКольоруП({біля:'зчитати'});
   return застосуватиКольори(model,null,'кадр-проби');
  },{model,measured,mode});
  await page.evaluate(()=>відкритиПрофіль('кол-блок'));
  await page.locator('#кол-блок').scrollIntoViewIfNeeded();
  const result=await page.evaluate(()=>({колір:КОЛІР,напис:document.getElementById('кол-стан').textContent,
    стилістка:вхідСтилісткиП(),вхід:вхідПалітри(),оцінка:ПОЛЯ_ПРОФІЛЮ_ОЦІНКИ.includes('портрет_вимір'),
    плитки:[...document.querySelectorAll('#кол-свотчі i')].map(i=>i.style.background)}));
  const dest=path.join(out,'review4405-'+mode+'.png');
  await page.screenshot({path:dest});
  results.push({режим:mode,...result});
  console.log(mode,result.колір.шкіра,!!result.стилістка.портрет_вимір,result.оцінка,result.напис);
  await page.close();
 }
 fs.writeFileSync(path.join(out,'review4405-browser.json'),JSON.stringify(results,null,2));
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
