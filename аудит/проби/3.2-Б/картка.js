/* 390×844 на шаблоні з довідником кожного дерева; без Pyodide й моделей. Стару основу можна передати аргументом. */
const fs=require('fs'),path=require('path'),repo=path.resolve(__dirname,'../../..');
const {chromium}=require(path.join(repo,'джерела/node_modules/playwright'));
const {прочитатиДовідникJSON,підставитиШаблон}=require(path.join(repo,'джерела/показ_шаблон.js'));
(async()=>{
const браузер=await chromium.launch({headless:true,executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
for(const [ім,root] of [...(process.argv[2]?[['до',path.resolve(process.argv[2])]]:[]),['після',repo]]){
 const джерело=root+'/джерела';let html=підставитиШаблон(fs.readFileSync(джерело+'/показ.html','utf8'),{
 __МОДУЛІ_ПОКАЗУ__:'ЗАГЛУШКА',__ЗБІРКА_ПОКАЗУ__:'3.2-Б',__ВІДБИТОК__:'3.2-Б',__ФІД_ПОКАЗУ__:'',__КАТАЛОГ_ПОКАЗУ__:'',__ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(джерело)});
 const page=await браузер.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
 await page.route('**/*',route=>route.abort());await page.setContent(html,{waitUntil:'domcontentloaded'});
 console.log(ім,await page.evaluate(()=>{
  режим('сценарій');
  ПАСПОРТ_П={джерело:'модель',подія:'Співбесіда в офісі',нагода:'співбесіда',місце:'офіс',ошатність:[7,7],причина_ошатності:'evaluated',джерело_полів:{ошатність:'розмова'}};
  ВИПАДОК_ЗМІНЕНО_П=false;застосуватиПаспортДоЕкрана(ПАСПОРТ_П);малюватиКарткуСценарію();
  document.querySelectorAll('[id^="е-"]').forEach(e=>{if(e.id!=='е-випадок'&&e.classList.contains('екран'))e.style.display='none'});
  const к=document.getElementById('сц-картка');к.hidden=false;к.scrollIntoView({block:'center'});
  return {рядок:ошатністьДжерело(),поля:ПОЛЯ_ВИПАДКУ.length,типові:ПОЛЯ_ТИПОВІ_ЧИСЛА};
 }));
 await page.screenshot({animations:'disabled',path:path.join(__dirname,'картка-'+ім+'.png')});if(ім==='після')console.log('Старий стан',await page.evaluate(()=>{застосуватиСценарій({поля:{'сц-нагода':'весілля_денне','сц-місце':'весілля_вечірнє'},паспорт:{джерело:'модель',нагода:'весілля_денне',місце:'весілля_вечірнє'}});return {нагода:ПАСПОРТ_П.нагода,місце:ПАСПОРТ_П.місце,поле:document.getElementById('сц-нагода').value}}));
 await page.close();
}
await браузер.close();
})().catch(e=>{console.error(e);process.exit(1)});
