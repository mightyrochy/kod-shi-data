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
  let reviewPhoto=null, reviewColumns=null, following=true, lastTurn=null;
  let originator=null, side='talk', extra='', pageMode='', headerKey='', scheduled=false, lastPhase='', other=false;
  const titles={'сценарій':'Образ','профіль':'Мій профіль','старт':'Мій профіль','оцінка':'Оцінити вбрання','сценарії':'Мої нагоди','образи':'Образ','бібліотека':'Мої образи','палітра':'Барви','очікування':'Збираю образи'};
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
  function setSide(next, scroll=false) {
    const changed=side!==next;
    side=next;
    document.documentElement.dataset.view=side;
    if(changed&&scroll) {
      const panel=side==='talk'?node('mirror-letter'):work;
      panel.scrollTop=0;
      if(mobile.matches)window.scrollTo(0,0);
      if(side!=='talk')work.focus({preventScroll:true});
    }
    navState();
  }
  mobile.addEventListener('change',()=>{schedule();requestAnimationFrame(decorateChoices);});
  function available(){return !!Екран.стан.запущено;}
  function closeExtras(){if(extra){extra='';node('mirror-extras').replaceChildren();node('mirror-extras').hidden=true;delete document.documentElement.dataset.extra;headerKey='';}}
  function route(mode,focus=true){
    if(!available())return;
    if(режимЕкрана()==='очікування'&&зрізЗбиранняП().зайнято){say('Триває збирання образу.');return;}
    close();closeExtras();if(Екран.стан.аркуш)закритиАркуш();режим(mode);sync();setSide(mode==='бібліотека'?'library':'face',focus);if(focus)work.scrollTop=0;
  }
  function showExtra(key, title, content,controls=''){
    if(!available())return;
    if(Екран.стан.аркуш)закритиАркуш();close();
    const changed=extra!==key;extra=key;document.documentElement.dataset.extra=key;
    const el=node('mirror-extras');el.hidden=false;el.innerHTML=content;
    headerKey='';setHeading(title,controls||button('face','До образу','назад'));
    node('mirror-native').hidden=true;setSide(key==='saved'||(key==='wardrobe'&&side==='library')?'library':'face',changed);if(changed)work.scrollTop=0;
  }
  function setHeading(title,controls){
    const signature=title+controls;if(headerKey===signature)return;headerKey=signature;
    node('mirror-heading').innerHTML='<h1>'+escape(title)+'</h1><div class="studio-heading-actions">'+controls+'</div>';
  }
  function navState(){
    const skip=document.querySelector('.studio-skip');
    skip.href=side==='talk'?'#mirror-occasions':'#mirror-work';
    skip.textContent=side==='talk'?'До розмови':'До основного вмісту';
    document.querySelectorAll('.studio-nav [data-ux]').forEach(b=>{
      if(b.dataset.ux===side)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');
    });
  }
  function renderPerson(){
    const b=node('mirror-person'),photo=node('ф-портрет')?.querySelector('img')?.getAttribute('src')||'';
    const initial=node('пф-ініціали')?.textContent.trim().replace('·','')||'';
    if(b._hand===M.get()&&b._photo===photo&&b._initial===initial)return;
    b._hand=M.get();b._photo=photo;b._initial=initial;
    b.innerHTML=Hand.mark(M.get(),44,photo)+(photo?'':'<span>'+(initial?escape(initial):ik('людина',17))+'</span>');
  }
  function themeButtons(){
    const hand=M.get();
    document.documentElement.dataset.hand=hand;
    node('mirror-home').innerHTML=M.mast();
    node('mirror-style').innerHTML='<span class="studio-binding">'+Hand.cover(hand)+'</span><span class="studio-hand-name">'+escape(M.label())+'<i aria-hidden="true"></i></span>';
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
    const face=document.createElement('div');face.id='mirror-face-pair';face.className='studio-face-pair';
    node('е-випадок').prepend(face);
    const toolshelf=document.createElement('div');toolshelf.id='mirror-case-tools';toolshelf.className='studio-case-tools';
    toolshelf.innerHTML='<div class="studio-tools">'+[...tools,['compose','Зібрати вручну','люстерко'],['closet','Мої речі','збірка']].map(([key,name,icon])=>button(key,name,icon,'','studio-tool')).join('')+'</div>';
    node('е-випадок').append(toolshelf);
  }
  function facePair(empty){
    const el=node('mirror-face-pair');
    el.hidden=!empty;if(!empty)return;
    const photo=node('ф-зріст')?.querySelector('img')?.getAttribute('src')||'';
    if(el._hand===M.get()&&el._photo===photo)return;
    el._hand=M.get();el._photo=photo;
    const own=photo?'<img class="studio-body-photo" src="'+escape(photo)+'" alt="Твоє фото">':'<span class="studio-photo-window">'+ik('камера',33)+'</span>';
    el.innerHTML='<button type="button" data-ux="body-photo">'+own+'<span>'+(photo?'Моє фото':'Додати моє фото')+'</span></button><button type="button" data-ux="compose"><span class="studio-first-seal">'+M.seal([],false,71)+'</span><span>Зібрати образ</span></button>';
  }
  function setupAssessment(){
    const area=node('е-оцінка'),photo=node('оц-фото').closest('.оц-поле'),question=node('оц-питання').closest('.оц-поле');
    const columns=document.createElement('div');columns.className='studio-assessment';photo.before(columns);columns.append(photo,question);reviewPhoto=photo;reviewColumns=columns;
    const results=node('оц-речі');question.after(results);results.classList.add('studio-assessed-items');
    const label=photo.querySelector('.поле-назва');if(label)label.textContent='Твоє фото';
    const head=question.querySelector('label');if(head)head.textContent='Що оцінити?';
    const mic=document.createElement('button'),voiceHint=document.createElement('small');
    mic.type='button';mic.className='studio-text';mic.id='mirror-review-mic';mic.innerHTML=ik('голос',17)+'<span>Сказати</span>';
    voiceHint.className='studio-voice-hint';voiceHint.setAttribute('role','status');question.append(mic,voiceHint);
    привʼязатиГолос({кнопка:mic,поле:node('оц-питання'),нота:voiceHint});
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
    const selectedKey=полеВипадкуП('сц-нагода');
    if(selectedKey)other=false;
    const own=node('mirror-choices').querySelectorAll('button');
    const options=[...own,...document.querySelectorAll('#аркуш .плитка,#пал-картка button[aria-pressed]')];
    for(const option of options){
      let selected;
      if(option.dataset.ux==='occasion'){
        selected=option.dataset.value?selectedKey===option.dataset.value:other;
        option.setAttribute('aria-pressed',String(selected));
      } else selected=option.classList.contains('вибр')||option.getAttribute('aria-pressed')==='true';
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
  function sync(){
    scheduled=false;
    const mode=режимЕкрана()||'сценарій';document.documentElement.dataset.room=mode;
    if(pageMode&&pageMode!==mode){closeExtras();setSide(mode==='сценарій'?'talk':mode==='бібліотека'?'library':'face');node('mirror-chat-status').textContent='';}
    pageMode=mode;
    move(node('сц-увага'),node('сц-увага-місце'));move(node('сц-картка'),node('сц-картка-місце'));
    if(!Екран.стан.аркуш||Екран.стан.аркуш.вузол!==node('ф-блок'))move(node('ф-блок'),node('ф-блок-місце'));
    move(node('чат-стрічка'),node('mirror-thread'));move(node('чат-ввід'),node('mirror-input'));move(node('чат-голос'),node('mirror-input'));move(node('чат-стан'),node('mirror-input'));
    move(node('сц-швидкі'),node('mirror-suggestions'));move(node('ніг-дії'),node('mirror-step-actions'));
    const inReview=mode==='оцінка'&&!extra, inCase=mode==='сценарій';
    const spreadReview=inReview&&!mobile.matches;
    const source=node('mirror-review-source');source.hidden=!spreadReview;
    if(reviewPhoto&&reviewColumns){
      if(spreadReview)move(reviewPhoto,source);
      else if(reviewPhoto.parentElement!==reviewColumns)reviewColumns.prepend(reviewPhoto);
    }
    document.documentElement.classList.toggle('mirror-review-spread',spreadReview);
    const prompt=node('mirror-occasions').querySelector('h1');
    const topic=inCase?'Куди збираємось?':inReview?'Твоє фото':mode==='профіль'?'Питання про профіль?':'Питання до стилістки?';
    if(prompt.lastChild.textContent!==topic)prompt.lastChild.textContent=topic;
    node('mirror-choices').hidden=!inCase;updateSend(inCase);placeNoteEdits();
    node('чат-поле').placeholder='Напиши стилістці…';
    node('mirror-input').hidden=inReview;node('чат-ввід').hidden=inReview;
    syncVoice();
    const empty=!hasCase();
    facePair(empty);
    node('mirror-native').hidden=!!extra;
    document.documentElement.classList.toggle('mirror-empty-case',empty);
    if(!extra){
      let title=titles[mode]||'Люстерко',controls='';
      if(mode==='сценарій'){title='Образ';if(!empty){const name=node('сц-назва')?.textContent.trim(),value=полеВипадкуП('сц-нагода');title=name&&!['Нагода','Новий сценарій'].includes(name)?name:ДОВІДНИК.нагоди.find(x=>x.ключ===value)?.підпис||'Моя нагода';}controls=button('cases','Мої нагоди','зберегти');}
      else if(mode==='бібліотека'){controls=button('closet','Мої речі','вішак');}
      else if(mode==='профіль'){controls=button('access','Доступ','', '', 'studio-text');}
      else if(mode!=='очікування'){controls=button('face','До образу','назад');}
      setHeading(title,controls);
    }
    if(mode==='очікування')progress();if(mode==='палітра')colorPair();if(mode==='образи')lookSides();
    if(mode==='бібліотека'){nativeSeals();if(window.Rack)Rack.library();}
    const last=ЧАТ_П.at(-1);
    if(last!==lastTurn&&last&&(side==='talk'||!mobile.matches)&&!inReview&&following){
      requestAnimationFrame(()=>{const letter=node('mirror-letter');letter.scrollTop=letter.scrollHeight;});
    }
    lastTurn=last;
    decorateChoices();renderPerson();navState();
  }
  function schedule(){if(!scheduled){scheduled=true;queueMicrotask(sync);}}
  function goTalk(scroll=true){
    if(!available())return;
    if(режимЕкрана()!=='сценарій'){
      if(режимЕкрана()==='очікування'&&зрізЗбиранняП().зайнято)return;
      route('сценарій',false);
    }
    setSide('talk',scroll);requestAnimationFrame(decorateChoices);
  }
  function goFace(){
    const hasLook=typeof П!=='undefined'&&П?.картки?.length;
    route(hasLook?'образи':'сценарій');
  }
  function syncVoice(){
    const native=node('чат-мікрофон'),control=node('mirror-speak'),listening=native.getAttribute('aria-pressed')==='true';
    control.setAttribute('aria-pressed',String(listening));control.disabled=native.disabled;
    control.querySelector('span').textContent=listening?'Зупинити':'Сказати';
  }
  function editWords(voice=false){
    if(!available())return;
    const review=режимЕкрана()==='оцінка'&&!extra;
    const field=node(review?'оц-питання':'чат-поле');
    if(voice){
      const mic=review?node('mirror-review-mic'):node('чат-мікрофон');
      if(mic&&!mic.hidden&&!mic.disabled&&mic.style.display!=='none'){
        mic.click();
        const status=node('mirror-speak');status.setAttribute('aria-pressed',String(mic.getAttribute('aria-pressed')==='true'));
        return;
      }
      say('Голосовий ввід недоступний у цьому браузері.');
    }
    field.focus({preventScroll:true});field.scrollIntoView?.({block:'nearest'});
  }
  function chooseOccasion(k){
    if(!available())return;
    close();
    if(режимЕкрана()!=='сценарій')return;
    other=k==='';
    прапорСценарію('рукою',true);Екран.відЖінки('нагода-обрати',k);показатиРозмову();sync();
    if(other)editWords();
  }
  function startWords(words,withPhoto=false){
    goTalk(false);const field=node('чат-поле');
    field.value=words;field.dispatchEvent(new Event('input',{bubbles:true}));
    if(withPhoto)node('чат-фото-вхід').click();else editWords();
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
    const send=node('чат-слати'),local=inCase&&localNotes();
    if(send._local===local)return;
    send._local=local;send.classList.toggle('studio-note-action',local);
    send.setAttribute('aria-label',local?'Зберегти в нагоді':'Надіслати');send.title=send.getAttribute('aria-label');
    send.innerHTML=local?ik('зберегти',16)+'<span>Зберегти</span>':ik('далі');
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
    if(b.id==='чат-слати'&&режимЕкрана()==='сценарій'&&localNotes())saveNote();else access(b.id);
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
    node('mirror-home').addEventListener('click',()=>goTalk());
    node('mirror-style').addEventListener('click',showThemes);node('mirror-person').addEventListener('click',()=>route('профіль'));
    node('чат-поле').setAttribute('aria-label','Повідомлення стилістці');node('чат-поле').placeholder='Напиши стилістці…';
    node('чат-слати').innerHTML=ik('далі');node('чат-слати').setAttribute('aria-label','Надіслати');
    if(window.ResizeObserver){
      const size=new ResizeObserver(()=>decorateChoices());size.observe(node('mirror-choices'));size.observe(node('аркуш'));
    }
    const mic=node('чат-мікрофон');
    new MutationObserver(syncVoice).observe(mic,{attributes:true,attributeFilter:['aria-pressed','disabled']});
    const letter=node('mirror-letter');
    letter.addEventListener('scroll',()=>{following=letter.scrollHeight-letter.scrollTop-letter.clientHeight<75;},{passive:true});
    let flip;looks.addEventListener('touchstart',e=>flip=e.touches[0],{passive:true});looks.addEventListener('touchend',e=>{if(!flip)return;const p=e.changedTouches[0];if(Math.abs(p.clientX-flip.clientX)>65&&Math.abs(p.clientY-flip.clientY)<40)actions.get('turn-look')();flip=null;},{passive:true});
    document.addEventListener('click',protectModel,true);
    document.addEventListener('submit',finishNote);
    document.addEventListener('keydown',e=>{if(e.target.id==='чат-поле'&&e.key==='Enter'&&!e.shiftKey&&!e.isComposing&&node('чат-поле').value.trim()){const b=node('чат-слати');if(!b.disabled){e.preventDefault();e.stopImmediatePropagation();b.click();}}},true);
    document.addEventListener('click',e=>{const b=e.target.closest('[data-ux]');if(b&&!b.disabled&&actions.has(b.dataset.ux)){actions.get(b.dataset.ux)(b.dataset.value||'',b);}});
    document.addEventListener('submit',e=>{if(e.target.matches('[data-form="access"]')){e.preventDefault();const token=new FormData(e.target).get('token').trim();if(!token)return;try{localStorage.setItem('міст:токен',token);}catch{}МІСТ_П.токен=token;close();say('Код збережено.');}});
    window.addEventListener(M.changeEvent,()=>{themeButtons();lastPhase='';schedule();window.Rack?.repaintArtwork();});
    themeButtons();sync();setSide(!available()||режимЕкрана()==='сценарій'?'talk':'face');
    Екран.малювач('дзеркало-робота',['режим','вхід','крок','запущено','панель','розмова','випадок','сценарій','профілі','поля','аркуш','збирання','образ','образи','палітра','фото','бібліотека','кошик'],schedule);
  }
  const handlers={talk:()=>goTalk(),speak:()=>editWords(true),write:()=>editWords(),face:goFace,cases:()=>route('сценарії'),assess:()=>route('оцінка'),library:()=>route('бібліотека'),profile:()=>route('профіль'),access,'edit-note':editNote,'save-note':saveNote,hand:k=>{M.set(k);close();},'close-sheet':close,occasion:chooseOccasion,
    'my-colors':personalColors,
    'body-photo':()=>{route('профіль',false);відкритиАркушПрофілю('ф-блок');},'turn-look':()=>{const el=node('mirror-look-sides');el.dataset.side=el.dataset.side==='back'?'front':'back';lookSides();},
    'take-photo':()=>startWords('Збери образ під мою річ.',true)};
  for(const [k,v] of Object.entries(handlers))actions.set(k,v);
  window.MirrorRoom={ik,escape,button,money,tone,dialog,close,route,showExtra,startWords,say,currentExtra:()=>extra,activeProfile,available,register:(k,fn)=>actions.set(k,fn),refresh:schedule};
  start();
})();
