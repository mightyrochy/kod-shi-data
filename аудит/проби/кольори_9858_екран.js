/* Функціональні знімки справжнього показу на даних Python-моста, без моделі.
   node аудит/проби/кольори_9858_екран.js <дані.json> <палітра-ДО.js> <тека-виходу>
   На всіх профілях явно обрано аналогову схему для огляду чипа і стрічки. */
const fs = require('fs'), path = require('path');
const {chromium} = require('../../джерела/node_modules/playwright');
const корінь = path.resolve(__dirname, '../..');

async function головна(){
  const сцени = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const вихід = path.resolve(process.argv[4]); fs.mkdirSync(вихід, {recursive:true});
  const html = fs.readFileSync(path.join(корінь, 'index.html'), 'utf8')
    .replace(/<script\b[^>]*>[\s\S]*?<\/script>/gi, '');
  const браузер = await chromium.launch({headless:true, executablePath:process.env.CHROMIUM});
  const факти = [];
  try{
    for (const сцена of сцени) for (const режим of ['ДО','ПІСЛЯ']){
      const стор = await браузер.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
      await стор.route('**/*', route=>route.abort());
      await стор.setContent(html);
      await стор.addScriptTag({content:`
        var ПАЛІТРА=null, ПАЛ_МОВА_ШАРУ=null, ПАСПОРТ_П=null;
        var КОЛІР={шкіра:'так', волосся:'так', очі:'так'};
        var ВИБІР={схема:'аналогова', смуга:'середні', вибір_кольору:{}};
        var ГАМИ=['приглушені','середні','насичені'];
        var ПОЛЯ_ОБХВАТІВ=[], НАПИС_БЕЗ_ТЕКСТУ_П='';
        var $=id=>document.getElementById(id);
        var ел=(tag,cls,text)=>{let e=document.createElement(tag);if(cls)e.className=cls;if(text)e.textContent=text;return e;};
        var станВиборуП=()=>{}, поколінняМістуП=()=>0, чиннеМістуП=()=>true;
        var завершитиДіюЯдра=()=>{}, драпЗЧатомП=()=>({});
        var повідомленнямП=async()=>({записи:[],тексти:{'пал-стан':'Функціональний повтор: аналогова схема'}});
      `});
      const js = fs.readFileSync(режим==='ДО' ? process.argv[3] : path.join(корінь,'джерела/показ/палітра.js'),'utf8');
      await стор.addScriptTag({content:js});
      await стор.evaluate(async дані=>{
        window.містП=async метод=>метод==='палітри'?дані:{повідомлення:{}};
        вхідПалітри=()=>({});
        стилісткаПалітриП=()=>({стан:'готово',р:null});
        document.documentElement.dataset.режим='палітра';
        $('поступ').style.display='none';
        document.querySelectorAll('.екран').forEach(e=>{e.classList.remove('активний');e.style.display='none';});
        const e=$('е-палітра'); e.hidden=false;e.style.display='block';e.classList.add('активний');
        await оновитиПалітруП();
      },сцена[режим]);
      const факт = await стор.evaluate(()=>({стан:$('пал-стан').textContent,
        чипи:[...document.querySelectorAll('#пал-схема .чип')].map(e=>({текст:e.textContent,
          кольори:[...e.querySelectorAll('.зразки i')].map(i=>i.style.backgroundColor)})),
        стрічка:[...document.querySelectorAll('#пал-стрічка i')].map(e=>e.style.backgroundColor)}));
      if (/не порахувалась/.test(факт.стан)) throw new Error(факт.стан);
      await стор.locator('#пал-стрічка').scrollIntoViewIfNeeded();
      await стор.screenshot({path:path.join(вихід,`${сцена.сцена}-${режим}.png`),animations:'disabled'});
      факти.push({сцена:сцена.сцена,режим,...факт});
      await стор.close();
    }
  }finally{await браузер.close();}
  fs.writeFileSync(path.join(вихід,'показ.json'),JSON.stringify(факти,null,2));
  console.log(`Записано ${факти.length} знімків 390×844 і кольори DOM.`);
}
головна().catch(e=>{console.error(e);process.exitCode=1;});
