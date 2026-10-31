const {chromium}=require('playwright');
const out=process.argv[2]; const fs=require('fs'); fs.mkdirSync(out,{recursive:true});
const URL='file:///home/user/kod-shi-data/index.html';
const CHAT='прогулянка містом у суботу вдень';
const log=[]; const L=(...a)=>{const s=a.map(x=>typeof x==='string'?x:JSON.stringify(x)).join(' ');console.log(s);log.push(s)};
async function показ(p){return p.evaluate(async()=>{
  const g=id=>document.getElementById(id);
  const зап=await усіСценарії();
  return {
   вибір:[...g('пф-вибір').options].map(o=>o.textContent),
   кнопка_title:g('пф-кнопка').title, ініціали:g('пф-ініціали').textContent,
   огляд:g('ог-імʼя').textContent,
   шапка:g('сц-назва').textContent,
   картки:[...document.querySelectorAll('#сцн-список .сцн-відкрити b')].map(b=>b.textContent),
   рейка:[...document.querySelectorAll('#бік-сценарії .бік-сцн')].map(b=>({текст:b.textContent,title:b.title})),
   профілі_сховище:(await читатиКв_('профілі')).map(п=>п.назва),
   сценарії_сховище:зап.map(с=>с.назва),
   позначка:await читатиКв_('назви-очищено')
  }})}
(async()=>{
 const b=await chromium.launch();
 const ctx=await b.newContext({viewport:{width:390,height:844}});
 const p=await ctx.newPage(); const err=[]; p.on('pageerror',e=>err.push(String(e)));
 await p.goto(URL); await p.waitForTimeout(2500);
 L('очиститиСтаріНазвиП у збірці:',await p.evaluate(()=>typeof очиститиСтаріНазвиП));
 // Крок А: нова користувачка, без імені
 await p.evaluate(()=>режим('профіль')); await p.waitForTimeout(500);
 const а0=await показ(p); L('А0 новий профіль без імені',а0);
 await p.screenshot({path:out+'/01_новий_профіль_без_імені.png'});
 // Крок Б: старий стан — як лишав старий код
 const ст=await p.evaluate(async()=>{
   КОЛІР={шкіра:'#f2d6c4',волосся:'#4a4644',очі:'#6b8cae',кільце:null,точки:null};
   for(const [і,v] of [['мр-зріст',167],['мр-плечі',96],['мр-груди',92],['мр-талія',74],['мр-стегна',100]]) document.getElementById(і).value=v;
   await писатиАктивний(); await створитиПрофіль(); await перемкнути(ПРОФІЛІ[0].ід); режим('сценарій');
   await зберегтиСценарій('Вечеря з Олею',true);
   const з=await зберегтиСценарій('',true);
   const напис='Сценарій '+new Date(з.час).toLocaleDateString('uk-UA');
   ПРОФІЛІ[0].назва='мій профіль'; ПРОФІЛІ[1].назва='профіль 2'; await писатиКв('профілі',ПРОФІЛІ);
   const d=await дб();
   await tx(d,'сценарії','readwrite',s=>s.put(Object.assign({},з,{назва:напис}),з.ід));
   const ч=await читатиКв_(ключЧернетки()); ч.сц.назва=напис; await писатиКв(ключЧернетки(),ч);
   await tx(d,'кв','readwrite',s=>s.delete('назви-очищено'));
   return {напис,ід:з.ід,профілі:(await читатиКв_('профілі')).map(п=>п.назва),позначка:await читатиКв_('назви-очищено')};
 });
 L('Б підготовка старих записів',ст);
 await p.reload(); await p.waitForTimeout(2500);
 await p.evaluate(()=>режим('профіль')); await p.waitForTimeout(500);
 const б1=await показ(p); L('Б1 після читання старих записів (профіль)',б1);
 await p.screenshot({path:out+'/02_старі_після_читання_профіль.png'});
 await p.evaluate(()=>режим('сценарій')); await p.waitForTimeout(500);
 const б2=await показ(p); L('Б2 сценарій після читання',б2);
 await p.screenshot({path:out+'/03_старі_після_читання_сценарій.png'});
 await p.evaluate(()=>режим('сценарії')); await p.waitForTimeout(500);
 await p.screenshot({path:out+'/04_старі_збережені.png'});
 await p.evaluate(()=>режим('сценарій')); await p.click('#сц-зберегти'); await p.waitForTimeout(400);
 L('Б форма збереження старого сценарію, поле назви:',JSON.stringify(await p.inputValue('#сц-назва-поле')));
 await p.screenshot({path:out+'/05_форма_збереження_порожня.png'});
 await p.evaluate(()=>показатиФормуЗбереження(false));
 // Крок В: вона вводить ім'я «мій профіль» і назву сценарію рівну напису
 await p.evaluate(()=>режим('профіль')); await p.waitForTimeout(300);
 await p.click('button[data-аркуш="проф-блок"]'); await p.waitForTimeout(500);
 await p.screenshot({path:out+'/05б_аркуш_імені.png'});
 await p.fill('#пр-імʼя','мій профіль');
 await p.click('#аркуш-готово'); await p.waitForTimeout(400);
 await p.evaluate(async(н)=>{await писатиАктивний(); await зберегтиСценарій(н,true);},ст.напис);
 await p.reload(); await p.waitForTimeout(2500);
 await p.evaluate(()=>режим('профіль')); await p.waitForTimeout(500);
 const в=await показ(p); L('В її слова дослівно після перезавантаження',в);
 await p.screenshot({path:out+'/06_її_слова.png'});
 // Крок Г: інше ім'я з лапками й емодзі
 const ІМ='Оля «К.» 🙂';
 await p.click('button[data-аркуш="проф-блок"]'); await p.waitForTimeout(400);
 await p.fill('#пр-імʼя',ІМ); await p.click('#аркуш-готово'); await p.waitForTimeout(300); await p.evaluate(()=>писатиАктивний()); await p.waitForTimeout(300);
 const г=await показ(p); L('Г ім\'я з лапками й емодзі',г,'вибір[0]===ім\'я:',г.вибір[0]===ІМ,'title:',г.кнопка_title===ІМ,'огляд:',г.огляд===ІМ);
 await p.screenshot({path:out+'/07_ім_я_дослівно.png'});
 await p.evaluate(()=>режим('сценарій')); await p.waitForTimeout(300);
 await p.fill('#чат-поле',CHAT); await p.click('#чат-слати'); await p.waitForTimeout(3000);
 L('чат: паспорт',await p.evaluate(()=>JSON.stringify(ПАСПОРТ_П)),'реплік',await p.evaluate(()=>ЧАТ_П.length));
 await p.screenshot({path:out+'/08_після_чату.png'});
 L('помилки сторінки:',err);
 fs.writeFileSync(out+'/вивід.txt',log.join('\n')+'\n');
 await b.close();
})();
