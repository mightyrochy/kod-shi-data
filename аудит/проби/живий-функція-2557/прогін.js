const {chromium}=require('playwright');
const out=process.argv[2]; const fs=require('fs'); fs.mkdirSync(out,{recursive:true});
const CHAT='прогулянка містом у суботу вдень';
const log=[]; const L=(...a)=>{const s=a.map(x=>typeof x==='string'?x:JSON.stringify(x)).join(' ');console.log(s);log.push(s)};
async function снап(p){return p.evaluate(async()=>{
  const g=id=>document.getElementById(id);
  const зап=await усіСценарії();
  return {
   шапка:g('сц-назва').textContent,
   статус:g('зб-статус').textContent,
   карти:[...document.querySelectorAll('#сцн-список .сцн-відкрити b')].map(b=>b.textContent),
   рейка:[...document.querySelectorAll('#бік-сценарії .бік-сцн')].map(b=>({текст:b.textContent,title:b.title})),
   оновити:g('сц-збер-оновити').textContent,
   запис:зап.map(с=>({ід:с.ід,назва:с.назва,час:с.час}))
  }})}
async function нова(c,w,h){const p=await c.newPage();await p.setViewportSize({width:w,height:h});return p}
(async()=>{
 const b=await chromium.launch();
 const ctx=await b.newContext({viewport:{width:390,height:844}});
 const p=await ctx.newPage(); const err=[]; p.on('pageerror',e=>err.push(String(e)));
 await p.goto('file:///home/user/kod-shi-data/index.html'); await p.waitForTimeout(2500);
 await p.evaluate(()=>режим('сценарій')); await p.waitForTimeout(400);
 await p.fill('#чат-поле',CHAT); await p.click('#чат-слати'); await p.waitForTimeout(4000);
 L('після чату: паспорт',await p.evaluate(()=>JSON.stringify(ПАСПОРТ_П)),'чат',await p.evaluate(()=>ЧАТ_П.length));
 await p.getByText('Або заповнити рукою').click(); await p.waitForTimeout(500);
 await p.locator('button',{hasText:'Звичайний день'}).first().click(); await p.waitForTimeout(500);
 L('нагода',await p.evaluate(()=>document.getElementById('сц-нагода').value));
 await p.screenshot({path:out+'/01_форма.png'});
 // 1) без назви
 await p.click('#аркуш-готово'); await p.waitForTimeout(500);
 await p.click('#сц-зберегти'); await p.waitForTimeout(500);
 L('поле перед збереженням:',JSON.stringify(await p.inputValue('#сц-назва-поле')));
 await p.screenshot({path:out+'/02_форма_збереження_порожня.png'});
 await p.click('#сц-збер-новий'); await p.waitForTimeout(800);
 await p.evaluate(()=>режим('сценарії')); await p.waitForTimeout(600);
 const s1=await снап(p); L('П1 після збереження без назви',s1);
 await p.screenshot({path:out+'/03_без_назви_збережені.png'});
 await p.evaluate(()=>режим('сценарій')); await p.waitForTimeout(400);
 await p.screenshot({path:out+'/04_без_назви_шапка.png'});
 await p.click('#сц-зберегти'); await p.waitForTimeout(500);
 L('П1 поле назви при повторному відкритті:',JSON.stringify(await p.inputValue('#сц-назва-поле')),'підпис кнопки оновити:',await p.evaluate(()=>document.getElementById('сц-збер-оновити').textContent));
 await p.screenshot({path:out+'/05_форма_повторно_порожня.png'});
 // 2) з назвою (як новий)
 const НАЗВА='Субота: кава й парк, «без метушні» 🙂';
 await p.fill('#сц-назва-поле',НАЗВА); await p.click('#сц-збер-новий'); await p.waitForTimeout(800);
 await p.screenshot({path:out+'/06_з_назвою_шапка.png'});
 await p.evaluate(()=>режим('сценарії')); await p.waitForTimeout(600);
 const s2=await снап(p); L('П2 після збереження з назвою',s2); L('П2 дослівно в шапці:',s2.шапка===НАЗВА,'в статусі:',s2.статус.includes(НАЗВА),'в картці:',s2.карти.includes(НАЗВА),'в рейці текст/title:',s2.рейка.some(r=>r.текст===НАЗВА),s2.рейка.some(r=>r.title===НАЗВА),'в записі:',s2.запис.some(z=>z.назва===НАЗВА));
 await p.screenshot({path:out+'/07_з_назвою_збережені.png'});
 await p.evaluate(()=>режим('сценарій')); await p.click('#сц-зберегти'); await p.waitForTimeout(500);
 L('П2 поле при повторному відкритті:',JSON.stringify(await p.inputValue('#сц-назва-поле')));
 await p.screenshot({path:out+'/08_форма_повторно_з_назвою.png'});
 // 3) старі записи
 await p.evaluate(async()=>{
   const d=await дб();
   const mk=(ід,назва,час)=>({...станСценарію(),ід,назва,профіль:АКТИВНИЙ,час});
   await new Promise((r,e)=>{const t=d.transaction('сценарії','readwrite');const s=t.objectStore('сценарії');
     for(const [ід,н,ч] of [['стар1','мій профіль','2026-09-01T10:00:00.000Z'],['стар2','Сценарій 01.09.2026','2026-09-01T11:00:00.000Z'],['стар3','День народження подруги','2026-09-02T09:00:00.000Z'],['стар4','Побачення','2026-09-03T09:00:00.000Z']]) s.put(mk(ід,н,ч),ід);
     t.oncomplete=r;t.onerror=()=>e(t.error)});
   await усіСценарії();
 });
 await p.reload(); await p.waitForTimeout(2500);
 await p.evaluate(()=>режим('сценарії')); await p.waitForTimeout(800);
 const s3=await снап(p); L('П3 старі записи (картки/рейка/запис)',s3);
 await p.screenshot({path:out+'/09_старі_записи_збережені.png'});
 for(const [ід,н] of [['стар1','мій профіль'],['стар2','Сценарій 01.09.2026'],['стар3','День народження подруги']]){
   await p.evaluate(x=>відкритиСценарій(x),ід); await p.waitForTimeout(600);
   L('П3 відкрито',ід,'шапка:',await p.evaluate(()=>document.getElementById('сц-назва').textContent));
   await p.click('#сц-зберегти'); await p.waitForTimeout(400);
   L('П3 поле назви у формі:',JSON.stringify(await p.inputValue('#сц-назва-поле')),'«Оновити»:',await p.evaluate(()=>document.getElementById('сц-збер-оновити').textContent));
   if(ід==='стар1')await p.screenshot({path:out+'/10_стар1_форма.png'});
   await p.evaluate(()=>показатиФормуЗбереження(false));
 }
 // рейка на широкому
 const w=await ctx.newPage(); await w.setViewportSize({width:1280,height:800});
 await w.goto('file:///home/user/kod-shi-data/index.html'); await w.waitForTimeout(2500);
 await w.evaluate(()=>режим('сценарій')); await w.waitForTimeout(800);
 await w.screenshot({path:out+'/11_рейка_широко.png'});
 L('рейка на широкому, видима:',await w.evaluate(()=>{const e=document.getElementById('бік-сценарії');return e&&e.offsetParent!==null}));
 L('помилки сторінки:',err);
 fs.writeFileSync(out+'/вивід.txt',log.join('\n')+'\n');
 await b.close();
})();
