const L=require('./lib.js');const fs=require('fs');
const out=[];const ok=(m,c)=>{out.push((c?'ПРОЙШЛО  ':'ПРОВАЛ   ')+m);console.log(out.at(-1));};
const річ=id=>({id,name:'Річ '+id,color:'#f0ede5',price:null,image:'',url:'',shop:'',slot:'top'});
const дані=p=>({version:1,closet:[річ('closet-'+p)],compare:{},outfit:{name:'',id:'',side:0,sets:[[],[]]},saved:[{id:'saved',name:'Комплект '+p,things:[річ('piece-'+p)],worn:false,date:1}]});
const key=p=>'дзеркало:речі:1:'+p;const [html,shots]=process.argv.slice(2);
(async()=>{const S=await L.start(html,{scale:2});
 const rd=(p,id)=>p.evaluate(k=>читатиКв(k),key(id));
 const ux=(p,k,v)=>p.locator('[data-ux="'+k+'"]'+(v===undefined?'':'[data-value="'+v+'"]')+':visible').first().click();
 try{
 for(const дія of ['rack-add','rack-own']){
  const p=await S.open();p.setDefaultTimeout(10000);
  await p.evaluate(async([a,b])=>{await писатиКв('профілі',[{ід:'A',назва:'Профіль А'},{ід:'B',назва:'Профіль Б'}]);await писатиКв('активний','A');await писатиКв('дзеркало:речі:1:A',a);await писатиКв('дзеркало:речі:1:B',b);},[дані('A'),дані('B')]);
  await p.reload();await p.waitForFunction(()=>window.MirrorRoom?.available());
  const before={A:await rd(p,'A'),B:await rd(p,'B')};
  await ux(p,'library');await ux(p,'rack-saved','saved');await ux(p,'rack-edit-saved','saved');
  let target;
  if(дія==='rack-add'){await ux(p,'rack-add-side','0');await ux(p,'rack-set-own');await ux(p,'rack-item','closet-A');target='closet-A';}
  else{target='piece-A';}
  const mid=await rd(p,'A');
  await p.evaluate(()=>{const o=window.дб;window.__held=0;window.__armed=true;window.дб=function(){if(window.__armed){window.__armed=false;window.__held++;const a=arguments;return new Promise(r=>{window.__gate=()=>r(o.apply(this,a));});}return o.apply(this,arguments);};});
  if(дія==='rack-add') await ux(p,'rack-add',target);
  else await p.evaluate(v=>{const b=document.createElement('button');b.dataset.ux='rack-own';b.dataset.value=v;b.id='__инж';document.body.appendChild(b);b.click();},target);
  await p.waitForTimeout(300);
  const held=await p.evaluate(()=>window.__held);
  await Promise.race([p.evaluate(()=>перемкнути('B')),new Promise((_,j)=>setTimeout(()=>j(new Error('перемкнути завис')),25000))]);
  const act=await p.evaluate(()=>MirrorRoom.activeProfile());
  await p.evaluate(()=>{window.__gate&&window.__gate();window.__armed=false;});
  await p.waitForTimeout(2000);
  const A=await rd(p,'A'),B=await rd(p,'B');
  await p.screenshot({path:`${shots}/4686-${дія}-після-A→Б.png`});
  ok(`${дія}: відкриття транзакції запису А затримано (${held}), активний став ${act}`,held>=1&&act==='B');
  if(дія==='rack-add') ok(`${дія}: річ ${target} додана в чернетку А (sets0: ${JSON.stringify(A.outfit.sets[0].map(x=>x.id))})`,A.outfit.sets[0].some(x=>x.id===target)&&!mid.outfit.sets[0].some(x=>x.id===target));
  else ok(`${дія}: річ ${target} потрапила в гардероб А (closet: ${JSON.stringify(A.closet.map(x=>x.id))})`,A.closet.some(x=>x.id===target));
  ok(`${дія}: профіль Б побайтово без змін`,JSON.stringify(B)===JSON.stringify(before.B));
  ok(`${дія}: активний профіль лишився Б, виняток сторінки: ${JSON.stringify(p.errs)}`,p.errs.length===0);
  await p.close();
 }
 fs.writeFileSync(shots+'/../4686-результати-б.txt',out.join('\n')+'\nЗАПИТАНІ URL: '+JSON.stringify([...new Set(S.log.all)])+'\nабort: '+JSON.stringify(S.log.blocked)+'\n');
 }catch(e){console.error('ВИНЯТОК',e)}finally{await S.br.close();}})();
