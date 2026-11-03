/* Знімок довгої події з DOM шаблону батареї, без моделі й карток. NODE_PATH=джерела/node_modules node <цей файл>. */
const fs=require('fs'), path=require('path'), Module=require('module');
const repo=path.resolve(__dirname,'..','..','..'), джерела=path.join(repo,'джерела');
const файл=path.join(джерела,'тест_показу.js'), код=fs.readFileSync(файл,'utf8');
const мод=new Module(файл); мод.filename=файл; мод.paths=Module._nodeModulePaths(джерела);
мод._compile(код.slice(0,код.indexOf('(async () => {'))+'\nmodule.exports={сторінка};',файл);
const {дом,w,d}=мод.exports.сторінка({url:'https://example.test/'});
const слова='Зустріч з подругами у старовинній бібліотеці після презентації нашої нової книжки';
w.__довге=слова;
w.eval("ВИПАДОК_ШМАТКИ_П=null; ВИПАДОК_ЛЮДИНІ_П=''; словаЛюдиниП=()=>window.__довге; $('сц-нагода').value=''; малюватиРядокВипадку(випадокШматками());");
for(const екран of d.querySelectorAll('.екран'))екран.style.display='none';
d.getElementById('е-образи').style.display='block';
for(const скрипт of d.querySelectorAll('script'))скрипт.remove();
const html=дом.serialize(); w.close();
(async()=>{
 const {chromium}=require(path.join(джерела,'node_modules','playwright'));
 const браузер=process.env.CHROMIUM || (process.platform==='win32' ? 'C:/Program Files/Google/Chrome/Application/chrome.exe' : null);
 const browser=await chromium.launch({...(браузер ? {executablePath:браузер} : {}),headless:true});
 try {
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  await page.route('**/*',route=>route.abort());
  await page.setContent(html);
  const факт=await page.locator('#обр-випадок').textContent();
  if(!факт.includes(слова))throw Error('Подія загублена у DOM');
  await page.screenshot({path:path.join(__dirname,'390x844.png'),animations:'disabled'});
  console.log('Шапка: повний текст у DOM, 390×844; ширина документа',await page.evaluate(()=>document.documentElement.scrollWidth));
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
