/* Проба: що з паспорта розмови їде в «Оціни мій образ» (`сценарійПаспортаП`). Типове (нагода «щоденне»
   під річ з фото, замовчування форми) — не її слово: у оцінку не йде. Друкує факт.
   Запуск із теки `джерела`: NODE_PATH=node_modules node проби/оцінка_типові_поля_паспорта.js */
const fs = require("fs"), path = require("path"), ДЖ = __dirname + "/..";
const { JSDOM } = require("jsdom"), { IDBFactory, IDBKeyRange } = require("fake-indexeddb");
const { прочитатиДовідникJSON, підставитиШаблон } = require(path.join(ДЖ, "показ_шаблон.js"));
const html = підставитиШаблон(fs.readFileSync(path.join(ДЖ, "показ.html"), "utf8"),
  {__МОДУЛІ_ПОКАЗУ__:"ЗАГЛУШКА", __ЗБІРКА_ПОКАЗУ__:"проба-оц", __ВІДБИТОК__:"abc",
   __ФІД_ПОКАЗУ__:"каталог_brief.xml", __КАТАЛОГ_ПОКАЗУ__:"каталог_стенд.xml",
   __ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(ДЖ)})
  .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, "<script>window.loadPyodide=null;</script>");
const w = new JSDOM(html, {runScripts:"dangerously", pretendToBeVisual:true, url:"https://x.github.io/показ.html",
  beforeParse(w){ w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange; w.scrollTo = ()=>{};
    w.fetch = ()=>Promise.reject(new Error("мережі в пробі нема")); w.Element.prototype.scrollIntoView = ()=>{}; }}).window;
const пауза = мс => new Promise(р=>setTimeout(р, мс));
const їде = (п) => { w.eval("ПАСПОРТ_П=" + JSON.stringify(п)); return JSON.stringify(w.eval("сценарійПаспортаП()")); };
(async ()=>{
  await пауза(900);
  const речі = {нагода:"щоденне", темп_c:18, джерело_полів:{нагода:"item_default", темп_c:"form_default"}};
  const її = {нагода:"театр", місце:"зал", темп_c:5, джерело_полів:{нагода:"conversation", місце:"conversation", темп_c:"her"}};
  const мішане = {нагода:"робота", дрес_код:"business casual", темп_c:18, джерело_полів:{нагода:"conversation", дрес_код:"conversation", темп_c:"form_default"}};
  console.log("типове під річ з фото → в оцінку: " + їде(речі));
  console.log("її слова → в оцінку: " + їде(її));
  console.log("мішане (темп_c — замовчування форми) → в оцінку: " + їде(мішане));
})();
