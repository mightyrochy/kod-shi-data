/* Повтор записаних дій без моделі-жінки. Запуск: node повтор.js <ситуація> <вихід> <порт>.
   STOR — свіжа збірка, PYODIDE — кеш. Слова беруться лише з хід.md першого прогону. */
const fs = require('fs'), path = require('path'), http = require('http');
const {chromium} = require('playwright');
const {знімокРук, доЗавантажитиФото} = require('./руки_зі_сторінки.js');
const джерело = fs.readFileSync(path.join(__dirname, 'людина.js'), 'utf8');
// Спільне визначення доступних на екрані елементів; жодного виклику моделі-жінки.
const екран = eval('(' + джерело.slice(джерело.indexOf('async function екран('), джерело.indexOf('const {знімокРук')).trim() + ')');
const ситуація = process.argv[2], вихід = path.resolve(process.argv[3]), порт = Number(process.argv[4]);
const перший = path.resolve(__dirname, '../../живий-як-людина-1', ситуація);
const тека = path.join(вихід, ситуація), службове = path.join(вихід, 'стенд/службове', ситуація);
for (const p of [тека, службове, path.join(тека, 'знімки')]) fs.mkdirSync(p, {recursive:true});
fs.copyFileSync(path.join(перший,'ситуація.md'),path.join(тека,'ситуація.md'));
const сон = n => new Promise(r=>setTimeout(r,n));
const запис = (name, text) => fs.appendFileSync(path.join(тека,name),text+'\n');
const дії = [...fs.readFileSync(path.join(перший,'хід.md'),'utf8').matchAll(/### (\d+) ·[^\n]*\n([\s\S]*?)(?=\n### |$)/g)].map(m=>({крок:Number(m[1]),текст:(m[2].match(/^- дія: ([\s\S]*?)(?=\n\n|$)/m)||[])[1]})).filter(x=>x.текст);
if(process.env.REPLAY_PLAN){console.log(JSON.stringify({ситуація,дій:дії.length,слова:дії.filter(x=>x.текст.startsWith('надрукувала в ')),новий:дії.filter(x=>x.текст==='натиснула «кнопка: Новий»')}));process.exit(0);}
let браузер, стор, активні=0, останнійВиклик=0, крок=0, прохід=1, слів=0, пропущено=0;
const summary={ситуація,початок:new Date().toISOString(),слова:[],розбіжності:[],руки:[]};
function розбіжність(дія,причина,стан){
  const r={прохід,крок:дія.крок,дія:дія.текст,причина,екран:стан.текст,елементи:стан.елем};
  summary.розбіжності.push(r);
  fs.appendFileSync(path.join(вихід,'розбіжності.md'),`\n- ${ситуація} · ${прохід} · ${дія.крок} · ${причина}; екран: ${стан.текст.replace(/\n/g,' ').slice(0,1200)}; слово/дія: ${дія.текст}\n`);
}
async function кадр(опис){
  крок++; const ім=String(крок).padStart(4,'0')+'.jpg';
  await стор.screenshot({path:path.join(тека,'знімки',ім),type:'jpeg',quality:72});
  const стан=await екран(стор);
  запис('хід.md',`\n### ${крок} · ${new Date().toISOString()} · прохід ${прохід} · знімок \`знімки/${ім}\`\n- дія скрипта: ${опис}`);
  fs.appendFileSync(path.join(службове,'екрани.jsonl'),JSON.stringify({крок,прохід,опис,...стан})+'\n');
  const руки=await знімокРук(стор);
  if(руки && руки.готово){summary.руки.push({крок,прохід,...руки});fs.appendFileSync(path.join(службове,'руки.jsonl'),JSON.stringify({крок,прохід,...руки})+'\n');}
  return стан;
}
async function спокій(){
  // Очікування визначається незавершеним запитом, а не записаними секундами іншої моделі.
  while(активні || Date.now()-останнійВиклик<900){await сон(2000);if(активні)await кадр('чекає відповіді моделі');}
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
  браузер=await chromium.launch({headless:true});
  const ctx=await браузер.newContext({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true,locale:'uk-UA',timezoneId:'Europe/Kyiv',ignoreHTTPSErrors:true,acceptDownloads:true});
  стор=await ctx.newPage();стор.setDefaultTimeout(15000);
  стор.on('console',m=>{if(['warning','error'].includes(m.type()))fs.appendFileSync(path.join(службове,'консоль.txt'),new Date().toISOString()+' '+m.text()+'\n');});
  стор.on('pageerror',e=>fs.appendFileSync(path.join(службове,'консоль.txt'),String(e)+'\n'));
  стор.on('response',r=>{if(r.request().resourceType()==='image')fs.appendFileSync(path.join(службове,'фото_речей.txt'),`${new Date().toISOString()} ${r.status()} ${r.url()}\n`);});
  стор.on('requestfailed',r=>{if(r.resourceType()==='image')fs.appendFileSync(path.join(службове,'фото_речей.txt'),`${new Date().toISOString()} FAIL ${JSON.stringify(r.failure())} ${r.url()}\n`);});
  стор.on('filechooser',()=>{});
  стор.on('download',async d=>{await d.saveAs(path.join(тека,d.suggestedFilename()));});
  const база='http://127.0.0.1:8765';
  await стор.route(u=>u.origin===база && !decodeURIComponent(u.pathname).endsWith('/міст'),async r=>{
    const ім=decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\//,'')||'index.html';const ф=path.join(process.env.STOR,ім);
    await r.fulfill({status:fs.existsSync(ф)?200:404,contentType:'text/html; charset=utf-8',body:fs.existsSync(ф)?fs.readFileSync(ф):'нема '+ім});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**',async r=>{
    const ім=new URL(r.request().url()).pathname.split('/').pop(),ф=path.join(process.env.PYODIDE,ім);
    await r.fulfill({status:fs.existsSync(ф)?200:404,contentType:ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream',body:fs.existsSync(ф)?fs.readFileSync(ф):'нема '+ім});
  });
  await стор.route(u=>decodeURIComponent(u.pathname).endsWith('/міст'),async route=>{
    активні++;останнійВиклик=Date.now();const тіло=route.request().postData()||'{}',початок=new Date().toISOString();
    try{
      const r=await new Promise((resolve,reject)=>{const q=http.request({host:'127.0.0.1',port:порт,path:'/',method:'POST',timeout:960000,headers:{'content-type':'application/json','content-length':Buffer.byteLength(тіло),'x-prohid':encodeURIComponent(ситуація+' · '+прохід)}},v=>{const a=[];v.on('data',x=>a.push(x));v.on('end',()=>resolve({status:v.statusCode,headers:v.headers,body:Buffer.concat(a).toString('utf8')}));});q.on('error',reject);q.on('timeout',()=>q.destroy(new Error('таймаут моста')));q.end(тіло);});
      fs.appendFileSync(path.join(службове,'обміни.jsonl'),JSON.stringify({початок,прохід,запит:тіло,статус:r.status,відповідь:r.body})+'\n');
      const headers={};for(const n of ['x-model','x-images-dropped'])if(r.headers[n])headers[n]=r.headers[n];
      await route.fulfill({status:r.status,contentType:'application/json',headers,body:r.body});
    }catch(e){fs.appendFileSync(path.join(службове,'обміни.jsonl'),JSON.stringify({початок,прохід,запит:тіло,помилка:String(e)})+'\n');await route.fulfill({status:502,body:JSON.stringify({error:{message:String(e)}})}).catch(()=>{});}
    finally{активні--;останнійВиклик=Date.now();}
  });
  await стор.goto(база+'/index.html#міст='+база+'/міст&т=tok-lyudyna&модель='+process.env.PRODUCT_MODEL+'&модель_мови='+process.env.PRODUCT_MODEL,{waitUntil:'load',timeout:180000});
  await сон(8000);await спокій();
  запис('хід.md',`# Повтор ${ситуація}: записані слова й дії; жінка — скрипт`);
  for(const дія of дії){
    await спокій();const стан=await кадр('джерело, крок '+дія.крок+': '+дія.текст);
    const ввід=дія.текст.match(/^надрукувала в «([\s\S]*?)»: «([\s\S]*)»$/),тап=дія.текст.match(/^натиснула «([\s\S]*?)»/);
    if(ввід || тап){
      const мітка=(ввід||тап)[1],знайдено=await знайти(мітка);
      if(!знайдено){розбіжність(дія,'записаного елемента немає',await екран(стор));if(ввід){пропущено++;summary.слова.push({прохід,крок:дія.крок,текст:ввід[2],лягло:false});}continue;}
      try{
        if(ввід){await знайдено.лок.fill(ввід[2]);слів++;summary.слова.push({прохід,крок:дія.крок,текст:ввід[2],лягло:true});}
        else{
          const тип=await знайдено.лок.evaluate(x=>x.tagName+':'+(x.type||''));
          if(!/INPUT:file/.test(тип))await знайдено.лок.click();
          if(мітка==='кнопка: Новий')прохід++;
        }
      }catch(e){розбіжність(дія,'дія не виконалась: '+String(e).split('\n')[0],await екран(стор));}
    }else if(/^гортнула /.test(дія.текст)){await стор.mouse.move(195,420);await стор.mouse.wheel(0,/вгору/.test(дія.текст)?-600:600);}
    else if(/^чекала /.test(дія.текст)){await сон(1000);await спокій();}
    else if(дія.текст==='готово')break;
    else розбіжність(дія,'невідома форма записаної дії',стан);
    await сон(700);await спокій();
  }
  await доЗавантажитиФото(стор);await сон(3000);await кадр('кінець записаного шляху');
  summary.кінець=new Date().toISOString();summary.слів_лягло=слів;summary.слів_пропущено=пропущено;summary.проходів=прохід;
  fs.writeFileSync(path.join(тека,'підсумок.json'),JSON.stringify(summary,null,2));
  const unique=new Map();for(const r of summary.руки)unique.set(r.прохід+'|'+r.прогін,r);
  for(const r of unique.values())for(const p of r.позиції)fs.appendFileSync(path.join(вихід,'руки.md'),`\n- ${ситуація} · ${r.прохід} · ${p.позиція} → рука ${p.рука}; ${p.рука==='2'?JSON.stringify(r.поломка_руки_2):''}\n`);
  console.log(JSON.stringify({ситуація,слів,пропущено,прохід,розбіжностей:summary.розбіжності.length,кроків:крок}));
}
головна().catch(e=>{fs.writeFileSync(path.join(тека,'збій.txt'),String(e.stack));console.error(e);process.exitCode=1;}).finally(async()=>{if(браузер)await браузер.close();});
