/* Ч4 (Q10): повтор с5/с8 проходу 21.11 на тій самій збірці (2c9c872f) у Chromium + Pyodide 0.26.4 з диска, БЕЗ МЕРЕЖІ:
   міст відповідає записами `стенд/службове/<с>/обміни.jsonl` (запит → відповідь; точний збіг тіла — та сама відповідь,
   інакше — невзятий запис із найдовшим спільним префіксом, і розбіжність пишеться), усе інше — abort.
   Кожен виклик воркера Python (`{тип:'виклик'}`) і його відповідь пишуться у `<вихід>/стенд/службове/<с>/воркер.jsonl` —
   входи для `знімок_мосту.py cpython` і вихід Pyodide для порівняння.
   Браузер — з проксі 127.0.0.1:9 (мертвий): мережі нема й для того, що route() не перехопив.
   Запуск: STOR=/tmp/ч4/стор PYODIDE=/tmp/pyodide OBMINY=<обміни.jsonl> VIEWPORT=… ONE_PASS=1 node відтворення.js <с> <вихід> 0
   Решта — `аудит/проби/Живий-через-міст/стенд/повтор_міст.js` як є. */
const fs = require('fs'), path = require('path'), http = require('http');
const {chromium} = require('playwright');
const {знімокРук, доЗавантажитиФото} = require('/home/user/kod-shi-data/аудит/проби/живий-як-людина-4/стенд/руки_зі_сторінки.js');
const джерело = fs.readFileSync(path.join('/home/user/kod-shi-data/аудит/проби/живий-як-людина-4/стенд/людина.js'), 'utf8');
// Спільне визначення доступних на екрані елементів; жодного виклику моделі-жінки.
const екран = eval('(' + джерело.slice(джерело.indexOf('async function екран('), джерело.indexOf('const {знімокРук')).trim() + ')');
const ситуація = process.argv[2], вихід = path.resolve(process.argv[3]), порт = Number(process.argv[4]);
const перший = path.resolve('/home/user/kod-shi-data/аудит/проби/живий-як-людина-3', process.env.SCENE_BASE || ситуація);
const тека = path.join(вихід, ситуація), службове = path.join(вихід, 'стенд/службове', ситуація);
for (const p of [тека, службове, path.join(тека, 'знімки')]) fs.mkdirSync(p, {recursive:true});
fs.copyFileSync(path.join(перший,'ситуація.md'),path.join(тека,'ситуація.md'));
const сон = n => new Promise(r=>setTimeout(r,n));
const запис = (name, text) => fs.appendFileSync(path.join(тека,name),text+'\n');
const ЗАПИСИ=fs.readFileSync(process.env.OBMINY,'utf8').split('\n').filter(Boolean).map((r,i)=>({і:i,...JSON.parse(r)})).filter(з=>з.запит&&з.відповідь!=null);
const взятоЗ=new Set(), мережа=[];
function спільний(а,б){let i=0;const n=Math.min(а.length,б.length);while(i<n&&а[i]===б[i])i++;return i;}
const СЛОВА_СЦЕНИ = process.env.SCENE_WORDS || null;
const дії = [...fs.readFileSync(path.join(перший,'хід.md'),'utf8').matchAll(/### (\d+) ·[^\n]*\n([\s\S]*?)(?=\n### |$)/g)].map(m=>({крок:Number(m[1]),текст:(m[2].match(/^- дія: ([\s\S]*?)(?=\n\n|$)/m)||[])[1]})).filter(x=>x.текст);
if(СЛОВА_СЦЕНИ){const р=дії.findIndex(x=>/^надрукувала в «поле для тексту: підказка: Напиши, як подрузі/.test(x.текст));if(р<0){console.error('нема кроку з нагодою');process.exit(3);}дії[р].текст=дії[р].текст.replace(/»: «[\s\S]*»$/,'»: «'+СЛОВА_СЦЕНИ.replace(/\$/g,'$$$$')+'»');}
if(process.env.REPLAY_PLAN){console.log(JSON.stringify({ситуація,дій:дії.length,слова:дії.filter(x=>x.текст.startsWith('надрукувала в ')),новий:дії.filter(x=>x.текст==='натиснула «кнопка: Новий»')}));process.exit(0);}
let викликів=0, браузер, стор, активні=0, останнійВиклик=0, крок=0, прохід=1, слів=0, пропущено=0, блокер=null;
const summary={ситуація,початок:new Date().toISOString(),слова:[],розбіжності:[],руки:[]};
function розбіжність(дія,причина,стан){
  const r={прохід,крок:дія.крок,дія:дія.текст,причина,екран:стан.текст,елементи:стан.елем};
  summary.розбіжності.push(r);
  fs.appendFileSync(path.join(тека,'розбіжності.md'),`\n- крок ${дія.крок} (прохід ${прохід}) · мало бути: ${дія.текст.replace(/\n/g,' ⏎ ')} · було: ${причина}; на екрані: ${стан.текст.replace(/\n/g,' / ').slice(0,900)}; можна було натиснути: ${(стан.елем||[]).slice(0,40).join(' | ')}\n`);
}
async function кадр(опис,показати){
  крок++; const ім=String(крок).padStart(4,'0')+'.jpg';
  // Знімок не успадковує 15-секундну стелю дотиків: у спробі /6
  // Chromium перевищив її під час збирання, і стенд обірвав другий прохід.
  await стор.screenshot({path:path.join(тека,'знімки',ім),type:'jpeg',quality:72,timeout:0});
  const стан=await екран(стор);
  запис('хід.md',`\n### ${крок} · ${new Date().toISOString()} · прохід ${прохід} · знімок \`знімки/${ім}\`\n- дія скрипта: ${опис}${показати?'\n- на екрані: '+стан.текст.replace(/\n/g,' / ').slice(0,700):''}`);
  fs.appendFileSync(path.join(службове,'екрани.jsonl'),JSON.stringify({крок,прохід,опис,...стан})+'\n');
  const руки=await знімокРук(стор);
  if(руки && руки.готово){summary.руки.push({крок,прохід,...руки});fs.appendFileSync(path.join(службове,'руки.jsonl'),JSON.stringify({крок,прохід,...руки})+'\n');}
  return стан;
}
async function спокій(){
  // Після дотику воркер ще може готувати запит. Чекаємо й видимий стан
  // сторінки, щоб не пропускати кнопки під час «Думаю…» до першого HTTP.
  let кадрО=Date.now();
  while(true){
    if(блокер && !активні)throw new Error(блокер);
    const думає=await стор.evaluate(()=>{
      const ткання=document.getElementById('е-очікування');
      const палітра=document.getElementById('пал-стан');
      return (ткання && ткання.getBoundingClientRect().height>0) ||
        (палітра && палітра.getBoundingClientRect().height>0 && /^(Ще мить…|…)\s*$/.test(палітра.innerText)) ||
        Array.from(document.querySelectorAll('input,textarea')).some(x=>x.disabled && x.getBoundingClientRect().height>0) ||
        /Думаю…/.test(document.body.innerText);
    });
    if(!активні && !думає && Date.now()-останнійВиклик>=1500)break;
    await сон(2000);
    if(Date.now()-кадрО>=15000){await кадр('чекає відповіді моделі й завершення роботи сторінки');кадрО=Date.now();}
  }
}
function відповідність(рядок,мітка){
  const a=рядок.replace(/^\[\d+\] /,'').replace(/ · зараз:.*$/,'').replace(/\s+/g,' ').trim();
  const b=мітка.replace(/ · зараз:.*$/,'').replace(/\s+/g,' ').trim();
  if(a===b || a.startsWith(b) || b.startsWith(a))return 2;
  // Значення рядків картки сценарію може змінитися, сам рядок лишається тим самим.
  if(/^кнопка: (Нагода|Де|Коли|Погода|Ошатність|Стиль) /.test(b))return a.startsWith(b.split(' ').slice(0,2).join(' ')+' ')?1:0;
  return 0;
}
async function знайти(мітка){
  for(const напрям of [0,600,-600]){
    let поп='';
    for(let i=0;i<(напрям?35:1);i++){
      const стан=await екран(стор), кандидати=стан.елем.map(s=>({s,оц:відповідність(s,мітка)})).filter(x=>x.оц).sort((a,b)=>b.оц-a.оц);
      if(кандидати.length){const n=Number(кандидати[0].s.match(/^\[(\d+)\]/)[1]);return {лок:стор.locator(`[data-люд="${n}"]`),мітка:кандидати[0].s,стан};}
      if(!напрям)break;
      const ключ=стан.прокрутка+'|'+стан.елем.join('|');if(ключ===поп)break;поп=ключ;
      await стор.mouse.move(195,420);await стор.mouse.wheel(0,напрям);await сон(180);
      await кадр('гортає до записаного елемента: '+мітка);
    }
  }
  return null;
}
async function головна(){
  браузер=await chromium.launch({headless:true,proxy:{server:'http://127.0.0.1:9'}});
  const [ШИР,ВИС]=(process.env.VIEWPORT||'390x844').split('x').map(Number),ТЕЛ=ШИР<600;
  const ctx=await браузер.newContext({viewport:{width:ШИР,height:ВИС},deviceScaleFactor:1,isMobile:ТЕЛ,hasTouch:ТЕЛ,locale:'uk-UA',timezoneId:'Europe/Kyiv',ignoreHTTPSErrors:true,acceptDownloads:true,serviceWorkers:'block',
    userAgent:ТЕЛ?'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36':undefined});
  await ctx.exposeBinding('__воркер',(_,рядок)=>fs.appendFileSync(path.join(службове,'воркер.jsonl'),рядок+'\n'));
  await ctx.addInitScript(()=>{const W=window.Worker;if(!W)return;
    window.Worker=function(...а){const w=new W(...а),pm=w.postMessage.bind(w);
      w.postMessage=function(m,...р){try{if(m&&(m.тип==='виклик'||m.тип==='продовжити'))window.__воркер(JSON.stringify({б:'туди',тип:m.тип,н:m.н,ім:m.ім,вхід:m.вхід,асинх:m.асинх,рання:m.рання,помилка:m.помилка,t:Date.now()}));}catch(_){}return pm(m,...р);};
      w.addEventListener('message',е=>{const д=е.data||{};if(д.тип==='відповідь'||д.тип==='перша_рука')window.__воркер(JSON.stringify({б:'звідти',тип:д.тип,н:д.н,вих:д.вих,помилка:д.помилка,вид:д.вид,t:Date.now()}));});
      return w;};
    window.Worker.prototype=W.prototype;});
  стор=await ctx.newPage();стор.setDefaultTimeout(15000);
  стор.on('console',m=>{if(['warning','error'].includes(m.type()))fs.appendFileSync(path.join(службове,'консоль.txt'),new Date().toISOString()+' '+m.text()+'\n');});
  стор.on('pageerror',e=>fs.appendFileSync(path.join(службове,'консоль.txt'),String(e)+'\n'));
  стор.on('response',r=>{if(r.request().resourceType()==='image')fs.appendFileSync(path.join(службове,'фото_речей.txt'),`${new Date().toISOString()} ${r.status()} ${r.url()}\n`);});
  стор.on('requestfailed',r=>{if(r.resourceType()==='image')fs.appendFileSync(path.join(службове,'фото_речей.txt'),`${new Date().toISOString()} FAIL ${JSON.stringify(r.failure())} ${r.url()}\n`);});
  стор.on('requestfailed',r=>{if(r.resourceType()!=='image')мережа.push('FAIL '+r.failure()?.errorText+' '+r.url().slice(0,160));});
  стор.on('filechooser',()=>{});
  стор.on('download',async d=>{await d.saveAs(path.join(тека,d.suggestedFilename()));});
  const база='https://mightyrochy.github.io', МІСТ='https://lyusterko-mist.mighty-rochy.workers.dev/';
  if(!process.env.PUBLISHED)await стор.route(u=>u.origin===база,async r=>{
    const ім=decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/kod-shi-data\//,'').replace(/^\//,'')||'index.html';const ф=path.join(process.env.STOR,ім);
    await r.fulfill({status:fs.existsSync(ф)?200:404,contentType:'text/html; charset=utf-8',body:fs.existsSync(ф)?fs.readFileSync(ф):'нема '+ім});
  });
  if(!process.env.PUBLISHED)await стор.route('https://cdn.jsdelivr.net/pyodide/**',async r=>{
    const ім=new URL(r.request().url()).pathname.split('/').pop(),ф=path.join(process.env.PYODIDE,ім);
    await r.fulfill({status:fs.existsSync(ф)?200:404,contentType:ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream',body:fs.existsSync(ф)?fs.readFileSync(ф):'нема '+ім});
  });
  await стор.route(u=>u.origin!==база && u.origin+'/'!==МІСТ && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href),async r=>{
    мережа.push(r.request().url().slice(0,200));await r.abort().catch(()=>{});
  });
  await стор.route(u=>u.origin+'/'===МІСТ,async route=>{
    if(route.request().method()!=='POST')return route.fallback();
    if(process.env.STELYA&&викликів>=Number(process.env.STELYA)){fs.appendFileSync(path.join(службове,'обміни.jsonl'),JSON.stringify({час:new Date().toISOString(),прохід,стеля:true})+'\n');return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{type:'стеля',message:'стеля проходу: міст не кликано'}})});}
    викликів++;активні++;останнійВиклик=Date.now();const т0=Date.now();const тіло=route.request().postData()||'{}',початок=new Date().toISOString();
    try{
      let з=ЗАПИСИ.find(з=>!взятоЗ.has(з.і)&&з.запит===тіло),точно=!!з,преф=тіло.length;
      if(!з){let к=null;for(const х of ЗАПИСИ){if(взятоЗ.has(х.і))continue;const п=спільний(х.запит,тіло);if(!к||п>к.п)к={х,п};}if(к){з=к.х;преф=к.п;}}
      if(!з)throw new Error('нема невзятого запису для виклику '+викликів);
      взятоЗ.add(з.і);
      fs.appendFileSync(path.join(службове,'обміни.jsonl'),JSON.stringify({час:початок,прохід,виклик:викликів,запис:з.і,точно,спільний_префікс:преф,довжина:тіло.length,довжина_запису:з.запит.length,
        розбіжність:точно?null:{тут:тіло.slice(Math.max(0,преф-150),преф+250),запис:з.запит.slice(Math.max(0,преф-150),преф+250)},запит:тіло})+'\n');
      await route.fulfill({status:з.статус||200,headers:{'content-type':'application/json',...(з.заголовки||{})},body:з.відповідь});
    }catch(e){fs.appendFileSync(path.join(службове,'обміни.jsonl'),JSON.stringify({час:початок,с:(Date.now()-т0)/1000,прохід,запит:тіло,помилка:String(e)})+'\n');await route.fulfill({status:502,body:JSON.stringify({error:{message:String(e)}})}).catch(()=>{});}
    finally{активні--;останнійВиклик=Date.now();}
  });
  await стор.goto(база+'/kod-shi-data/index.html#міст='+МІСТ+'&т=tok-stub',{waitUntil:'load',timeout:180000});
  await сон(8000);await спокій();
  запис('хід.md',`# Повтор ${ситуація}: записані слова й дії; жінка — скрипт`);
  summary.кроки=[];
  const ляг=(дія,так,чому)=>summary.кроки.push({крок:дія.крок,прохід,дія:дія.текст.slice(0,200),лягло:так,...(так?{}:{чому})});
  for(const дія of дії){
    await спокій();const стан=await кадр('джерело, крок '+дія.крок+': '+дія.текст,true);
    const ввід=дія.текст.match(/^надрукувала в «([\s\S]*?)»: «([\s\S]*)»$/),тап=дія.текст.match(/^натиснула «([\s\S]*?)»/);
    if(ввід || тап){
      const мітка=(ввід||тап)[1],знайдено=await знайти(мітка);
      if(!знайдено){розбіжність(дія,'записаного елемента немає на екрані',await екран(стор));ляг(дія,false,'елемента немає');if(ввід){пропущено++;summary.слова.push({прохід,крок:дія.крок,текст:ввід[2],лягло:false});}continue;}
      try{
        if(ввід){await знайдено.лок.fill(ввід[2]);слів++;summary.слова.push({прохід,крок:дія.крок,текст:ввід[2],лягло:true});}
        else{
          if(мітка==='кнопка: Новий'&&process.env.ONE_PASS){ляг(дія,true);break;}   // один прохід: до «Новий», без нього
          const тип=await знайдено.лок.evaluate(x=>x.tagName+':'+(x.type||''));
          if(!/INPUT:file/.test(тип))await знайдено.лок.click();
          if(мітка==='кнопка: Новий')прохід++;
          if(process.env.SCENE_STOP_AFTER_COLLECT && мітка==='кнопка: Зібрати образи'){ляг(дія,true);await сон(5000);await спокій();await кадр('сцена: після збирання образів — один прохід',true);break;}
        }
        ляг(дія,true);
      }catch(e){
        розбіжність(дія,'дія не виконалась: '+String(e).split('\n')[0],await екран(стор));ляг(дія,false,'дія не виконалась');
        if(ввід){пропущено++;summary.слова.push({прохід,крок:дія.крок,текст:ввід[2],лягло:false});}
      }
    }else if(/^гортнула /.test(дія.текст)){await стор.mouse.move(195,420);await стор.mouse.wheel(0,/вгору/.test(дія.текст)?-600:600);ляг(дія,true);}
    else if(/^чекала /.test(дія.текст)){await сон(1000);await спокій();ляг(дія,true);}
    else if(дія.текст==='готово'){ляг(дія,true);break;}
    else {розбіжність(дія,'невідома форма записаної дії',стан);ляг(дія,false,'невідома форма');}
    await сон(700);await спокій();
  }
  await доЗавантажитиФото(стор);await сон(3000);await кадр('кінець записаного шляху');
  if(process.env.ONE_PASS){   // хвіст одного проходу: «Усі образи» і файл вердиктів — той, що тестувальниця прикріплює до повідомлення
    try{const о=await знайти('кнопка: Образи');if(о){await о.лок.click();await сон(1500);await кадр('один прохід: Образи',true);}
      const у=await знайти('кнопка: Усі образи ›');if(у){await у.лок.click();await сон(1500);await кадр('один прохід: Усі образи',true);}
      await стор.locator('#журнал > summary').click();await сон(800);await кадр('один прохід: відкрито «Вердикти на цьому телефоні»',true);
      await стор.locator('#ж-файл').first().click();await сон(4000);await кадр('один прохід: «Зберегти всі вердикти файлом»',true);
    }catch(e){fs.appendFileSync(path.join(тека,'розбіжності.md'),'\n- хвіст одного проходу не виконався: '+String(e).split('\n')[0]+'\n');}
  }
  summary.кінець=new Date().toISOString();summary.мережа_спроб=мережа.length;summary.мережа=мережа.slice(0,50);summary.записів=ЗАПИСИ.length;summary.взято_записів=взятоЗ.size;summary.невзяті=ЗАПИСИ.filter(з=>!взятоЗ.has(з.і)).map(з=>з.і);summary.слів_лягло=слів;summary.слів_пропущено=пропущено;summary.проходів=прохід;summary.кроків_джерела=дії.length;summary.кроків_лягло=summary.кроки.filter(x=>x.лягло).length;
  fs.writeFileSync(path.join(тека,'підсумок.json'),JSON.stringify(summary,null,2));
  const unique=new Map();for(const r of summary.руки)unique.set(r.прохід+'|'+r.прогін,r);
  for(const r of unique.values())for(const p of r.позиції)fs.appendFileSync(path.join(вихід,'руки.md'),`\n- ${ситуація} · ${r.прохід} · ${p.позиція} → рука ${p.рука}; ${p.рука==='2'?JSON.stringify(r.поломка_руки_2):''}\n`);
  console.log(JSON.stringify({ситуація,слів,пропущено,прохід,розбіжностей:summary.розбіжності.length,кроків:крок,кроків_джерела:дії.length,кроків_лягло:summary.кроків_лягло}));
}
головна().catch(e=>{fs.writeFileSync(path.join(тека,'збій.txt'),String(e.stack));console.error(e);process.exitCode=1;}).finally(async()=>{if(браузер)await браузер.close();});
