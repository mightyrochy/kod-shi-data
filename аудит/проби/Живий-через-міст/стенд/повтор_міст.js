/* Прилад проби «Живий-як-людина-4»: повтор записаних дій без моделі-жінки (скрипт із хід.md третього прогону). Запуск: node повтор.js <ситуація> <вихід> <порт>.
   STOR — свіжа збірка, PYODIDE — кеш. Слова беруться лише з хід.md третього прогону. */
const fs = require('fs'), path = require('path'), http = require('http');
const {chromium} = require('playwright');
const {знімокРук, доЗавантажитиФото} = require('../../живий-як-людина-4/стенд/руки_зі_сторінки.js');
const джерело = fs.readFileSync(path.join(__dirname, '../../живий-як-людина-4/стенд/людина.js'), 'utf8');
// Спільне визначення доступних на екрані елементів; жодного виклику моделі-жінки.
const екран = eval('(' + джерело.slice(джерело.indexOf('async function екран('), джерело.indexOf('const {знімокРук')).trim() + ')');
const ситуація = process.argv[2], вихід = path.resolve(process.argv[3]), порт = Number(process.argv[4]);
const перший = path.resolve(__dirname, '../../живий-як-людина-3', process.env.SCENE_BASE || ситуація);
const тека = path.join(вихід, ситуація), службове = path.join(вихід, 'стенд/службове', ситуація);
for (const p of [тека, службове, path.join(тека, 'знімки')]) fs.mkdirSync(p, {recursive:true});
fs.copyFileSync(path.join(перший,'ситуація.md'),path.join(тека,'ситуація.md'));
const сон = n => new Promise(r=>setTimeout(r,n));
const запис = (name, text) => fs.appendFileSync(path.join(тека,name),text+'\n');
const СЛОВА_СЦЕНИ = process.env.SCENE_WORDS || null;
const дії = [...fs.readFileSync(path.join(перший,'хід.md'),'utf8').matchAll(/### (\d+) ·[^\n]*\n([\s\S]*?)(?=\n### |$)/g)].map(m=>({крок:Number(m[1]),текст:(m[2].match(/^- дія: ([\s\S]*?)(?=\n\n|$)/m)||[])[1]})).filter(x=>x.текст);
if(СЛОВА_СЦЕНИ){const р=дії.findIndex(x=>/^надрукувала в «поле для тексту: підказка: Напиши, як подрузі/.test(x.текст));if(р<0){console.error('нема кроку з нагодою');process.exit(3);}дії[р].текст=дії[р].текст.replace(/»: «[\s\S]*»$/,'»: «'+СЛОВА_СЦЕНИ.replace(/\$/g,'$$$$')+'»');}
if(process.env.REPLAY_PLAN){console.log(JSON.stringify({ситуація,дій:дії.length,слова:дії.filter(x=>x.текст.startsWith('надрукувала в ')),новий:дії.filter(x=>x.текст==='натиснула «кнопка: Новий»')}));process.exit(0);}
let браузер, стор, активні=0, останнійВиклик=0, крок=0, прохід=1, слів=0, пропущено=0, блокер=null;
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
  браузер=await chromium.launch({headless:true,proxy:process.env.HTTPS_PROXY?{server:process.env.HTTPS_PROXY,bypass:'localhost,127.0.0.1'}:undefined});
  const ctx=await браузер.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true,locale:'uk-UA',timezoneId:'Europe/Kyiv',ignoreHTTPSErrors:true,acceptDownloads:true,
    userAgent:'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36'});
  стор=await ctx.newPage();стор.setDefaultTimeout(15000);
  стор.on('console',m=>{if(['warning','error'].includes(m.type()))fs.appendFileSync(path.join(службове,'консоль.txt'),new Date().toISOString()+' '+m.text()+'\n');});
  стор.on('pageerror',e=>fs.appendFileSync(path.join(службове,'консоль.txt'),String(e)+'\n'));
  стор.on('response',r=>{if(r.request().resourceType()==='image')fs.appendFileSync(path.join(службове,'фото_речей.txt'),`${new Date().toISOString()} ${r.status()} ${r.url()}\n`);});
  стор.on('requestfailed',r=>{if(r.resourceType()==='image')fs.appendFileSync(path.join(службове,'фото_речей.txt'),`${new Date().toISOString()} FAIL ${JSON.stringify(r.failure())} ${r.url()}\n`);});
  стор.on('filechooser',()=>{});
  стор.on('download',async d=>{await d.saveAs(path.join(тека,d.suggestedFilename()));});
  const база='https://mightyrochy.github.io', МІСТ='https://lyusterko-mist.mighty-rochy.workers.dev/';
  await стор.route(u=>u.origin===база,async r=>{
    const ім=decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/kod-shi-data\//,'').replace(/^\//,'')||'index.html';const ф=path.join(process.env.STOR,ім);
    await r.fulfill({status:fs.existsSync(ф)?200:404,contentType:'text/html; charset=utf-8',body:fs.existsSync(ф)?fs.readFileSync(ф):'нема '+ім});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**',async r=>{
    const ім=new URL(r.request().url()).pathname.split('/').pop(),ф=path.join(process.env.PYODIDE,ім);
    await r.fulfill({status:fs.existsSync(ф)?200:404,contentType:ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream',body:fs.existsSync(ф)?fs.readFileSync(ф):'нема '+ім});
  });
  await стор.route(u=>u.origin!==база && u.origin+'/'!==МІСТ && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href),async r=>{
    try{await r.fulfill({response:await r.fetch({timeout:15000})});}catch(_){await r.abort().catch(()=>{});}
  });
  await стор.route(u=>u.origin+'/'===МІСТ,async route=>{
    if(route.request().method()!=='POST')return route.fallback();
    активні++;останнійВиклик=Date.now();const т0=Date.now();const тіло=route.request().postData()||'{}',початок=new Date().toISOString();
    try{
      const r=await route.fetch({timeout:960000});const body=await r.text();const h=r.headers();
      const x={};for(const n in h)if(/^x-|^retry-after|^anthropic-ratelimit/.test(n))x[n]=h[n];
      fs.appendFileSync(path.join(службове,'обміни.jsonl'),JSON.stringify({час:початок,с:(Date.now()-т0)/1000,прохід,статус:r.status(),заголовки:x,запит:тіло,відповідь:body})+'\n');
      if(r.status()===429||r.status()===402)блокер='ЗАБЛОКОВАНО: '+r.status()+' від моста: '+body.slice(0,300);
      await route.fulfill({response:r,body});
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
  summary.кінець=new Date().toISOString();summary.слів_лягло=слів;summary.слів_пропущено=пропущено;summary.проходів=прохід;summary.кроків_джерела=дії.length;summary.кроків_лягло=summary.кроки.filter(x=>x.лягло).length;
  fs.writeFileSync(path.join(тека,'підсумок.json'),JSON.stringify(summary,null,2));
  const unique=new Map();for(const r of summary.руки)unique.set(r.прохід+'|'+r.прогін,r);
  for(const r of unique.values())for(const p of r.позиції)fs.appendFileSync(path.join(вихід,'руки.md'),`\n- ${ситуація} · ${r.прохід} · ${p.позиція} → рука ${p.рука}; ${p.рука==='2'?JSON.stringify(r.поломка_руки_2):''}\n`);
  console.log(JSON.stringify({ситуація,слів,пропущено,прохід,розбіжностей:summary.розбіжності.length,кроків:крок,кроків_джерела:дії.length,кроків_лягло:summary.кроків_лягло}));
}
головна().catch(e=>{fs.writeFileSync(path.join(тека,'збій.txt'),String(e.stack));console.error(e);process.exitCode=1;}).finally(async()=>{if(браузер)await браузер.close();});
