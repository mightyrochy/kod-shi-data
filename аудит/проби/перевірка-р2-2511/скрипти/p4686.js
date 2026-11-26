const assert=require('node:assert/strict');const L=require('./lib.js');
const out=[];const ok=(m,c)=>{out.push((c?'ПРОЙШЛО  ':'ПРОВАЛ   ')+m);console.log(out.at(-1));};
const key=p=>'дзеркало:речі:1:'+p;
const річ=id=>({id,name:'Річ '+id,color:'#f0ede5',price:null,image:'',url:'',shop:'',slot:'top'});
const дані=p=>({version:1,closet:[річ('closet-'+p)],compare:{},outfit:{name:'',id:'',side:0,sets:[[],[]]},saved:[{id:'saved',name:'Комплект '+p,things:[річ('piece-'+p)],worn:false,date:1}]});
const html=process.argv[2],shots=process.argv[3];
(async()=>{
  const S=await L.start(html,{scale:2});
  const seed=async(p,a,b)=>p.evaluate(async([a,b])=>{await писатиКв('профілі',[{ід:'A',назва:'Профіль А'},{ід:'B',назва:'Профіль Б'}]);await писатиКв('активний','A');await писатиКв('дзеркало:речі:1:A',a);await писатиКв('дзеркало:речі:1:B',b);},[a,b]);
  const ux=async(p,k,v)=>{console.log('  ux',k,v);return ux0(p,k,v);};const ux0=(p,k,v)=>p.locator('[data-ux="'+k+'"]'+(v===undefined?'':'[data-value="'+v+'"]')+':visible').first().click();
  const rd=(p,id)=>p.evaluate(k=>читатиКв(k),key(id));
  try{
    // ---- 1. дія зберігається в початковому профілі при A→Б під час затриманого читання
    for(const дія of ['rack-edit-saved','rack-own','rack-add']){
      const p=await S.open();p.setDefaultTimeout(8000);console.log('→',дія);
      await seed(p,дані('A'),дані('B'));
      await p.reload();await p.waitForFunction(()=>window.MirrorRoom?.available());
      const before={A:await rd(p,'A'),B:await rd(p,'B')};
      await ux(p,'library');
      if(дія==='rack-edit-saved'){await ux(p,'rack-saved','saved');}
      else {await ux(p,'rack-saved','saved');await ux(p,'rack-edit-saved','saved');await ux(p,'rack-add-side','0');}
      // армуємо затримку читання сховища А
      await p.evaluate(k=>{window.__gate=null;window.__held=0;const o=window.читатиКв;window.__o=o;window.читатиКв=function(key){if(key===k&&window.__armed){window.__held++;return new Promise(r=>{window.__gate=()=>{window.__armed=false;r(o(key));};});}return o.apply(this,arguments);};},key('A'));
      await p.evaluate(()=>{window.__armed=true;});
      const val=дія==='rack-edit-saved'?'saved':(дія==='rack-own'?'piece-A':'closet-A');
      // дія: клік через справжній делегат
      if(дія==='rack-own'||дія==='rack-add'){ try{await ux(p,'rack-set-own');}catch(e){} }
      await p.evaluate(([d,v])=>{const b=document.querySelector('[data-ux="'+d+'"][data-value="'+v+'"]')||document.querySelector('[data-ux="'+d+'"]');if(b)b.click();window.__clicked=!!b;},[дія,val]);
      const clicked=await p.evaluate(()=>window.__clicked);
      const held=await p.evaluate(()=>window.__held);
      console.log('  перемкнути');await Promise.race([p.evaluate(()=>перемкнути('B')),new Promise((_,j)=>setTimeout(()=>j(new Error('перемкнути завис >20с')),20000))]);console.log('  перемкнено');
      const activeB=await p.evaluate(()=>MirrorRoom.activeProfile());
      const heldEnd=await p.evaluate(()=>{const h=window.__held;window.__gate&&window.__gate();window.__armed=false;return h;});console.log('  затримано читань А:',heldEnd);
      await p.waitForTimeout(1500);
      const after={A:await rd(p,'A'),B:await rd(p,'B')};
      const heading=await p.evaluate(()=>document.querySelector('#mirror-heading h1')?.textContent||'');
      const bodyA=await p.evaluate(()=>document.body.innerText.includes('Комплект A')||document.body.innerText.includes('Річ closet-A'));
      await p.screenshot({path:`${shots}/4686-${дія}-після-A→Б.png`});
      ok(`${дія}: клік=${clicked}, затримано читань=${held}, активний після перемикання=${activeB}`,clicked&&activeB==='B');
      ok(`${дія}: профіль Б не змінено`,JSON.stringify(after.B)===JSON.stringify(before.B));
      ok(`${дія}: запис пішов у А (A.outfit.id/sets змінились або дія виконана): outfit.id=${after.A.outfit.id} sets0=${after.A.outfit.sets[0].length}`,JSON.stringify(after.A)!==JSON.stringify(before.A));
      ok(`${дія}: екран Б не показує дані А (заголовок «${heading}»)`,!bodyA);
      ok('без винятків сторінки: '+JSON.stringify(p.errs),p.errs.length===0);
      await p.close();
    }
    // ---- 3. дві вкладки: застаріла згода не перезаписує новішу чернетку
    for(const зміна of ['інша чернетка','та сама чернетка']){
      const синт=дані('A');синт.saved.push({id:'інший',name:'Інший образ',things:[річ('one'),річ('two')],worn:false,date:2});
      синт.outfit={id:'чернетка',name:'Початкова чернетка',side:0,sets:[[річ('one'),річ('two')],[]]};
      const s0=await S.open();await seed(s0,синт,дані('B'));await s0.close();
      const p1=await S.open(),p2=await S.open();p1.setDefaultTimeout(8000);p2.setDefaultTimeout(8000);console.log('→',зміна);
      const conf='#mirror-sheet[open] [data-ux="rack-confirm-edit"]';
      const edit=async(p,id)=>{await p.evaluate(()=>MirrorRoom.route('бібліотека'));await ux(p,'rack-saved',id);await ux(p,'rack-edit-saved',id);};
      await edit(p1,'saved');
      await p1.waitForSelector(conf);
      await p1.screenshot({path:`${shots}/4686-дві-вкладки-${зміна}-діалог-вкладка1.png`});
      if(зміна==='інша чернетка'){await edit(p2,'інший');await p2.locator(conf).first().click();}
      else{await p2.evaluate(()=>MirrorRoom.route('бібліотека'));await p2.locator('#mirror-saved-manual [data-ux="compose"]').first().click();}
      await p2.waitForTimeout(800);
      const до=await rd(p2,'A');
      if(зміна==='та сама чернетка'){await ux(p2,'rack-edit','0|two');await p2.locator('#mirror-sheet[open] [data-ux="rack-drop"][data-value="0|two"]').first().click();await p2.waitForTimeout(800);}
      const змінена=await rd(p2,'A');
      await p1.locator(conf).first().click();await p1.waitForTimeout(1200);
      const після=await rd(p1,'A');
      const msg=await p1.evaluate(()=>document.querySelector('#mirror-sheet-content')?.textContent||'');
      await p1.screenshot({path:`${shots}/4686-дві-вкладки-${зміна}-після-старої-згоди.png`});
      ok(`${зміна}: стара згода не перезаписала новішу чернетку (outfit.id ${змінена.outfit.id}→${після.outfit.id}, речей ${змінена.outfit.sets[0].length}→${після.outfit.sets[0].length})`,JSON.stringify(після.outfit)===JSON.stringify(змінена.outfit));
      ok(`${зміна}: вкладка 1 повідомляє про конфлікт («${msg.slice(0,90)}»)`,/Чернетка змінилася|підтвердити заміну|Не вдалося/.test(msg));
      ok('профіль Б цілий',JSON.stringify(await rd(p1,'B'))===JSON.stringify(дані('B')));
      await p1.close();await p2.close();
    }
    const запити=S.log.all||[];
    console.log('ЗАПИТАНІ URL:',JSON.stringify([...new Set(запити)]),'заблоковано:',JSON.stringify(S.log.blocked));
    require('fs').writeFileSync(shots+'/../4686-результати.txt',out.join('\n')+'\nЗАПИТАНІ URL: '+JSON.stringify([...new Set(запити)])+'\nзаблоковано (abort): '+JSON.stringify(S.log.blocked)+'\n');
  }catch(e){console.error('ВИНЯТОК',e);}finally{await S.br.close();}
})();
