// QA3 b722: новий незалежний прогін; адаптовано транспорт QA2, додано власні перевірки видимості, звуження пулу та збережених трас.
// Незалежна QA 4945: справжні показ, Pyodide, міст і IndexedDB; синтетична лише модель.
const fs = require('fs'), path = require('path'), assert = require('assert'), crypto = require('crypto');
const { chromium } = require('playwright');
const ART = '/workspace/replace4945-ui-final-evidence/index.html';
const HEAD = 'b722c8867f671c612e71c5f5828f8befbf642111';
const ART_SHA = '1c376f922b1a2c10492d710b6b1e98200dcab9a0aeab99ec7b9fbf2536f821df';
const OUT = __dirname, sha = x => crypto.createHash('sha256').update(x).digest('hex');
const fixture = JSON.parse(fs.readFileSync(OUT + '/fixture.json'));
assert.equal(sha(fs.readFileSync(ART)), ART_SHA);
const server = require('http').createServer((req, res) => {
  const f = req.url === '/' ? ART : req.url.startsWith('/pyodide/') ? path.join('/workspace/scratch/liusterko-4944/.qa4944/pyodide', path.basename(req.url)) : null;
  if (!f || !fs.existsSync(f)) { res.writeHead(404); return res.end(); }
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Content-Type', req.url === '/' ? 'text/html; charset=utf-8' : req.url.endsWith('.wasm') ? 'application/wasm' : req.url.endsWith('.js') ? 'application/javascript' : 'application/octet-stream');
  fs.createReadStream(f).pipe(res);
});
const result = { attempt: 'final-after-explicit-resume', pid:process.pid, startedAt:new Date().toISOString(), head: HEAD, artifact: ART, artifactSHA256: ART_SHA, viewport: '390x844', synthetic: 'Тільки відповіді моделі; каталог і виконання справжні. Не оцінка семантики моделі чи фото.', cases: [], visibility: [], errors: [], blocked: [], requests: [] };
let browser;
const deadline=setTimeout(async()=>{result.failure='Перевищено межу 15 хвилин незалежного прогону';result.finishedAt=new Date().toISOString();fs.writeFileSync(OUT+'/final-native.json',JSON.stringify(result,null,2)+'\n');if(browser)await browser.close();server.close();process.exit(124);},900000);deadline.unref();
async function visibility(p, state, pos, screenshot) {
  const v = await p.evaluate(({state,pos}) => {
    const card=$('к-'+pos), header=$('обр-не-ця');
    const visible=e=>!!e && getComputedStyle(e).display!=='none' && getComputedStyle(e).visibility!=='hidden' && e.getBoundingClientRect().width>0 && e.getBoundingClientRect().height>0;
    return {state,pos,bodyText:document.body.innerText,cardText:card.innerText,
      oldNodeCount:document.querySelectorAll('.відп-заміни').length,
      oldPromiseVisible:document.body.innerText.includes('коли збиратиму образи знову'),
      oldPromiseInCards:$('картки').textContent.includes('коли збиратиму образи знову'),
      headerText:header.innerText,headerVisible:visible(header),resetVisible:visible(header.querySelector('button')),
      disabled:[...card.querySelectorAll('button.замін')].map(b=>b.disabled)};
  },{state,pos});
  result.visibility.push(v);
  assert.equal(v.oldNodeCount,0,state+': старі вузли відповіді');
  assert(!v.oldPromiseVisible && !v.oldPromiseInCards,state+': стара обіцянка');
  if(state.includes('pending')) assert(v.disabled.every(Boolean),state+': активна кнопка під час запиту');
  if(!state.includes('initial')) {
    assert(v.headerVisible && v.resetVisible,state+': шапка/повернення');
    assert(v.headerText.includes('Ти позначила на заміну ') && v.headerText.includes('— у наступному зборі на цей сценарій ') && v.headerText.includes('не буде.') && v.headerText.includes('Повернути всі'),state+': правдива шапка');
  }
  if(screenshot) {
    await p.locator('#к-'+pos).scrollIntoViewIfNeeded();
    await p.screenshot({path:OUT+'/final-'+state+'.png',caret:'initial'});
  }
}
async function install(p, pos, mode, reset = true) {
  await p.evaluate(async ({ fixture, pos, mode, reset }) => {
    if (reset) {
      П = structuredClone(fixture); Object.keys(В).forEach(k => delete В[k]); НЕ_ЦЯ_П.clear();
      ЗАМІНУ_ВЖЕ_РОЗУМІЄ_П = false;
      ЗБ = { картки: П.картки, діагноз: [], готово: true, стадії: [], етап: [] };
      if (mode === 'unknown') delete П.знімок;
      if (mode === 'notfound') П.картки[pos].речі[2].id = 'ж-qa-notfound@fixture.invalid';
      if (mode === 'noeligible') {
        const ids = JSON.parse(pyodide_показу.runPython('import json, bridge\njson.dumps([str(r["id"]) for p in bridge._КЕШ_ПАКЕТА.values() for r in p["_каталог"]])'));
        if (!ids.length) throw Error('QA requires a warmed real catalogue');
        ids.forEach(id => НЕ_ЦЯ_П.add(id));
      }
      const v = відповідь(pos); v.коментар = 'SYNTHETIC: збережені слова'; v.для_мене = 'mine';
      рендер();
      await new Promise(r => setTimeout(r, 50));
    }
    window.показатиОбраз(pos, true);
    await window.зберегтиОбраз();
    window.qaCalls = []; window.qaRelease = null; window.qaMode = mode;
    window.qaPendingStages = []; window.qaOtherNodes = П.картки.map((_, i) => $('к-' + i));
    window.qaCapture = () => {
      const index = pos < 2 ? 2 : 0;
      window.qaBefore = { cards: П.картки.map(x => JSON.stringify(x)), dom: П.картки.map((_, i) => $('к-' + i).innerHTML),
        snapshot: JSON.stringify(П.знімок), pager: $('пейджер').innerHTML, choices: JSON.stringify(В),
        old: structuredClone(П.картки[pos].речі[index]), pos, index };
    };
    модельП = async prompt => {
      const body = JSON.parse(prompt), entry = { prompt: body }; qaCalls.push(entry);
      if (qaMode === 'error') throw Error('SYNTHETIC транспортна відмова');
      if (qaMode === 'delay') await new Promise(r => { window.qaRelease = r; });
      let answer;
      if (body.items) answer = { version: '1', ratings: Object.fromEntries(Object.values(body.items).flat().map(x => [x.n, 'fits'])) };
      else if (body.groups) answer = { version: '1', winners: Object.fromEntries(Object.entries(body.groups).map(([g, xs]) => [g, xs.slice(-2).map(x => x.n)])) };
      else if (!body.pool) answer = { items: [{ name: 'Ботильйони', details: 'Гладка шкіра', slot: qaMode === 'wrongslot' ? 'bag' : 'shoes', color_hex: '#553322', own: null, worn: true }] };
      else answer = { version: '1', outfits: [{ id: 'o1', items: qaMode === 'none' ? [] : [qaMode === 'same' ? qaBefore.old.id : body.pool.at(-1).n] }] };
      entry.answer = answer; return JSON.stringify(answer);
    };
  }, { fixture, pos, mode, reset });
  // Приховані картки мають lazy-фото; очікуємо лише вже запитані видимі кадри.
  await p.waitForFunction(() => [...document.querySelectorAll('.картка:not([hidden]) img')].every(i => i.complete || i.loading === 'lazy'));
  await p.waitForTimeout(400);
  await p.evaluate(() => qaCapture());
}
async function measure(p, name, pos, choice, mode, reset = true) {
  await install(p, pos, mode, reset);
  const index = pos < 2 ? 2 : 0;
  await visibility(p,choice+'-'+name+'-initial',pos,choice==='list'&&name==='hand1');
  await p.locator('#к-' + pos + ' button.замін').nth(index).tap();
  if (mode === 'delay') {
    await p.waitForFunction(() => typeof qaRelease === 'function');
    await visibility(p,choice+'-'+name+'-pending',pos,name==='rapid');
    await p.evaluate(pos => { qaPendingStages.push(ЗАМІНИ_П.get(П.картки[pos])); }, pos);
    if (name === 'rapid') await p.evaluate(({pos,index}) => $('к-' + pos).querySelectorAll('button.замін')[index].click(), {pos,index});
    if (name === 'late-outfit') await p.evaluate(() => window.показатиОбраз(1, true));
    if (name === 'late-navigation') await p.evaluate(() => режим('сценарій'));
    await p.evaluate(() => qaRelease());
  }
  await p.waitForFunction(pos => !ЗАМІНИ_П.has(П.картки[pos]), pos);
  if(!name.startsWith('late-')) await visibility(p,choice+'-'+name+'-finished',pos,['hand1','hand3','error'].includes(name));
  const r = await p.evaluate(async pos => {
    const b = qaBefore, k = П.картки[pos];
    const library = await tx(await дб(), 'образи', 'readonly', s => s.get(П.прогін));
    return { pos, before: b, cards: П.картки.map(x => JSON.stringify(x)), dom: П.картки.map((_, i) => $('к-' + i).innerHTML),
      nodesSame: П.картки.map((_, i) => qaOtherNodes[i] === $('к-' + i)), calls: qaCalls,
      stage: k.етапи?.заміни?.at(-1) || qaPendingStages.at(-1),
      snapshot: JSON.stringify(П.знімок), pager: $('пейджер').innerHTML, marks: [...НЕ_ЦЯ_П],
      choices: JSON.parse(JSON.stringify(В)), saved: library.П,
      verdicts: (await усіВердикти()).length,
      resetVisible: !!$('обр-не-ця').querySelector('button') && getComputedStyle($('обр-не-ця')).display !== 'none',
      status: $('к-' + pos).querySelector('.не-ця-рядок')?.textContent,
      source: k.речі[b.index], buttonsEnabled: [...$('к-' + pos).querySelectorAll('button.замін')].every(b => !b.disabled) };
  }, pos);
  r.name = name; r.choice = choice;
  const current = JSON.parse(r.cards[pos]), before = JSON.parse(r.before.cards[pos]);
  r.changed = r.source.id !== r.before.old.id;
  r.otherCardsExact = r.cards.every((x, i) => i === pos || x === r.before.cards[i]);
  r.otherDOMExact = r.dom.every((x, i) => i === pos || x === r.before.dom[i]);
  r.savedOtherCardsExact = r.saved.картки.every((x, i) => i === pos || JSON.stringify(x) === r.before.cards[i]);
  r.fixedItemsExact = current.речі.every((x, i) => i === index || JSON.stringify(x) === JSON.stringify(before.речі[i]));
  r.stageSavedExact = JSON.stringify(r.saved.картки[pos].етапи?.заміни?.at(-1)) === JSON.stringify(current.етапи?.заміни?.at(-1));
  result.cases.push(r);
  assert(r.otherCardsExact && r.otherDOMExact && r.savedOtherCardsExact && r.fixedItemsExact, name + ': інші речі/картки/DOM/сховище');
  assert(r.nodesSame.every(Boolean), name + ': DOM-вузол замінено');
  assert.equal(r.source.слот, r.before.old.слот, name + ': слот');
  assert.equal(r.snapshot, r.before.snapshot, name + ': знімок входу');
  assert.equal(r.verdicts, 0, name + ': незапитаний запис вердикта');
  assert(r.buttonsEnabled && r.resetVisible, name + ': кнопки/повернення');
  const beforeChoice = JSON.parse(r.before.choices)[pos] || {}, afterChoice = r.choices[pos] || {};
  for (const [k, v] of Object.entries(beforeChoice)) if (!['замінити', 'зміна'].includes(k)) assert.deepEqual(afterChoice[k], v, name + ': вибір ' + k);
  for (const call of r.calls) {
    if(call.prompt.pool) assert(call.prompt.pool.every(x=>x.slot==='shoes'),name+': пул іншого слота');
    if(call.prompt.items) assert.deepEqual(Object.keys(call.prompt.items),['shoes'],name+': оцінка іншого слота');
    const c = call.prompt.replacement; assert(c && c.slot === 'shoes', name + ': контекст слота');
    assert.equal(c.fixed_outfit.length, before.речі.length - 1, name + ': повний незмінний образ');
    assert.deepEqual(c.fixed_outfit.map(x => x.name), before.речі.filter((_,i) => i !== index).map(x => x.назва), name + ': склад контексту');
    assert(!JSON.stringify(call.prompt.task).includes('not as part of an outfit'), name + ': ізольована оцінка');
  }
  if (name.startsWith('hand') || name.startsWith('policy') || name === 'rapid') {
    assert(r.changed, name + ': річ лишилася');
    assert.equal(r.calls.length, choice === 'tournament' ? 2 : 1, name + ': найменший шлях');
    assert.equal(r.pager, r.before.pager, name + ': пейджер');
    assert(r.stageSavedExact && r.stage.закінчено >= r.stage.почато && r.stage.застаріло === false, name + ': етап не збережено повністю');
    assert.deepEqual(r.saved.картки[pos], current, name + ': поточна картка не збережена');
  } else {
    assert(!r.changed, name + ': помилкова заміна');
    if (['unknown-source', 'not-found', 'no-eligible'].includes(name)) assert.equal(r.calls.length, 0, name + ': зайвий виклик');
    if (name.startsWith('late-')) assert(r.stage.закінчено && r.stage.застаріло === true, name + ': запізніла відповідь');
    else assert(r.stageSavedExact && r.stage.закінчено && r.stage.застаріло === false, name + ': помилка не збережена повністю');
  }
  if(r.stage && !name.startsWith('late-')) {
    assert.equal(r.stage.виклики.length,r.calls.length,name+': число викликів у збереженому етапі');
    for(let j=0;j<r.calls.length;j++) assert.deepEqual(JSON.parse(r.stage.виклики[j].промпт),r.calls[j].prompt,name+': збережений промпт');
  }
  r.beforeHash = r.before.cards.map(sha); r.afterHash = r.cards.map(sha);
  delete r.dom; delete r.before.dom;
  if (['hand1', 'hand3', 'policy-second', 'error', 'late-outfit'].includes(name)) {
    await p.locator('#к-' + (name === 'late-outfit' ? 1 : pos)).scrollIntoViewIfNeeded();
    await p.screenshot({ path: OUT + '/final-' + choice + '-' + name + '.png' });
  }
  console.log('PASS', choice, name, 'changed', r.changed, 'calls', r.calls.length, 'DOM/JSON/storage', r.otherDOMExact, r.otherCardsExact, r.savedOtherCardsExact);
}
(async () => {
  await new Promise(r => server.listen(0, '127.0.0.1', r));
  const origin = 'http://127.0.0.1:' + server.address().port;
  browser = await chromium.launch({ executablePath: '/usr/bin/chromium', args: ['--no-sandbox', '--disable-dev-shm-usage'] });
  result.chromium = browser.version();
  for (const choice of ['list', 'assess', 'tournament']) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    const p = await ctx.newPage(); p.setDefaultTimeout(120000);
    p.on('request',r=>result.requests.push({method:r.method(),url:r.url()}));
    p.on('pageerror', e => result.errors.push(String(e)));
    await p.route('**/*', r => {
      const u = new URL(r.request().url()); if (u.origin === origin) return r.continue();
      if (u.href.includes('/pyodide/')) return r.fulfill({ status: 302, headers: { location: origin + '/pyodide/' + path.basename(u.pathname), 'access-control-allow-origin': '*' } });
      const f = u.href.includes('/Fixel@main/fonts/webfonts/') ? path.join('/workspace/scratch/liusterko-4942/.qa4942/fonts', path.basename(u.pathname)) : null;
      if (f && fs.existsSync(f)) return r.fulfill({ path: f });
      result.blocked.push({ method: r.request().method(), url: u.href }); return r.abort();
    });
    await p.goto(origin + '/#model_mova=off&vybir=' + choice);
    await p.waitForFunction(() => typeof document.getElementById('сц-рукою-показати').onclick === 'function');
    await p.evaluate(async origin => { ДЗЕРКАЛА_П[0][1] = origin + '/pyodide/'; await підняти_міст_показу(); }, origin);
    result.pyodide = await p.evaluate(() => pyodide_показу.version);
    const cases = choice === 'list' ? [['hand1',0,'ok'], ['hand2',1,'ok'], ['hand3',2,'ok'], ['hand4',3,'ok'],
      ['sameSKU',0,'same'], ['refusal',0,'none'], ['error',0,'error'], ['rapid',0,'delay'], ['late-outfit',0,'delay'],
      ['late-navigation',0,'delay'], ['unknown-source',0,'unknown'], ['not-found',0,'notfound'], ['no-eligible',0,'noeligible'], ['wrong-slot-hand3',2,'wrongslot']]
      : [['hand1',0,'ok'], ['hand2',1,'ok']];
    for (const [name,pos,mode] of cases) { console.log('START',choice,name); await measure(p,name,pos,choice,mode); }
    if (choice === 'list') {
      await measure(p, 'policy-first', 0, choice, 'ok');
      await measure(p, 'policy-second', 1, choice, 'ok', false);
      const policy = result.cases.at(-1); assert.deepEqual(policy.marks, [fixture.картки[0].речі[2].id], 'політика А: X лишається');
      const before = await p.evaluate(() => П.картки.map(x => JSON.stringify(x)));
      await p.locator('#обр-не-ця button').tap();
      const reset = await p.evaluate(() => ({ marks:[...НЕ_ЦЯ_П], cards:П.картки.map(x => JSON.stringify(x)), choices:В, calls:qaCalls.length }));
      assert.equal(reset.marks.length,0); assert.deepEqual(reset.cards,before); assert.equal(reset.calls,1);
      assert(Object.values(reset.choices).every(v => !v.замінити?.length)); result.reset = reset;
    }
    await ctx.close();
  }
  assert.equal(result.errors.length,0);
  result.modelPOSTs = result.requests.filter(x => x.method === 'POST').length; assert.equal(result.modelPOSTs,0);
  assert.equal(sha(fs.readFileSync(ART)), ART_SHA);
})().catch(e => { result.failure = String(e.stack || e); console.error(e); process.exitCode = 1; }).finally(async () => {
  clearTimeout(deadline);result.finishedAt=new Date().toISOString();
  fs.writeFileSync(OUT + '/final-native.json', JSON.stringify(result,null,2) + '\n');
  if (browser) await browser.close(); await new Promise(r => server.close(r));
});
