const L=require('./lib.js');const fs=require('fs');
const out=[];const ok=(m,c)=>{out.push((c?'ПРОЙШЛО  ':'ПРОВАЛ   ')+m);console.log(out.at(-1));};
const [html,shots]=process.argv.slice(2);
const png=Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==','base64');
const U=n=>'https://img.invalid/'+n+'.jpg';
const річ=(id,o={})=>({id,назва:'Річ '+id,слот:'верх',фото:U(id+'1'),фото_усі:[U(id+'1'),U(id+'2'),U(id+'3')],ціна:1000,урл:'https://shop.invalid/'+id,кадр_виміру:{стан:'measured'},клас_кадру:'ціла_річ',...o});
const кейси={
 'A відхилено підтверджений кадр':{x:річ('a@s'),відх:[{id:'a@s',адреси:[U('a@s1')],неоднозначно:false}],чекаємо:{запитано:[],силует:true}},
 'B відхилено інший кадр, підтверджений не чіпати':{x:річ('b@s'),відх:[{id:'b@s',адреси:[U('b@s2')],неоднозначно:false}],чекаємо:{запитано:[U('b@s1')],силует:'після помилки підтвердженого'}},
 'C неоднозначне відхилення':{x:річ('c@s'),відх:[{id:'c@s',адреси:[],неоднозначно:true}],чекаємо:{запитано:[],силует:true}},
 'D контроль без відхилення (кадри вичерпуються)':{x:річ('d@s'),відх:[],чекаємо:{запитано:[U('d@s1'),U('d@s2'),U('d@s3')],силует:'після вичерпання'}},
 'E стара картка: позначка лише на рівні речі':{x:річ('e@s'),відх:undefined,не_ті:['e@s'],чекаємо:{запитано:[],силует:true}},
};
(async()=>{const S=await L.start(html,{scale:2,file:true,fake:{[U('f@s1')]:png}});
 try{
  for(const [назва,k] of Object.entries(кейси)){
    const p=await S.open();p.setDefaultTimeout(20000);
    const до=(S.log.all||[]).length;
    await p.evaluate(()=>{window.__src=[];const d=Object.getOwnPropertyDescriptor(HTMLImageElement.prototype,'src');Object.defineProperty(HTMLImageElement.prototype,'src',{configurable:true,set(v){window.__src.push(v);d.set.call(this,v);},get(){return d.get.call(this)}});});
    await p.evaluate(([x,відх,неТі])=>{const КК=[{рука:'1',текст:'Повний образ.',неповний:'',речі:[x],мітки:[],знахідки:[],...(відх!==undefined?{відхилення_кадрів:відх}:{}),фото_не_ті:неТі||[]}];
      П={в:'ПОКАЗ-V1',картки:КК,збірка:'проба',каталог:'',профіль:'Проба',підпис:null,розклад:'',прогін:'p-1',токени:{},пул:null,модель:'-',палітра:{},випадок_рядок:'',випадок_шматки:'',сценарій:{ід:'x',назва:'x',час:null},ядро:{}};рендер();},[k.x,k.відх,k.не_ті]);
    await p.waitForTimeout(3500);
    const запитано=(S.log.all||[]).slice(до).filter(u=>u.includes('img.invalid'));
    const st=await p.evaluate(()=>({силуетів:[...document.querySelectorAll('#картки .арка')].filter(e=>!e.closest('#mirror-look-sides')).length,
      встановленоSrc:window.__src.filter(u=>u&&u.includes('img.invalid')),
      imgПоза_pair:[...document.querySelectorAll('#картки img')].filter(i=>!i.closest('#mirror-look-sides')).map(i=>i.getAttribute('src')),
      imgУ_pair:[...document.querySelectorAll('#mirror-look-sides img')].map(i=>i.getAttribute('src')),тьм:[...document.querySelectorAll('#картки .тьм')].map(x=>x.textContent)}));
    await p.screenshot({path:`${shots}/4687-${назва.slice(0,1)}-${назва.slice(2).replace(/[ ,]/g,'_')}.png`});
    console.log(назва,JSON.stringify({запитано,...st}));
    const дозв=k.чекаємо.запитано;
    const колаж=[...new Set(st.встановленоSrc)];
    ok(`${назва}: КОЛАЖ/МІНІАТЮРА (змінений код) не запитують зайвого: src виставлено ${JSON.stringify(колаж)}, очікувалось ⊆ ${JSON.stringify(дозв)}`,колаж.every(u=>дозв.includes(u))&&(дозв.length===0?колаж.length===0:true));
    ok(`${назва}: силует на місці речі в колажі/мініатюрі (${st.силуетів}), img поза «парою»: ${JSON.stringify(st.imgПоза_pair)}`,st.силуетів>=1&&st.imgПоза_pair.every(s=>!s));
    const зпари=запитано.filter(u=>!колаж.includes(u));
    ok(`${назва}: УСЯ СТОРІНКА не запитує відхилений URL — запитано ${JSON.stringify(запитано)}; із них поза змінених компонентів (компонент «пара» #mirror-look-sides: img ${JSON.stringify(st.imgУ_pair)}): ${JSON.stringify(зпари)}`,запитано.every(u=>дозв.includes(u)));
    ok('без винятків: '+JSON.stringify(p.errs),p.errs.length===0);
    await p.close();
  }
  fs.writeFileSync(shots+'/../4687-результати.txt',out.join('\n')+'\nЗАПИТАНІ URL (усі): '+JSON.stringify([...new Set(S.log.all)])+'\nabort: '+JSON.stringify([...new Set(S.log.blocked)])+'\n');
 }catch(e){console.error('ВИНЯТОК',e)}finally{await S.br.close();}})();
