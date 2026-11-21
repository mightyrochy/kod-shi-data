/* Знімки картки сценарію 390×844 і рядки «записане» ДО/ПІСЛЯ (наряд Картка-записане-її-слово): паспорти — ті, що дає
   `паспорт_з_шару` на записаних відповідях моделі (`мірило.py` пише їх у `паспорти-<мітка>.json`), і йдуть вони на екран тим самим
   шляхом, що в продукті: `змінитиПаспортП` + `застосуватиПаспортДоЕкрана` — а не рукописним об'єктом.
   Запуск з теки `джерела` (шляхи шаблону — від неї):
     ПАСПОРТИ=<файл.json> OUT=<тека> LBL=ДО|ПІСЛЯ [РЕЖИМ=рядки] NODE_PATH=node_modules node ../аудит/проби/Е2-записане-її-слово/знімок.js
   РЕЖИМ=рядки — без знімків друкує JSON: на кожен паспорт рядки, які малює картка (назва, текст, поле, цитата). */
const fs=require('fs'), path=require('path'), Module=require('module');
const repo=path.resolve(__dirname,'..','..','..'), джерела=path.join(repo,'джерела');
const вихід=process.env.OUT||__dirname, мітка=process.env.LBL||'ПІСЛЯ', режим=process.env.РЕЖИМ||'знімки';
const паспорти=JSON.parse(fs.readFileSync(process.env.ПАСПОРТИ||path.join(__dirname,"паспорти.json"),'utf8'));
process.argv.length=2;   // `тест_показу.js` читає argv[2] як шлях до зібраного html
const файл=path.join(джерела,'тест_показу.js'), код=fs.readFileSync(файл,'utf8');
const мод=new Module(файл); мод.filename=файл; мод.paths=Module._nodeModulePaths(джерела);
мод._compile(код.slice(0,код.indexOf('(async () => {'))+'\nmodule.exports={сторінка};',файл);
function показати(п){
 const {дом,w,d}=мод.exports.сторінка({url:'https://example.test/'});
 w.eval("змінитиПаспортП('знімок', 'замінити', "+JSON.stringify(п)+"); застосуватиПаспортДоЕкрана(ПАСПОРТ_П); ВИПАДОК_ЗМІНЕНО_П = false; показатиСценарій()");
 return {дом,w,d};
}
(async()=>{
 if(режим==='рядки'){
  const вих={};
  for(const [ім,п] of Object.entries(паспорти)){
   const {w,d}=показати(п);
   вих[ім]={рядки:[...d.querySelectorAll('#сц-записане>*')].map(р=>({назва:р.children[0].textContent,текст:р.children[1].textContent,
             поле:р.dataset.записане||null,кнопка:р.tagName==='BUTTON',цитата:р.children[1].className==='типово'})),
            слова:d.getElementById('зн-слова').textContent, нагода:d.getElementById('зн-нагода').textContent,
            коли:d.getElementById('зн-коли').textContent};
   w.close();
  }
  console.log(JSON.stringify(вих)); return;
 }
 const {chromium}=require(path.join(джерела,'node_modules','playwright'));
 const browser=await chromium.launch({headless:true});
 try{
  for(const [ім,п] of Object.entries(паспорти)){
   const {дом,w,d}=показати(п);
   for(const екран of d.querySelectorAll('.екран'))екран.style.display='none';
   d.getElementById('е-випадок').style.display='block';
   for(const скрипт of d.querySelectorAll('script'))скрипт.remove();
   const html=дом.serialize(); w.close();
   const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:2});
   await page.route('**/*',route=>route.abort()); await page.setContent(html);
   await page.locator('#сц-картка').scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(вихід,`${ім.replace(/\//g,'-')}-${мітка}-390x844.png`),animations:'disabled'});
   console.log(ім, мітка, (await page.locator('#сц-картка').innerText()).replace(/\n+/g,' | ').slice(0,420));
   await page.close();
  }
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
