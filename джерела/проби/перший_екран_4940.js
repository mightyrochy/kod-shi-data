/* 4940/4941: справжній Chromium, зібрана сторінка, 390×844; мережа й моделі вимкнені.
   node проби/перший_екран_4940.js <html> <ДО|ПІСЛЯ>; знімки в аудит/знімки_4940/. */
const fs = require('fs'), path = require('path'), {chromium} = require('playwright');
const { чекатиСтан } = require('./очікування.js');
(async()=>{
  const б = await chromium.launch({executablePath:process.env.CHROMIUM || '/usr/bin/chromium', args:['--no-sandbox']});
  try{
    const с = await б.newPage({viewport:{width:390,height:844}, reducedMotion:'reduce'}), етап = process.argv[3];
    const html = fs.readFileSync(process.argv[2], 'utf8').replace(/<script[^>]*src="https:[^>]*><\/script>/g, '');
    await с.route('**/*', р=>{ const u = new URL(р.request().url());
      if(u.href === 'https://probe.invalid/') return р.fulfill({contentType:'text/html', body:html});
      const файл = u.pathname.startsWith('/шрифти/') || decodeURI(u.pathname).startsWith('/шрифти/')
        ? path.resolve(__dirname, '../..', decodeURI(u.pathname).slice(1))
        : process.env.FONTS && u.hostname === 'cdn.jsdelivr.net' ? path.join(process.env.FONTS, path.basename(u.pathname)) : '';
      return файл && fs.existsSync(файл) ? р.fulfill({path:файл}) : р.abort(); });
    await с.goto('https://probe.invalid/');
    await чекатиСтан(с, 'кнопка сц-рукою-показати готова', () => typeof document.getElementById('сц-рукою-показати').onclick === 'function');
    for(const ід of ['е-лице','е-мірки','е-випадок']){
      await с.locator('#н-далі').click(); await чекатиСтан(с, 'показ кроку знайомства ' + ід, ід => document.getElementById(ід).style.display === 'block', ід); }
    await с.evaluate(()=>document.fonts.ready);
    const тека = path.resolve(__dirname, '../../аудит/знімки_4940'); fs.mkdirSync(тека, {recursive:true});
    await с.screenshot({path:path.join(тека, етап + '_4940_профіль.png')});
    const профіль = await с.evaluate(()=>({текст: $('сц-увага').textContent, верх: $('сц-увага').getBoundingClientRect().top,
      низ: $('сц-увага').getBoundingClientRect().bottom, панель: $('ніг').getBoundingClientRect().top}));
    await с.locator('#сц-рукою-показати').click();
    await с.evaluate(()=>{ закритиАркуш(); ПОРОЖНІ_ВІДКРИТО_П = true;
      $('сц-нагода').value = ДОВІДНИК.нагоди.filter(x=>x.плитка).at(-1).ключ;
      $('сц-місце').selectedIndex = $('сц-місце').options.length - 1;
      $('сц-макіяж').value = 'яскравий'; $('сц-прикраси').value = 'етно'; $('сц-мета').value = 'приховати';
      ['сц-година','сц-темп'].forEach(і=>ТИПОВІ_НЕ_РУКОЮ_П.delete(і)); $('сц-година').value = '19';
      $('сц-темп').value = '-5'; $('сц-опади').value = 'можливий_дощ';
      $('сц-вітер').value = '2'; $('сц-реагенти').value = '1'; малюватиЧатП(); });
    const безПрокрутки = await с.evaluate(()=>({кнопка:$('зб-зібрати').getBoundingClientRect().toJSON(), панель:$('ніг').getBoundingClientRect().top}));
    await с.screenshot({path:path.join(тека, етап + '_4941_ручний_верх.png')});
    await с.mouse.move(10, 200); await с.mouse.wheel(0, 844);
    await чекатиСтан(с, 'кнопка зб-зібрати вище панелі ніг', () => { const к = document.getElementById('зб-зібрати').getBoundingClientRect(), п = document.getElementById('ніг').getBoundingClientRect(); return к.bottom <= п.top; });
    await с.locator('#зб-зібрати').click({trial:true});
    await с.screenshot({path:path.join(тека, етап + '_4941_ручний.png')});
    const ручний = await с.evaluate(()=>({картка: $('сц-картка').offsetHeight, кнопка: $('зб-зібрати').getBoundingClientRect().toJSON(), панель: $('ніг').getBoundingClientRect().top}));
    console.log(JSON.stringify({етап, профіль, безПрокрутки, ручний}, null, 2));
    if(профіль.верх<0 || профіль.низ>профіль.панель) throw Error('profile_action_below_panel');
    if(етап === 'ПІСЛЯ' && !профіль.текст.includes('допоможуть підібрати образи')) throw Error('profile_benefit_missing');
  }finally{await б.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
