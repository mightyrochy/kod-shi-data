/* НАСКРІЗНИЙ ПРОГІН: реальний JS показу (jsdom) + реальний Python-міст (HTTP) + сценарна модель. */
const fs = require("fs"), path = require("path"), http = require("http");
const { JSDOM } = require("jsdom"); const { IDBFactory, IDBKeyRange } = require("fake-indexeddb");
const html = fs.readFileSync(process.env.POKAZ || path.join(__dirname, "показ.html"), "utf8")
  .replace("__МОДУЛІ_ПОКАЗУ__", "").replace("__ЗБІРКА_ПОКАЗУ__", "тест").replace("__ВІДБИТОК__", "0").replace("__ФІД_ПОКАЗУ__", "каталог_жіночий.xml").replace("__КАТАЛОГ_ПОКАЗУ__", "каталог_жіночий.xml · 8666 оферів");
const дом = new JSDOM(html, {runScripts: "dangerously", pretendToBeVisual: true, url: "https://x.test/", beforeParse(w){ w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange; w.fetch = async () => ({ok:false, status:0, text: async()=>""}); w.scrollTo = () => {}; }});
const w = дом.window; const пауза = мс => new Promise(р=>setTimeout(р, мс));
const винятки = []; w.addEventListener("error", e => винятки.push(String(e.error || e.message)));
w.console.warn = () => {}; w.console.error = (...a) => винятки.push(a.map(String).join(" ").slice(0,200));
function міст(ім, дані){ return new Promise((ok, no) => { const б = Buffer.from(JSON.stringify({ім, дані})); const q = http.request({host:"127.0.0.1", port:8765, method:"POST", headers:{"Content-Length": б.length}}, r => { let s=""; r.on("data", d => s+=d); r.on("end", () => { try{ ok(JSON.parse(s)); }catch(e){ no(e); } }); }); q.on("error", no); q.end(б); }); }
w._мостHTTP = { runPythonAsync: async (код) => { const m = код.match(/bridge\.виклик\("([^"]+)", json\.loads\((".*")\)\)/s); const ім = m[1]; const дані = JSON.parse(JSON.parse(m[2])); const р = await міст(ім, дані); if (ім === "показ" || (р && р.помилка)) console.log("МІСТ", ім, JSON.stringify(р).slice(0,300)); return JSON.stringify(р); } };
w.eval("pyodideП = window._мостHTTP; підняти_міст_показу = async () => pyodideП; підняти_pyodide_показу = async () => pyodideП;");
const СЛОТИ = ["верх","низ","сукня","комплект","взуття","сумка","пояс","головний_убір","шарф","прикраси","сережки","намисто","кольє","браслет","каблучка","брошка"];
function пул(промпт){ const п = {}; let сл = null; for (const л of промпт.split("\n")){ const т = л.trim(); const h = СЛОТИ.find(s => т.toLowerCase().replace(/^·\s*/, "").startsWith(s + ":") && !т.startsWith("#")); if (h && !т.startsWith("[")) { сл = h; continue; } const m = т.match(/^(#\d+·\d\d)\s/); if (m && сл){ (п[сл] = п[сл] || []).push(m[1]); } } return п; }
function образиЗ(промпт){ const бл = []; for (const ч of промпт.split(/── образ \d+/).slice(1)){ const ids = [...new Set((ч.match(/#\d+·\d\d/g) || []))]; if (ids.length) бл.push(ids); } return бл; }
const виклики = []; let n = 0;
w.модельП_блоки = async (блоки) => { const т = блоки.filter(b=>b.type==="text").map(b=>b.text).join("\n"); const ф = блоки.filter(b=>b.type==="image"); return [{type:"text", text: await w.модельП(т, ф.map(x=>x.source.url))}]; };
w.модельП = async (промпт, фото) => { n++; виклики.push({n, довж: промпт.length, фото: (фото||[]).length, тип: null});
  const з = виклики[виклики.length-1];
  if (/заповни паспорт/.test(промпт)) { з.тип = "паспорт"; return JSON.stringify({подія:"літературний фестиваль просто неба, потім денний театр", формат:"змішано", тривалість_год:5, рух:"ходити", дрес_код:"business casual", ошатність:[4,6], година:13, темп_c:26, опади:"ні", намір:"conventional", бажання:["лляна сорочка"], вето:{типи:[],тканини:[],принти:[],кольори:["чорний"],зони:[]}, настрій:["легко"], невідомо:["опади"]}); }
  if (/Рівно (\d+) образів/.test(промпт)) { з.тип = "склад"; const N = +промпт.match(/Рівно (\d+) образів/)[1]; const п = пул(промпт); const об = [];
    for (let i=0;i<N;i++){ const g = k => (п[k]||[])[i % Math.max(1,(п[k]||[]).length)]; const речі = (i%3===2 && п["сукня"]) ? [g("сукня"), g("взуття"), g("сумка")] : [g("верх"), g("низ"), g("взуття"), g("сумка")]; об.push({підпис:"задум "+(i+1), речі: речі.filter(Boolean), свідомо:[]}); }
    return JSON.stringify({образи: об, потрібно: ["біла лляна сорочка"]}); }
  if (/допрацьованих образи/.test(промпт)) { з.тип = "ремонт"; const бл = образиЗ(промпт).slice(0,5); return JSON.stringify({образи: бл.map((ids,i)=>({підпис:"ремонт "+(i+1), речі: ids, свідомо:[]}))}); }
  if (/задум обраного образу/.test(промпт)) { з.тип = "вибір"; const бл = образиЗ(промпт); return JSON.stringify({підпис:"обраний", чому:"бо пасує до випадку", речі: бл[0] || []}); }
  if (/Взуття й аксесуари — ЛИШЕ/.test(промпт)) { з.тип = "опис"; return "Сорочка лляна, вільна, кольору піску. Штани прямі.\nВзуття й аксесуари: лофери, сумка.\nЧому це працює: легко і по погоді.\nСВІДОМО: сорочка навипуск — бо спека."; }
  if (/Взуття й аксесуари\. Верхній шар — лише/.test(промпт)) { з.тип = "рука3/4"; return "**1. Речі**\n* Базовий топ: сорочка лляна пісочна, вільна (#D8C3A5)\n* Штани: широкі штани бежеві (#C9B79C)\n* Взуття: сандалі шкіряні (#8B6F47)\n* Сумка: сумка плетена (#A67B5B)\n3. Чому: спека, простір неба."; }
  з.тип = "інше"; return "…"; };
(async () => {
  await пауза(300);
  w.eval("МІСТ_П.адреса='https://x.test/міст'; МІСТ_П.токен='tok-test';");
  w.eval("КОЛІР = {шкіра:'#e9c6aa', волосся:'#7d5330', очі:'#7a8a99', кільце:null, точки:null}");
  for (const [ід, v] of [["мр-плечі",40],["мр-груди",92],["мр-талія",74],["мр-стегна",98],["мр-зріст",168],["сц-нагода","щоденне"],["сц-місце","театр"],["сц-година","13"],["сц-темп","26"],["сц-слова","літературний фестиваль просто неба, потім денний театр; хочу лляну сорочку, не хочу чорного"]]) { const е = w.document.getElementById(ід); if (е) е.value = v; else винятки.push("нема поля "+ід); }
  const вх = w.eval("JSON.stringify(зібратиВхід())"); console.log("зібратиВхід:", вх.slice(0,300));
  const t = Date.now(); w.eval("зібратиОбразиП().catch(e=>console.error('зібратиОбразиП: '+e.message))");
  await пауза(500);
  while (!w.eval("(ЗБ && ЗБ.готово) ? 1 : 0") && Date.now()-t < 250000) await пауза(2000);
  if (!w.eval("ЗБ ? 1 : 0")) { console.log("ЗБ не створено — збирання не стартувало; статус:", w.eval("($('зб-статус')||{}).textContent")); console.log("винятки:", винятки); process.exit(0); }
  console.log("готово:", w.eval("ЗБ.готово"), "за", Math.round((Date.now()-t)/1000), "с; викликів моделі:", n, JSON.stringify(виклики.map(x=>x.тип)));
  console.log("паспорт у П:", w.eval("JSON.stringify(ПАСПОРТ_П||null)").slice(0,140)); console.log("шапка:", w.eval("випадокРядком()[0]"));
  console.log("діагноз:", w.eval("JSON.stringify(ЗБ.діагноз)").slice(0,900));
  const картки = JSON.parse(w.eval("JSON.stringify((ЗБ.картки||[]).map(к=>к&&({рука:к.рука, речей:(к.речі||[]).length, назви:(к.речі||[]).filter(x=>x.назва).length, підпис:к.підпис, текст:(к.текст||'').slice(0,60), частини:(к.речі||[]).filter(x=>x.частина_комплекту).length, поломки:(к.палітра||{}).поломки})))"));
  console.log("картки:", JSON.stringify(картки));
  console.log("винятки:", винятки.length ? винятки : "нема");
  try { w.eval("В[0]=Object.assign(відповідь(0),{верд:'вдягну як є', для_мене:'саме моє', коментар:'проба'}); записати(0)"); await пауза(800); console.log("вердикт записано:", w.eval("JSON.stringify((В[0]||{}).записано)")); } catch(e){ console.log("записати:", e.message); }
  process.exit(0);
})();
