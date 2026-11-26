const L=require('./lib.js');const fs=require('fs');
const out=[];const ok=(m,c)=>{out.push((c?'ПРОЙШЛО  ':'ПРОВАЛ   ')+m);console.log(out.at(-1));};
const [html,shots,w0,h0]=process.argv.slice(2);const W=+w0||390,H=+h0||844,tag=W+'x'+H;
const mount=()=>{
  const px='iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==';
  try{режим('оцінка');}catch(e){window.__режимПомилка=String(e)}
  ОЦ.фото=[{ід:'ф1',тип:'image/png',дані:px},{ід:'ф2',тип:'image/png',дані:px}];
  ОЦ.перелік={так:true};
  ОЦ.результат={картка:{відповідь:'Так, кольори поєднуються.',вердикт:'wear_with_change',вдало:[{про:'palette',речі:['ф1'],текст:'Хакі біля обличчя — у твоїй палітрі.'}],змінити:[],не_знаю:[]},суд:{},сценарій:{},допит:[]};
  намалюватиКарткуОцінки();
  window.__смонтовано={картка:!!$('оц-картка'),зап:!!$('зап-оц'),ком:!!$('ком-оц'),вст:!!$('вст-оц')};
};(async()=>{const S=await L.start(html,{w:W,h:H,scale:2,file:true,touch:W<600});
 try{
  const p=await S.open();p.setDefaultTimeout(15000);
  await p.evaluate(mount);await p.waitForTimeout(800);
  const м=await p.evaluate(()=>({...window.__смонтовано,реж:window.__режимПомилка||null,кількість:document.querySelectorAll('#зап-оц').length,вРяду:!!$('зап-оц')&&!!$('зап-оц').closest('.ряд-запису'),вФормі:!!$('зап-оц')&&!!$('зап-оц').closest('.форма-вердикту'),disabled:$('зап-оц')&&$('зап-оц').disabled,екранОцінки:getComputedStyle($('е-оцінка')).display}));
  console.log('МОНТУВАННЯ',JSON.stringify(м));
  ok(`${tag}: фотооцінка змонтована справжнім кодом (#оц-картка, #зап-оц, #ком-оц)`,м.картка&&м.зап&&м.ком);
  ok(`${tag}: #зап-оц єдина, у .ряд-запису і .форма-вердикту, не disabled (${JSON.stringify(м)})`,м.кількість===1&&м.вРяду&&м.вФормі&&!м.disabled);
  const geo=()=>p.evaluate(()=>{const b=$('зап-оц'),т=$('ком-оц'),ф=b.closest('.форма-вердикту'),к=ф.querySelector('.керування-вердикту');
    const rb=b.getBoundingClientRect(),rk=к.getBoundingClientRect(),rt=т.getBoundingClientRect(),vv=visualViewport;
    const cx=rb.left+rb.width/2,cy=rb.top+rb.height/2;const hit=document.elementFromPoint(cx,cy);
    const панель=document.getElementById('чат-панель')||document.querySelector('[id*=панель]');
    const lastChip=[...к.querySelectorAll('button,.чип')].filter(x=>x!==b).pop();
    return {btn:[Math.round(rb.top),Math.round(rb.bottom)],керув:[Math.round(rk.top),Math.round(rk.bottom)],керСкрол:[к.scrollTop,к.scrollHeight,к.clientHeight],
      поле:[Math.round(rt.top),Math.round(rt.bottom),т.scrollHeight>т.clientHeight],vh:innerHeight,vv:[vv.height,vv.offsetTop],
      кнопкаПерекритаКерувань:rb.top<rk.bottom-0.5&&rb.bottom>rk.top&&rb.left<rk.right&&rb.right>rk.left,
      кнопкаУВікні:rb.top>=0&&rb.bottom<=innerHeight,цільКнопка:hit===b||b.contains(hit),хто:hit&&(hit.id||hit.className||hit.tagName),
      позиціяРяду:getComputedStyle(b.closest('.ряд-запису')).position,displayФорми:getComputedStyle(ф).display,scrollY:Math.round(scrollY)};});
  // довести картку до вердикту
  await p.evaluate(()=>$('ком-оц').closest('.форма-вердикту').scrollIntoView({block:'end'}));await p.waitForTimeout(500);
  let g=await geo();console.log('ПОЧАТОК',JSON.stringify(g));
  await p.screenshot({path:`${shots}/4696n-оц-${tag}-01-початок.png`});
  ok(`${tag}: 0 px перекриття кнопка↔керування на початку (кнопка ${g.btn}, керування ${g.керув})`,!g.кнопкаПерекритаКерувань);
  if(W<600) ok(`${tag}: кнопка досяжна (елемент у її центрі = кнопка; в вікні=${g.кнопкаУВікні}; хто: ${g.хто})`,g.цільКнопка&&g.кнопкаУВікні);
  // 12+ рядків реальною клавіатурою
  await p.evaluate(()=>$('ком-оц').focus());
  for(let i=1;i<=14;i++){await p.keyboard.type('рядок відгуку '+i+' про образ');await p.keyboard.press('Enter');}
  await p.waitForTimeout(800);
  g=await geo();console.log('14 РЯДКІВ',JSON.stringify(g));
  await p.screenshot({path:`${shots}/4696n-оц-${tag}-02-14-рядків.png`});
  ok(`${tag}: після 14 рядків 0 px перекриття (кнопка ${g.btn}, керування ${g.керув})`,!g.кнопкаПерекритаКерувань);
  ok(`${tag}: після 14 рядків кнопка досяжна без гортання (в вікні=${g.кнопкаУВікні}, хто: ${g.хто}, scrollY=${g.scrollY})`,g.цільКнопка&&g.кнопкаУВікні);
  // імітація клавіатури: зменшення вікна (НЕ справжня екранна клавіатура)
  if(W<600){
   await p.setViewportSize({width:W,height:480});await p.waitForTimeout(900);
   g=await geo();console.log('ВІКНО 480',JSON.stringify(g));await p.screenshot({path:`${shots}/4696n-оц-${tag}-03-вікно-480-імітація-клавіатури.png`});
   ok(`${tag}: «клавіатура» (вікно 390×480, ІМІТАЦІЯ resize): 0 px перекриття`,!g.кнопкаПерекритаКерувань);
   out.push('СПОСТЕРЕЖЕННЯ '+tag+': «клавіатура» (імітація 390×480) після 14 рядків: без гортання кнопка під шапкою (btn '+g.btn+', у центрі '+g.хто+') — гортач mirror-work');
   const дост=await p.evaluate(()=>{const b=$('зап-оц');b.scrollIntoView({block:'center'});const q=b.getBoundingClientRect();const h=document.elementFromPoint(q.left+q.width/2,q.top+q.height/2);return {top:Math.round(q.top),ok:h===b||b.contains(h)}});
   ok(`${tag}: «клавіатура» (імітація): кнопка досяжна одним гортанням mirror-work (top ${дост.top}, ціль = кнопка)`,дост.ok);
   await p.screenshot({path:`${shots}/4696n-оц-${tag}-03б-після-гортання-480.png`});
   // дотик по кнопці
   const bb=await p.evaluate(()=>{const r=$('зап-оц').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]});
   await p.touchscreen.tap(bb[0],bb[1]);await p.waitForTimeout(600);
   const ст=await p.evaluate(()=>($('вст-оц')||{}).textContent);console.log('після тапу статус:',ст);
   // фізичні жести обох осей (CDP)
   await p.setViewportSize({width:W,height:H});await p.waitForTimeout(600);
   const cdp=await S.ctx.newCDPSession(p);
   const swipe=async(x1,y1,x2,y2)=>{await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:x1,y:y1}]});
     for(let i=1;i<=10;i++){await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:x1+(x2-x1)*i/10,y:y1+(y2-y1)*i/10}]});await p.waitForTimeout(16);}
     await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await p.waitForTimeout(500);};
   const до0=await geo();console.log('ПІСЛЯ ПОВЕРНЕННЯ ВІКНА 844',JSON.stringify(до0),await p.evaluate(()=>{const f=$('ком-оц').closest('.форма-вердикту');return [f.style.getPropertyValue('--висота-вердикту'),Math.round(f.getBoundingClientRect().top),Math.round(f.getBoundingClientRect().height),scrollY,document.documentElement.scrollHeight]}));await p.screenshot({path:`${shots}/4696n-оц-${tag}-03б-після-повернення-вікна.png`});console.log('СПОСТЕРЕЖЕННЯ: після повернення вікна 844 без гортання кнопка нижче краю (btn '+до0.btn+') — сторінка не перегорнута сама');await p.evaluate(()=>$('ком-оц').closest('.форма-вердикту').scrollIntoView({block:'end'}));await p.waitForTimeout(500);{const г=await geo();await p.screenshot({path:`${shots}/4696n-оц-${tag}-03в-після-догортання.png`});ok(`${tag}: після закриття «клавіатури» і догортання кнопка у вікні й досяжна (кнопка ${г.btn}, vh ${г.vh}, хто ${г.хто})`,г.кнопкаУВікні&&г.цільКнопка&&!г.кнопкаПерекритаКерувань);}
   const ядро=await p.evaluate(()=>{const к=$('ком-оц').closest('.форма-вердикту').querySelector('.керування-вердикту');const r=к.getBoundingClientRect();return [r.left+r.width/2,r.top+Math.min(r.height-20,150)]});
   const до=await geo();
   await swipe(ядро[0],ядро[1]+60,ядро[0],ядро[1]-60); // палець вгору по керуваннях (вісь Y)
   const піс=await geo();
   ok(`${tag}: вертикальний жест по керуваннях гортає їх (scrollTop ${до.керСкрол[0]}→${піс.керСкрол[0]}), кнопка на місці (${до.btn}→${піс.btn})`,піс.керСкрол[0]>до.керСкрол[0]&&до.btn[0]===піс.btn[0]);
   await swipe(ядро[0],ядро[1]-40,ядро[0],ядро[1]+120);
   const н3=await geo();console.log('жест вниз',JSON.stringify(н3.керСкрол),JSON.stringify(н3.btn));
   // горизонтальна вісь: жест по ряду осі не має зсувати кнопку/сторінку
   const sx0=await p.evaluate(()=>scrollX);await swipe(ядро[0]-100,ядро[1],ядро[0]+100,ядро[1]);
   const sx1=await p.evaluate(()=>scrollX);const н4=await geo();
   ok(`${tag}: горизонтальний жест не зсуває сторінку (scrollX ${sx0}→${sx1}) і кнопку (${до.btn}→${н4.btn})`,sx0===sx1&&н4.btn[0]===до.btn[0]);
   await p.screenshot({path:`${shots}/4696n-оц-${tag}-04-після-жестів.png`});
  }else{
   // 1280×800: липка кнопка збережена
   ok(`${tag}: ряд запису лишається липким (position=${g.позиціяРяду}) і display форми=${g.displayФорми} (не grid)`,g.позиціяРяду==='sticky'&&g.displayФорми!=='grid');
   await p.evaluate(()=>scrollTo(0,0));await p.waitForTimeout(400);const г2=await geo();
   ok(`${tag}: кнопка у вікні при прокрутці вгору (кнопка ${г2.btn}, vh ${г2.vh})`,г2.кнопкаУВікні);
  }
  const арт=p.errs.filter(e=>/reading 'питання'/.test(e)),інші=p.errs.filter(e=>!/reading 'питання'/.test(e));
  if(арт.length) out.push('СПОСТЕРЕЖЕННЯ '+tag+': тап по #зап-оц досяг справжнього обробника «оцінка-записати»; він впав на ОЦ.етапи=null — артефакт мого синтетичного стану (ОЦ.етапи не заповнено, повного конвеєра без моделі нема): '+JSON.stringify(арт));
  ok(`${tag}: інших винятків сторінки нема: ${JSON.stringify(інші)}`,інші.length===0);
  fs.writeFileSync(`${shots}/../4696n-оц-результати-${tag}.txt`,out.join('\n')+'\nЗАПИТАНІ URL: '+JSON.stringify([...new Set(S.log.all)])+'\nabort: '+JSON.stringify(S.log.blocked)+'\n');
 }catch(e){console.error('ВИНЯТОК',e)}finally{await S.br.close();}})();
