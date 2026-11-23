"use strict";
(() => {
  const node = id => document.getElementById(id);
  const M = window.MirrorMaterial;
  const mobile = window.matchMedia?.("(max-width: 999px)") || {matches:false,addEventListener(){}};
  const ik = (id, size=22) => '<svg class="мі-ік" width="'+size+'" height="'+size+'" aria-hidden="true"><use href="#мі-'+id+'"/></svg>';
  const escape = text => String(text ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const button = (action, title, symbol='', value='', cls='studio-text') => '<button type="button" class="'+cls+'" data-ux="'+action+'" data-value="'+escape(value)+'">'+(symbol?ik(symbol):'')+'<span>'+escape(title)+'</span></button>';
  const money = amount => new Intl.NumberFormat('uk-UA',{maximumFractionDigits:2}).format(amount)+' ₴';
  const tone = v => typeof v === 'string' && /^#[\da-f]{3}([\da-f]{3})?$/i.test(v) ? v : '';
  const sheet = node('mirror-sheet'), work=node('mirror-work');
  let following=true, lastTurn=null, drawerOpen=false;
  let contextWords='', originator=null, extra='', pageMode='', headerKey='', scheduled=false, other=false;
  const titles={'сценарій':'Образ','профіль':'Мій профіль','старт':'Мій профіль','оцінка':'Оцінити вбрання','сценарії':'Мої нагоди','образи':'Образ','бібліотека':'Мої образи','палітра':'Барви','очікування':'Збираю образи'};
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
  function setDrawer(open,focus=false){
    drawerOpen=!!open;const expanded=!mobile.matches||drawerOpen;
    document.documentElement.dataset.drawer=expanded?'open':'closed';
    node('pair-handle').setAttribute('aria-expanded',String(expanded));
    node('pair-curtain').hidden=!(mobile.matches&&drawerOpen);
    work.inert=mobile.matches&&drawerOpen;document.querySelector('.pair-mast').inert=work.inert;
    if(focus)node('чат-поле').focus({preventScroll:true});
  }
  function keyboardSpace(){
    const view=window.visualViewport,root=document.documentElement;
    if(view&&mobile.matches&&view.scale===1)root.style.setProperty('--pair-height',Math.round(view.height)+'px');
    else root.style.removeProperty('--pair-height');
  }
  window.visualViewport?.addEventListener('resize',keyboardSpace);
  mobile.addEventListener('change',()=>{keyboardSpace();setDrawer(false);schedule();});
  function available(){return !!Екран.стан.запущено;}
  function closeExtras(){if(extra){extra='';offerContext();node('mirror-extras').replaceChildren();node('mirror-extras').hidden=true;delete document.documentElement.dataset.extra;headerKey='';}}
  function route(mode,focus=true){
    if(!available())return;
    if(режимЕкрана()==='очікування'&&зрізЗбиранняП().зайнято){say('Триває збирання образу.');return;}
    close();closeExtras();if(Екран.стан.аркуш)закритиАркуш();режим(mode);setDrawer(false);sync();if(focus){work.scrollTop=0;work.focus({preventScroll:true});}
  }
  function offerContext(label='',words=''){
    contextWords=words;const host=node('pair-chat-context'),b=host.querySelector('button');
    host.hidden=!words;if(words)b.textContent=label;
  }
  function showExtra(key, title, content,controls='',context=null){
    if(!available())return;
    if(Екран.стан.аркуш)закритиАркуш();close();
    const changed=extra!==key;extra=key;offerContext(context?.[0],context?.[1]);document.documentElement.dataset.extra=key;
    const el=node('mirror-extras');el.hidden=false;el.innerHTML=content;
    headerKey='';setHeading(title,controls||button('face','До образу','назад'));
    pair.render(режимЕкрана(),extra);if(changed){setDrawer(false);work.scrollTop=0;work.focus({preventScroll:true});}
  }
  function setHeading(title,controls){
    const signature=title+controls;if(headerKey===signature)return;headerKey=signature;
    node('mirror-heading').innerHTML='<h1>'+escape(title)+'</h1><div class="studio-heading-actions">'+controls+'</div>';
  }
  function renderPerson(){
    const b=node('mirror-person'),photo=node('ф-портрет')?.querySelector('img')?.getAttribute('src')||'';
    if(b._hand===M.get()&&b._photo===photo)return;b._hand=M.get();b._photo=photo;
    b.innerHTML=Hand.mark(M.get(),28,photo)+'<span>Мій профіль</span>';b.title='Мій профіль';
  }
  function themeButtons(){
    const hand=M.get();
    document.documentElement.dataset.hand=hand;
    node('mirror-home').innerHTML=M.mast();
    node('mirror-header-art').innerHTML=Hand.cover(hand);
    node('mirror-style').innerHTML='<span class="studio-hand-name">'+escape(M.label())+'<i aria-hidden="true"></i></span>';
    node('mirror-style').setAttribute('aria-label','Оформлення · '+M.label());
    node('mirror-prompt-mark').innerHTML=Hand.mark(hand);
    const icon=Hand.mark(hand).replace(/style="fill:var\(--tlo\)"/g,'fill="'+(hand==='klyny'?'#e6e0d0':'#faf6ea')+'"');
    document.documentElement.style.setProperty('--speaker-mark','url("data:image/svg+xml,'+encodeURIComponent(icon)+'")');
    const meta=document.querySelector('meta[name=theme-color]');if(meta)meta.content=hand==='klyny'?'#e6e0d0':'#faf6ea';
    renderPerson();
  }
  function showThemes(){
    const choices=Object.entries(M.labels).map(([id,name])=>'<button type="button" data-swatch="'+id+'" data-ux="hand" data-value="'+id+'" aria-pressed="'+(id===M.get())+'"><span class="studio-swatch" aria-hidden="true">'+Hand.art(id,'welcome')+'</span><span class="studio-swatch-name">'+name+(id===M.get()?ik('так',17):'')+'</span></button>').join('');
    dialog('Оформлення','<div class="studio-theme-list">'+choices+'</div>');
  }
  const occasions=[['щоденне','звичайний день'],['робота','робота'],['побачення','побачення'],['свято','свято'],['театр','театр'],['спорт','спорт'],['подорож','подорож'],['','інше']];
  function hasCase(){return !!(єВипадокП()||ЧАТ_П.length||ПАСПОРТ_П||(Екран.стан.сценарій||{}).рукою);}
  function makeHome(){
    node('mirror-choices').innerHTML=occasions.map(([id,label])=>'<button type="button" data-ux="occasion" data-value="'+id+'" aria-pressed="false"><span>'+label+'</span></button>').join('');
  }
  function setupAssessment(){
    const area=node('е-оцінка'),photo=node('оц-фото').closest('.оц-поле'),question=node('оц-питання').closest('.оц-поле');
    const columns=document.createElement('div');columns.className='studio-assessment';photo.before(columns);columns.append(photo);const right=document.createElement('section');right.className='pair-review-read';right.innerHTML='<h3>Речі на фото</h3><div class="pair-read-empty">Після оцінки тут з’являться розпізнані речі.</div>';columns.append(right);columns.after(question);
    const results=node('оц-речі');right.append(results);results.classList.add('studio-assessed-items');
    const label=photo.querySelector('.поле-назва');if(label)label.textContent='Твоє фото';
    const head=question.querySelector('label');if(head)head.textContent='Що оцінити?';
    const mic=document.createElement('button'),voiceHint=document.createElement('small');
    mic.type='button';mic.className='studio-text';mic.id='mirror-review-mic';mic.innerHTML=ik('голос',17)+'<span>Сказати</span>';
    voiceHint.className='studio-voice-hint';voiceHint.setAttribute('role','status');question.append(mic,voiceHint);
    привʼязатиГолос({кнопка:mic,поле:node('оц-питання'),нота:voiceHint});
    const weather=node('оц-нагода').closest('.оц-поле'),details=document.createElement('details');details.className='studio-weather';details.innerHTML='<summary>Нагода й погода</summary>';weather.before(details);details.append(weather);weather.querySelector('.поле-назва')?.remove();
    if(!area.querySelector('#mirror-review-list')){const list=document.createElement('div');list.id='mirror-review-list';area.append(list);}
  }
  function decorateChoices(){
    const selectedKey=полеВипадкуП('сц-нагода');
    if(selectedKey)other=false;
    const own=node('mirror-choices').querySelectorAll('button');
    const options=[...own,...document.querySelectorAll('#аркуш .плитка,#пал-картка button[aria-pressed],.pair-intent button,.pair-fact .pair-confirmed')];
    for(const option of options){
      let selected;
      if(option.dataset.ux==='occasion'){
        selected=option.dataset.value?selectedKey===option.dataset.value:other;
        option.setAttribute('aria-pressed',String(selected));
      } else selected=option.classList.contains('pair-confirmed')||option.classList.contains('вибр')||option.getAttribute('aria-pressed')==='true';
      const mark=option.querySelector(':scope > .plama');
      if(!selected){mark?.remove();delete option.dataset.paint;continue;}
      const w=option.offsetWidth,h=option.offsetHeight;
      if(!w||!h)continue;
      const signature=M.get()+'/'+w+'/'+h;
      if(mark&&option.dataset.paint===signature)continue;
      mark?.remove();option.dataset.paint=signature;
      option.insertAdjacentHTML('afterbegin',Hand.impression(M.get(),w,h));
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
  function nativeSeals(){
    if(typeof БІБЛІОТЕКА_П==='undefined')return;
    БІБЛІОТЕКА_П.плитки.forEach((entry,i)=>{
      const tile=node('біб-образ-'+i);
      if(!tile)return;
      tile.hidden=!pair.blindShelf()&&['2','3','4'].includes(String(entry.картка?.рука));
      const colors=gatherColors(entry.картка?.речі),worn=!!window.Rack?.nativeWorn(entry.ід),key=M.get()+colors.join()+worn;
      if(tile.dataset.sealHand===key)return;
      const pattern=M.seal(colors,worn,38);
      tile.querySelector('.studio-native-seal')?.remove();
      if(pattern){const seal=document.createElement('span');seal.className='studio-native-seal';seal.innerHTML=pattern;tile.append(seal);}
      tile.dataset.sealHand=key;tile.classList.toggle('pair-worn-card',worn);
    });
  }
  function sync(){
    scheduled=false;
    const mode=режимЕкрана()||'сценарій';document.documentElement.dataset.room=mode;
    if(pageMode&&pageMode!==mode){closeExtras();setDrawer(false);say('');work.scrollTop=0;}
    pageMode=mode;
    const feedback=node('pair-feedback'),inCase=mode==='сценарій',review=mode==='оцінка'&&!extra;
    for(const id of ['сц-увага','зб-питання','зб-статус'])move(node(id),feedback);
    if(!Екран.стан.аркуш||Екран.стан.аркуш.вузол!==node('ф-блок'))move(node('ф-блок'),node('ф-блок-місце'));
    move(node('чат-стрічка'),node('mirror-thread'));move(node('чат-ввід'),node('mirror-input'));move(node('чат-голос'),node('mirror-input'));move(node('чат-стан'),node('mirror-input'));
    move(node('сц-швидкі'),node('mirror-suggestions'));move(node('ніг-дії'),node('mirror-step-actions'));
    updateSend(inCase);placeNoteEdits();node('чат-ввід').hidden=false;
    node('pair-review-chat').hidden=!review;
    if(!inCase&&!extra)setHeading(titles[mode]||'Люстерко',mode==='бібліотека'?button('closet','Мої речі','вішак'):mode==='профіль'?button('access','Доступ'):button('face','До люстерка','назад'));
    pair.render(mode,extra);
    feedback.hidden=!!extra||!inCase||document.documentElement.dataset.pairPage!=='understood';
    if(mode==='бібліотека'&&!extra){nativeSeals();node('mirror-saved-manual').hidden=pair.blindShelf();if(!pair.blindShelf())window.Rack?.library();}
    const last=ЧАТ_П.at(-1);
    if(last!==lastTurn&&last&&following&&(!mobile.matches||drawerOpen)){
      requestAnimationFrame(()=>{const letter=node('mirror-letter');letter.scrollTop=letter.scrollHeight;});
    }
    lastTurn=last;decorateChoices();renderPerson();
  }
  function schedule(){if(!scheduled){scheduled=true;queueMicrotask(sync);}}
  function goTalk(focus=false){if(available())setDrawer(true,focus);}
  function goFace(){pair.stage('mirror');}
  function editWords(voice=false){
    if(!available())return;setDrawer(true,!voice);
    if(voice){const mic=node('чат-мікрофон');if(!mic.disabled)mic.click();}
  }
  function chooseOccasion(k){
    if(!available())return;
    close();
    if(режимЕкрана()!=='сценарій')return;
    other=k==='';
    прапорСценарію('рукою',true);Екран.відЖінки('нагода-обрати',k);показатиРозмову();sync();
    pair.afterOccasion(k);
  }
  function startWords(words,withPhoto=false){
    close();goTalk(false);const field=node('чат-поле');
    const draft=field.value.trim();if(!draft||!draft.includes(words))field.value=draft?draft+'\n'+words:words;field.dispatchEvent(new Event('input',{bubbles:true}));
    if(withPhoto)node('чат-фото-вхід').click();else field.focus({preventScroll:true});
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
  function localNotes(){
    return location.hostname!=='mightyrochy.github.io'&&!(МІСТ_П.адреса&&МІСТ_П.адреса!==ТИПОВИЙ_МІСТ_П);
  }
  function updateSend(inCase){
    const send=node('чат-слати'),local=localNotes();
    if(send._local===local)return;
    send._local=local;send.classList.toggle('studio-note-action',local);
    send.setAttribute('aria-label',local?'Зберегти в нагоді':'Надіслати');send.title=send.getAttribute('aria-label');
    send.innerHTML=local?ik('зберегти',20):ik('далі');
  }
  function placeNoteEdits(){
    const entries=node('чат-стрічка').children;
    ЧАТ_П.forEach((note,index)=>{
      if(!note.локальна||!entries[index]||entries[index].querySelector('.studio-note-edit'))return;
      entries[index].insertAdjacentHTML('beforeend',button('edit-note','Змінити', '',note.локальна,'studio-note-edit'));
    });
  }
  function editNote(id){
    const note=ЧАТ_П.find(n=>n.локальна===id);if(!note)return;
    dialog('Слова про нагоду','<form data-form="note" data-id="'+escape(id)+'"><textarea name="words" aria-label="Слова про нагоду">'+escape(note.текст)+'</textarea><button type="submit" class="studio-primary">Зберегти</button></form>');
  }
  function finishNote(event){
    const form=event.target;if(!form.matches('[data-form="note"]'))return;
    event.preventDefault();
    const note=ЧАТ_П.find(n=>n.локальна===form.dataset.id);if(!note){close();return;}
    const words=new FormData(form).get('words').trim();
    if(!words&&!note.фото?.length){form.elements.words.focus();return;}
    note.текст=words;позначитиЗміну();показатиРозмову();зберегтиЧернетку();close();schedule();
  }
  function saveNote(){
    const input=node('чат-поле'),text=input.value.trim(),photos=ФОТО_ВКЛАДЕНІ_П.slice();
    if(!text&&!photos.length){close();return;}
    const note={хто:'людина',текст:text,тема:'сценарій',локальна:globalThis.crypto?.randomUUID?.()||Date.now().toString(36)};
    if(photos.length)note.фото=photos;
    if(ЧАТ_ГОЛОСОМ_П)note.голосом=true;
    following=true;ЧАТ_П.push(note);ЧАТ_ГОЛОСОМ_П=false;ФОТО_ВКЛАДЕНІ_П=[];input.value='';
    позначитиЗміну();показатиРозмову();зберегтиЧернетку();close();say('Збережено в нагоді.');schedule();
  }
  function protectModel(ev){
    const b=ev.target.closest('#чат-слати,#зб-зібрати,#зб-пуск,#оц-оцінити');if(!b||b.disabled)return;
    const official=location.hostname==='mightyrochy.github.io',custom=МІСТ_П.адреса&&МІСТ_П.адреса!==ТИПОВИЙ_МІСТ_П;
    if((official||custom)&&МІСТ_П.токен)return;
    if(b.id==='чат-слати'&&!node('чат-поле').value.trim()&&!node('чат-вкладення').children.length)return;
    if(b.id==='оц-оцінити'&&!node('оц-фото')?.querySelector('img'))return;
    if((b.id==='зб-зібрати'||b.id==='зб-пуск')&&чогоБракує().length)return;
    ev.preventDefault();ev.stopImmediatePropagation();
    if(b.id==='чат-слати'&&localNotes())saveNote();else access(b.id);
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
    const colors=document.createElement('div');colors.id='mirror-my-colors';node('пал-картка').before(colors);
    const looks=document.createElement('div');looks.id='mirror-look-sides';node('картки').before(looks);
    move(node('журнал'),node('е-огляд'));
    const shelf=document.createElement('div');shelf.id='mirror-saved-manual';node('біб-список').before(shelf);
    node('mirror-home').addEventListener('click',goFace);
    node('mirror-style').addEventListener('click',showThemes);node('mirror-person').addEventListener('click',()=>route('профіль'));
    node('чат-поле').setAttribute('aria-label','Повідомлення стилістці');node('чат-поле').placeholder='Напиши…';
    node('чат-слати').innerHTML=ik('далі');node('чат-слати').setAttribute('aria-label','Надіслати');
    if(window.ResizeObserver){
      const size=new ResizeObserver(()=>decorateChoices());size.observe(node('mirror-choices'));size.observe(node('аркуш'));size.observe(node('pair-scene'));size.observe(node('пал-картка'));
    }
    const handle=node('pair-handle'),letter=node('mirror-letter');
    handle.addEventListener('click',()=>{if(mobile.matches)setDrawer(!drawerOpen);});
    node('pair-curtain').addEventListener('click',()=>setDrawer(false));
    let y=null,lastSwipe=0;
    handle.addEventListener('touchstart',ev=>{y=ev.touches[0].clientY;},{passive:true});
    handle.addEventListener('touchend',ev=>{if(y===null)return;const delta=ev.changedTouches[0].clientY-y;y=null;
      if(Math.abs(delta)>25){lastSwipe=Date.now();setDrawer(delta<0);}},{passive:true});
    handle.addEventListener('click',ev=>{if(Date.now()-lastSwipe<400)ev.stopImmediatePropagation();},true);
    letter.addEventListener('scroll',()=>{following=letter.scrollHeight-letter.scrollTop-letter.clientHeight<75;},{passive:true});
    for(const id of ['ф-зріст','ф-портрет'])if(node(id))new MutationObserver(schedule).observe(node(id),{subtree:true,childList:true,attributes:true,attributeFilter:['src']});
    document.addEventListener('keydown',ev=>{if(ev.key==='Escape'&&drawerOpen&&!sheet.open&&!Екран.стан.аркуш){setDrawer(false);handle.focus({preventScroll:true});}});
    document.addEventListener('click',protectModel,true);
    document.addEventListener('submit',finishNote);
    document.addEventListener('keydown',e=>{if(e.target.id==='чат-поле'&&e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&node('чат-поле').value.trim()){const b=node('чат-слати');if(!b.disabled){e.preventDefault();e.stopImmediatePropagation();b.click();}}},true);
    document.addEventListener('click',e=>{const b=e.target.closest('[data-ux]');if(b&&!b.disabled&&actions.has(b.dataset.ux)){actions.get(b.dataset.ux)(b.dataset.value||'',b);}});
    document.addEventListener('submit',e=>{if(e.target.matches('[data-form="access"]')){e.preventDefault();const token=new FormData(e.target).get('token').trim();if(!token)return;try{localStorage.setItem('міст:токен',token);}catch{}МІСТ_П.токен=token;close();say('Код збережено.');}});
    window.addEventListener(M.changeEvent,()=>{themeButtons();schedule();window.Rack?.repaintArtwork();});
    themeButtons();keyboardSpace();setDrawer(false);sync();
    Екран.малювач('дзеркало-робота',['режим','вхід','крок','запущено','панель','розмова','випадок','сценарій','профілі','поля','аркуш','збирання','образ','образи','палітра','фото','бібліотека','кошик','заміна','картка','статус_збирання','стан_палітри','оцінка'],schedule);
  }
  const handlers={talk:()=>goTalk(),speak:()=>editWords(true),write:()=>editWords(),face:goFace,cases:()=>route('сценарії'),assess:()=>route('оцінка'),library:()=>pair.dailyShelf(),profile:()=>route('профіль'),access,'edit-note':editNote,'save-note':saveNote,hand:k=>{M.set(k);close();},'close-sheet':close,occasion:chooseOccasion,
    'context-question':()=>{if(contextWords)startWords(contextWords);},'my-colors':personalColors, collapse:()=>{setDrawer(false);node('pair-handle').focus({preventScroll:true});},
    'ask-review':()=>{setDrawer(false);node('оц-питання').focus();},
    'body-photo':()=>pair.handlers['pair-photo'](),'take-photo':()=>startWords('Збери образ під мою річ.',true)};
  const pair=window.createMirrorPair({node,ik,escape,button,money,tone,dialog,close,route,showExtra,
    available,hasCase,heading:setHeading,refresh:schedule,closeDrawer:()=>setDrawer(false),openDrawer:focus=>setDrawer(true,focus)});
  for(const [k,v] of Object.entries({...handlers,...pair.handlers}))actions.set(k,v);
  window.MirrorRoom={pair,ik,escape,button,money,tone,dialog,close,route,showExtra,startWords,say,currentExtra:()=>extra,activeProfile,available,register:(k,fn)=>actions.set(k,fn),refresh:schedule};
  start();
})();
