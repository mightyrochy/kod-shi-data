/* Обгортка рв6: знімки телефона й стан у мить завершення рук. Жодних живих API. */
const fs = require('fs'), path = require('path'), pw = require('playwright');
const output = path.resolve(process.env.REVIEW_OUT);
fs.mkdirSync(output, {recursive:true});
const mode = process.env.REVIEW_MODE || 'stay';
const launch = pw.chromium.launch.bind(pw.chromium);
pw.chromium.launch = async (...args) => {
  const browser = await launch(...args);
  const context = browser.newContext.bind(browser);
  browser.newContext = async (...a) => {
    const ctx = await context(...a), newPage = ctx.newPage.bind(ctx);
    ctx.newPage = async (...b) => {
      const page = await newPage(...b);
      await page.setViewportSize({width:390,height:844});
      const observer = (async () => {
        await page.waitForFunction(() => typeof ЗБ !== 'undefined' && ЗБ && !ЗБ.готово
          && typeof П !== 'undefined' && П && П.картки.length === 1 && document.getElementById('к-0'), null, {timeout:1200000});
        await page.screenshot({path:path.join(output,'рання.png'),animations:'disabled'});
        const early = await page.evaluate(() => ({підпис:document.getElementById('обр-підпис').textContent,прогін:П.прогін,руки:П.картки.map(k=>k.рука)}));
        if (mode === 'same') await page.evaluate(async () => {await оновитиБібліотеку(); const n=БІБЛІОТЕКА_П.плитки.findIndex(x=>x.ід.startsWith(П.прогін+'#')); відкритиОбразБібліотекиП(n);});
        if (mode === 'other') await page.evaluate(() => {П=JSON.parse(JSON.stringify(П));П.прогін='інший-прогін-перевірки';рендер();});
        else {
          await page.getByText('вдягну як є',{exact:true}).first().click();
          await page.locator('textarea[placeholder^="Наприклад"]').first().fill('Мої слова до кінця рук');
          await page.locator('textarea[placeholder^="Наприклад"]').first().scrollIntoViewIfNeeded();
        }
        const before = await page.evaluate(() => {
          window.__node4350=document.getElementById('к-0');window.__p4350=П;
          const read=()=>({scrollY,підпис:document.getElementById('обр-підпис').textContent,прогін:П.прогін,
            руки:П.картки.map(k=>({рука:k.рука,збій:!!k.збій})),поле:document.querySelector('textarea[placeholder^="Наприклад"]')?.value,
            межі_поля:(()=>{const r=document.querySelector('textarea[placeholder^="Наприклад"]')?.getBoundingClientRect();return r?{верх:r.top,низ:r.bottom,висота:r.height}:null;})(),
            відповідь:В[0]?.верд,той_самий_DOM:document.getElementById('к-0')===window.__node4350,той_самий_обєкт:П===window.__p4350});
          const done=завершитиДіюЯдра;
          const append=дописатиОбрази;
          дописатиОбрази=function(...a){window.__appendBefore4350=read();const r=append(...a);
            requestAnimationFrame(()=>requestAnimationFrame(()=>window.__appendAfter4350=read()));return r;};
          завершитиДіюЯдра=function(name,...a){if(name==='збирання')window.__final4350=read();return done(name,...a);};return read();
        });
        await page.screenshot({path:path.join(output,'дія-до.png'),animations:'disabled'});
        await page.waitForFunction(append=>!!window.__final4350 && (!append || !!window.__appendAfter4350),mode!=='other',{timeout:1200000});
        const final = await page.evaluate(()=>({after:window.__final4350,append_before:window.__appendBefore4350,append_after:window.__appendAfter4350}));
        const after=final.after;
        await page.screenshot({path:path.join(output,'дія-після.png'),animations:'disabled'});
        const storage = await page.evaluate(async pr=>{await ЗАПИС_ОБРАЗУ_П;return {
          бібліотека:(await усіОбрази()).filter(x=>x.прогін===pr).map(x=>({прогін:x.прогін,руки:x.П.картки.map(k=>({рука:k.рука,збій:!!k.збій}))})),
          журнал:(await усіВердикти()).filter(x=>x.прогін===pr).map(x=>({прогін:x.прогін,рука:x.рука,позиція:x.позиція})),діагноз:ЗБ.діагноз};},early.прогін);
        const result={mode,early,before,...final,storage};
        fs.writeFileSync(path.join(output,'стан.json'),JSON.stringify(result,null,2));
        console.log('ПЕРЕВІРКА4350 '+JSON.stringify(result));
        if (process.env.REVIEW_TARGET === '1') for(let i=0;i<after.руки.length;i++){
          await page.evaluate(i=>показатиОбраз(i),i);
          await page.screenshot({path:path.join(output,'картка-'+i+'.png'),animations:'disabled'});
        }
      })().catch(e=>{global.__review4350Error=e;fs.writeFileSync(path.join(output,'помилка.txt'),String(e.stack||e));console.log('ПЕРЕВІРКА4350 ПОМИЛКА '+e);});
      global.__review4350Done=observer;
      const close=browser.close.bind(browser);browser.close=async()=>{await observer;return close();};
      return page;
    };return ctx;
  };return browser;
};
const stand=path.resolve(process.argv[2]);process.argv.splice(2,1);
if(process.env.REVIEW_TARGET === '1'){
  /* Прицільний прохід завершується після мірила; наступні сценарії стенда очікують картку без наших дотиків. */
  const Module=require('module'),m=new Module(stand,module);m.filename=stand;m.paths=Module._nodeModulePaths(path.dirname(stand));
  const needle="  await зведенняПланувальника(стор, 'збирання → чотири картки', відЗбирання);";
  const code=fs.readFileSync(stand,'utf8');if(code.split(needle).length!==2)throw Error('Не знайдено єдиної межі збирання');
  m._compile(code.replace(needle,needle+"\n  await global.__review4350Done; if(global.__review4350Error)throw global.__review4350Error; await браузер.close(); кінецьПрогону('прицільне мірило #4350', провалів ? 1 : 0); return;\n"),stand);
}else require(stand);
