/* Перевіряє той самий сценарій у справжньому Chromium 390×844. */
const fs=require('fs'),path=require('path'),Module=require('module');
const {chromium}=require('playwright');
const root=process.argv[2],out=process.argv[3],source=path.join(root,'джерела');
process.argv=process.argv.slice(0,2);
const filename=path.join(source,'тест_показу.js'),code=fs.readFileSync(filename,'utf8');
const helper=new Module(filename,module);helper.filename=filename;helper.paths=Module._nodeModulePaths(source);
helper._compile(code.slice(0,code.indexOf('\n(async () => {'))+`\nmodule.exports={html:підставити(шаблон,'каталог_brief.xml','каталог_стенд.xml · 639 речей')};`,filename);
const html=helper.exports.html.replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^\"]*"[^>]*><\/script>/,'');
(async()=>{
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true});
 try{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  await context.route('**/*',r=>r.request().url().startsWith('http://probe.local/')?r.fulfill({contentType:'text/html',body:html}):r.abort());
  const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(String(e)));
  await page.goto('http://probe.local/#міст=http://localhost:8787&т=probe&модель_мови=нема');
  await page.waitForFunction(()=>typeof П!=='undefined' && typeof БІБЛІОТЕКА_П!=='undefined');
  await page.evaluate(()=>{
   чогоБракує=()=>[];немаВизначальнихП=()=>false;
   ПАСПОРТ_П={джерело:'модель',ошатність:[3,5],нагода:'робота',вето:{}};ВИПАДОК_ЗМІНЕНО_П=false;
   стилісткаОбираєП=async()=>null;вхідМостаП=()=>({імʼя:'Перевірка',сід:3});
   містП=async ім=>ім==='запити'?{руки:{'1':'"outfits":','2':'"outfits":','3':'3','4':'4'},правила_рук:{},пул_речей:1}:{};
   перемішатиП=()=>['1','2','3','4'];
   window.__gate=new Promise(r=>window.__release=r);
   window.__oneHand=async поз=>{if(поз)await window.__gate;ЗБ.картки[поз]={рука:String(поз+1),текст:'Сукня для роботи.',
    речі:[{id:'probe-'+поз,назва:'Початкова сукня',ціна:1000,слот:'сукня'}],мітки:[],знахідки:[],збирання:{позиція:поз},етапи:{}};
    ЗБ.готові_мс[поз]=Date.now()-ЗБ.почато;};
  });
  await page.evaluate(src=>{window.__coordinator=eval('(function(однаРука){'+src+'\nreturn зібратиОбразиП;})(window.__oneHand)');window.__build=window.__coordinator();},fs.readFileSync(path.join(source,'показ','збирання_образів.js'),'utf8'));
  await page.waitForFunction(()=>П && П.картки.length===1 && ЗБ.руки_йдуть);
  await page.evaluate(async()=>{await оновитиБібліотеку();const i=БІБЛІОТЕКА_П.плитки.findIndex(x=>String(x.ід).startsWith(П.прогін+'#'));if(i<0)throw Error('нема бібліотеки');await відкритиОбразБібліотекиП(i);});
  await page.evaluate(async()=>{
   містП=async ім=>ім==='від_моделі'?{заміна:{готово:true,річ:{id:'замінена',слот:'сукня'},ід:['замінена'],вердикт:{}}}
     :ім==='показ'?[{id:'замінена',назва:'Обрана сукня після заміни',слот:'сукня',ціна:900}]:{};
   мовоюКарткуП=async()=>{};await замінитиРічП(0,'probe-0');
   if(П.картки[0].речі[0].id!=='замінена')throw Error('заміна не застосувалася');
   window.__node=document.getElementById('к-0');window.__before=П;
  });
  await page.screenshot({path:path.join(out,'бібліотека-до.png')});
  const before=await page.evaluate(()=>({річ:П.картки[0].речі[0].id,підпис:document.getElementById('обр-підпис').textContent}));
  await page.evaluate(async()=>{window.__release();await window.__build;});
  const after=await page.evaluate(()=>({річ:П.картки[0].речі[0].id,той_самий_DOM:document.getElementById('к-0')===window.__node,
   той_самий_П:П===window.__before,підпис:document.getElementById('обр-підпис').textContent,текст:document.getElementById('к-0').innerText}));
  await page.screenshot({path:path.join(out,'бібліотека-після-рук.png')});
  await page.evaluate(async()=>{await оновитиБібліотеку();const i=БІБЛІОТЕКА_П.плитки.findIndex(x=>String(x.ід).startsWith(П.прогін+'#'));await відкритиОбразБібліотекиП(i);});
  await page.screenshot({path:path.join(out,'бібліотека-після-повторного-відкриття.png')});
  const reopened=await page.evaluate(()=>({річ:П.картки[0].речі[0].id,текст:document.getElementById('к-0').innerText}));
  const result={ДО:before,ПІСЛЯ:after,ПОВТОРНЕ_ВІДКРИТТЯ:reopened,помилки:errors};
  fs.writeFileSync(path.join(out,'браузер.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
