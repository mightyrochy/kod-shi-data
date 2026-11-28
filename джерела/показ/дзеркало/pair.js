"use strict";

// The object in the centre stays in place while the conversation opens below it.
window.createMirrorPair = function(R) {
  const {node,button:b,escape:e,ik,money,tone}=R, M=window.MirrorMaterial;
  let page='mirror', modeSeen='', testing=false, caseIdentity='', pendingPage=null;
  const stages=new Set(['mirror','occasion','understood']);
  const host=node('pair-scene'), choices=node('mirror-occasions');
  const byText=id=>node(id)?.textContent.trim()||'';
  const photoURL=value=>typeof value==='string'&&/^(?:blob:|data:image\/|https?:)/i.test(value)?value:'';
  const bodyPhoto=()=>photoURL(node('ф-зріст')?.querySelector('img')?.getAttribute('src'));
  const image=(url,label,cls='')=>photoURL(url)?'<img class="'+cls+'" src="'+e(url)+'" alt="'+e(label)+'">':'';
  const action=(key,name,val='',primary=false)=>b(key,name,'',val,primary?'studio-primary':'studio-text');
  function place(el,html){
    if(el._pairMarkup===html)return;
    el._pairMarkup=html;el.innerHTML=html;
  }
  function relation(left,sign,right,cls='',name=''){
    return '<div class="pair-spread '+cls+'"><section class="pair-left">'+left+'</section><span class="pair-axis" aria-label="'+e(name||sign)+'">'+e(sign)+'</span><section class="pair-right">'+right+'</section></div>';
  }
  function person(){
    const pic=bodyPhoto();
    return '<button type="button" class="pair-image pair-person-photo" data-ux="pair-photo" aria-label="'+(pic?'Змінити фото на повний зріст':'Додати фото на повний зріст')+'">'+(pic?image(pic,'Твоє фото'):'<span class="pair-photo-add">'+ik('камера',27)+'<strong>Додати фото</strong></span>')+'</button>';
  }
  const label=(name,value)=>'<div class="pair-eyebrow">'+e(name)+'</div>'+value;
  const family=()=>[['шкіра','Шкіра'],['волосся','Волосся'],['очі','Очі']].map(([key,name])=>[tone(КОЛІР[key]),name]);
  function swatches(colors){
    return '<div class="pair-swatches">'+colors.map(([c,name])=>'<div><i'+(c?' style="background:'+c+'"':'')+'></i><span>'+e(name)+'</span></div>').join('')+'</div>';
  }
  const homeArt=new Map(), seenGarments=new Map();
  let reverseKey='',failureEvent='',testingShelf=false,openingBlind=false;
  const cardKey=(pack,pos)=>ключЗаписуОбразуП(pack)+'#'+pos;
  const measurements=()=>[['мр-зріст','Зріст'],['мр-талія','Талія']].filter(([id])=>Number(node(id)?.value)>0).map(([id,name])=>'<small>'+name+' · '+e(node(id).value)+' см</small>').join('');
  function home(){
    return '<div class="pair-start-actions">'+action(R.hasCase()?'pair-summary':'pair-occasion','Зібрати образ','',true)+action('assess','Оцінити вбрання')+'</div>'+
      '<div class="pair-shortcuts">'+b('library','Мої образи','збірка')+b('anchor','Під мою річ','вішак')+b('buy','Купити чи ні?','сумка')+b('catalog','Знайти річ','пошук')+b('closet','Мої речі','шафа')+b('compose','Зібрати вручну','плюс')+'</div>'+
      '<div class="pair-future-link">'+action('features','Можливості')+' · '+action('pair-plans','У планах')+'</div>';
  }

  function row(left,sign,right,css=''){
    return '<div class="pair-fact '+css+'"><div>'+left+'</div><i aria-hidden="true">'+e(sign)+'</i><div>'+right+'</div></div>';
  }
  const fields=[['нагода','Нагода','сц-нагода'],['місце','Місце','сц-місце'],['дрес','Ошатність','сц-дрес'],['коли','Коли й погода',''],['макіяж','Макіяж','сц-макіяж'],['прикраси','Прикраси','сц-прикраси'],['мета','Мета','сц-мета']];
  /* `#ядро=1`: «Люстерко зрозуміло» — з картки сценарію ядра (поля Ситуації, Т36), а не зі старого паспорта: її уривок
     ліворуч, назва поля праворуч; число — з одиницею, тап — підписом плитки; «Не записано» — `сказала.без_поля` */
  function coreFacts(card){
    const rows=[];
    for(const r of card.рядки||[]){
      const name=НАЗВИ_ПОЛІВ_ЯДРА_П[r.поле];if(!name)continue;
      const tile=r.джерело==='форма'?підписПлиткиЯдраП(r.поле):null;
      const value=typeof r.значення==='number'?r.значення+(ОДИНИЦІ_ЯДРА_П[r.поле]||''):tile;
      const left=r.уривок?'«'+e(r.уривок)+'»':tile?'Твій вибір':null;
      if(!left)continue;
      rows.push(row(left,'=','<small>'+e(name)+'</small>'+(value?'<strong>'+e(value)+'</strong>':'')));
    }
    for(const phrase of new Set(card.не_записано||[]))rows.push(row('«'+e(phrase)+'»','?',action('write','Уточнити словами')));
    return rows;
  }
  function structuredFacts(){
    const core=typeof картаСценаріюЯдраП==='function'?картаСценаріюЯдраП():null;
    if(core)return coreFacts(core);
    const passport=ПАСПОРТ_П;if(!passport)return [];
    const facts={...passport.картка_запиту};
    for(const [key,quote] of Object.entries(passport.цитати_полів||{})){
      if(!facts[key]&&quote&&passport[key]!=null)facts[key]={значення:passport[key],джерело:'reading',уривок:quote};
    }
    const rows=[];
    for(const [key,f] of Object.entries(facts)){
      const meta=ОПИС_ПОЛІВ_П[key];
      if(!meta||f?.значення==null||f.значення==='')continue;
      const form=ЕЛЕМЕНТИ_ПОЛІВ_П.find(x=>x.ключ===key);
      const edit=fields.find(([, ,id])=>id&&id===form?.ід);
      const name=meta.назва_картки||edit?.[1],value=значенняЗаписаногоП(meta,f.значення)||f.уривок;
      if(!name||!value)continue;
      const sure=фактНаЇїСловахП(f),quote=f.уривок?'«'+e(f.уривок)+'»':f.джерело==='hand'?'Твій вибір':sure?'Твої слова':f.джерело==='default'?'Типове значення':'Припущення';
      const ops=sure?'':'<div class="pair-inline">'+action('pair-agree','Так',key)+action('pair-remove','Прибрати',key)+'</div>';
      rows.push(row(quote,sure?'=':'?', '<small>'+e(name)+'</small><strong>'+e(value)+'</strong>'+ops,sure?'':'assumption'));
    }
    for(const phrase of рядкиЗаписаногоП(passport).незаписано)rows.push(row('«'+e(phrase)+'»','?',action('write','Уточнити словами')));
    return rows;
  }
  function occasionLabel(){
    const value=полеВипадкуП('сц-нагода');
    return ДОВІДНИК.нагоди.find(x=>x.ключ===value)?.підпис||'';
  }
  function understood(){
    const utterances=ЧАТ_П.filter(n=>n.хто==='людина'&&n.текст&&(n.тема==='сценарій'||!n.тема));
    const nativeFacts=structuredFacts();
    const selected=occasionLabel();
    let content='<div class="pair-column-titles"><span>Ти сказала</span><span>Люстерко зрозуміло</span></div>';
    if(selected&&!nativeFacts.length)content+=row('<strong>'+e(selected)+'</strong>','=',b('pair-edit',selected,'','нагода','studio-text pair-confirmed'),'key');
    if(nativeFacts.length)content+=nativeFacts.join('');
    if(utterances.length&&!nativeFacts.length){
      const note=utterances.at(-1);
      content+=row('«'+e(note.текст)+'»',note.локальна?'·':'…',note.локальна?'Збережено в нагоді':'Очікує уточнення');
    }
    if(!selected&&!utterances.length&&!nativeFacts.length)content+=row(action('pair-occasion','Обрати нагоду'),'?','Куди збираєшся?');
    const more=fields.filter(([key])=>key!=='нагода').map(([key,title])=>{
      const val=byText('зн-'+key);
      const filled=val&&!/^(—|не (обрано|вказано)|не задано|за нагодою)$/i.test(val);
      return '<button type="button" data-ux="pair-edit" data-value="'+key+'"><span>'+title+'</span><strong>'+e(filled?val:'Додати')+'</strong></button>';
    }).join('');
    const intent=[['приховати','Тихо'],['лестити','Звично'],['експресія','Помітно']].map(([key,name])=>'<button type="button" data-ux="pair-goal" data-value="'+key+'" aria-pressed="'+(полеВипадкуП('сц-мета')===key)+'">'+name+'</button>').join('');
    const status=зрізЗбиранняП().статус?.код,failed=['збій','збій_каталогу'].includes(status);
    const retry=failed?relation('Моя нагода','×','<strong>Образ не зібрано</strong>'+action('pair-build','Повторити'),'pair-failure'):'';
    return retry+'<div class="pair-understanding">'+content+'</div><div class="pair-intent" role="group" aria-label="Бажана увага">'+intent+'</div><details class="pair-conditions"><summary>Уточнити умови</summary><div>'+more+'</div>'+action('pair-future','Прогноз погоди · у планах','weather')+'</details>'+
      '<div class="pair-links">'+action('pair-palette','Барви образу')+action('pair-save-case','Зберегти нагоду')+'</div>'+
      '<div class="pair-actions">'+action('pair-build','Так, збирай','',true)+action('compose','Зібрати вручну')+'</div>';
  }
  function stage(name){
    if(!stages.has(name)||!R.available())return;
    pendingPage=name;R.route('сценарій',false);if(режимЕкрана()!=='сценарій'){pendingPage=null;return;}page=name;pendingPage=null;R.closeDrawer();
    render('сценарій','');node('mirror-work').scrollTop=0;
  }
  function openEdit(key){
    if(!fields.some(([k])=>k===key))return;
    const native=document.querySelector('[data-редактор="ред-'+key+'"]');
    if(native)native.click();
  }
  function factDecision(key,keep){
    const fact=ПАСПОРТ_П?.картка_запиту?.[key];if(!fact)return;
    const binding=ЕЛЕМЕНТИ_ПОЛІВ_П.find(x=>x.ключ===key&&x.ід&&node(x.ід));
    if(binding){записатиПолеВипадкуП(binding.ід,keep?fact.значення:'');рукаТоркнуласьП(binding.ід);поляЗміненоП();}
    подіяРукиП(key,keep?fact.значення:null);показатиСценарій();зберегтиВипадок();R.refresh();
  }
  function nativePalette(){
    const host=node('mirror-my-colors');if(!host)return;
    const bar=node('пал-стрічка'),strip=bar?.querySelector('.стрічка'),caption=bar?.querySelector('.стрічка-підпис')?.textContent||'';
    const chosen=!!strip?.querySelector('i[style]');
    const note=chosen||strip?.classList.contains('очікує-тону')?'<small>'+e(caption)+'</small>':'<span>Ще не обрано</span>';
    place(host,relation(label('Твої барви',swatches(family())+action('my-colors','Виправити')),'·',label('Барви образу',(chosen?strip.outerHTML:'')+note),'pair-palette')+'<div class="pair-actions">'+(chosen?action('pair-build','Зібрати з цими','',true):action('my-colors','Додати барви'))+action('pair-summary','Моя нагода')+'</div>');
  }
  let reveal=null, pendingBuild=null, buildStarted=0, buildExpected=180;
  const fittingAttempts=new WeakSet();
  const automaticFittingCard=c=>c&&!c.збій&&c.речі?.length&&(String(c.рука)==='1'||!c.рука);
  function waitView(){
    const s=зрізЗбиранняП(),failed=s.готово&&!s.успіх;
    const target=node('mirror-making');if(!target)return;
    place(target,failed?'<div class="pair-making-art">'+M.error()+'</div>':'<div class="pair-making-art" data-reveal-art aria-label="Збираю образ"></div>');
  }
  // Controller after rendering: a fresh collection gets one fitting, never all experimental hands.
  function advance(mode,extra){
    const s=зрізЗбиранняП();
    if(mode==='очікування'&&s.є&&!s.готово){
      pendingBuild=Number(s.почато)||Date.now();buildStarted=pendingBuild;buildExpected=Number(s.минулий_с)||180;
    }
    if(mode==='образи'&&!extra&&pendingBuild&&!testing){
      const pack=typeof П!=='undefined'?П:null;
      const index=(pack?.картки||[]).findIndex(automaticFittingCard);
      const card=pack?.картки?.[index];
      if(card){
        pendingBuild=null;
        if(!кадрПоказуП(card)&&!fittingAttempts.has(card)&&!показПриміркиП(index).іде){
          fittingAttempts.add(card);void приміряти(index);
        }
      }
    }else if(!['очікування','образи'].includes(mode)){pendingBuild=null;}
    const art=!extra&&(mode==='очікування'?node('mirror-making'):mode==='образи'?node('mirror-look-sides'):null)?.querySelector('[data-reveal-art]');
    if(reveal&&(reveal.host!==art||reveal.theme!==M.get())){reveal.stop();reveal=null;}
    if(art&&!reveal){
      const start=Number(art.dataset.started)||buildStarted||Date.now();
      reveal=M.reveal(art,{startedAt:start,expectedSeconds:buildExpected});
    }
  }
  function pieceImage(p,j,cls=''){
    return '<img class="'+cls+'" data-pair-piece-photo="'+j+'" alt="'+e(p.назва||'Річ')+'">';
  }
  function bindPiecePhotos(root,pieces,card){
    root.querySelectorAll('[data-pair-piece-photo]').forEach(img=>{
      const p=pieces[Number(img.dataset.pairPiecePhoto)];if(!p)return;
      підставитиКадр(img,p,()=>{const text=document.createElement('span');text.textContent=p.назва||'Фото недоступне';img.replaceWith(text);},відхиленняКадруРечі(card,p));
    });
  }
  function nativeVariants(){
    const target=node('mirror-look-sides');
    if(!target)return;
    const i=Екран.стан.образ.поз,c=П?.картки?.[i];
    document.documentElement.dataset.pairLooks=testing?'blind':'product';
    // Відмова вже має напис на цій позиції в горталці.
    target.hidden=!c||!!c.збій;
    if(target.hidden)return;
    const fitted=photoURL(кадрПоказуП(c)),pieces=речіДляПоказуП(c),key=cardKey(П,i);
    const кадрРечі=p=>кадриРечі(p,відхиленняКадруРечі(c,p)).find(photoURL);
    const tiles=pieces.map((p,j)=>'<button type="button" data-ux="pair-piece" data-value="'+i+'|'+j+'" aria-label="'+e(p.назва||'Річ')+'">'+pieceImage(p,j)+'</button>').join('');
    const fitState=показПриміркиП(i),fitMessage=node('прм-'+i)?.textContent||'';
    const fitting=fitState.іде||(!testing&&pendingBuild&&automaticFittingCard(c));
    const picture=fitted?'<div class="pair-image pair-fitted">'+image(fitted,'Приміряний образ')+'</div>':
      '<div class="pair-fitting-placeholder">'+(fitting?'<div class="pair-making-art" data-reveal-art data-started="'+(buildStarted||fitState.почато||Date.now())+'"></div><p role="status">Приміряю образ…</p>':
        '<p>'+(e(fitMessage)||'Примірка ще не готова')+'</p>'+action(fitState.код==='нема_фото'&&!bodyPhoto()?'pair-photo':'pair-fit',fitState.код==='нема_фото'&&!bodyPhoto()?'Додати фото':'Приміряти образ',String(i),true))+'</div>';
    const colors=pieces.map(x=>tone(x.hex)).filter(Boolean),worn=!!window.Rack?.nativeWorn(key);
    const entry=БІБЛІОТЕКА_П.плитки.find(x=>x.ід===key),group=entry&&БІБЛІОТЕКА_П.групи.find(g=>g.плитки?.some(x=>x.ід===key));
    let spread='<section class="pair-result-hero">'+picture+'</section>';
    if(reverseKey===key){
      const keyArt=[M.get(),key,colors,worn].join('/');
      if(target._stampKey!==keyArt){target._stampKey=keyArt;target._stamp=M.seal(colors,worn,76);}
      const meta=[group?.нагода,entry?.дата].filter(Boolean).map(t=>'<small>'+e(t)+'</small>').join('');
      spread='<section class="pair-result-record">'+target._stamp+meta+(worn?'<strong>Вдягала</strong>':'')+action('pair-worn',worn?'Зняти позначку':'Вдягала',key)+'</section>';
    }
    const stampButton=action('pair-reverse',reverseKey===key?'До образу':'Зворот',String(i));
    let recent='';
    const cacheKey=АКТИВНИЙ+'/'+key+'/',saved=seenGarments;
    pieces.forEach(p=>saved.set(cacheKey+p.id,{...p,фото:кадрРечі(p),фото_усі:[]}));
    const swap=(c.етапи?.заміни||[]).filter(x=>x.нова).at(-1);
    if(swap){
      const old=saved.get(cacheKey+swap.ід),next=pieces.find(p=>p.id===swap.нова);
      if(old===undefined&&String(swap.ід).includes('@')){
        saved.set(cacheKey+swap.ід,null);
        MirrorIndex.get(swap.ід).then(p=>{if(p){saved.set(cacheKey+swap.ід,{id:swap.ід,назва:p.name,фото:p.image,ціна:p.price});R.refresh();}}).catch(()=>{});
      }
      if(next&&old)recent=relation(label('Була',itemPreview(old)),'→',label('Тепер',itemPreview(next)),'pair-replacement');
    }
    function itemPreview(p){return image(кадрРечі(p),p.назва||'Річ','pair-swap-photo')+'<strong>'+e(p.назва||'Річ')+'</strong>'+(typeof p.ціна==='number'?'<small>'+e(money(p.ціна))+'</small>':'');}
    const itemRows=pieces.map((p,j)=>{
      const shop=/^https?:\/\//i.test(p.урл||'')?'<a class="studio-link" href="'+e(p.урл)+'" target="_blank" rel="noopener noreferrer">До крамниці</a>':'';
      const replace=node('замін-'+i+'-'+j);
      const native=node('к-'+i)?.querySelectorAll('.список>.річ .н')[j]?.innerHTML;
      return pieceImage(p,j,'pair-swap-photo')+(native||((typeof p.ціна==='number'?'<small>'+e(money(p.ціна))+'</small>':'')+shop))+(!testing?'<div class="pair-inline">'+(replace?action('pair-native-replace','Не ця · замінити',i+'|'+j):'')+action('pair-own-piece','Маю свою',i+'|'+j)+'</div>':'');
    });
    target._itemDetails=itemRows;target._pieces=pieces;target._card=c;
    const signature=[key,testing,M.get(),worn,reverseKey,recent,itemRows,picture,tiles,JSON.stringify(pieces.map(p=>кадриРечі(p,відхиленняКадруРечі(c,p)))),bodyPhoto(),entry?.дата,group?.нагода].join('·');
    if(target._renderKey===signature)return;target._renderKey=signature;
    place(target,spread+stampButton+recent+'<div class="pair-outfit-grid pair-reverse-pieces" aria-label="Речі образу">'+tiles+'</div>'+
      (testing?action('pair-result','До мого образу'):''));
    bindPiecePhotos(target,pieces,c);
  }
  function showProduct(){
    testing=false;R.route('образи');
  }
  function blind(){
    if(typeof П!=='undefined'&&П?.картки?.length){testing=true;R.route('образи');nativeVariants();return;}
    R.route('бібліотека');testingShelf=true;R.refresh();
  }
  function render(mode,extra){
    if(modeSeen!==mode){if(mode==='сценарій')page=pendingPage||(R.hasCase()?'understood':'mirror');modeSeen=mode;}
    const identity=(typeof АКТИВНИЙ==='string'?АКТИВНИЙ:'')+'/'+(СЦ?.ід||'');
    if(identity!==caseIdentity){caseIdentity=identity;if(!pendingPage&&mode==='сценарій')page=R.hasCase()?'understood':'mirror';}
    const status=зрізЗбиранняП().статус||{};
    if(mode==='сценарій'&&!pendingPage&&['збій','збій_каталогу'].includes(status.код)){
      const sig=status.код+'/'+status.подій;if(failureEvent!==sig){failureEvent=sig;page='understood';}
    }
    if(mode==='образи'&&openingBlind){testing=true;openingBlind=false;}
    if(mode!=='образи'){testing=false;reverseKey='';}
    if(mode!=='бібліотека')testingShelf=false;
    const inCase=mode==='сценарій'&&!extra;
    document.documentElement.dataset.pairPage=extra||(inCase?page:mode);
    choices.hidden=!inCase||page!=='occasion';host.hidden=!inCase;
    node('pair-chat-welcome').hidden=!inCase||page!=='mirror'||ЧАТ_П.length>0;
    const finish=node('pair-profile-finish');
    const profile=!extra&&(mode==='профіль'||mode==='старт')?зрізПрофіляП():null;
    finish.hidden=!profile||profile.профілі.створено;
    if(!finish.hidden){
      const missing=бракПрофілюП(profile).map(item=>item.назва);
      const hint=node('pair-profile-missing');
      const message=missing.length?'Ще треба: '+missing.join(', ')+'.':'';
      if(hint.textContent!==message)текстЖінціП(hint,message);
    }
    if(inCase){
      const title=page==='understood'?'Моя нагода':page==='occasion'?'Куди збираємось?':'';
      node('mirror-heading').hidden=!title;
      if(title)R.heading(title,action('pair-home','До люстерка'));
      place(host,page==='mirror'?home():page==='understood'?understood():'');
      if(page==='occasion')place(node('pair-case-next'),action('pair-summary','До умов нагоди','',true)+action('write','Сказати своїми словами'));
    }else {
      node('mirror-heading').hidden=false;
      if(mode==='бібліотека'&&testingShelf&&!extra){
        R.heading('Сліпий перегляд',action('library','Мої образи'));host.hidden=false;
        place(host,(БІБЛІОТЕКА_П.плитки.length?'':'<p>Ще немає образів для перегляду.</p>')+action('pair-occasion','Зібрати для нагоди')+' '+action('pair-future','Кабінет тестувальниці · у планах','tester'));
      }
      if(mode==='профіль'&&!extra){
        host.hidden=false;
        const name=node('пр-імʼя')?.value||'Як до тебе звертатися?';
        const portrait=photoURL(node('ф-портрет')?.querySelector('img')?.getAttribute('src'));
        place(host,'<div class="pair-profile-intro"><button type="button" class="studio-text" data-ux="pair-name">'+e(name)+'</button>'+relation(label('Портрет','<button type="button" class="pair-image" data-ux="pair-photos">'+(portrait?image(portrait,'Портрет'):ik('камера',27)+' Додати портрет')+'</button>'),'',label('На повний зріст',person()),'pair-profile')+'</div>');
      }
    }
    if(!extra&&mode==='образи')nativeVariants();else delete document.documentElement.dataset.pairLooks;
    if(!extra&&mode==='палітра')nativePalette();
    if(!extra&&mode==='очікування')waitView();
    node('mirror-native').hidden=!!extra;
    node('pair-latest').textContent='Запитай';
  }
  const live=[
    ['Образ',[['pair-occasion','Зібрати для нагоди'],['pair-summary','Умови нагоди'],['pair-palette','Барви образу'],['compose','Два варіанти вручну'],['assess','Оцінити моє вбрання'],['anchor','Підібрати під мою річ']]],
    ['Речі',[['catalog','Знайти річ у крамницях'],['buy','Купити чи ні?'],['closet','Мої речі']]],
    ['Моє',[['library','Мої образи та приміряння'],['cases','Мої нагоди'],['profile','Профіль і фото'],['pair-measures','Мої мірки'],['my-colors','Мої барви'],['pair-drape','Що мені до лиця']]],
    ['Розмова',[['write','Написати або надиктувати'],['access','Доступ до стилістки']]],
    ['Тестування',[['pair-test','Сліпий перегляд і відгуки']]]
  ];
  const planned=[
    ['wardrobe','Виділити речі з фото','Моє фото','Речі до гардероба','Підтвердити окремі речі з фотографії перед додаванням.'],
    ['closet-search','Пошук у моїх речах','Мій опис','Річ із гардероба','Знайти власну річ за описом у розмові.'],
    ['conversation','Дії в розмові','Мої слова','Дія у Люстерку','Поповнювати гардероб і завершувати вибір у шухляді розмови.'],
    ['two','Два образи від стилістки','Як просила','На крок сміливіше','Порівняти два добори від стилістки для однієї нагоди.'],
    ['weather','Прогноз для нагоди','Де й коли','Прогноз','Підставити прогноз для місця події та уточнити його.'],
    ['photo-buy','Порівняння двох фото перед покупкою','Перша річ','Друга річ','Порівняти дві покупки за фото з урахуванням мірок і барв.'],
    ['tester','Кабінет тестувальниці','Анонімні образи','Звіт','Зібрати сліпі оцінки та звіти в окремому кабінеті.'],
    ['stores','Точніші дані крамниць','Варіант товару','Його фото й характеристики','Показувати фото та відомості саме про вибраний варіант, коли їх передає крамниця.'],
    ['offline','Застосунок без мережі','Мої дані','На пристрої','Окремий застосунок для телефона й комп’ютера.']
  ];
  function tools(plansOnly=false){
    let all='';
    if(!plansOnly)all=live.map(([name,items])=>'<section class="pair-feature-group"><h2>'+name+'</h2>'+items.map(([key,title])=>action(key,title)).join('')+'</section>').join('');
    const next='<section class="pair-feature-group planned"><h2>У планах</h2>'+planned.map(([key,name])=>b('pair-future',name,'',key,'studio-text')).join('')+'</section>';
    R.showExtra(plansOnly?'plans':'features',plansOnly?'Майбутні можливості':'Можливості',all+next,action('pair-home','До люстерка'));
  }
  function future(key){
    const f=planned.find(t=>t[0]===key);if(!f)return;
    R.dialog(f[1],'<p class="pair-plan-status">У планах</p>'+relation(e(f[2]),'·',e(f[3]),'pair-plan')+'<p>'+e(f[4])+'</p>');
  }
  function photo(){const field=node('ф-зріст')?.querySelector('input[type=file]');if(field)field.click();else{R.route('профіль',false);відкритиАркушПрофілю('ф-блок');}}
  function afterOccasion(key){if(!key)R.openDrawer(true);}
  const handlers={'pair-profile-done':async()=>{if(await завершитиОнбординг())stage('mirror');else відкритиБракПрофілюП();},'pair-name':()=>відкритиАркушПрофілю('проф-блок'),'pair-photos':()=>відкритиАркушПрофілю('ф-блок'),'pair-home':()=>stage('mirror'),'pair-occasion':()=>stage('occasion'),'pair-summary':()=>stage('understood'),'pair-photo':photo,'pair-edit':openEdit,'pair-save-case':()=>node('сц-зберегти').click(),
    'pair-build':()=>{if(режимЕкрана()!=='сценарій')stage('understood');Екран.відЖінки('розуміння-так');node('зб-зібрати').click();},'pair-palette':()=>R.route('палітра'),'pair-agree':k=>factDecision(k,true),'pair-remove':k=>factDecision(k,false),
    'pair-result':showProduct,
    'pair-reverse':pos=>{if(!П?.картки?.[Number(pos)])return;const key=cardKey(П,Number(pos));reverseKey=reverseKey===key?'':key;nativeVariants();},
    'pair-worn':async key=>{if(window.Rack)await Rack.toggleNativeWorn(key);R.refresh();},
    'pair-fit':value=>{const i=Number(value);if(П?.картки?.[i])void приміряти(i);},
    'pair-piece':value=>{const [i,j]=value.split('|').map(Number),host=node('mirror-look-sides'),p=host._pieces?.[j],html=host._itemDetails?.[j];if(П?.картки?.[i]!==host._card||!p||!html)return;R.dialog(p.назва||'Річ','<div class="pair-piece-detail">'+html+'</div>');bindPiecePhotos(node('mirror-sheet-content'),host._pieces,host._card);},
    'pair-native-replace':value=>{R.close();const [i,j]=value.split('|');node('замін-'+i+'-'+j)?.click();},
    'pair-own-piece':value=>{R.close();window.Rack?.substituteNative(value);},'pair-test':blind,'pair-goal':key=>{Екран.відЖінки('мета-обрати',key);R.refresh();},
    'pair-measures':()=>{R.route('профіль',false);відкритиАркушПрофілю('мір-блок');},'pair-drape':()=>{R.route('профіль',false);відкритиАркушПрофілю('др-блок');},features:()=>tools(false),'pair-plans':()=>tools(true),'pair-future':future};
  const dailyShelf=()=>{testingShelf=false;R.route('бібліотека');};
  document.addEventListener('click',event=>{if(event.target.closest('.біб-образ'))openingBlind=testingShelf;},true);
  return {render,advance,dailyShelf,blindShelf:()=>testingShelf,afterOccasion,stage,handlers,person,relation,bodyPhoto,occasionLabel,swatches,tools};
};
