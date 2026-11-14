// Додаткове питання на історії вже записаного прогону; розмову й руки повторно не генерує.
const fs = require('fs'), path = require('path'), {spawn} = require('child_process');
const {chromium} = require('playwright');
const out = __dirname, tree = process.argv[2], cache = process.argv[3];
const scene = path.join(out, 'ж2_довга_розмова_слова');
const question = 'Що я казала про зал на початку?';
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function api(suffix = '', body) {
  const r = await fetch('http://127.0.0.1:1234/api/v1/models' + suffix,
    body ? {method:'POST', headers:{'content-type':'application/json'}, body:JSON.stringify(body)} : {});
  const v = await r.json();
  if (!r.ok || v.error) throw Error(JSON.stringify(v));
  return v;
}
async function main() {
  const recorded = fs.readdirSync(path.join(scene, 'VIDPOVIDI/обмін')).filter(x => /^\d+\.json$/.test(x)).sort()
    .map(x => JSON.parse(fs.readFileSync(path.join(scene, 'VIDPOVIDI/обмін', x), 'utf8')));
  const women = [JSON.parse(fs.readFileSync(path.join(scene, 'повтор.json'), 'utf8')).змінні.CHAT_TEXT,
    ...JSON.parse(fs.readFileSync(path.join(tree, 'аудит/проби/е2_втрата_слова_розмова.json'), 'utf8')).map(x => x.вона)];
  const history = [];
  for (const v of recorded) {
    let p; try { p = JSON.parse(v.запит.messages[0].content[0].text); } catch { continue; }
    const n = women.indexOf(p.her_new_message);
    if (n < 0 || !Array.isArray(p.conversation)) continue;
    const offset = 2 * n - p.conversation.length;
    p.conversation.forEach((s, i) => {
      if (!/^(She|You): /.test(s)) throw Error('Невідомий формат репліки');
      history[offset + i] = {хто:s.startsWith('She: ') ? 'людина' : 'ші', текст:s.replace(/^(She|You): /, '')};
    });
  }
  const log = fs.readFileSync(path.join(scene, 'лог.txt'), 'utf8');
  const turns = [...log.matchAll(/1ж\. М-5 · хід (\d+)\r?\n   ВОНА: ([\s\S]*?)\r?\n   СТИЛІСТКА: ([\s\S]*?)\r?\n   ПАСПОРТ:/g)];
  for (const m of turns) {
    const n = Number(m[1]) - 1;
    history[2*n] = {хто:'людина', текст:m[2]};
    history[2*n+1] = {хто:'ші', текст:m[3]};
  }
  if (history.length !== 20 || Array.from({length:20}, (_, i) => history[i]).some(x => !x))
    throw Error('Нема всіх двадцяти записаних реплік');
  fs.writeFileSync(path.join(out, 'допит-історія.json'), JSON.stringify(history, null, 2));
  if ((await api()).models.some(m => m.loaded_instances.length)) throw Error('Сервер тримає чужу модель');
  let browser, proxy;
  const logfile = path.join(out, 'допит-проксі.txt'), fd = fs.openSync(logfile, 'w');
  try {
    proxy = spawn(process.execPath, [path.join(tree, 'аудит/ноутбук_стенд_2/проксі_почергове.js')], {
      cwd:tree, windowsHide:true, stdio:['ignore',fd,fd], env:{...process.env,LMS_MODE:'http',PORT:'1235',
        CTX:JSON.stringify({'qwen/qwen3.5-9b':57344,'mamaylm-gemma-3-12b-it-v2.0':16384})}});
    let ready = false;
    for (let i=0;i<50;i++) {
      if (proxy.exitCode !== null) throw Error('Проксі завершився');
      try { const r=await fetch('http://127.0.0.1:1235/.well-known/lyusterko-5190'); if(r.ok) {ready=true;break;} } catch {}
      await sleep(100);
    }
    if (!ready) throw Error('Проксі не піднявся');
    browser = await chromium.launch({headless:true});
    const page = await browser.newPage({viewport:{width:390,height:844}});
    await page.route('**/*', async route => {
      const u = new URL(route.request().url());
      let file, type;
      if (u.origin === 'http://127.0.0.1:8765') {
        file=path.join(tree, decodeURIComponent(u.pathname).replace(/^\//,'') || 'index.html');
        type=file.endsWith('.html')?'text/html; charset=utf-8':'text/plain';
      } else if (u.href.startsWith('https://cdn.jsdelivr.net/pyodide/')) {
        file=path.join(cache,u.pathname.split('/').pop());
        type=file.endsWith('.wasm')?'application/wasm':file.endsWith('.js')?'application/javascript':'application/octet-stream';
      } else return route.abort();
      return route.fulfill({status:fs.existsSync(file)?200:404,contentType:type,body:fs.existsSync(file)?fs.readFileSync(file):'нема'});
    });
    let request, response;
    await page.exposeFunction('модельДопиту', async prompt => {
      request={model:'qwen/qwen3.5-9b',messages:[{role:'user',content:prompt}],max_tokens:1000,temperature:0,reasoning_effort:'none'};
      fs.writeFileSync(path.join(out,'допит-запит.json'),JSON.stringify(request,null,2));
      const r=await fetch('http://127.0.0.1:1235/v1/chat/completions',{
        method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(request),signal:AbortSignal.timeout(300000)});
      response={status:r.status,body:await r.text()};
      fs.writeFileSync(path.join(out,'допит-відповідь.json'),JSON.stringify(response,null,2));
      if (!r.ok) throw Error(response.body);
      const v=JSON.parse(response.body);
      return v.choices[0].message.content;
    });
    await page.goto('http://127.0.0.1:8765/index.html#модель=qwen%2Fqwen3.5-9b&модель_мови=mamaylm-gemma-3-12b-it-v2.0');
    await page.waitForFunction(() => typeof помічникП === 'function' && !!document.getElementById('н-далі')?.onclick, null, {timeout:180000});
    const answer=await page.evaluate(async ({history,question}) => {
      ЧАТ_П=history.concat({хто:'людина',текст:question});
      модельП=async prompt => window.модельДопиту(prompt);
      return await помічникП(question,'English');
    },{history,question});
    const prompt=JSON.parse(request.messages[0].content);
    const result={час_utc:new Date().toISOString(),метод:'додатковий виклик помічникП у Chromium на відновлених двадцяти репліках записаної сцени; розмову й руки повторно не генеровано',
      питання:question,очікувано:history.length,отримано:prompt.conversation.length,
      дослівно:JSON.stringify(prompt.conversation)===JSON.stringify(history.map(x=>({from:x.хто==='людина'?'her':'you',text:x.текст}))),
      поточне_питання_окремо:prompt.question===question,відповідь:answer,http:response.status};
    fs.writeFileSync(path.join(out,'допит-результат.json'),JSON.stringify(result,null,2));
    console.log(JSON.stringify(result,null,2));
    if (!result.дослівно || !result.поточне_питання_окремо) process.exitCode=1;
  } finally {
    if (browser) await browser.close();
    if (proxy && proxy.exitCode===null) {proxy.kill();await new Promise(r=>proxy.once('exit',r));}
    fs.closeSync(fd);
    const owned=new Set([...fs.readFileSync(logfile,'utf8').matchAll(/HTTP власний екземпляр (.+)/g)].map(m=>m[1].trim()));
    for (const m of (await api()).models) for (const i of m.loaded_instances) if(owned.has(i.id)) await api('/unload',{instance_id:i.id});
  }
}
main().catch(e=>{console.error(e.stack);process.exitCode=2;});
