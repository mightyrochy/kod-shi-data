const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), assert = require('assert'), crypto = require('crypto');
const dir = '/tmp/pachka-1310-evidence/native5070'; fs.mkdirSync(dir, {recursive:true});
const cache='/workspace/scratch/liusterko-5070-evidence';
const input={...JSON.parse(fs.readFileSync(cache+'/before/colors-only-facts.json')).input,випадок:'офіс',сценарій:{нагода:'робота',місце:'офіс'},відповідь:'{}'};
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
(async()=>{
 const browser=await chromium.launch({executablePath:'/usr/bin/chromium',args:['--no-sandbox']});
 try {
  const all={before:JSON.parse(fs.readFileSync(dir+'/before-native.json'))};
  for(const [label,file] of [['after','/tmp/pachka-1310-evidence/index.html']]){
   const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
   const errors=[],blocked=[];page.on('pageerror',e=>errors.push(String(e)));
   await page.route('**/*',r=>{const u=new URL(r.request().url()); let local;
    if(u.hostname==='qa.local')local=file;
    else if(u.href.includes('/pyodide/'))local=path.join(cache,'pyodide',path.basename(u.pathname));
    else if(u.href.includes('/Fixel@main/fonts/webfonts/'))local=path.join(cache,'fonts',path.basename(u.pathname));
    else blocked.push(u.hostname+u.pathname);
    return local&&fs.existsSync(local)?r.fulfill({path:local}):r.abort();});
   await page.goto('http://qa.local'); await page.waitForFunction(()=>typeof document.getElementById('пал-назад').onclick==='function');
   await page.evaluate(()=>підняти_міст_показу());
   const version=await page.evaluate(()=>pyodide_показу.version); assert.strictEqual(version,'0.26.4');
const producer=JSON.parse(await page.evaluate(code=>pyodide_показу.runPythonAsync(code),"import json,пакет_моделі as П,дріт_моделі as Д\n_inputs=[{'id':'probe-u','hex':'#808080','колір_невідомий':True},{'id':'probe-k','hex':'#808080'}]\n_rows=П._рядки_кандидатів({}, {}, None, {'_кандидати':{'верх':_inputs}})['верх']\n_checks=[]\nfor _short in [False,True]:\n for _idx,_r in enumerate(_rows):\n  _in=П._річ_пулу(_r,{})\n  if _short:_in['розбір']={'type':'blouse'}\n  _wire=Д.пакет({'пул':{'верх':[_in]},'завдання':{'короткий_запис':_short}})['pool'][0]\n  _key=lambda k:Д.КОРОТКІ_КЛЮЧІ[k] if _short else k\n  if _idx==0:\n   assert _r['колір_невідомий'] and all(_r.get(k) is None for k in ['hex','сім_я','у_дузі'])\n   assert all(_key(k) not in _wire for k in ['hex','family'])\n  else:assert _wire[_key('hex')]=='#808080' and _wire[_key('family')]=='neutral_achromatic'\n  _checks.append({'short':_short,'idx':_idx,'wire':_wire})\njson.dumps(_checks,ensure_ascii=False)")); fs.writeFileSync(dir+'/producer5030-native.json',JSON.stringify(producer,null,2));

   await page.evaluate(()=>pyodide_показу.runPythonAsync(`import json,sys,os\n_qa_calls=[]\ndef _qa_trace(f,e,a):\n if e=='return' and a is not None and os.path.basename(f.f_code.co_filename)=='міст_вхід.py' and f.f_code.co_name=='_збірка':\n  _qa_calls.append(dict(height=a[2],body=None if a[1] is None else type(a[1]).__name__))\n if e=='return' and a is not None and os.path.basename(f.f_code.co_filename)=='міст_основи.py' and f.f_code.co_name=='_пакет':\n  _qa_calls.append(dict(scale=a['особа']['масштаб'],missing=a['бракує_входів'],body_calculated=a['форма']['проганялось']))\nsys.setprofile(_qa_trace)`));
   const states=label==='before'?[['short',148,{плечі:98,груди:92,талія:74,стегна:99}],['full',168,{плечі:98,груди:92,талія:74,стегна:99}],['tall',188,{плечі:98,груди:92,талія:74,стегна:99}]]:[['none',null,{}],['one',null,{плечі:98}],['body_no_height',null,{плечі:98,груди:92,талія:74,стегна:99}],['height_only',168,{}],['short',148,{плечі:98,груди:92,талія:74,стегна:99}],['full',168,{плечі:98,груди:92,талія:74,стегна:99}],['tall',188,{плечі:98,груди:92,талія:74,стегна:99}]];
   const native={};
   for(const [state,height,measure] of states){
    const data={...input,зріст:height,обхвати:measure};
    native[state]=await page.evaluate(async data=>{
     pyodide_показу.globals.set('_qa_json',JSON.stringify(data));
     return JSON.parse(await pyodide_показу.runPythonAsync(`import bridge,json\n_qa_d=json.loads(_qa_json)\njson.dumps({k:bridge.виклик(k,_qa_d) for k in ['палітри','вибір_палітри']},ensure_ascii=False)`));
    },data);
   }
   const rejection=await page.evaluate(async data=>{pyodide_показу.globals.set('_qa_json',JSON.stringify(data));return JSON.parse(await pyodide_показу.runPythonAsync(`import json,bridge\nfrom міст_вхід import _збірка\n_qa_d=json.loads(_qa_json)\n_qa_reject={}\nfor _qa_k in ['палітри','вибір_палітри','запити','від_моделі','донор']:\n try:\n  if _qa_k=='донор': _збірка(_qa_d,донорський=True)\n  else: bridge.виклик(_qa_k,_qa_d)\n  _qa_reject[_qa_k]='OK'\n except Exception as e: _qa_reject[_qa_k]=str(e)\njson.dumps(_qa_reject,ensure_ascii=False)`));}, {...input,зріст:null,обхвати:{плечі:98,груди:92,талія:74,стегна:99}});
   const calls=JSON.parse(await page.evaluate(()=>pyodide_показу.runPythonAsync('sys.setprofile(None)\njson.dumps(_qa_calls,ensure_ascii=False)')));
   console.log(label,rejection);fs.writeFileSync(dir+'/'+label+'-native.json',JSON.stringify({native,calls,rejection,errors,blocked,version},null,2));
   for(const k of ['запити','від_моделі','донор']) assert(rejection[k].includes('зріст'),k);
   if(label==='before') for(const k of ['палітри','вибір_палітри']) assert(rejection[k].includes('зріст'),k);
   else {
    assert(rejection.палітри==='OK'&&rejection.вибір_палітри==='OK');
    assert(calls.some(x=>x.height===null&&x.body===null));
    assert(calls.some(x=>x.scale===null&&JSON.stringify(x.missing).includes('зріст')));
    await page.evaluate(()=>{КОЛІР={шкіра:'#edc4ad',волосся:'#66412f',очі:'#6f7858',кільце:null,точки:{шкіра:['#edc4ad'],волосся:['#66412f']}};ПРОФІЛЬ_СТВОРЕНО=true;$('мр-зріст').value='';ПАСПОРТ_П={нагода:'робота',місце:'офіс',джерело_полів:{}};режим('сценарій');малюватиКарткуСценарію();});
    await page.locator('#пал-кнопка').tap();await page.waitForFunction(()=>!!ПАЛІТРА);
    assert.strictEqual(await page.evaluate(()=>вхідПалітри().зріст),null);
    assert.strictEqual(await page.locator('#пал-схема .чип').count(),7);
    assert.strictEqual(await page.locator('#пал-основа .чип').count(),32);
    assert.strictEqual(await page.locator('#пал-гама .чип').count(),4);
    assert(!(await page.locator('#е-палітра').innerText()).includes('Traceback'));
    await page.screenshot({path:dir+'/none.png'});
    await page.locator('#пал-схема').scrollIntoViewIfNeeded();await page.screenshot({path:dir+'/none-schemes.png'});
    for(let i=1;i<7;i++){await page.locator('#пал-схема .чип').nth(i).tap();await page.waitForFunction(()=>ВИБІР.схема===ПАЛІТРА.гілки[ВИБІР.гілка].схема);}
    for(let i=1;i<4;i++){await page.locator('#пал-гама .чип').nth(i).tap();await page.waitForFunction(()=>ВИБІР.вибір_кольору.насиченість===ПАЛІТРА.вибір_кольору.насиченість);}
    await page.locator('#пал-основа .чип').nth(2).tap();await page.waitForFunction(()=>ВИБІР.вибір_кольору.база===ПАЛІТРА.вибір_кольору.база);
    await page.screenshot({path:dir+'/selected.png'});
   }
   assert.deepStrictEqual(errors,[]);all[label]={native,calls,rejection,errors,blocked,version}; await page.close();
  }
  for(const endpoint of ['палітри','вибір_палітри']){
   assert.strictEqual(all.before.native.short[endpoint],all.before.native.full[endpoint]);assert.strictEqual(all.before.native.tall[endpoint],all.before.native.full[endpoint]);
   for(const state of ['short','full','tall'])assert.strictEqual(all.after.native[state][endpoint],all.before.native[state][endpoint]);
   const norm=x=>{const p=JSON.parse(x);if(endpoint==='палітри')delete p.слід_правил;return JSON.stringify(p)};
   for(const state of Object.keys(all.after.native))assert.strictEqual(norm(all.after.native[state][endpoint]),norm(all.after.native.full[endpoint]));
  }
  fs.writeFileSync(dir+'/native.json',JSON.stringify(all,null,2));
  console.log(JSON.stringify({before_raw_hashes:Object.fromEntries(['палітри','вибір_палітри'].map(k=>[k,['short','full','tall'].map(s=>hash(all.before.native[s][k]))])),after_states:Object.keys(all.after.native),version:all.after.version,errors:all.after.errors,blocked:all.after.blocked,mandatory_rejections:all.after.rejection},null,2));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
