const { chromium } = require('playwright');
const fs=require('fs');
const OUT='/tmp/f/out';
const R=[]; 
function T(сцена,н,ок,дет){R.push({сцена,н,ок:!!ок,дет:ок?undefined:дет}); console.log((ок?'✓ ':'✗ ')+сцена+' · '+н+(ок?'':' → '+JSON.stringify(дет)));}
const JA='{"photo":"usable","skin":["#f2d6c4"],"hair":["#4a4644"],"eyes":"#6b8cae"}';
const JA2='{"photo":"usable","skin":["#e8c4a8"],"hair":["#2a1d16"],"eyes":"#5a7a3c"}';
const JX='{"photo":"usable","skin":["#111111"],"hair":["#222222"],"eyes":"#333333"}';
async function setup(b,tag){
 const ctx=await b.newContext({viewport:{width:390,height:844},deviceScaleFactor:1});
 const p=await ctx.newPage(); const errs=[]; p.on('pageerror',e=>errs.push(String(e).slice(0,200)));
 await p.goto('http://localhost:8765/index.html#міст=http://localhost:8787&т=tok-a1',{waitUntil:'domcontentloaded'});
 await p.waitForFunction(()=>typeof зчитатиКольориЗПортрета==='function'&&typeof ПРОФІЛІ!=='undefined');
 await p.waitForTimeout(3000);
 // портрет у сховищі активного профілю + екран профілю
 await p.evaluate(async()=>{
   const c=document.createElement('canvas');c.width=40;c.height=40;c.getContext('2d').fillRect(0,0,40,40);
   const bl=await new Promise(r=>c.toBlob(r,'image/png'));
   await писатиКв(ключФото('портрет'),bl);
   window.__виклики=0; window.__ж='';
   window.__міст=(відп)=>async(ім,вх)=>{ if(ім!=='колір') throw new Error('міст:'+ім);
      if(вх.відповідь_моделі===null) return {готово:true};
      const j=JSON.parse(вх.відповідь_моделі); return {стан:'готово',шкіра:j.skin,волосся:j.hair,очі:j.eyes,кільце:null,освітлення:null};};
   window.__збійМосту=()=>{ містП=async()=>{throw new Error('Pyodide впав');}; };
   window.__міст_ок=()=>{ містП=window.__міст(); };
   window.__модель=(відп)=>{ модельП_блоки=async()=>{window.__виклики++;return [{type:'text',text:відп}];}; };
   режим('старт'); екран(0);
 });
 await p.waitForTimeout(500);
 return {ctx,p,errs};
}
const st=p=>p.evaluate(()=>({шкіра:КОЛІР.шкіра,повторВидно:!document.getElementById('кол-повтор').hidden,повторDis:document.getElementById('кол-повтор').disabled,зчитатиDis:document.getElementById('кол-зчитати').disabled,стан:document.getElementById('кол-стан').textContent,поле:document.getElementById('кол-відповідь').value,виклики:window.__виклики,профіль:АКТИВНИЙ}));
const shot=(p,n)=>p.locator('#кол-зчитати').scrollIntoViewIfNeeded().then(()=>p.screenshot({path:`${OUT}/${n}.png`}));

(async()=>{
 const b=await chromium.launch();
 // ===== сцена 1
 {const С='ж1_кольори_повтор_профілі'; const {p,errs}=await setup(b,1);
  const А=await p.evaluate(()=>АКТИВНИЙ);
  await p.evaluate(([a])=>{window.__модель(a);window.__збійМосту();},[JA]);
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>/Не вдалось/.test(document.getElementById('кол-стан').textContent)&&!document.getElementById('кол-зчитати').disabled);
  let s=await st(p); await shot(p,'1_01_збій_моста');
  T(С,'збій моста: рядок «Не вдалось…», кнопка повтору видна, кольори не змінились, модель кликано 1 раз, сирий текст у полі відсутній',/Не вдалось/.test(s.стан)&&s.повторВидно&&!s.шкіра&&s.виклики===1&&s.поле==='',s);
  T(С,'у видимому стані нема сирої відповіді моделі й тексту винятку («usable», «Pyodide»)',!/usable|Pyodide|photo/.test(s.стан),s.стан);
  await p.evaluate(()=>{window.__міст_ок(); модельП_блоки=async()=>{window.__виклики++;throw new Error('повторний виклик моделі');};});
  await p.click('#кол-повтор'); await p.waitForFunction(()=>/Прочитано/.test(document.getElementById('кол-стан').textContent));
  s=await st(p); await shot(p,'1_02_повтор_застосував');
  T(С,'повтор після відновлення застосовує кольори А без нового виклику моделі, кнопка сховалась, поле порожнє',s.шкіра==='#f2d6c4'&&s.виклики===1&&!s.повторВидно&&s.поле==='',s);
  // ізоляція А → Б
  await p.evaluate(([j])=>{window.__модель(j);window.__збійМосту();КОЛІР={шкіра:null,волосся:null,очі:null,кільце:null,точки:null};},[JA2]);
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>!document.getElementById('кол-повтор').hidden);
  await p.evaluate(()=>створитиПрофіль()); await p.waitForTimeout(400);
  s=await st(p); await p.evaluate(()=>{режим('старт');екран(0);}); await shot(p,'1_03_профіль_Б_після_збою_А');
  T(С,'збій А → створено Б: кнопка повтору, відповідь, стан і ручне поле скинуті; профіль змінився',s.профіль!==А&&!s.повторВидно&&!s.шкіра&&s.поле===''&&s.стан==='',s);
  await p.evaluate(()=>{window.__міст_ок();}); 
  await p.evaluate(()=>document.getElementById('кол-повтор').onclick({currentTarget:document.getElementById('кол-повтор')}));
  await p.waitForTimeout(300); s=await st(p);
  T(С,'примусовий виклик повтору в Б не застосовує кольори А',!s.шкіра,s);
  // відкладена відповідь А після створення Б (перемикаємось на А, стартуємо, створюємо Б)
  await p.evaluate(async(a)=>{await перемкнути(a);},А);
  await p.evaluate(([j])=>{window.__міст_ок(); window.__відкл=null; модельП_блоки=()=>new Promise(r=>{window.__відкл=()=>r([{type:'text',text:j}]);});},[JX]);
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>window.__відкл);
  await p.evaluate(()=>створитиПрофіль()); await p.waitForTimeout(300);
  await p.evaluate(()=>window.__відкл()); await p.waitForTimeout(800);
  s=await st(p);
  T(С,'відповідь незавершеного читання А не потрапляє до нового профілю: кольорів нема, повтор прихований',!s.шкіра&&!s.повторВидно&&!/Прочитано/.test(s.стан),s);
  await p.evaluate(async(a)=>{await перемкнути(a);},А);
  // нове читання під час відкладеного повтору, новий збій → повтор доступний
  await p.evaluate(([j])=>{КОЛІР={шкіра:null,волосся:null,очі:null,кільце:null,точки:null}; window.__модель(j); window.__збійМосту();},[JA]);
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>!document.getElementById('кол-повтор').hidden);
  await p.evaluate(()=>{ window.__р=null; містП=async()=>new Promise(r=>{window.__р=()=>r({стан:'готово',шкіра:['#111111'],волосся:['#222222'],очі:'#333333'});}); });
  await p.click('#кол-повтор'); await p.waitForFunction(()=>window.__р);
  await p.evaluate(()=>{ містП=async()=>{throw new Error('новий збій');}; });
  await p.evaluate(()=>зчитатиКольориЗПортрета()); 
  await p.evaluate(()=>window.__р()); await p.waitForTimeout(600);
  s=await st(p); await shot(p,'1_04_нове_читання_під_час_повтору');
  T(С,'нове читання під час повтору: повтор знову доступний (не disabled), старі кольори #111111 не застосовано',s.повторВидно&&!s.повторDis&&s.шкіра!=='#111111',s);
  await p.evaluate(()=>{window.__міст_ок();}); await p.click('#кол-повтор'); await p.waitForFunction(()=>/Прочитано/.test(document.getElementById('кол-стан').textContent)); s=await st(p);
  T(С,'після нового збою повтор працює: кольори А з останньої відповіді',s.шкіра==='#f2d6c4'&&!s.повторDis,s);
  T(С,'без винятків сторінки',errs.length===0,errs);
 }
 // ===== сцена 2
 {const С='ж7_прогулянка_субота'; const {p,errs}=await setup(b,2);
  const А=await p.evaluate(()=>АКТИВНИЙ);
  await p.evaluate(([j])=>{window.__модель(j);window.__збійМосту();},[JA2]);
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>!document.getElementById('кол-повтор').hidden);
  let s=await st(p); await shot(p,'2_01_збій_А');
  T(С,'збій моста на кольорах А: повтор доступний, модель кликано 1 раз',s.повторВидно&&s.виклики===1&&!s.шкіра,s);
  await p.evaluate(()=>{window.__міст_ок(); модельП_блоки=async()=>{window.__виклики++;throw new Error('нова модель');};});
  await p.click('#кол-повтор'); await p.waitForFunction(()=>/Прочитано/.test(document.getElementById('кол-стан').textContent));
  s=await st(p); await shot(p,'2_02_повтор_А');
  T(С,'повтор зчитує кольори профілю А (#e8c4a8) без нового виклику моделі',s.шкіра==='#e8c4a8'&&s.виклики===1,s);
  // створити Б і зчитати його кольори, потім повернутися на А: А не отримує Б (і навпаки)
  await p.evaluate(()=>створитиПрофіль()); await p.waitForTimeout(300);
  const Б=await p.evaluate(()=>АКТИВНИЙ);
  await p.evaluate(async()=>{const c=document.createElement('canvas');c.width=40;c.height=40;c.getContext('2d').fillRect(0,0,40,40);const bl=await new Promise(r=>c.toBlob(r,'image/png'));await писатиКв(ключФото('портрет'),bl);});
  await p.evaluate(([j])=>{window.__модель(j);window.__міст_ок();},[JX]);
  await p.evaluate(()=>{режим('старт');екран(0);});
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>/Прочитано/.test(document.getElementById('кол-стан').textContent));
  s=await st(p); T(С,'профіль Б зчитав свої кольори (#111111), не кольори А',s.шкіра==='#111111'&&s.профіль===Б,s);
  await p.evaluate(async(a)=>{await перемкнути(a);},А); await p.waitForTimeout(400); s=await st(p);
  await shot(p,'2_03_повернення_на_А');
  T(С,'повернення на А: повтору й відповіді Б нема, кнопка читання доступна',!s.повторВидно&&!s.зчитатиDis&&s.профіль===А,s);
  // збій → повтор → нове читання під час повтору: кнопка не лишається disabled
  await p.evaluate(([j])=>{window.__модель(j);window.__збійМосту();КОЛІР={шкіра:null,волосся:null,очі:null,кільце:null,точки:null};},[JA2]);
  await p.click('#кол-зчитати'); await p.waitForFunction(()=>!document.getElementById('кол-повтор').hidden);
  await p.evaluate(()=>{ window.__р=null; містП=async()=>new Promise(r=>{window.__р=()=>r({стан:'готово',шкіра:['#111111'],волосся:['#222222'],очі:'#333333'});}); });
  await p.click('#кол-повтор'); await p.waitForFunction(()=>window.__р);
  s=await st(p); T(С,'під час повтору кнопка повтору недоступна (disabled), інакше подвійний запуск',s.повторDis,s);
  await p.evaluate(()=>{ містП=async()=>{throw new Error('новий збій');}; });
  await p.evaluate(()=>зчитатиКольориЗПортрета()); await p.evaluate(()=>window.__р()); await p.waitForTimeout(600);
  s=await st(p); await shot(p,'2_04_після_нового_запуску');
  T(С,'після нового запуску під час повтору кнопка повтору видима й не disabled; чужі кольори не застосовано',s.повторВидно&&!s.повторDis&&s.шкіра!=='#111111',s);
  T(С,'без винятків сторінки',errs.length===0,errs);
 }
 fs.writeFileSync(OUT+'/результат.json',JSON.stringify(R,null,1));
 await b.close();
})().catch(e=>{console.error('ПАДІННЯ',e);process.exit(2);});
