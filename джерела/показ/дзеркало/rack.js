"use strict";
(() => {
  const R=window.MirrorRoom,M=window.MirrorMaterial,I=window.MirrorIndex;
  const e=R.escape,b=R.button,ik=R.ik,$=id=>document.getElementById(id);
  const catalogOptions={top:'Верх',bottom:'Низ',dress:'Сукня',coat:'Верхній шар',shoes:'Взуття',bag:'Сумка',jewels:'Прикраси',other:'Інше'};
  const makeId=()=>globalThis.crypto?.randomUUID?.()||Date.now().toString(36)+Math.random().toString(36).slice(2);
  const safeLink=s=>{try{const u=new URL(s);return ['https:','http:'].includes(u.protocol)?u.href:'';}catch{return '';}};
  const imageUrl=s=>typeof s==='string'&&s.startsWith('data:image/jpeg;base64,')?s:safeLink(s);
  const cash=p=>typeof p?.price==='number'&&Number.isFinite(p.price)?R.money(p.price):'Ціну не вказано';
  const blank=()=>({version:1,closet:[],saved:[],outfit:{name:'',side:0,sets:[[],[]],id:''},compare:{left:null,right:null,decision:''}});
  const key=p=>'дзеркало:речі:1:'+p;
  const cache=new Map(),handles=new Map(),products=new Map();
  let picker='',query='',offset=0,seq=0,shown=[],total=0,selectedRecord=null,chosenSide=null,actionSeq=0;
  const future=(key,name)=>b('pair-future',name+' · у планах','',key,'studio-text pair-planned');
  async function load(p){
    if(!p)return blank();
    if(!cache.has(p)&&!handles.has(p)){
      const promise=читатиКв(key(p)).then(v=>{if(!cache.has(p))cache.set(p,v?.version===1?v:blank());return cache.get(p);}).finally(()=>handles.delete(p));
      handles.set(p,promise);
    }
    return cache.get(p)||handles.get(p);
  }
  async function change(edit,p){
    if(!p)throw Error('Профіль ще завантажується.');
    const db=await дб();
    return new Promise((ok,no)=>{
      const tx=db.transaction('кв','readwrite'),store=tx.objectStore('кв'),get=store.get(key(p));let updated;
      get.onsuccess=()=>{try{updated=get.result?.version===1?get.result:blank();edit(updated);store.put(updated,key(p));}catch(err){tx.abort();no(err);}};
      tx.oncomplete=()=>{cache.set(p,updated);ok(updated);};tx.onerror=()=>no(tx.error);tx.onabort=()=>no(tx.error||Error('Не вдалося зберегти.'));
    });
  }
  const scope=()=>({profile:R.activeProfile(),screen:R.currentExtra()});
  const current=ctx=>!!ctx.profile&&ctx.profile===R.activeProfile()&&ctx.screen===R.currentExtra();
  function once(action){return async (...args)=>{const ctx=scope();try{return await action(...args);}catch(err){if(current(ctx))R.dialog('Не вдалося зберегти','<p>'+e(err?.message||'Перевір доступ до пам’яті браузера.')+'</p>');}};}
  const set=(name,fn)=>R.register(name,once(fn));
  function amount(items,d){return items.reduce((s,p)=>{if(d.closet.some(x=>x.id===p.id))return s;if(typeof p.price==='number')s.sum+=p.price;else s.unknown++;return s;},{sum:0,unknown:0});}
  function receipt(items,d){const a=amount(items,d);return R.money(a.sum)+(a.unknown?' · без ціни '+a.unknown:'');}
  function photo(p){const src=imageUrl(p?.image);return '<span class="rack-photo">'+(src?'<img alt="'+e(p.name)+'" src="'+e(src)+'" loading="lazy" referrerpolicy="no-referrer">':'')+'<span class="rack-noimage">'+ik('вішак')+'<small>Фото відсутнє</small></span></span>';}
  document.addEventListener('error',ev=>{const im=ev.target;if(im?.tagName==='IMG'&&im.closest('.rack-photo'))im.hidden=true;},true);
  function slim(p){return {id:p.id,name:p.name,price:p.price??null,shop:p.shop||'',slot:p.slot||'other',slotLabel:p.slotLabel||'',color:R.tone(p.color),hue:p.hue||'',image:p.image||'',url:safeLink(p.url),material:p.material||''};}
  async function lookup(id,profile){const d=await load(profile);
    return d.closet.find(p=>p.id===id)||d.outfit.sets.flat().find(p=>p.id===id)||d.saved.flatMap(r=>r.things).find(p=>p.id===id)||[d.compare.left,d.compare.right].find(p=>p?.id===id)||products.get(id)||await I.get(id);}
  function tile(p,action='rack-item',own=false){return '<button type="button" class="rack-tile" data-ux="'+action+'" data-value="'+e(p.id)+'">'+photo(p)+'<small>'+e(p.shop||p.slotLabel||'Своя річ')+'</small><b>'+e(p.name)+'</b><span>'+e(own?'У гардеробі':cash(p))+'</span></button>';}
  function catalogTitle(){return ({left:'Річ із крамниці',right:'Друга річ',set:'Річ до образу',anchor:'Під одну річ'})[picker]||'Каталог';}
  function pickerBack(){return picker==='left'||picker==='right'?'buy':picker==='set'?'compose':picker==='anchor'?'anchor':'face';}
  function searchPage(purpose='',keep=false){
    if(!keep){picker=purpose;query='';offset=0;shown=[];}
    R.showExtra('catalog',catalogTitle(),'<form id="rack-search" class="rack-search">'+ik('пошук')+'<label for="rack-query" class="rack-sr">Пошук речі</label><input type="search" enterkeyhint="search" id="rack-query" value="'+e(query)+'" placeholder="Назва, барва, ціна"><button class="studio-primary" type="submit">Знайти</button></form><div id="rack-results" aria-live="polite"></div>',b(pickerBack(),'Назад','назад'));
    find(false);
  }
  async function find(more){
    const ticket=++seq,div=$('rack-results');if(!div)return;
    if(!more){offset=0;shown=[];div.textContent='Шукаю…';}
    try{
      const result=await I.search(query,{offset:more?offset:0,limit:18});
      if(ticket!==seq||!div.isConnected)return;
      const fresh=result.results.map(slim);fresh.forEach(p=>products.set(p.id,p));shown=more?[...shown,...fresh]:fresh;total=result.total;offset=shown.length;
      if(!shown.length){div.innerHTML='<p>Нічого не знайдено.</p>';return;}
      let grid=div.querySelector('.rack-grid');
      if(!more||!grid){div.innerHTML='<p class="rack-count">'+new Intl.NumberFormat('uk-UA').format(total)+' · ціни каталогу</p><div class="rack-grid"></div>';grid=div.querySelector('.rack-grid');}
      grid.insertAdjacentHTML('beforeend',fresh.map(p=>tile(p)).join(''));div.querySelector('[data-ux="rack-more"]')?.remove();if(offset<total)div.insertAdjacentHTML('beforeend',b('rack-more','Ще речі','плюс'));
    }catch{if(ticket===seq&&div.isConnected)div.innerHTML='<p>Каталог недоступний.</p>'+b('rack-retry','Повторити','оберт');}
  }
  document.addEventListener('submit',ev=>{if(ev.target.id==='rack-search'){ev.preventDefault();query=$('rack-query').value.trim();find(false);}});
  async function item(id){
    const ctx=scope(),p=await lookup(id,ctx.profile),d=await load(ctx.profile);if(!p||!current(ctx))return;
    const own=d.closet.some(x=>x.id===id);
    let primary=picker==='left'||picker==='right'?b('rack-use','Порівняти','',id,'studio-primary'):picker==='set'?b('rack-add','Додати до образу','',id,'studio-primary'):picker==='anchor'?b('rack-anchor','Зібрати під цю річ','',id,'studio-primary'):b('rack-add','Додати до образу','',id,'studio-primary');
    R.dialog(p.name,'<div class="rack-detail">'+photo(p)+'<div><b>'+e(own?'Своя річ':cash(p))+'</b><small>'+e(p.shop||p.slotLabel)+'</small>'+(p.hue?'<p>'+e(p.hue)+'</p>':'')+(p.material?'<p>'+e(p.material)+'</p>':'')+(p.url?'<a class="studio-link" target="_blank" rel="noopener noreferrer" href="'+e(p.url)+'">До крамниці</a>':'')+'</div></div><div class="rack-actions">'+primary+
      (!['left','right','anchor','set'].includes(picker)?b('rack-candidate','Порівняти','',id):'')+
      (own?b('rack-remove-own','Прибрати з гардероба','',id):b('rack-own','Маю цю річ','',id))+'</div>');
  }
  function toolsLine(list){return '<div class="rack-actions">'+list.join('')+'</div>';}
  async function closet(purpose='',ctx=scope()){
    if(!current(ctx))return;
    const ticket=++actionSeq,d=await load(ctx.profile);if(ticket!==actionSeq||!current(ctx))return;
    picker=purpose;
    const head=purpose==='right'?'З мого гардероба':purpose==='anchor'?'Під мою річ':'Мої речі';
    const content=toolsLine([b('rack-new-own','Додати свою річ','плюс','','studio-primary'),b('rack-scan',purpose==='anchor'?'Знайти в каталозі':'Каталог','пошук')])+
      (d.closet.length?'<div class="rack-grid">'+d.closet.map(it=>tile(it,'rack-item',true)).join('')+'</div>':'<p class="rack-empty">У гардеробі ще немає речей.</p>')+
      (purpose==='anchor'?b('take-photo','Додати фото до розмови','камера'):'')+
      toolsLine([future('wardrobe','Виділити речі з фото'),future('closet-search','Пошук у моїх речах')])+
      (previousCloset(d)?b('rack-import','Перенести свої речі з попередньої версії','вішак'):'');
    R.showExtra('wardrobe',head,content,b(purpose==='right'?'buy':purpose==='set'?'compose':'face','Назад','назад'));
  }
  function previousCloset(d){
    let old;
    try{old=JSON.parse(localStorage.getItem('liusterko-mirror-3'));}catch{return null;}
    if(!old?.pid||d.imports?.includes(old.pid))return null;
    const items=(old.closet||[]).filter(it=>it.pid===old.pid&&it.id&&!it.ref&&it.name&&(!it.photo||it.photo.startsWith('photo-')));
    return items.length?{pid:old.pid,items}:null;
  }
  async function importOwn(){
    const ctx=scope(),profile=ctx.profile,old=previousCloset(await load(profile));
    if(!old||!current(ctx))return;
    const use=picker;
    let db;
    if(old.items.some(it=>it.photo)){
      db=await new Promise((resolve,reject)=>{
        const req=indexedDB.open('liusterko-local-photos');
        req.onsuccess=()=>resolve(req.result);req.onerror=()=>reject(req.error);
      });
    }
    let items;
    try{
      items=await Promise.all(old.items.map(async it=>{
        let image='';
        if(it.photo&&db?.objectStoreNames.contains('images'))image=await new Promise((resolve,reject)=>{
          const req=db.transaction('images').objectStore('images').get(it.photo);
          req.onsuccess=()=>resolve(imageUrl(req.result));req.onerror=()=>reject(req.error);
        });
        return {id:'legacy-'+it.id,name:String(it.name),image,shop:'',price:null,slot:it.slot||'other',slotLabel:catalogOptions[it.slot]||'',color:R.tone(it.color),hue:it.hue||'',url:'',material:''};
      }));
    }finally{db?.close();}
    await change(d=>{
      d.imports ||= [];
      if(d.imports.includes(old.pid))return;
      for(const it of items)if(!d.closet.some(existing=>existing.id===it.id))d.closet.push(it);
      d.imports.push(old.pid);
    },profile);
    if(current(ctx))await closet(use,ctx);
  }
  function ownForm(){R.dialog('Своя річ','<form id="rack-own-form"><label>Фото<input type="file" name="image" accept="image/*"></label><div class="rack-sampler" hidden><canvas aria-label="Вибрати відтінок на фото"></canvas><small>Торкнися фото, щоб узяти відтінок.</small></div><label>Назва<input name="name" required maxlength="110" autocomplete="off"></label><label>Вид речі<select name="slot">'+Object.entries(catalogOptions).map(([k,n])=>'<option value="'+k+'">'+n+'</option>').join('')+'</select></label><div class="rack-fields"><label>Барва<input name="hue" maxlength="45"></label><label>Відтінок<input type="color" name="swatch" value="#796e60"><input type="hidden" name="color" value=""></label></div><button class="studio-primary" type="submit">Додати</button></form>');}
  document.addEventListener('input',ev=>{
    if(ev.target.matches('#rack-own-form [name=swatch]'))ev.target.form.elements.color.value=ev.target.value;
  });
  document.addEventListener('change',async ev=>{
    const input=ev.target;if(!input.matches('#rack-own-form [name=image]'))return;
    const box=input.form.querySelector('.rack-sampler'),file=input.files[0];box.hidden=true;
    if(!file||!file.type.startsWith('image/')||file.size>18*1024*1024)return;
    const url=URL.createObjectURL(file);
    try{
      const img=new Image();img.src=url;await img.decode();if(input.files[0]!==file||!box.isConnected)return;
      const c=box.querySelector('canvas'),scale=Math.min(1,650/Math.max(img.width,img.height));
      c.width=Math.max(1,Math.round(img.width*scale));c.height=Math.max(1,Math.round(img.height*scale));
      c.getContext('2d',{willReadFrequently:true}).drawImage(img,0,0,c.width,c.height);box.hidden=false;
    }catch{box.hidden=true;}finally{URL.revokeObjectURL(url);}
  });
  document.addEventListener('click',ev=>{
    const c=ev.target;if(!c.matches('.rack-sampler canvas'))return;
    const rect=c.getBoundingClientRect(),x=Math.min(c.width-1,Math.max(0,Math.floor((ev.clientX-rect.left)*c.width/rect.width)));
    const y=Math.min(c.height-1,Math.max(0,Math.floor((ev.clientY-rect.top)*c.height/rect.height)));
    const pixel=c.getContext('2d').getImageData(x,y,1,1).data;
    const value='#'+Array.from(pixel.slice(0,3),n=>n.toString(16).padStart(2,'0')).join('');
    const f=c.closest('form');f.elements.swatch.value=f.elements.color.value=value;
  });
  async function localPhoto(file){
    if(!file?.size)return '';if(file.size>18*1024*1024||!file.type.startsWith('image/'))throw Error('Обери зображення до 18 МБ.');
    const ref=URL.createObjectURL(file);try{const img=new Image();img.src=ref;await img.decode();const scale=Math.min(1,1080/Math.max(img.naturalWidth,img.naturalHeight)),c=document.createElement('canvas');
      c.width=Math.max(1,Math.round(img.naturalWidth*scale));c.height=Math.max(1,Math.round(img.naturalHeight*scale));const ctx=c.getContext('2d');ctx.fillStyle='white';ctx.fillRect(0,0,c.width,c.height);ctx.drawImage(img,0,0,c.width,c.height);return c.toDataURL('image/jpeg',.83);
    }finally{URL.revokeObjectURL(ref);}
  }
  async function addToSet(id,ctx=scope()){
    if(!ctx.profile)return;
    const {side,id:draft}= (await load(ctx.profile)).outfit;
    const p=await lookup(id,ctx.profile);if(!p)return;
    await change(d=>{if(d.outfit.id!==draft||d.outfit.side!==side)return;const list=d.outfit.sets[side];if(!list.some(x=>x.id===id))list.push(slim(p));},ctx.profile);
    if(current(ctx)){R.close();await compose(ctx);}
  }
  async function compareUse(id,side,ctx){const p=await lookup(id,ctx.profile);if(!p||!current(ctx))return;
    await change(d=>{d.compare[side]=slim(p);d.compare.decision='';},ctx.profile);if(current(ctx))await buy(ctx);}
  function compareHalf(p,side,owned=false){
    const options=side==='left'?b('rack-left',p?'Змінити':'Обрати в каталозі','пошук'):b('rack-right',p?'Змінити':'Обрати річ','плюс');
    return '<section><h2>'+(side==='left'?'У крамниці':'Для порівняння')+'</h2>'+(p?photo(p)+'<h3>'+e(p.name)+'</h3><small>'+e(p.shop||'Моя річ')+'</small><b>'+e(owned?'Є в гардеробі':cash(p))+'</b>':'<div class="rack-outline">'+ik(side==='left'?'сумка':'вішак',34)+'</div>')+options+'</section>';
  }
  async function buy(ctx=scope()){
    const d=await load(ctx.profile);if(!current(ctx))return;picker='';const {left,right,decision}=d.compare;
    const own=right&&d.closet.some(x=>x.id===right.id);let note='';
    if(left&&right){
      if(own&&typeof left.price==='number')note='Своя річ заощадить '+cash(left)+'.';
      else if(typeof left.price==='number'&&typeof right.price==='number'){const diff=left.price-right.price;note=diff>0?'Перша дорожча на '+R.money(diff)+'.':diff<0?'Перша дешевша на '+R.money(-diff)+'.':'Ціна однакова.';}
    }
    const intro='<div class="rack-pair"'+(left&&right?' data-relation="чи"':'')+'>'+compareHalf(left,'left')+compareHalf(right,'right',own)+'</div>';
    let info='';
    if(left&&right)info='<div class="rack-summary">'+(note?'<b>'+e(note)+'</b>':'')+(left.slotLabel&&right.slotLabel?'<span>'+e(left.slotLabel+' · '+right.slotLabel)+'</span>':'')+'</div>';
    if(left)info+=toolsLine([b('rack-decide',decision==='Беру'?'У гардеробі':'Беру','так','Беру','studio-primary'),b('rack-decide',decision==='Відкласти'?'Відкладено':'Відкласти','зберегти','Відкласти'),b('rack-advice','Спитати стилістку','розмова')]);
    R.showExtra('buy','Купити чи ні?',intro+info+future('photo-buy','Порівняння двох фото'),'',left?['Спитати про покупку','Чи варто купити «'+left.name+'»'+(right?', якщо є «'+right.name+'»':'')+'?']:null);
  }
  function compareOptions(){R.dialog('З чим порівняти?','<div class="studio-menu">'+b('rack-compare-own','З моєю річчю','вішак')+b('rack-compare-store','З річчю з каталогу','пошук')+'</div>');}
  function composePart(list,side,d){
    const items=list.map((p,i)=>'<button type="button" class="'+(i===0?'pair-variant-lead':'rack-mini')+'" data-ux="rack-edit" data-value="'+side+'|'+e(p.id)+'">'+photo(p)+'<span><b>'+e(p.name)+'</b><small>'+e(d.closet.some(x=>x.id===p.id)?'Своя річ':cash(p))+'</small></span></button>').join('');
    const choose=list.length?'<div class="rack-side-total">'+e(receipt(list,d))+'</div>'+b('rack-choose','Обрати цей','',side,'studio-primary'):'';
    return '<section><div class="rack-side-label"><h2>Варіант '+(side+1)+'</h2>'+M.seal(list.map(v=>v.color),false,37)+'</div>'+(items||'<div class="rack-outline">'+ik('вішак')+'</div>')+
      b('rack-add-side','Додати річ','плюс',side)+choose+'</section>';
  }
  async function compose(ctx=scope()){
    const d=await load(ctx.profile);if(!current(ctx))return;
    picker='';replace=null;chosenSide=null;const outfit=d.outfit;
    const grid='<div class="rack-pair rack-sets"'+(outfit.sets.every(items=>items.length)?' data-relation="чи"':'')+'>'+outfit.sets.map((list,i)=>composePart(list,i,d)).join('')+'</div>';
    const acts=outfit.sets.some(x=>x.length)?toolsLine([b('rack-save-outfit','Зберегти образ','зберегти','','studio-primary')]):'';
    R.showExtra('compose',outfit.name||'Мій комплект',grid+acts+future('two','Два образи від стилістки'),b('library','Мої образи','збірка'));
  }
  function details(items,d,side){
    return items.map(p=>{
      const own=d.closet.some(q=>q.id===p.id),v=side+'|'+p.id;
      const shop=p.url?'<a class="studio-link" href="'+e(safeLink(p.url))+'" target="_blank" rel="noopener noreferrer">До крамниці</a>':'';
      return '<details class="pair-item-details"><summary>'+e(p.name)+'</summary><div class="rack-detail">'+photo(p)+'<div><b>'+e(own?'Моя річ':cash(p))+'</b><small>'+e(p.shop||p.slotLabel)+'</small><p>'+e([p.hue,p.material].filter(Boolean).join(' · '))+'</p>'+shop+'</div></div>'+
        (side!==null?toolsLine([b('rack-replace','Не ця · замінити','оберт',v),b('rack-own-instead','Маю свою','вішак',v)]):'')+'</details>';
    }).join('');
  }
  function shelf(items){return '<div class="pair-piece-shelf" aria-label="Речі образу">'+items.map(p=>'<button type="button" data-ux="rack-item" data-value="'+e(p.id)+'" aria-label="'+e(p.name)+'">'+photo(p)+'</button>').join('')+'</div>';}
  function reverse(record,d){
    return M.seal(record.things.map(t=>t.color),record.worn,76)+'<p><strong>'+e(record.name)+'</strong></p><small>'+e([record.occasion,record.date?new Intl.DateTimeFormat('uk-UA',{day:'numeric',month:'long',year:'numeric'}).format(record.date):''].filter(Boolean).join(' · '))+'</small><p>'+e(receipt(record.things,d))+' до придбання</p>'+(record.worn?'<strong>Вдягала</strong>':'');
  }
  async function chosen(side,ctx=scope()){
    if(![0,1].includes(side))return;
    const d=await load(ctx.profile);if(!current(ctx))return;const list=d.outfit.sets[side];if(!list.length)return compose(ctx);
    chosenSide=side;picker='';
    R.showExtra('manual-look','Варіант '+(side+1),R.pair.relation('<div class="pair-eyebrow">Ти</div>'+R.pair.person(),'','<div class="pair-eyebrow">Комплект</div>'+photo(list[0]),'pair-outfit')+
      shelf(list)+details(list,d,side)+toolsLine([b('rack-save-chosen','Зберегти образ','зберегти',side,'studio-primary'),b('compose','Обидва варіанти')]),b('compose','До варіантів','назад'),['Спитати про цей образ','Як носити разом '+list.map(p=>'«'+p.name+'»').join(', ')+'?']);
  }
  async function editPiece(value){
    const ctx=scope(),p=await lookup(value.slice(value.indexOf('|')+1),ctx.profile);if(!p||!current(ctx))return;
    const side=Number(value.slice(0,value.indexOf('|')));
    R.dialog(p.name,'<div class="rack-detail">'+photo(p)+'<div><b>'+e(cash(p))+'</b><p>'+e(p.shop)+'</p></div></div>'+toolsLine([b('rack-replace','Замінити','оберт',value,'studio-primary'),b('rack-drop','Прибрати з варіанта '+(side+1),'',value)]));
  }
  let replace=null;
  async function setPicker(side,old='',ctx=scope()){
    if(![0,1].includes(side)||!current(ctx))return;
    const back=chosenSide;await change(d=>{d.outfit.side=side;},ctx.profile);if(!current(ctx))return;
    replace=old?{side,id:old,profile:ctx.profile,back}:null;
    R.dialog('Річ до образу','<div class="studio-menu">'+b('rack-set-store','З каталогу','пошук')+b('rack-set-own','З гардероба','вішак')+'</div>');
  }
  async function chooseSetItem(id){
    const ctx=scope(),pending=replace;
    if(picker!=='set'||!pending)return addToSet(id,ctx);
    if(pending.profile!==ctx.profile)return;
    const p=await lookup(id,ctx.profile),d=await load(ctx.profile);if(!p||pending!==replace||!current(ctx))return;
    const old=d.outfit.sets[pending.side].find(it=>it.id===pending.id);if(!old)return compose();
    if(id===old.id||d.outfit.sets[pending.side].some(it=>it.id===id))throw Error('Ця річ уже є в цьому варіанті.');
    pending.candidate=slim(p);picker='';
    const half=(label,p)=>'<div class="pair-eyebrow">'+label+'</div>'+photo(p)+'<strong>'+e(p.name)+'</strong><small>'+e(d.closet.some(it=>it.id===p.id)?'Моя річ':cash(p))+'</small>';
    R.showExtra('replacement','Замінити річ?',R.pair.relation(half('Була',old),'→',half('Натомість',p),'pair-replacement')+
      toolsLine([b('rack-accept-replacement','Взяти цю','так','','studio-primary'),b('rack-keep-piece','Залишити попередню'),b('rack-another','Ще варіант','оберт')]),b('rack-keep-piece','Назад','назад'),['Спитати про заміну','Чи підійде «'+p.name+'» замість «'+old.name+'»?']);
  }
  async function finishReplacement(accept){
    const ctx=scope(),old=replace;if(!old||old.profile!==ctx.profile)return;
    if(accept){await change(d=>{
      const list=d.outfit.sets[old.side],idx=list.findIndex(it=>it.id===old.id);
      if(idx<0||!old.candidate||list.some(it=>it.id===old.candidate.id))throw Error('Комплект змінився. Обери заміну ще раз.');
      list[idx]=old.candidate;
    },old.profile);}
    if(!current(ctx)||old!==replace)return;
    replace=null;return [0,1].includes(old.back)?chosen(old.side,ctx):compose(ctx);
  }
  async function saveForm(selected){
    const ctx=scope(),d=await load(ctx.profile);if(!current(ctx))return;
    const s=d.outfit,side=[0,1].includes(selected)?selected:s.side;
    let choices=s.sets.map((z,i)=>z.length?'<label><input type="radio" name="side" value="'+i+'" '+(side===i||!s.sets[side].length?'checked':'')+'>Варіант '+(i+1)+'</label>':'').join('');
    R.dialog('Зберегти образ','<form id="rack-save-form"><label>Назва<input name="name" maxlength="90" value="'+e(s.name)+'" required></label><div class="rack-which">'+choices+'</div><button class="studio-primary">Зберегти</button></form>');
  }
  function library(){
    const p=R.activeProfile(),el=$('mirror-saved-manual');if(!p||!el)return;
    load(p).then(d=>{
      if(p!==R.activeProfile()||!el.isConnected)return;
      const nativeCount=БІБЛІОТЕКА_П.плитки.length,emptyShelf=БІБЛІОТЕКА_П.стан==='порожньо'&&!nativeCount&&!d.saved.length;
      const signature=JSON.stringify([p,M.get(),nativeCount,emptyShelf,d.saved.map(r=>[r.id,r.name,r.worn,r.things.map(t=>[t.id,t.color]),receipt(r.things,d)])]);
      if(el.dataset.revision!==signature){
        const cards=d.saved.map(v=>'<button type="button" class="rack-saved-card" data-ux="rack-saved" data-value="'+e(v.id)+'">'+M.seal(v.things.map(t=>t.color),v.worn,77)+'<span><b>'+e(v.name)+'</b><small>'+e(v.worn?'Вдягала':receipt(v.things,d))+'</small></span></button>');
        const start=emptyShelf?'<button type="button" class="rack-first-look" data-ux="compose"><span class="rack-first-print" aria-hidden="true">'+Hand.art(M.get(),'welcome')+'</span><span>Зібрати перший образ '+ik('рух',18)+'</span></button>':toolsLine([b('compose','Зібрати вручну','плюс','','studio-primary')]);
        el.innerHTML=start+toolsLine([b('cases','Мої нагоди','зберегти'),b('closet','Мої речі','вішак')])+(cards.length?'<div class="rack-saved">'+cards.join('')+'</div>':'');
        el.dataset.revision=signature;
      }
      const empty=$('біб-стан');
      if(empty)empty.hidden=БІБЛІОТЕКА_П.стан==='порожньо'&&(emptyShelf||d.saved.length>0);
    }).catch(()=>{el.textContent='Пам’ять браузера недоступна.';});
  }
  let editConfirmation=null;
  async function editSaved(id,ctx,expectedDraft){
    if(!ctx.profile)return;
    if(expectedDraft===undefined){
      // Інша вкладка може змінити чернетку після того, як load() заповнив кеш.
      const state=await читатиКв(key(ctx.profile));
      const outfit=state?.version===1?state.outfit:blank().outfit;
      expectedDraft=JSON.stringify(outfit);
      if(outfit.sets.some(list=>list.length)){
        if(!current(ctx))return;
        const token=makeId();
        editConfirmation={id,ctx,token,expectedDraft};
        R.dialog('Замінити чернетку комплекту?',toolsLine([b('rack-confirm-edit','Замінити','',token,'studio-primary'),b('close-sheet','Залишити чернетку')]));
        return;
      }
    }
    await change(d=>{
      const record=d.saved.find(v=>v.id===id);
      if(!record)return;
      if(JSON.stringify(d.outfit)!==expectedDraft)throw Error('Чернетка змінилася. Відкрий редагування ще раз, щоб підтвердити заміну.');
      d.outfit={name:record.name,id:record.id,editSide:0,side:0,sets:[record.things.map(thing=>({...thing})),[]]};
    },ctx.profile);
    if(current(ctx))await compose(ctx);
  }
  async function saved(id,ctx=scope()){
    const d=await load(ctx.profile);if(!current(ctx))return;
    const v=d.saved.find(r=>r.id===id);if(!v)return;selectedRecord=id;picker='';
    const first=v.things.find(t=>imageUrl(t.image))||v.things[0];
    R.showExtra('saved',v.name,R.pair.relation('<div class="pair-eyebrow">Образ</div>'+(first?photo(first):''),'','<div class="pair-eyebrow">Зворот</div>'+reverse(v,d),'pair-record')+
      shelf(v.things)+details(v.things,d,null)+toolsLine([b('rack-worn',v.worn?'Зняти позначку «Вдягала»':'Позначити «Вдягала»','так',v.id),b('rack-edit-saved','Редагувати','',v.id)]),b('library','Мої образи','назад'),['Спитати про збережений образ','Що можна змінити в образі «'+v.name+'» з речами '+v.things.map(p=>'«'+p.name+'»').join(', ')+'?']);
  }
  const registrations={
    catalog:()=>searchPage(),anchor:()=>closet('anchor'),buy:()=>buy(),closet:()=>closet(),compose:()=>compose(),
    'rack-scan':()=>searchPage(picker||''),'rack-more':()=>find(true),'rack-retry':()=>find(false),'rack-item':item,'rack-new-own':ownForm,'rack-import':importOwn,
    'rack-use':id=>compareUse(id,picker==='right'?'right':'left',scope()),
    'rack-candidate':id=>compareUse(id,'left',scope()),
    'rack-left':()=>searchPage('left'),'rack-right':compareOptions,'rack-compare-own':()=>closet('right'),'rack-compare-store':()=>searchPage('right'),
    'rack-decide':async v=>{const ctx=scope();await change(d=>{d.compare.decision=v;const p=d.compare.left;if(p&&v==='Беру'&&!d.closet.some(x=>x.id===p.id))d.closet.unshift(p);},ctx.profile);if(current(ctx))await buy(ctx);},
    'rack-advice':async()=>{const ctx=scope(),{left,right}= (await load(ctx.profile)).compare;if(current(ctx)&&left)R.startWords('Чи варто купити «'+left.name+'»'+(typeof left.price==='number'?' за '+cash(left):'')+(right?', якщо маю на вибір «'+right.name+'»':'')+'?');},
    'rack-own':async id=>{const ctx=scope(),use=picker;if(!ctx.profile)return;
      const p=await lookup(id,ctx.profile);if(!p)return;
      await change(d=>{if(!d.closet.some(q=>q.id===id))d.closet.unshift(slim(p));},ctx.profile);
      if(!current(ctx))return;R.close();if(ctx.screen==='wardrobe')await closet(use,ctx);else R.say('Річ у гардеробі.');},
    'rack-remove-own':id=>R.dialog('Прибрати річ із гардероба?',toolsLine([b('rack-delete-own','Прибрати','',id,'studio-primary'),b('close-sheet','Залишити')])),
    'rack-delete-own':async id=>{const ctx=scope(),use=picker;await change(d=>{d.closet=d.closet.filter(q=>q.id!==id);},ctx.profile);if(current(ctx))await closet(use,ctx);},
    'rack-anchor':async id=>{const ctx=scope(),p=await lookup(id,ctx.profile);if(!p||!current(ctx))return;
      await change(d=>{d.outfit.sets.forEach(list=>{if(!list.some(q=>q.id===id))list.unshift(slim(p));});},ctx.profile);
      if(current(ctx))await compose(ctx);},
    'rack-add-side':side=>setPicker(Number(side)), 'rack-set-store':()=>searchPage('set'),'rack-set-own':()=>closet('set'),'rack-add':chooseSetItem,'rack-edit':editPiece,
    'rack-choose':v=>chosen(Number(v)),'rack-save-chosen':v=>saveForm(Number(v)),
    'rack-another':()=>replace&&setPicker(replace.side,replace.id),'rack-accept-replacement':()=>finishReplacement(true),'rack-keep-piece':()=>finishReplacement(false),
    'rack-own-instead':async v=>{const ctx=scope(),i=v.indexOf('|');await setPicker(Number(v.slice(0,i)),v.slice(i+1),ctx);if(current(ctx))return closet('set',ctx);},
    'rack-replace':v=>{const j=v.indexOf('|');return setPicker(Number(v.slice(0,j)),v.slice(j+1));},
    'rack-drop':async v=>{const ctx=scope(),j=v.indexOf('|'),side=Number(v.slice(0,j)),id=v.slice(j+1);await change(d=>{d.outfit.sets[side]=d.outfit.sets[side].filter(p=>p.id!==id);},ctx.profile);if(current(ctx))await compose(ctx);},
    'rack-save-outfit':saveForm,'rack-saved':id=>saved(id),
    'rack-worn':async id=>{const ctx=scope();await change(d=>{const r=d.saved.find(v=>v.id===id);if(r)r.worn=!r.worn;},ctx.profile);if(current(ctx))await saved(id,ctx);},
    'rack-edit-saved':id=>{editConfirmation=null;return editSaved(id,scope());},
    'rack-confirm-edit':token=>{const pending=editConfirmation;
      if(!pending||pending.token!==token||!current(pending.ctx))return;
      editConfirmation=null;return editSaved(pending.id,pending.ctx,pending.expectedDraft);}
  };
  Object.entries(registrations).forEach(([name,fn])=>set(name,fn));
  document.addEventListener('submit',ev=>{
    if(!['rack-own-form','rack-save-form'].includes(ev.target.id))return;ev.preventDefault();const form=ev.target,fd=new FormData(form),ctx=scope(),pid=ctx.profile,use=picker,occasion=R.pair.occasionLabel();
    const submit=form.querySelector('button[type=submit],button:not([type])');if(submit)submit.disabled=true;
    once(async()=>{
      if(form.id==='rack-own-form'){const name=String(fd.get('name')).trim();if(!name)throw Error('Введи назву.');const image=await localPhoto(fd.get('image'));if(!current(ctx))return;
        const p={id:'own-'+makeId(),name,image,shop:'',price:null,slot:fd.get('slot'),slotLabel:catalogOptions[fd.get('slot')],color:fd.get('color'),hue:String(fd.get('hue')||'').trim(),url:'',material:''};
        await change(d=>d.closet.unshift(p),pid);if(!current(ctx))return;await closet(use,ctx);return;}
      const name=String(fd.get('name')).trim(),side=Number(fd.get('side'));if(!name||![0,1].includes(side))return;
      await change(d=>{const things=d.outfit.sets[side];if(!things.length)throw Error('Спершу додай річ до образу.');
        const old=(d.outfit.editSide??0)===side?d.saved.find(v=>v.id===d.outfit.id):null,entry={id:old?.id||makeId(),name,things:[...things],worn:old?.worn||false,date:old?.date||Date.now(),occasion:old?.occasion||occasion};if(old)Object.assign(old,entry);else d.saved.unshift(entry);
        d.outfit.sets[side]=[];d.outfit.side=1-side;
        if(old||!d.outfit.sets[1-side].length){d.outfit.name='';d.outfit.id='';}
      },pid);
      if(current(ctx)){R.route('бібліотека');library();}
    })().finally(()=>{if(submit?.isConnected)submit.disabled=false;});
  });
  function repaintArtwork(){if(R.currentExtra()==='compose')compose();else if(R.currentExtra()==='manual-look')chosen(chosenSide);else if(R.currentExtra()==='saved'&&selectedRecord)saved(selectedRecord);else if(режимЕкрана()==='бібліотека')library();}
  const nativeWorn=id=>!!cache.get(R.activeProfile())?.wornCards?.includes(id);
  async function toggleNativeWorn(id){
    const profile=R.activeProfile();
    if(!id||typeof П==='undefined'||!П?.картки?.some((_,i)=>ключЗаписуОбразуП(П)+'#'+i===id))return;
    await change(d=>{const ids=new Set(d.wornCards||[]);if(ids.has(id))ids.delete(id);else ids.add(id);d.wornCards=[...ids];},profile);
  }
  async function substituteNative(value,accepted=false){
    const [pos,j]=value.split('|').map(Number),card=typeof П!=='undefined'&&П?.картки?.[pos],target=card?.речі?.[j];
    if(!target||режимЕкрана()!=='образи')return;
    const ctx=scope(),profile=ctx.profile,d=await load(profile);if(!current(ctx))return;
    if(!accepted&&d.outfit.sets[0].length){
      R.dialog('Замінити перший ручний варіант?',toolsLine([b('rack-copy-native','Перенести цей образ','',value,'studio-primary'),b('close-sheet','Залишити чернетку')]));return;
    }
    await change(state=>{state.outfit.id='';state.outfit.name='';state.outfit.side=0;
      state.outfit.sets[0]=card.речі.map((p,i)=>slim({id:p.id||'piece-'+i,name:p.назва||'Річ',price:p.ціна,shop:p.id?.includes('@')?крамниця(p.id):'',slot:p.слот,image:card.фото_не_ті?.includes(p.id)?'':p.фото,color:p.hex,url:p.урл}));},profile);
    if(!current(ctx))return;
    chosenSide=0;await setPicker(0,target.id||'piece-'+j,ctx);if(current(ctx))await closet('set',ctx);
  }
  set('rack-copy-native',v=>substituteNative(v,true));
  window.Rack={library,repaintArtwork,nativeWorn,toggleNativeWorn:once(toggleNativeWorn),substituteNative:once(substituteNative)};

})();
