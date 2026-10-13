const fs = require('fs'), path = require('path'), assert = require('assert');
const {chromium} = require('playwright');
const out = __dirname, repo = '/workspace/scratch/qa-batch-next/repo';
const fixture = JSON.parse(fs.readFileSync('/workspace/scratch/liusterko-4943/.qa4943/fixture.json'));
(async () => {
  const browser = await chromium.launch({executablePath: '/usr/bin/chromium', args: ['--no-sandbox']});
  const result = {head: '31257c15337a12f5f08a4cd72b1548adf3afdb70', viewport: [390, 844],
    chromium: browser.version(), apiLive: 0, fixture: {kind: fixture.kind, source: fixture.source,
      source_sha256: fixture.source_sha256}, errors: [], targets: [], contrast: [], focus: [], states: [], layout: []};
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true});
    page.setDefaultTimeout(5000);
    page.on('pageerror', error => result.errors.push(String(error)));
    await page.route('**/*', async route => {
      const u = new URL(route.request().url()), p = decodeURIComponent(u.pathname);
      let file = null;
      if (u.hostname === 'batch1005.local') file = p.startsWith('/шрифти/') ? path.join(repo, p) : path.join(out, p === '/' ? 'index.html' : p);
      else if (u.href.includes('/pyodide/')) file = path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide', path.basename(p));
      else if (u.href.includes('/Fixel@main/fonts/webfonts/')) file = path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts', path.basename(p));
      if (file && fs.existsSync(file)) await route.fulfill({path: file});
      else await route.abort();
    });
    await page.goto('http://batch1005.local');
    await page.waitForFunction(() => typeof document.getElementById('сц-рукою-показати').onclick === 'function', null, {timeout: 30000});
    await page.evaluate(() => document.fonts.ready); await page.waitForTimeout(650);
    await page.evaluate(()=>{window.qaChat=document.getElementById('чат-поле');window.qaChatMoves=[];new MutationObserver(ms=>{for(const m of ms)for(const n of m.removedNodes)if(n===window.qaChat||n.contains?.(window.qaChat))window.qaChatMoves.push({target:m.target.id,node:n.id});}).observe(document.body,{childList:true,subtree:true});});
    const target = async selector => {
      await page.locator(selector).first().evaluate(e => {if(e.type==='file'&&getComputedStyle(e).opacity==='0')e=e.closest('label')||e;e.scrollIntoView({block:'center'});});
      await page.waitForTimeout(80);
      const item = await page.locator(selector).first().evaluate(e => {
        if(e.type==='file'&&getComputedStyle(e).opacity==='0')e=e.closest('label')||e;
        const box=e.getBoundingClientRect(), cs=getComputedStyle(e);
        const hits=[[-11,-11],[11,-11],[-11,11],[11,11],[0,0]].map(([dx,dy])=>{const found=document.elementFromPoint(box.x+box.width/2+dx,box.y+box.height/2+dy);return found===e||e.contains(found);});
        return {id:e.id,width:box.width,height:box.height,hits,clip:cs.clipPath};
      });
      result.targets.push({selector,...item});
      assert(item.width>=24 && item.height>=24, selector+' розмір'); assert(item.hits.every(Boolean), selector+' точки влучання');
    };
    const contrast = async (selector,pseudo=null) => {
      const item=await page.locator(selector).first().evaluate((e,pseudo)=>{
        const rgb=c=>c.match(/[\d.]+/g).map(Number), mix=(a,b,alpha)=>a.slice(0,3).map((v,i)=>v*alpha+b[i]*(1-alpha));
        const lum=a=>a.map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4}).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
        let chain=[], bg=[255,255,255], opacity=1;for(let n=e;n;n=n.parentElement)chain.unshift(n);
        for(const n of chain){const cs=getComputedStyle(n),c=rgb(cs.backgroundColor);bg=mix(c,bg,c[3]??1);opacity*=+cs.opacity;}
        const cs=getComputedStyle(e,pseudo),fg=rgb(cs.color);if(pseudo)opacity*=+cs.opacity;
        const effective=mix(fg,bg,opacity*(fg[3]??1)),a=lum(effective),b=lum(bg);
        return {foreground:effective,background:bg,opacity,ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
      },pseudo);
      result.contrast.push({selector,pseudo,...item}); assert(item.ratio>=4.5,selector+' контраст');
    };
    const screenshot = async name => {
      await page.waitForTimeout(450);
      const layout=await page.evaluate(()=>({viewport:innerWidth,scroll:document.documentElement.scrollWidth}));
      result.layout.push({name,...layout}); assert.equal(layout.viewport,390);assert.equal(layout.scroll,390);
      await page.screenshot({path:path.join(out,name+'.png')});
    };
    const focus=async selector=>{
      await page.keyboard.press('Tab');await page.locator(selector).focus();
      result.focus.push({selector,...await page.locator(selector).evaluate(e=>({active:document.activeElement===e,focusVisible:e.matches(':focus-visible'),outline:getComputedStyle(e).outline,boxShadow:getComputedStyle(e).boxShadow}))});
    };
    await target('#тема-кнопка');await target('#пр-згода');await target('#кол-блок details summary');
    await screenshot('профіль');
    console.log('beforeScenario',await page.evaluate(()=>({chat:!!document.getElementById('чат-поле'),parent:document.getElementById('чат-ввід')?.parentElement?.id,mode:РЕЖИМ})));
    console.log('afterScenario',await page.evaluate(()=>{ПРОФІЛЬ_СТВОРЕНО=true;режим('сценарій');const before=!!document.getElementById('чат-поле');ПАСПОРТ_П={джерело:'модель',нагода:'робота',місце:'офіс',джерело_полів:{}};застосуватиПаспортДоЕкрана(ПАСПОРТ_П);return {before,chat:!!document.getElementById('чат-поле'),parent:document.getElementById('чат-ввід')?.parentElement?.id,mode:РЕЖИМ};}));
    await page.waitForTimeout(600);
    console.log('settledScenario',await page.evaluate(()=>({chat:!!document.getElementById('чат-поле'),attached:qaChat.isConnected,parents:[qaChat.parentNode?.id,qaChat.parentNode?.parentNode?.id,qaChat.parentNode?.parentNode?.parentNode?.id],moves:qaChatMoves,mode:РЕЖИМ,url:location.href})),result.errors);
    await contrast('#чат-поле','::placeholder');await contrast('#сц-вступ em');
    await target('#сц-зберегти');await target('#вк-оцінка');await target('#чат-фото-вхід');
    await focus('#чат-поле');await screenshot('сценарій-фокус');
    await page.locator('#сц-зберегти').hover();
    const box=await page.locator('#сц-зберегти').boundingBox();await page.mouse.move(box.x+box.width/2,box.y+box.height/2);await page.mouse.down();
    result.states.push({selector:'#сц-зберегти',state:'active',...await page.locator('#сц-зберегти').evaluate(e=>({active:e.matches(':active'),opacity:getComputedStyle(e).opacity}))});
    await contrast('#сц-зберегти');await page.mouse.move(0,0);await page.mouse.up();
    await page.evaluate(async f=>{const d=await дб();await tx(d,'образи','readwrite',s=>s.put(f.record,f.record.ключ));режим('бібліотека');await оновитиБібліотеку();},fixture);
    await page.locator('.біб-образ').first().tap();await page.waitForFunction(()=>РЕЖИМ==='образи'&&!!П?.картки?.length);await page.waitForTimeout(650);
    await contrast('.пж-оц');await target('#к-0 .чип.ок');await page.locator('#к-0 .чип.ок').first().tap();await page.waitForTimeout(350);
    result.states.push({selector:'#к-0 .чип.ок',state:'selected',...await page.locator('#к-0 .чип.ок').first().evaluate(e=>({selected:e.classList.contains('вибр'),ariaPressed:e.getAttribute('aria-pressed')}))});
    assert(result.states.at(-1).selected);await contrast('#к-0 .чип.ок.вибр');await target('#к-0 .поле-вердикту');
    await focus('#к-0 .поле-вердикту');await screenshot('картка-вибір-фокус');
    await page.locator('#к-0 details').evaluateAll(es=>es.forEach(e=>e.open=true));await target('#кф-0');
    await page.evaluate(()=>document.documentElement.dataset.тема='темна');await contrast('#к-0 .чип.ок.вибр');await contrast('.пж-оц');
    await focus('#к-0 .поле-вердикту');await screenshot('картка-темна');
    assert.equal(result.errors.length,0);
    fs.writeFileSync(path.join(out,'native.json'),JSON.stringify(result,null,2));
    console.log('PASS',result.targets.length,'цілей',result.targets.reduce((s,t)=>s+t.hits.length,0),'влучань',result.contrast.length,'контрастів',result.errors.length,'pageerrors');
  } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
