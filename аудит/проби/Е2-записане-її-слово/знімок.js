/* Знімки картки сценарію 390×844 ДО/ПІСЛЯ (наряд Картка-записане-її-слово): паспорти с8 і с5 — з записаної відповіді моделі
   (`мірило.py`). Запуск з теки `джерела` (шляхи шаблону — від неї): OUT=<тека> LBL=ДО|ПІСЛЯ NODE_PATH=node_modules node ../аудит/проби/Е2-записане-її-слово/знімок.js
   На дереві бази (git worktree) рядків «записане» нема — малювача там нема. */
const fs=require('fs'), path=require('path'), Module=require('module');
const repo=path.resolve(__dirname,'..','..','..'), джерела=path.join(repo,'джерела');
const вихід=process.env.OUT||__dirname, мітка=process.env.LBL||'ПІСЛЯ';
process.argv.length=2;   // `тест_показу.js` читає argv[2] як шлях до зібраного html
const файл=path.join(джерела,'тест_показу.js'), код=fs.readFileSync(файл,'utf8');
const мод=new Module(файл); мод.filename=файл; мод.paths=Module._nodeModulePaths(джерела);
мод._compile(код.slice(0,код.indexOf('(async () => {'))+'\nmodule.exports={сторінка};',файл);
const СЦЕНИ={
 с8:{нагода:'робота',місце:'офіс',місце_слова:'Офіс',пора:null,подія:'на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин',рух:'walk',дорога_пішки_хв:20,
     смуга_погоди:'deep_frost',опади:'snow',ошатність:[3,5],
     цитати_полів:{нагода:'йду на роботу',місце:'на роботу',рух:'пішки 20 хвилин',дорога_пішки_хв:'пішки 20 хвилин',смуга_погоди:'мінус десять',опади:'сніг'}},
 с5:{нагода:'весілля_гість',місце:'весілля_денне',місце_слова:'Весілля',пора:'день',подія:'гостя на весіллі сестри, церемонія надворі, потім ресторан',
     формат:'mixed',місяць:'august',роль:'guest',ошатність:[6,8],
     цитати_полів:{нагода:'я гостя на весіллі',формат:'церемонія надворі, потім ресторан',місяць:'в серпні',пора:'о 16:00',роль:'я гостя'}}};
(async()=>{
 const {chromium}=require(path.join(джерела,'node_modules','playwright'));
 const browser=await chromium.launch({headless:true});
 try{
  for(const [ім,п] of Object.entries(СЦЕНИ)){
   const {дом,w,d}=мод.exports.сторінка({url:'https://example.test/'});
   w.eval("змінитиПаспортП('знімок', 'замінити', Object.assign({джерело:'модель', джерело_полів:{}, вето:{типи:[],тканини:[],принти:[],кольори:[],зони:[]}}, "+JSON.stringify(п)+")); ВИПАДОК_ЗМІНЕНО_П = false; показатиСценарій()");
   for(const екран of d.querySelectorAll('.екран'))екран.style.display='none';
   d.getElementById('е-випадок').style.display='block';
   for(const скрипт of d.querySelectorAll('script'))скрипт.remove();
   const html=дом.serialize(); w.close();
   const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:2});
   await page.route('**/*',route=>route.abort()); await page.setContent(html);
   const картка=page.locator('#сц-картка'); await картка.scrollIntoViewIfNeeded();
   await page.screenshot({path:path.join(вихід,`${ім}-${мітка}-390x844.png`),animations:'disabled'});
   console.log(ім, мітка, (await page.locator('#сц-картка').innerText()).replace(/\n+/g,' | ').slice(0,420));
   await page.close();
  }
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
