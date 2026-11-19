/* Знімки раннього показу на штатному каталожному стенді. */
const fs=require('fs'),path=require('path'),pw=require('playwright'),Module=require('module');
const root=process.argv[2],site=process.argv[3],out=process.argv[4];fs.mkdirSync(out,{recursive:true});
const launch=pw.chromium.launch.bind(pw.chromium);
pw.chromium.launch=async(...args)=>{
 const browser=await launch(...args),newContext=browser.newContext.bind(browser);
 browser.newContext=async(...args)=>{
  const context=await newContext(...args),newPage=context.newPage.bind(context);
  context.newPage=async(...args)=>{
   const page=await newPage(...args),wait=page.waitForFunction.bind(page);
   const observer=(async()=>{
    await wait(()=>typeof П!=='undefined' && П && typeof ЗБ!=='undefined' && ЗБ && ЗБ.руки_йдуть,null,{timeout:1200000});
    await page.setViewportSize({width:390,height:844});
    await page.getByText('вдягну як є',{exact:true}).first().click();
    await page.locator('textarea[placeholder^="Наприклад"]').first().fill('слова перевірки до кінця рук');
    await page.evaluate(()=>{window.scrollTo(0,900);window.__probeCard=document.getElementById('к-0');
     window.__probeScroll=[];const scroll=window.scrollTo;window.scrollTo=function(...args){window.__probeScroll.push(args);return scroll.apply(this,args)};});
    const read=()=>page.evaluate(()=>({готово:ЗБ.готово,прогін:П.прогін,руки:П.картки.map(x=>x.рука),scrollY,
     слова:document.querySelector('textarea[placeholder^="Наприклад"]').value,
     підпис:document.getElementById('обр-підпис').textContent,той_самий_DOM:document.getElementById('к-0')===window.__probeCard,
     scrollTo:window.__probeScroll}));
    await page.evaluate(()=>document.querySelectorAll('#к-0 img').forEach(i=>i.loading='eager'));
    await wait(()=>[...document.querySelectorAll('#к-0 img')].every(i=>i.complete),null,{timeout:30000});
    const before=await read();await page.screenshot({path:path.join(out,'каталог-до-кінця-рук.png')});
    await wait(()=>ЗБ.готово,null,{timeout:1200000});
    const after=await read();await page.screenshot({path:path.join(out,'каталог-після-кінця-рук.png')});
    fs.writeFileSync(path.join(out,'каталог.json'),JSON.stringify({ДО:before,ПІСЛЯ:after},null,2));
    console.log('ПЕРЕВІРКА КАТАЛОГУ: '+JSON.stringify({ДО:before,ПІСЛЯ:after}));
   })();
   observer.catch(e=>console.error('ПОМИЛКА ПРОБИ КАТАЛОГУ',e));
   page.waitForFunction=async(fn,...args)=>{const result=await wait(fn,...args);
    if(String(fn).includes('ЗБ.готово') && !String(fn).includes('руки_йдуть')
       && await page.evaluate(()=>typeof ЗБ!=='undefined' && ЗБ && ЗБ.готово))await observer;return result;};
   return page;
  };return context;
 };return browser;
};
process.argv=[process.argv[0],path.join(root,'аудит','проби','рв6_стенд.js'),'http://127.0.0.1:8765',site,
 'C:/Users/gemini/gemini-runs/pyodide-0.26.4','3'];
const filename=process.argv[1],marker='  /* 3. промпти між ітераціями';
const source=fs.readFileSync(filename,'utf8');if(!source.includes(marker))throw Error('маркер прицільного завершення не знайдено');
const instrumented=source.replace(marker,"  await браузер.close(); кінецьПрогону('ПРИЦІЛЬНО: початковий каталог, руки 1–4, фото й знімки', провалів ? 1 : 0); return;\n"+marker);
const helper=new Module(filename,module);helper.filename=filename;helper.paths=Module._nodeModulePaths(path.dirname(filename));helper._compile(instrumented,filename);
