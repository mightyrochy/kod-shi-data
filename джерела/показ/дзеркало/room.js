"use strict";
(() => {
  const node = id => document.getElementById(id);
  const M = window.MirrorMaterial;
  const mobile = window.matchMedia?.("(max-width: 879px)") || {matches:false,addEventListener(){}};
  const ik = (id, size=22) => '<svg class="мі-ік" width="'+size+'" height="'+size+'" aria-hidden="true"><use href="#мі-'+id+'"/></svg>';
  const escape = text => String(text ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const button = (action, title, symbol='', value='', cls='studio-text') => '<button type="button" class="'+cls+'" data-ux="'+action+'" data-value="'+escape(value)+'">'+(symbol?ik(symbol):'')+'<span>'+escape(title)+'</span></button>';
  const money = amount => new Intl.NumberFormat('uk-UA',{maximumFractionDigits:2}).format(amount)+' ₴';
  const tone = v => typeof v === 'string' && /^#[\da-f]{3}([\da-f]{3})?$/i.test(v) ? v : '';
  const sheet = node('mirror-sheet'), work=node('mirror-work');
  let originator=null, openDrawer=false, extra='', pageMode='', headerKey='', scheduled=false, lastPhase='', gesture=null;
  const pigments={kahlia:'#25825e',vytynanka:'#aa233e',klyny:'#597876'};
  const titles={'сценарій':'Нагода','профіль':'Мій профіль','старт':'Мій профіль','оцінка':'Оцінити вбрання','сценарії':'Мої нагоди','образи':'Образ','бібліотека':'Мої образи','палітра':'Барви','очікування':'Збираю образи'};
  const tools=[['assess','Оцінити вбрання','камера'],['anchor','Під мою річ','вішак'],['buy','Брати чи ні?','сумка'],['catalog','Знайти річ','пошук']];
  const actions=new Map();
  function move(item, parent){if(item&&parent&&item.parentNode!==parent)parent.append(item);}
  function activeProfile(){return АКТИВНИЙ;}
  function dialog(title, content){
    if(!sheet.open)originator=document.activeElement;
    node('mirror-sheet-title').textContent=title;node('mirror-sheet-content').innerHTML=content;
    if(!sheet.open)sheet.showModal();sheet.scrollTop=0;node('mirror-sheet-title').tabIndex=-1;node('mirror-sheet-title').focus({preventScroll:true});
  }
  function close(){if(sheet.open)sheet.close();}
  sheet.addEventListener('close',()=>{if(sheet.open)return;if(originator?.isConnected)originator.focus({preventScroll:true});originator=null;});
  sheet.addEventListener('click',ev=>{if(ev.target===sheet){const r=sheet.getBoundingClientRect();if(ev.clientX<r.left||ev.clientX>r.right||ev.clientY<r.top||ev.clientY>r.bottom)close();}});
  function say(text){node('mirror-chat-status').textContent=text;}
  function drawer(on,focus=false){
    openDrawer=!!on;document.documentElement.classList.toggle('mirror-drawer',openDrawer);
    node('mirror-grip').setAttribute('aria-expanded',String(openDrawer));
    if(mobile.matches)work.inert=openDrawer;else work.inert=false;
    if(on){node('mirror-thread').scrollTop=node('mirror-thread').scrollHeight;if(focus)node('чат-поле').focus({preventScroll:true});}
    if(!on&&mobile.matches&&node('mirror-thread').contains(document.activeElement))node('mirror-grip').focus({preventScroll:true});
    navState();
  }
  mobile.addEventListener('change',()=>{drawer(false);sync();});
  function available(){return !!Екран.стан.запущено;}
  function closeExtras(){if(extra){extra='';node('mirror-extras').replaceChildren();node('mirror-extras').hidden=true;delete document.documentElement.dataset.extra;headerKey='';}}
  function route(mode,focus=true){
    if(!available())return;
    if(режимЕкрана()==='очікування'&&зрізЗбиранняП().зайнято){say('Триває збирання образу.');return;}
    close();drawer(false);closeExtras();if(Екран.стан.аркуш)закритиАркуш();режим(mode);sync();if(focus){work.focus({preventScroll:true});scrollTo(0,0);}
  }
  function showExtra(key, title, content,controls=''){
    if(!available())return;
    if(Екран.стан.аркуш)закритиАркуш();close();drawer(false);
    const changed=extra!==key;extra=key;document.documentElement.dataset.extra=key;
    const el=node('mirror-extras');el.hidden=false;el.innerHTML=content;
    headerKey='';setHeading(title,controls||button('face','До нагоди','назад'));
    node('mirror-native').hidden=true;navState();if(changed){work.focus({preventScroll:true});scrollTo(0,0);}
  }
  function setHeading(title,controls){
    const signature=title+controls;if(headerKey===signature)return;headerKey=signature;
    node('mirror-heading').innerHTML='<h1>'+escape(title)+'</h1><div class="studio-heading-actions">'+controls+'</div>';
  }
  function navState(){
    const native=режимЕкрана();
    document.querySelectorAll('.studio-nav [data-ux]').forEach(b=>{
      const a=b.dataset.ux,chosen=a==='talk'?openDrawer:a==='library'?(!openDrawer&&(extra==='wardrobe'||extra==='saved'||native==='бібліотека'&&!extra)):!openDrawer&&(extra!=='wardrobe'&&extra!=='saved'&&(native!=='бібліотека'||!!extra));
      if(chosen)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');
    });
  }
  function renderPerson(){
    const button=node('mirror-person'),name=node('пф-ініціали')?.textContent.trim(),initial=name==='·'?'':name||'';
    const photo=node('ф-портрет')?.querySelector('img')?.getAttribute('src')||'';
    if(button._shownHand===M.get()&&button._shownName===initial&&button._shownPhoto===photo)return;
    button._shownHand=M.get();button._shownName=initial;button._shownPhoto=photo;
    button.innerHTML=Hand.voice(M.get(),photo)+(photo?'':'<span>'+(initial?escape(initial):ik('людина',17))+'</span>');
  }
  function themeButtons(){
    node('mirror-home').innerHTML=M.mast();
    node('mirror-hands').innerHTML=Object.entries(M.labels).map(([id,name])=>'<button type="button" data-ux="hand" data-value="'+id+'" aria-pressed="'+(id===M.get())+'">'+Hand.petal(id,pigments[id],21)+'<span>'+name+'</span></button>').join('');
    node('mirror-style').innerHTML=M.petal(pigments[M.get()],21)+'<span>'+M.label()+'</span>';node('mirror-style').setAttribute('aria-label','Оформлення · '+M.label());
    renderPerson();
    document.documentElement.dataset.hand=M.get();
    const meta=document.querySelector('meta[name=theme-color]');if(meta)meta.content=({kahlia:'#faf6ea',vytynanka:'#fbf5e9',klyny:'#efeee7'})[M.get()];
  }
  function showThemes(){dialog('Оформлення','<div class="studio-theme-list">'+Object.entries(M.labels).map(([id,name])=>'<button type="button" data-ux="hand" data-value="'+id+'" aria-pressed="'+(id===M.get())+'">'+Hand.petal(id,pigments[id],32)+'<b>'+name+'</b>'+(id===M.get()?ik('так'): '')+'</button>').join('')+'</div>');}
  function homeMarkup(){
    const byKey=new Map(ДОВІДНИК.нагоди.map(o=>[o.ключ,o.підпис]));
    const quick=[['щоденне','На щодень'],['робота','На роботу'],['побачення','Побачення'],['свято','На свято'],['прогулянка','Прогулянка']];
    return '<div class="studio-occasion-pair">'+quick.filter(([id])=>byKey.has(id)).map(([id,title],i)=>'<button type="button" data-ux="occasion" data-value="'+id+'"><span class="studio-occasion-mark">'+M.petal([pigments[M.get()],'#a98546','#a15b5c','#bc713c','#526f76'][i],21)+'</span><span>'+title+'</span></button>').join('')+button('all-occasions','Інша нагода','плюс','','studio-other')+'</div>'+
    '<h2 class="studio-section-title">Речі</h2><div class="studio-tools">'+[...tools,['compose','Зібрати вручну','люстерко'],['closet','Мої речі','збірка']].map(([key,name,icon])=>button(key,name,icon,'','studio-tool')).join('')+'</div>';
  }
  function hasCase(){return !!(єВипадокП()||ЧАТ_П.length||ПАСПОРТ_П||(Екран.стан.сценарій||{}).рукою);}
  function makeHome(){
    const el=document.createElement('div');el.id='mirror-occasions';node('е-випадок').prepend(el);
    const access=document.createElement('div');access.id='mirror-case-tools';access.className='studio-case-tools';access.innerHTML=button('compose','Зібрати вручну','вішак')+button('case-tools','Дії з речами','плюс');
    node('е-випадок').append(access);
  }
  function setupAssessment(){
    const area=node('е-оцінка'),photo=node('оц-фото').closest('.оц-поле'),question=node('оц-питання').closest('.оц-поле');
    const columns=document.createElement('div');columns.className='studio-assessment';photo.before(columns);columns.append(photo,question);
    const results=node('оц-речі');question.after(results);results.classList.add('studio-assessed-items');
    const label=photo.querySelector('.поле-назва');if(label)label.textContent='Твоє фото';
    const head=question.querySelector('label');if(head)head.textContent='Що оцінити?';
    const weather=node('оц-нагода').closest('.оц-поле'),details=document.createElement('details');details.className='studio-weather';details.innerHTML='<summary>Нагода й погода</summary>';weather.before(details);details.append(weather);weather.querySelector('.поле-назва')?.remove();
    if(!area.querySelector('#mirror-review-list')){const list=document.createElement('div');list.id='mirror-review-list';area.append(list);}
  }
  function progress(){
    const state=зрізЗбиранняП(),phase=state.готово&&state.успіх?5:Math.max(1,Math.min(4,Number(state.етап||0)+1));
    const failed=!!(state.готово&&!state.успіх),key=M.get()+'/'+phase+'/'+failed;
    if(lastPhase!==key){node('mirror-making').innerHTML=failed?M.error():M.waiting(phase);lastPhase=key;}
  }
  function colorPair(){
    const el=node('mirror-my-colors');if(!el)return;
    const colors=[['шкіра','Шкіра'],['волосся','Волосся'],['очі','Очі']].map(([k,t])=>[tone(КОЛІР[k]),t]);
    el.innerHTML='<div class="studio-tone-title">Твої барви</div><div class="studio-tone-list">'+colors.map(([c,t])=>'<button type="button" data-ux="my-colors">'+(c?M.petal(c,23):'<i></i>')+escape(t)+'</button>').join('')+'</div>';
  }
  function decorateChoices(){
    const options = document.querySelectorAll('#аркуш .плитка,#пал-картка button[aria-pressed]');
    for(const option of options){
      const selected=option.classList.contains('вибр')||option.getAttribute('aria-pressed')==='true';
      const mark=option.querySelector(':scope > .chosen-material');
      if(!selected){mark?.remove();delete option.dataset.handMark;continue;}
      if(mark&&option.dataset.handMark===M.get())continue;
      const backdrop=mark||document.createElement('span');
      backdrop.className='chosen-material';backdrop.setAttribute('aria-hidden','true');
      backdrop.innerHTML=M.choice(({kahlia:'#d6d6ac',vytynanka:'#ecd1bf',klyny:'#bed0bf'})[M.get()],140,38);
      if(!mark)option.prepend(backdrop);
      option.dataset.handMark=M.get();
    }
  }
  const indexedColors=new Map(),fetchingColors=new Set();
  function gatherColors(items){
    const missing=(items||[]).map(t=>t.id).filter(id=>id&&id.includes('@')&&!indexedColors.has(id)&&!fetchingColors.has(id));
    if(missing.length){
      missing.forEach(id=>fetchingColors.add(id));
      Promise.all(missing.map(async id=>{
        try{indexedColors.set(id,tone((await MirrorIndex.get(id))?.color));}catch{}finally{fetchingColors.delete(id);}
      })).then(()=>{if(missing.some(id=>indexedColors.get(id)))schedule();});
    }
    return (items||[]).map(t=>tone(t.колір_hex)||tone(t.hex)||tone(t.color)||tone(t.колір)||tone(t.барва?.hex)||tone(t.основний_колір?.hex)||indexedColors.get(t.id)).filter(Boolean);
  }
  function lookSides(){
    const host=node('mirror-look-sides');if(!host)return;
    const pack=typeof П!=='undefined'?П:null,cards=pack?.картки||[],cur=cards[Екран.стан.образ?.поз||0];if(!cur){host.hidden=true;return;}
    const garments=cur.речі||cur.предмети||[];const colors=gatherColors(garments);
    const face=node('ф-зріст')?.querySelector('img')?.getAttribute('src');
    const frame=кадрПоказуП(cur);
    const safeImage=url=>typeof url==='string'&&/^(https?:|data:image\/|blob:)/i.test(url);
    const pictures=garments.filter(x=>safeImage(x.фото)&&!cur.фото_не_ті?.includes(x.id)).slice(0,4);
    host.hidden=!(face||frame||pictures.length||colors.length);if(host.hidden)return;
    const back=host.dataset.side==='back';
    const view=frame&&safeImage(frame)
      ? '<img src="'+escape(frame)+'" alt="Приміряний образ">'
      : '<span class="studio-real-collage">'+pictures.map(it=>'<img src="'+escape(it.фото)+'" alt="'+escape(it.назва||'Річ')+'">').join('')+'</span>';
    host.innerHTML=back?'<div class="studio-print">'+M.seal(colors,false,90)+'<div><b>'+escape(node('обр-випадок')?.textContent||'Мій образ')+'</b><ul>'+garments.map(it=>it.назва?'<li>'+escape(it.назва)+'</li>':'').join('')+'</ul></div></div>':
    '<div class="studio-look-pair"><div><b>Моє фото</b>'+(face?'<img src="'+escape(face)+'" alt="Твоє фото">':button('body-photo','Додати фото','камера'))+'</div><div><b>'+(frame?'Приміряння':'Комплект')+'</b>'+(pictures.length||frame?view:M.seal(colors,false,86))+'</div></div>';
    host.insertAdjacentHTML('beforeend',button('turn-look',back?'До образу':'Зворот','оберт'));
  }
  function nativeSeals(){
    if(typeof БІБЛІОТЕКА_П==='undefined')return;
    БІБЛІОТЕКА_П.плитки.forEach((entry,i)=>{
      const tile=node('біб-образ-'+i);
      if(!tile)return;
      const colors=gatherColors(entry.картка?.речі),key=M.get()+colors.join();
      if(tile.dataset.sealHand===key)return;
      const pattern=M.seal(colors,!!entry.вердикт?.вдягала,38);
      tile.querySelector('.studio-native-seal')?.remove();
      if(pattern){const seal=document.createElement('span');seal.className='studio-native-seal';seal.innerHTML=pattern;tile.append(seal);}
      tile.dataset.sealHand=key;
    });
  }
  function idlePanel(){
    if(node('mirror-chat-empty'))return;
    const frag=document.createElement('div');frag.id='mirror-chat-empty';
    frag.innerHTML=button('cases','Мої нагоди','збірка')+button('closet','Мої речі','вішак');node('mirror-thread').append(frag);
  }
  function sync(){
    scheduled=false;
    const mode=режимЕкрана()||'сценарій';document.documentElement.dataset.room=mode;
    if(pageMode&&pageMode!==mode){closeExtras();drawer(false);node('mirror-chat-status').textContent='';}
    pageMode=mode;
    move(node('сц-увага'),node('сц-увага-місце'));move(node('сц-картка'),node('сц-картка-місце'));
    if(!Екран.стан.аркуш||Екран.стан.аркуш.вузол!==node('ф-блок'))move(node('ф-блок'),node('ф-блок-місце'));
    move(node('чат-стрічка'),node('mirror-thread'));move(node('чат-ввід'),node('mirror-input'));move(node('чат-голос'),node('mirror-input'));move(node('чат-стан'),node('mirror-input'));
    move(node('сц-швидкі'),node('mirror-suggestions'));move(node('ніг-дії'),node('mirror-step-actions'));
    const inReview=mode==='оцінка'&&!extra;
    const grip=node('mirror-grip');const latest=[...ЧАТ_П].reverse().find(g=>g.хто==='ші'&&g.текст);
    grip.querySelector('span').textContent=inReview?'Питання про вбрання':latest?.текст||'Розмова';grip.setAttribute('aria-label',inReview?'До питання про вбрання':'Відкрити розмову');
    node('чат-поле').placeholder='Напиши стилістці…';
    node('mirror-input').hidden=inReview;node('чат-ввід').hidden=inReview;document.documentElement.classList.toggle('mirror-context-photo',inReview);
    const empty=!hasCase();node('mirror-occasions').hidden=!empty;node('mirror-case-tools').hidden=empty;
    node('mirror-occasions').innerHTML ||= homeMarkup();
    node('mirror-chat-empty').hidden=ЧАТ_П.length>0;
    node('mirror-native').hidden=!!extra;
    document.documentElement.classList.toggle('mirror-empty-case',empty);
    if(!extra){
      let title=titles[mode]||'Люстерко',controls='';
      if(mode==='сценарій'){title=empty?'Нагода':node('сц-назва')?.textContent.trim()||'Нагода';if(!empty&&['Нагода','Новий сценарій'].includes(title)){const value=полеВипадкуП('сц-нагода');title=ДОВІДНИК.нагоди.find(x=>x.ключ===value)?.підпис||'Нагода';}controls=button('cases','Збережені','зберегти');}
      else if(mode==='бібліотека'){controls=button('closet','Мої речі','вішак');}
      else if(mode==='профіль'){controls=button('access','Доступ','', '', 'studio-text');}
      else if(mode!=='очікування'){controls=button('face','До нагоди','назад');}
      setHeading(title,controls);
    }
    if(mode==='очікування')progress();if(mode==='палітра')colorPair();if(mode==='образи')lookSides();
    if(mode==='бібліотека'){nativeSeals();if(window.Rack)Rack.library();}
    decorateChoices();renderPerson();navState();
  }
  function schedule(){if(!scheduled){scheduled=true;queueMicrotask(sync);}}
  function chooseOccasion(k){
    if(!available())return;close();route('сценарій',false);прапорСценарію('рукою',true);Екран.відЖінки('нагода-обрати',k);показатиРозмову();sync();
    node('mirror-work').focus({preventScroll:true});scrollTo(0,0);
  }
  function talk(){
    if(!available())return;
    if(режимЕкрана()==='оцінка'&&!extra){const q=node('оц-питання');q.scrollIntoView({block:'center'});q.focus();return;}
    if(mobile.matches){drawer(!openDrawer);if(openDrawer&&!ЧАТ_П.length)node('чат-поле').focus({preventScroll:true});}else node('чат-поле').focus();
  }
  function startWords(words,withPhoto=false){
    route('сценарій',false);const f=node('чат-поле');f.value=words;f.dispatchEvent(new Event('input',{bubbles:true}));
    if(withPhoto){node('чат-фото-вхід').click();}else {if(mobile.matches)drawer(true);f.focus();}
  }
  function access(context=''){
    const host=location.hostname;
    const official=host==='mightyrochy.github.io';
    const remote=!!МІСТ_П.адреса && !МІСТ_П.адреса.startsWith('https://lyusterko-mist.mighty-rochy.workers.dev');
    const field=official||remote?'<form data-form="access"><label>Код доступу<input type="password" name="token" autocomplete="off" required maxlength="240"></label><button class="studio-primary">Застосувати</button></form>':
      '<p>Сервіс стилістки дозволяє підключення з офіційної адреси Люстерка.</p><a class="studio-link" href="https://mightyrochy.github.io/kod-shi-data/" target="_blank" rel="noopener noreferrer">Офіційне Люстерко</a>';
    let alternate='';
    if(context==='чат-слати'&&режимЕкрана()==='сценарій')
      alternate=button('save-note','Зберегти в нагоді','зберегти','','studio-primary');
    else if(context==='зб-зібрати'||context==='зб-пуск')
      alternate=button('compose','Зібрати вручну','вішак','','studio-primary');
    dialog('Доступ до стилістки',field+(alternate?'<div class="rack-actions">'+alternate+'</div>':''));
  }
  function saveNote(){
    const input=node('чат-поле'),text=input.value.trim(),photos=ФОТО_ВКЛАДЕНІ_П.slice();
    if(!text&&!photos.length){close();return;}
    const note={хто:'людина',текст:text,тема:'сценарій'};
    if(photos.length)note.фото=photos;
    if(ЧАТ_ГОЛОСОМ_П)note.голосом=true;
    ЧАТ_П.push(note);ЧАТ_ГОЛОСОМ_П=false;ФОТО_ВКЛАДЕНІ_П=[];input.value='';
    позначитиЗміну();показатиРозмову();зберегтиЧернетку();close();say('Збережено в нагоді.');schedule();
  }
  function protectModel(ev){
    const b=ev.target.closest('#чат-слати,#зб-зібрати,#зб-пуск,#оц-оцінити');if(!b||b.disabled)return;
    const official=location.hostname==='mightyrochy.github.io',custom=МІСТ_П.адреса&&МІСТ_П.адреса!==ТИПОВИЙ_МІСТ_П;
    if((official||custom)&&МІСТ_П.токен)return;
    if(b.id==='чат-слати'&&!node('чат-поле').value.trim()&&!node('чат-вкладення').children.length)return;
    if(b.id==='оц-оцінити'&&!node('оц-фото')?.querySelector('img'))return;
    if((b.id==='зб-зібрати'||b.id==='зб-пуск')&&чогоБракує().length)return;
    ev.preventDefault();ev.stopImmediatePropagation();access(b.id);
  }
  function personalColors(){route('профіль',false);відкритиАркушПрофілю('кол-блок');}
  function start(){
    const root=document.documentElement;root.classList.add('mirror-ready');root.removeAttribute('data-тема');
    move(node('колонка'),node('mirror-native'));
    const follow=document.createElement('div');follow.id='mirror-step-actions';node('mirror-native').append(follow);
    makeHome();setupAssessment();
    node('сц-картка').append(node('зб-зібрати').parentElement);
    node('сц-назва-поле').placeholder='Назва нагоди';
    node('сц-зберегти').textContent='Зберегти нагоду';
    const making=document.createElement('div');making.id='mirror-making';node('ткання').before(making);
    const colors=document.createElement('div');colors.id='mirror-my-colors';node('пал-картка').prepend(colors);
    const looks=document.createElement('div');looks.id='mirror-look-sides';node('картки').before(looks);
    move(node('журнал'),node('е-огляд'));
    const shelf=document.createElement('div');shelf.id='mirror-saved-manual';node('біб-список').before(shelf);
    node('mirror-home').addEventListener('click',()=>route('сценарій'));
    node('mirror-style').addEventListener('click',showThemes);node('mirror-person').addEventListener('click',()=>route('профіль'));
    node('mirror-grip').addEventListener('click',talk);
    node('чат-поле').setAttribute('aria-label','Повідомлення стилістці');node('чат-поле').placeholder='Напиши стилістці…';
    node('чат-слати').innerHTML=ik('далі');node('чат-слати').setAttribute('aria-label','Надіслати');
    node('mirror-conversation').addEventListener('touchstart',ev=>{gesture=mobile.matches&&ev.target.closest('.studio-grip,.studio-talk-head')?ev.touches[0]:null;},{passive:true});
    node('mirror-conversation').addEventListener('touchend',ev=>{if(!gesture)return;const t=ev.changedTouches[0],dy=t.clientY-gesture.clientY;gesture=null;if(Math.abs(dy)>40)drawer(dy<0);},{passive:true});
    let flip;looks.addEventListener('touchstart',e=>flip=e.touches[0],{passive:true});looks.addEventListener('touchend',e=>{if(!flip)return;const p=e.changedTouches[0];if(Math.abs(p.clientX-flip.clientX)>65&&Math.abs(p.clientY-flip.clientY)<40)actions.get('turn-look')();flip=null;},{passive:true});
    document.addEventListener('click',protectModel,true);
    document.addEventListener('keydown',e=>{if(e.target.id==='чат-поле'&&e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&node('чат-поле').value.trim()){const b=node('чат-слати');if(!b.disabled){e.preventDefault();e.stopImmediatePropagation();b.click();}}if(e.key==='Escape'&&!sheet.open&&openDrawer)drawer(false);},true);
    document.addEventListener('click',e=>{const b=e.target.closest('[data-ux]');if(b&&!b.disabled&&actions.has(b.dataset.ux)){actions.get(b.dataset.ux)(b.dataset.value||'',b);}});
    document.addEventListener('submit',e=>{if(e.target.matches('[data-form="access"]')){e.preventDefault();const token=new FormData(e.target).get('token').trim();if(!token)return;try{localStorage.setItem('міст:токен',token);}catch{}МІСТ_П.токен=token;close();say('Код збережено.');}});
    window.addEventListener(M.changeEvent,()=>{themeButtons();node('mirror-occasions').innerHTML=homeMarkup();lastPhase='';schedule();window.Rack?.repaintArtwork();});
    idlePanel();themeButtons();sync();
    Екран.малювач('дзеркало-робота',['режим','вхід','крок','запущено','панель','розмова','випадок','сценарій','профілі','поля','аркуш','збирання','образ','образи','палітра','фото','бібліотека','кошик'],schedule);
  }
  const handlers={talk,collapse:()=>drawer(false),face:()=>route('сценарій'),cases:()=>route('сценарії'),assess:()=>route('оцінка'),library:()=>route('бібліотека'),profile:()=>route('профіль'),access,'save-note':saveNote,hand:k=>{M.set(k);close();},'close-sheet':close,occasion:chooseOccasion,
    'all-occasions':()=>{route('сценарій',false);Екран.відЖінки('картку-показати');},'my-colors':personalColors,
    'case-tools':()=>dialog('Речі','<div class="studio-menu">'+tools.map(([a,l,i])=>button(a,l,i)).join('')+'</div>'),
    'body-photo':()=>{route('профіль',false);відкритиАркушПрофілю('ф-блок');},'turn-look':()=>{const el=node('mirror-look-sides');el.dataset.side=el.dataset.side==='back'?'front':'back';lookSides();},
    'take-photo':()=>startWords('Збери образ під мою річ.',true)};
  for(const [k,v] of Object.entries(handlers))actions.set(k,v);
  window.MirrorRoom={ik,escape,button,money,tone,dialog,close,route,showExtra,startWords,say,currentExtra:()=>extra,activeProfile,available,register:(k,fn)=>actions.set(k,fn),refresh:schedule};
  start();
})();
