/* Проба рядка 197: що саме стоїть у плитці «Не хочу» на паспорті Ір («можна
   куртку чи жакет, не темного кольору») і чи лишився під нею другий рядок про
   почуте. Друкує факт. Запуск із теки `джерела`:
   NODE_PATH=node_modules node проби/ne_khochu_197.js */
const fs = require("fs"), path = require("path"), ДЖ = __dirname + "/..";
const { JSDOM } = require("jsdom"), { IDBFactory, IDBKeyRange } = require("fake-indexeddb");
const { прочитатиДовідникJSON, підставитиШаблон } = require(path.join(ДЖ, "показ_шаблон.js"));
const html = підставитиШаблон(fs.readFileSync(path.join(ДЖ, "показ.html"), "utf8"),
  {__МОДУЛІ_ПОКАЗУ__:"ЗАГЛУШКА", __ЗБІРКА_ПОКАЗУ__:"проба-197", __ВІДБИТОК__:"abc",
   __ФІД_ПОКАЗУ__:"каталог_brief.xml", __КАТАЛОГ_ПОКАЗУ__:"каталог_стенд.xml",
   __ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(ДЖ)})
  .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, "<script>window.loadPyodide=null;</script>");
const w = new JSDOM(html, {runScripts:"dangerously", pretendToBeVisual:true, url:"https://x.github.io/показ.html",
  beforeParse(w){ w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange; w.scrollTo = ()=>{};
    w.fetch = ()=>Promise.reject(new Error("мережі в пробі нема")); w.Element.prototype.scrollIntoView = ()=>{}; }}).window;
const d = w.document, $ = і => d.getElementById(і), пауза = мс => new Promise(р=>setTimeout(р, мс));
const ІР = "ПАСПОРТ_П = {джерело:'модель', нагода:'щоденне', місце:'парк',"
  + " вето:{типи:['блейзер','куртка'], тканини:[], принти:[], кольори:['темні кольори'], зони:[]},"
  + " вето_тверде:{типи:[], тканини:[], принти:[], кольори:['темні кольори'], зони:[],"
  + "              слоти:{'темні кольори':['верх']}, без_читача:[]}};";
(async ()=>{
  await пауза(900);
  const ряд = d.querySelector('[data-редактор="ред-вето"]');
  console.log("назва плитки: " + JSON.stringify(ряд.querySelector("span").textContent)
              + " · заголовок аркуша: " + JSON.stringify(ряд.dataset.назва));
  w.eval(ІР + "малюватиКарткуСценарію();");
  console.log("паспорт Ір · у плитці: " + JSON.stringify($("зн-вето").textContent));
  console.log("почуте, але не тримане (блейзер, куртка) у плитці: "
              + (/куртк|блейзер/i.test(ряд.textContent) ? "Є, ЦЕ ПОЛОМКА" : "нема"));
  console.log("вузол другого рядка `зн-вето-почуто`: "
              + ($("зн-вето-почуто") ? "Є, ЦЕ ПОЛОМКА" : "нема — місця під собою не лишає"));
  console.log("рядок над образами: " + JSON.stringify(w.eval("рядокСценаріюСловами()")));
  $("сц-вето-зони").value = "ноги,плечі"; w.eval("малюватиКарткуСценарію(); малюватиЧипиВето();");
  console.log("з її чипами зон · у плитці: " + JSON.stringify($("зн-вето").textContent));
  console.log("чипи аркуша (ключ → підпис): " + JSON.stringify([...d.querySelectorAll("#сц-вето-чипи .чип")]
              .map(ч=>ч.dataset.зона + "→" + ч.textContent)));
})();
