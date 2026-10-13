// 4941: функціональний вимір штатної збірки; записи архівні/синтетичні, API=0.
const fs=require('fs'),path=require('path'),assert=require('assert'),{chromium}=require('playwright');
(async()=>{
 const base=process.cwd(),stage=process.argv[2],out=path.join(base,'.qa4941',stage);
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 const all=[],errors=[],blocked=[];
 try{
  for(const scene of ['ручний608','ручнийпорожній','паспортдовгий','звичайний','нічний','повнийпрофіль','профіль']){
   const page=await browser.newPage({viewport:{width:390,height:844},hasTouch:true,isMobile:true,reducedMotion:'reduce'});
   page.on('pageerror',e=>errors.push(String(e)));
   await page.route('**/*',r=>{
    const u=new URL(r.request().url()),name=decodeURIComponent(u.pathname).slice(1);
    let file='';
    if(u.hostname==='probe.invalid') file=name.startsWith('шрифти/')?path.join('/workspace/kod-shi-data',name):path.join(out,name||'index.html');
    else if(u.href.includes('/pyodide/')) file=path.join(base,'.qa4941/pyodide',path.basename(name));
    else if(u.href.includes('/Fixel@main/fonts/webfonts/')) file=path.join(base,'.qa4941/fonts',path.basename(name));
    if(file&&fs.existsSync(file)) return r.fulfill({path:file});
    blocked.push(u.hostname+u.pathname);return r.abort();
   });
   await page.goto('https://probe.invalid/');
   await page.waitForFunction(()=>typeof document.getElementById('сц-рукою-показати').onclick==='function');
   for(const id of ['е-лице','е-мірки','е-випадок']){
    await page.locator('#н-далі').tap(); await page.waitForFunction(id=>document.getElementById(id).style.display==='block',id);
   }
   await page.evaluate(()=>document.fonts.ready);
   if(scene==='профіль'){
    await page.locator('#пф-кнопка').tap();
   }else{
    await page.locator('#сц-рукою-показати').tap();
    await page.evaluate(scene=>{
     закритиАркуш();
     if(scene==='ручний608'){
      ПОРОЖНІ_ВІДКРИТО_П=true;
      $('сц-нагода').value=ДОВІДНИК.нагоди.filter(x=>x.плитка).at(-1).ключ;
      $('сц-місце').selectedIndex=$('сц-місце').options.length-1;
      $('сц-макіяж').value='яскравий';$('сц-прикраси').value='етно';$('сц-мета').value='приховати';
      ['сц-година','сц-темп'].forEach(id=>ТИПОВІ_НЕ_РУКОЮ_П.delete(id));
      $('сц-година').value='19';$('сц-темп').value='-5';$('сц-опади').value='можливий_дощ';$('сц-вітер').value='2';$('сц-реагенти').value='1';
     }else if(scene==='паспортдовгий'){
      const місце=ДОВІДНИК.місця.find(x=>!x.плитка&&x.слова).ключ; ПАСПОРТ_П={джерело:'модель',нагода:'робота',місце,місце_слова:'Зустріч із колегами у просторому залі офісу перед довгою вечірньою прогулянкою містом',година:19,темп_c:-5,макіяж:'яскравий',прикраси:'етно',мета:'приховати',джерело_полів:{місце:'розмова',година:'розмова',темп_c:'розмова'}};
      застосуватиПаспортДоЕкрана(ПАСПОРТ_П);
     }else if((scene==='звичайний'||scene==='нічний'||scene==='повнийпрофіль')){
      $('сц-нагода').value='робота';$('сц-місце').value='офіс';
     }
     if(scene==='повнийпрофіль'){КОЛІР={шкіра:'#edc4ad',волосся:'#66412f',очі:'#6f7858'};for(const [id,v] of [['мр-зріст',168],['мр-плечі',98],['мр-груди',92],['мр-талія',74],['мр-стегна',99]])$(id).value=v;}
     малюватиЧатП();
    },scene);
   }
   if(scene==='нічний') await page.locator('#тема-кнопка').tap();
   await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
   const facts=await page.evaluate(()=>{
    const rect=id=>$(id).getBoundingClientRect().toJSON(),btn=$('зб-зібрати'),b=rect('зб-зібрати');
    const points=[[b.x+b.width/2,b.y+b.height/2],[b.x+15,b.y+15],[b.right-15,b.bottom-15]];
    return {scroll:{window:scrollY,card:$('сц-картка').scrollTop},card:rect('сц-картка'),button:b,panel:rect('ніг'),hit:points.map(([x,y])=>document.elementFromPoint(x,y)?.closest('#зб-зібрати')===btn),rows:[...document.querySelectorAll('#сц-картка>.ряд-паспорта')].filter(x=>!x.hidden).map(x=>x.innerText),colors:{bg:getComputedStyle(btn).backgroundColor,image:getComputedStyle(btn).backgroundImage,fg:getComputedStyle(btn).color},mode:РЕЖИМ};
   });
   facts.scene=scene;
   await page.screenshot({path:path.join(out,scene+'.png')});
   if(scene!=='профіль'){
    assert.equal(facts.scroll.window,0);assert.equal(facts.scroll.card,0);
    if(stage==='after'){
     assert(facts.button.bottom<=facts.panel.top&&facts.button.top>=0,scene+' button behind panel');assert(facts.hit.every(Boolean),scene+' hit');
     await page.evaluate(()=>{window.clicked4941=0;$('зб-зібрати').addEventListener('click',e=>{if(e.isTrusted)window.clicked4941++;});});
     await page.touchscreen.tap(facts.button.x+facts.button.width/2,facts.button.y+facts.button.height/2);
     await page.waitForFunction(()=>window.clicked4941===1&&document.getElementById('зб-статус').textContent.length>0);
     facts.tap=await page.evaluate(()=>({trusted:window.clicked4941,status:$('зб-статус').textContent,scroll:scrollY,card:$('сц-картка').scrollTop}));
     assert.equal(facts.tap.scroll,0);assert.equal(facts.tap.card,0);
     await page.screenshot({path:path.join(out,scene+'-тап.png')});
     // Справжній Tab: кнопка отримує фокус без примусових focus()/прокрутки.
     await page.keyboard.press('Tab');await page.keyboard.press('Shift+Tab');
     facts.focus=await page.evaluate(()=>({id:document.activeElement.id,scroll:scrollY,outline:getComputedStyle(document.activeElement).outline}));
     assert.equal(facts.focus.id,'зб-зібрати');assert.equal(facts.focus.scroll,0);
     await page.screenshot({path:path.join(out,scene+'-фокус.png')});
    }
   }
   all.push(facts);console.log(JSON.stringify(facts));await page.close();
  }
 }finally{await browser.close();fs.writeFileSync(path.join(out,'facts.json'),JSON.stringify({all,errors,blocked},null,2));}
 assert.equal(errors.length,0);
})().catch(e=>{console.error(e);process.exitCode=1});
