/* Лише спостереження: первинний таймаут стенда завжди кидається повторно. */
const pw = require('playwright');
const launch = pw.chromium.launch.bind(pw.chromium);
pw.chromium.launch = async (...args) => {
 const browser = await launch(...args), newContext = browser.newContext.bind(browser);
 browser.newContext = async (...ca) => {
  const context = await newContext(...ca), newPage = context.newPage.bind(context);
  context.newPage = async (...pa) => {
   const page = await newPage(...pa), wait = page.waitForFunction.bind(page), evaluate = page.evaluate.bind(page);
   page.on('console', m => {if(m.type() === 'error') console.log('ДІАГНОСТИКА КОНСОЛІ:', m.text());});
   page.on('pageerror', e => console.log('ДІАГНОСТИКА СТОРІНКИ:',String(e)));
   page.waitForFunction = async (...wa) => {try{return await wait(...wa);}catch(e){
    const state = await evaluate(() => ({режим: typeof РЕЖИМ !== 'undefined' && РЕЖИМ, готово: typeof ЗБ !== 'undefined' && ЗБ && ЗБ.готово, діагноз: typeof ЗБ !== 'undefined' && ЗБ && ЗБ.діагноз && ЗБ.діагноз.slice(-8), міст:typeof ЧЕКАЮТЬ_МОСТА_П !== 'undefined' && [...ЧЕКАЮТЬ_МОСТА_П.values()]})).catch(()=>null);
    console.log('ДІАГНОСТИКА ТАЙМАУТУ:',JSON.stringify(state));
    if(String(wa[0]).includes('очікування')){
     try{
      await wait(() => typeof П !== 'undefined' && П && П.картки && П.картки.length === 4 && typeof ЗБ !== 'undefined' && ЗБ.готово, null, {timeout:300000});
      console.log('ДІАГНОСТИКА ПІСЛЯ ТАЙМАУТУ (провал стенда збережено):',JSON.stringify(await evaluate(() => {
       const в = (П.знімок || {}).вхід || {};
       return {знімок: {в:в.в,колір:!!(в.колір || {}).шкіра,мірки:!!(в.мірки || {}).обхвати,драп:!!в.драп,сценарій:!!в.сценарій,палітра:!!в.палітра},картки:П.картки.map(к => ({рука:к.рука,питань:(к.питання || []).length,речень:(к.питання_жінці || []).length})),діагноз:ЗБ.діагноз.slice(-8)};
      })));
     }catch(extra){console.log('ДОДАТКОВЕ СПОСТЕРЕЖЕННЯ:',String(extra).slice(0,350));}
    }
    throw e;}};
   return page;
  };return context;
 };return browser;
};
