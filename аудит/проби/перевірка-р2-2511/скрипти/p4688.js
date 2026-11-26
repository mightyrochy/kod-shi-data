const L=require('./lib.js');const fs=require('fs');
const out=[];const ok=(m,c)=>{out.push((c?'ПРОЙШЛО  ':'ПРОВАЛ   ')+m);console.log(out.at(-1));};
const [html,shots]=process.argv.slice(2);
(async()=>{const S=await L.start(html,{scale:2,file:true});
 try{
  let p=await S.open();p.setDefaultTimeout(20000);
  const reopen=async()=>{await p.close();p=await S.open();p.setDefaultTimeout(20000);};
  await p.evaluate(async()=>{await писатиКв('профілі',[{ід:'A',назва:'Профіль А'},{ід:'B',назва:'Профіль Б'}]);await писатиКв('активний','A');});
  await reopen();
  const jpg=await p.evaluate(async()=>{const c=document.createElement('canvas');c.width=400;c.height=500;const x=c.getContext('2d');
    const g=x.createLinearGradient(0,0,400,0);g.addColorStop(0,'#fff6e8');g.addColorStop(1,'#1c1410');x.fillStyle=g;x.fillRect(0,0,400,500);
    x.fillStyle='#d9a98a';x.beginPath();x.ellipse(200,230,90,120,0,0,7);x.fill();
    const b=await new Promise(r=>c.toBlob(r,'image/jpeg',.9));return Array.from(new Uint8Array(await b.arrayBuffer()));});
  fs.writeFileSync(shots+'/../синтетичний-портрет.jpg',Buffer.from(jpg));
  const openFoto=async()=>{await p.getByText('Мій профіль').first().click();await p.waitForTimeout(700);await p.getByText('Фото',{exact:true}).first().click();await p.waitForTimeout(900);};
  const upload=async()=>{await p.setInputFiles('#ф-портрет input[type=file]',{name:'p.jpg',mimeType:'image/jpeg',buffer:Buffer.from(jpg)});
    await p.waitForFunction(async()=>{try{const r=await читатиПортретП();return !!r.блоб;}catch(e){return false;}});};
  const stubs=(кер)=>p.evaluate((кер)=>{ // підставні лише міст моделі й міст виміру; код екрана, читач/писач, мовний шар — штатні
    window.модельРукиП=async()=>'synthetic';
    const o=window.__містO||(window.__містO=window.містП);window.містП=async(ім,дані)=>{if(ім==='колір'&&дані&&'відповідь_моделі' in дані)return {стан:'готово',шкіра:['#d9a98a'],волосся:['#2a1d16'],очі:'#4a3a2a',кільце:null,освітлення:null,зони:{}};throw new Error('мосту нема (синтетична проба)');};
    window.вимірПортретаП=async()=>кер==='світло'?{стан:'поза_воротами',причини:['portrait_uneven_light']}:{стан:'вимір',шкіра:{hex:'#d9a98a'},волосся:{hex:'#2a1d16'},очі:{hex:'#4a3a2a'},причини:[]};
  },кер);
  const run=async(кер)=>{await stubs(кер);await p.evaluate(()=>зчитатиКольориЗПортрета());await p.waitForTimeout(1500);console.log('DBG',JSON.stringify(await p.evaluate(()=>({стан:СТАН_КОЛЬОРУ_П,зріз:зрізЧитанняКольорівП(),колір:КОЛІР&&{п:КОЛІР.походження,пр:КОЛІР.причина_портрета}}))));};
  const порада=()=>p.evaluate(()=>{const v=document.getElementById('ф-світло-портрета');if(!v)return null;const r=v.getBoundingClientRect(),t=document.getElementById('ф-портрет')?.getBoundingClientRect();
    const cs=getComputedStyle(v);return {text:v.textContent.trim(),visible:r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none',top:r.top,bottom:r.bottom,photoTop:t&&t.top,photoBottom:t&&t.bottom,vh:innerHeight,подсказкаHidden:v.nextElementSibling?.hidden};});
  const ІДЕАЛ=/нерівномірно|освітлен/i;
  await openFoto();await upload();
  await p.screenshot({path:shots+'/4688-01-портрет-завантажено.png'});
  // 1. нерівне світло, мовний шар без відповіді (нема моста) → конкретна порада поряд із фото
  await run('світло');
  let d=await порада();console.log('порада:',JSON.stringify(d));
  await p.screenshot({path:shots+'/4688-02-порада-після-виміру.png'});
  ok('порада про нерівне світло присутня й видима: «'+(d?.text||'')+'»',!!d&&d.visible&&ІДЕАЛ.test(d.text));
  ok('позначка «оцінка моделі» поруч',!!d&&/оцінка моделі/i.test(d.text));
  ok('порада не загальний «на око» (не витіснена): ',!!d&&!/^Кольори з фото — на око/.test(d.text));
  // 2. reload
  await reopen();await p.waitForTimeout(1500);await openFoto();
  d=await порада();console.log('після reload:',JSON.stringify(d));await p.screenshot({path:shots+'/4688-03-після-reload.png'});
  ok('після reload порада відновлена',!!d&&d.visible&&ІДЕАЛ.test(d.text));
  // 3. А→Б→А
  await p.evaluate(()=>перемкнути('B'));await p.waitForTimeout(800);await openFoto();
  const б=await порада();await p.screenshot({path:shots+'/4688-04-профіль-Б.png'});
  ok('у профілі Б старої поради А нема',!б||!б.text||!ІДЕАЛ.test(б.text));
  await p.evaluate(()=>перемкнути('A'));await p.waitForTimeout(1200);await openFoto();
  d=await порада();await p.screenshot({path:shots+'/4688-05-знову-А.png'});
  ok('після А→Б→А порада А на місці',!!d&&d.visible&&ІДЕАЛ.test(d.text));
  const A2=await p.evaluate(()=>читатиКв('дзеркало:кольори:'+АКТИВНИЙ).catch(()=>null));
  // 4. успішний вимір знімає
  await run('вимір');d=await порада();await p.screenshot({path:shots+'/4688-06-успішний-вимір.png'});
  ok('успішний вимір знімає пораду',!d||!d.text);
  // 5. знову нерівне → заміна кадру знімає
  await run('світло');d=await порада();ok('порада повернулась на новому нерівному вимірі',!!d&&ІДЕАЛ.test(d.text));
  const ver=()=>p.evaluate(async()=>(await читатиПортретП()).версія);
  const v0=await ver();await p.evaluate(()=>{window.модельРукиП=async()=>{throw new Error('моста нема');};});
  await p.setInputFiles('#ф-портрет input[type=file]',{name:'p2.jpg',mimeType:'image/jpeg',buffer:Buffer.from(jpg)});
  await p.waitForFunction(async v=>(await читатиПортретП()).версія!==v,v0,{timeout:8000}).catch(()=>{});
  await p.waitForTimeout(2500);
  const v1=await ver();d=await порада();await p.screenshot({path:shots+'/4688-07-після-заміни-кадру.png'});
  console.log('версія слота',v0,'→',v1,JSON.stringify(d));
  {const st=await p.evaluate(()=>({пр:КОЛІР.причина_портрета||null,св:зрізЧитанняКольорівП().світло_портрета}));console.log('ДО reload стан',JSON.stringify(st));await reopen();await openFoto();const dd=await порада();console.log('ПІСЛЯ reload',JSON.stringify(dd&&dd.text));ok('(довідково) після заміни кадру і reload порада: '+(dd&&dd.text?'є':'нема'),!dd||!dd.text);await openFoto().catch(()=>{});}
  ok(`заміна кадру (версія ${v0}→${v1}) знімає пораду`,v1!==v0&&(!d||!d.text||!ІДЕАЛ.test(d.text)));
  // 6. вилучення знімає
  await run('світло');d=await порада();ok('порада знову є перед вилученням',!!d&&ІДЕАЛ.test(d.text));
  await p.locator('#ф-портрет button:visible').last().click().catch(e=>console.log('× не натиснуто',String(e).slice(0,100)));
  await p.waitForTimeout(2000);d=await порада();await p.screenshot({path:shots+'/4688-08-після-вилучення.png'});
  console.log('після вилучення',JSON.stringify(d));
  ok('вилучення портрета знімає пораду',!d||!d.text||!ІДЕАЛ.test(d.text));
  ok('без винятків сторінки: '+JSON.stringify(p.errs),p.errs.length===0);
  fs.writeFileSync(shots+'/../4688-результати.txt',out.join('\n')+'\nЗАПИТАНІ URL: '+JSON.stringify([...new Set(S.log.all)])+'\nabort: '+JSON.stringify(S.log.blocked)+'\n');
 }catch(e){console.error('ВИНЯТОК',e)}finally{await S.br.close();}})();
