/* Проба рядка 167 (голос): біля яких полів є кнопка мікрофона, що стається без
   розпізнавання і чи жодна гілка голосу не надсилає текст сама. Друкує факт.
   Запуск із теки `джерела`: NODE_PATH=node_modules node проби/holos_167.js */
const fs = require("fs"), path = require("path"), ДЖ = __dirname + "/..";
const { JSDOM } = require("jsdom"), { IDBFactory, IDBKeyRange } = require("fake-indexeddb");
const { прочитатиДовідникJSON, підставитиШаблон } = require(path.join(ДЖ, "показ_шаблон.js"));
const СКАЗАНЕ = "в суботу весілля подруги о п'ятій, хочу щось легке";
class Фейк {                                     // підставне розпізнавання браузера
  start(){ setTimeout(()=>this.onresult && this.onresult({results:[[{transcript:СКАЗАНЕ}]], resultIndex:0}), 0); }
  stop(){ this.onend && this.onend({}); }
}
const html = підставитиШаблон(fs.readFileSync(path.join(ДЖ, "показ.html"), "utf8"),
  {__МОДУЛІ_ПОКАЗУ__:"ЗАГЛУШКА", __ЗБІРКА_ПОКАЗУ__:"проба-167", __ВІДБИТОК__:"abc",
   __ФІД_ПОКАЗУ__:"каталог_brief.xml", __КАТАЛОГ_ПОКАЗУ__:"каталог_стенд.xml",
   __ДОВІДНИК_ПОКАЗУ__:прочитатиДовідникJSON(ДЖ)})
  .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, "<script>window.loadPyodide=null;</script>");
const w = new JSDOM(html, {runScripts:"dangerously", pretendToBeVisual:true, url:"https://x.github.io/показ.html",
  beforeParse(w){ w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange; w.scrollTo = ()=>{};
    w.fetch = ()=>Promise.reject(new Error("мережі в пробі нема")); w.Element.prototype.scrollIntoView = ()=>{};
    w.SpeechRecognition = Фейк; }}).window;
const $ = і => w.document.getElementById(і), пауза = мс => new Promise(р=>setTimeout(р, мс));
(async ()=>{
  await пауза(900);
  w.eval("П={картки:[{рука:'1',речі:[],знахідки:[],питання:[],мітки:[],підпис:'п',текст:'т'}]}");
  w.document.body.appendChild(w.eval("рендерКартку(0)"));
  for (const [і, п, к] of [["розмова", "чат-поле", "чат-мікрофон"], ["«Своїми словами»", "ком-0", "мік-ком-0"]])
    console.log("кнопка біля поля " + і + ": " + (!!$(п) && !!$(к)) + " (" + к + ")");
  $("чат-мікрофон").click(); await пауза(30);
  console.log("продиктовано в поле розмови: " + JSON.stringify($("чат-поле").value));
  console.log("реплік у стрічці після диктування: " + w.eval("ЧАТ_П.length")
              + "  (текст сам НЕ надіслано — надсилає дотик «Надіслати»)");
  $("мік-ком-0").click(); await пауза(30);
  console.log("продиктовано в «Своїми словами»: " + JSON.stringify(w.eval("відповідь(0).коментар"))
              + " · позначка `коментар_голосом` = " + w.eval("відповідь(0).коментар_голосом"));
  console.log("у модулі голосу викликів `слатиЧатП`/`записати` — "
              + (/слатиЧатП|записати\(/.test(w.eval("String(привʼязатиГолос)")) ? "Є, ЦЕ ПОЛОМКА" : "нема"));
  delete w.SpeechRecognition;                    // прогін без розпізнавання
  $("чат-голос").textContent = ""; $("чат-мікрофон").click();
  console.log("без розпізнавання, дотик по кнопці: " + JSON.stringify($("чат-голос").textContent));
})();
