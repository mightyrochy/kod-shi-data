/* Прототип кроку 4.1 (К-7): Pyodide 0.26.4 у Web Worker. Те саме тіло показу (`МОДУЛІ_ПОКАЗУ`, zip), той самий
   `bridge.виклик` / `bridge.виклик_а`, але головний потік сторінки Python не виконує зовсім.
   Чому так: збір — 52 с Python у головному потоці, сторінка заморожена ≈ 89 % збору.

   Повідомлення (головний потік → воркер):
     {тип: 'підйом', indexURL, модулі: ArrayBuffer | рядок base64}   — модулі передаються (transfer), не копіюються
     {тип: 'виклик', н, пок, ім, вхід: рядок JSON, асинх}            — дані йдуть аргументом функції, не кодом Python
   Відповіді (воркер → головний потік):
     {тип: 'готово', мс: {pyodide, модулі, імпорт}}
     {тип: 'відповідь', н, пок, вих: рядок JSON | помилка: рядок, мс_python}
   `н` і `пок` воркер лише повертає: що з відповіддю робити (і чи вона застаріла), вирішує головний потік.
   Кирилиця в іменах Python через проксі Pyodide крихка між версіями (`bridge.виклик`, докстрінг), тож функції
   моста беремо з глобалей під латинськими іменами, а кириличні лишаються всередині Python. */
let пд = null;
let виклик = null, виклик_а = null;

async function підняти(п){
  const т0 = performance.now();
  importScripts(п.indexURL + 'pyodide.js');
  пд = await loadPyodide({indexURL: п.indexURL});
  const т1 = performance.now();
  const байти = typeof п.модулі === 'string'
    ? Uint8Array.from(atob(п.модулі), с => с.charCodeAt(0)) : new Uint8Array(п.модулі);
  пд.unpackArchive(байти.buffer, 'zip', {extractDir: '/показ'});
  const т2 = performance.now();
  /* Той самий порядок, що `підняти_міст_показу`; обгортки лише розбирають рядок входу і, коли ендпойнт віддав не
     рядок, кладуть вихід у JSON — головному потоку йде завжди рядок (PyProxy через межу потоку не ходить). */
  await пд.runPythonAsync(
    'import sys, os, json\n' +
    'sys.path.insert(0, "/показ"); os.chdir("/показ")\n' +
    'import bridge\n' +
    'def _vyklyk(im, ryadok):\n' +
    '    r = bridge.виклик(im, json.loads(ryadok))\n' +
    '    return r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)\n' +
    'async def _vyklyk_a(im, ryadok):\n' +
    '    r = await bridge.виклик_а(im, json.loads(ryadok))\n' +
    '    return r if isinstance(r, str) else json.dumps(r, ensure_ascii=False)\n');
  виклик = пд.globals.get('_vyklyk');
  виклик_а = пд.globals.get('_vyklyk_a');
  const т3 = performance.now();
  postMessage({тип: 'готово', мс: {pyodide: т1 - т0, модулі: т2 - т1, імпорт: т3 - т2}});
}

/* Кожне повідомлення — окреме продовження: синхронний `виклик` займає воркер до кінця (як займав головний потік),
   а `виклик_а` поступається між частинами — і тоді наступне повідомлення починається, як у сторінці доти. */
async function виконати(п){
  const т0 = performance.now();
  try{
    const вих = п.асинх ? await виклик_а(п.ім, п.вхід) : виклик(п.ім, п.вхід);
    postMessage({тип: 'відповідь', н: п.н, пок: п.пок, вих, мс_python: performance.now() - т0});
  }catch(е){
    postMessage({тип: 'відповідь', н: п.н, пок: п.пок, помилка: String((е && е.message) || е), мс_python: performance.now() - т0});
  }
}

onmessage = е => {
  const п = е.data;
  if (п.тип === 'підйом') підняти(п).catch(е => postMessage({тип: 'збій', помилка: String((е && е.message) || е)}));
  else if (п.тип === 'виклик') виконати(п);
};
