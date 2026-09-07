/* Прогін ПОКАЗУ в jsdom БЕЗ Pyodide й без мережі: IndexedDB підмінено
   fake-indexeddb, `fetch` — заглушкою. Ловить те, чого не бачить node --check:
   мертву сторінку на хеші з параметрами, старий шлях під новою кнопкою,
   виклик моделі без кольорів/обхватів, розсинхрон парсера.

   Запуск:  NODE_PATH=<тека з jsdom і fake-indexeddb> node тест_показу.js
   Тестується ШАБЛОН показу з підставленими плейсхолдерами — тобто та сама
   логіка, що й у збірці; вантаж Python сюди не входить (це не його тест). */
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");
const { IDBFactory, IDBKeyRange } = require("fake-indexeddb");

let провалів = 0;
const тест = (н, у, що) => { if (у) console.log("  ✓ " + н);
  else { провалів++; console.log("  ✗ " + н + "  →  " + JSON.stringify(що)); } };
const пауза = мс => new Promise(р => setTimeout(р, мс));

const шаблон = fs.readFileSync(path.join(__dirname, "показ.html"), "utf8");

function сторінка({url, фід = "каталог_brief.xml", підпис = "каталог_стенд.xml · 639 речей"} = {}) {
  let html = шаблон
    .replace("__МОДУЛІ_ПОКАЗУ__", "ЗАГЛУШКА").replace(/__ЗБІРКА_ПОКАЗУ__/g, "тест")
    .replace("__ВІДБИТОК__", "abc").replace("__ФІД_ПОКАЗУ__", фід).replace("__КАТАЛОГ_ПОКАЗУ__", підпис)
    .replace(/<script src="https:\/\/cdn\.jsdelivr\.net[^"]*"><\/script>/, "<script>window.loadPyodide=null;</script>");
  const помилки = [];
  const дом = new JSDOM(html, {runScripts: "dangerously", pretendToBeVisual: true, url,
    beforeParse(w) {
      w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange;
      w.fetch = () => Promise.reject(new Error("мережі в тесті нема"));
      w.scrollTo = () => {};
      w.document.execCommand = () => true;
      w.Blob = Blob; w.Response = Response; w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
      w.CompressionStream = CompressionStream; w.DecompressionStream = DecompressionStream;
      w.Element.prototype.scrollIntoView = () => {};
    }});
  дом.window.addEventListener("error", e => помилки.push(String(e.message)));
  return {дом, w: дом.window, d: дом.window.document, помилки};
}

(async () => {
  console.log("1. СТАРТ БЕЗ ХЕША: повна збірка");
  {
    const {w, d, помилки} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html"});
    await пауза(300);
    const $ = id => d.getElementById(id);
    тест("скрипт піднявся без винятків", помилки.length === 0, помилки);
    тест("екран профілю видно, навігація на місці",
         $("е-профіль").style.display !== "none" && $("ніг").style.display !== "none", null);
    тест("ЄДИНА_СТОРІНКА: картка «Зібрати образи» видно, картка «окрема сторінка» схована",
         $("зб-картка").style.display === "block" && $("перехід").style.display === "none",
         [$("зб-картка").style.display, $("перехід").style.display]);
    тест("у міст іде ім'я фіду від збирача, не літерал",
         w.eval("вхідМостаП().каталог") === "каталог_brief.xml", w.eval("вхідМостаП().каталог"));
    тест("П.каталог для людини й вердикта — підпис збирача",
         w.eval("КАТАЛОГ_ПІДПИС_П") === "каталог_стенд.xml · 639 речей", w.eval("КАТАЛОГ_ПІДПИС_П"));
    /* «Далі» на останньому екрані — збирання ТУТ, а не перехід у стенд */
    w.eval("екран(3)");
    тест("на палітрі кнопка підписана «Зібрати образи»", $("н-далі").textContent === "Зібрати образи", $("н-далі").textContent);
    $("н-далі").click(); await пауза(300);
    тест("без кольорів/обхватів/нагоди збирання НЕ стартує і каже, чого бракує (нема виклику моделі)",
         /Спершу додайте/.test($("зб-статус").textContent) && /кольори/.test($("зб-статус").textContent)
         && /обхвати/.test($("зб-статус").textContent), $("зб-статус").textContent);
    тест("старий шлях не зачепило: статус переходу порожній", $("п-стан").textContent === "", $("п-стан").textContent);
    тест("кнопка «Зібрати чотири образи» не заблокована після відмови", !$("зб-пуск").disabled, $("зб-пуск").disabled);
  }

  console.log("2. ХЕШ ІЗ ПАРАМЕТРАМИ МОСТУ — НЕ ПАКЕТ");
  {
    const {w, d, помилки} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html#міст=https://lyusterko-mist.mighty-rochy.workers.dev&т=tok-a1&модель=claude-sonnet-5"});
    await пауза(300);
    const $ = id => d.getElementById(id);
    тест("без винятків", помилки.length === 0, помилки);
    тест("екрани введення НЕ сховано, навігація є",
         $("е-профіль").style.display !== "none" && $("ніг").style.display !== "none"
         && $("смуга-профілів").style.display !== "none", null);
    тест("шапка не каже «Пакет не розпакувався»", !/не розпакувався/.test($("ш-рядок").textContent), $("ш-рядок").textContent);
    тест("адреса й токен мосту прочитані з хеша", w.eval("МІСТ_П.адреса") === "https://lyusterko-mist.mighty-rochy.workers.dev"
         && w.eval("МІСТ_П.токен") === "tok-a1", w.eval("JSON.stringify(МІСТ_П)"));
    тест("модель із хеша переважує збірку", w.eval("МОДЕЛЬ_П") === "claude-sonnet-5", w.eval("МОДЕЛЬ_П"));
    тест("…і збережені на пристрої для наступного відкриття без хеша",
         w.localStorage.getItem("міст:адреса") === "https://lyusterko-mist.mighty-rochy.workers.dev"
         && w.localStorage.getItem("міст:токен") === "tok-a1", null);
  }

  console.log("2б. БЕЗ МОСТУ НА PAGES — ВІДМОВА СЛОВАМИ, НЕ ЧОТИРИ ЗБОЇ; HASHCHANGE ПІДХОПЛЮЄ МІСТ");
  {
    const {w, d, помилки} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html"});
    await пауза(300);
    const $ = id => d.getElementById(id);
    /* профіль заповнено, щоб дійти до перевірки мосту */
    w.eval("КОЛІР = {шкіра:'#f2d6c4', волосся:'#4a4644', очі:'#6b8cae', кільце:null, точки:null}");
    for (const [і, v] of [["мр-плечі", 96], ["мр-груди", 92], ["мр-талія", 74], ["мр-стегна", 100]]) $(і).value = v;
    $("сц-слова").value = "кафе з подругою";
    w.eval("зібратиОбразиП()"); await пауза(200);
    /* 04.09.2026: адреса мосту на Pages тепер типова — бракувати може лише ТОКЕНА */
    тест("без токена на https-походженні збирання не стартує і каже, як відкрити посилання (#токен)",
         /токен/.test($("зб-статус").textContent) && !$("зб-пуск").disabled, $("зб-статус").textContent);
    тест("жодного виклику моделі не було", помилки.length === 0, помилки);
    w.location.hash = "#міст=https://m.workers.dev&т=tok-b2";
    await пауза(400);
    тест("hashchange: адреса й токен підхоплені без перезавантаження",
         w.eval("МІСТ_П.адреса") === "https://m.workers.dev" && w.eval("МІСТ_П.токен") === "tok-b2"
         && w.localStorage.getItem("міст:токен") === "tok-b2", w.eval("JSON.stringify(МІСТ_П)"));
    тест("…і екрани введення після hashchange не сховано", $("е-профіль").style.display !== "none", null);
  }

  console.log("2в. КОЛЬОРИ З ПОРТРЕТА — СТОРІНКА КЛИЧЕ МОДЕЛЬ САМА");
  {
    const {w, d, помилки} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html#міст=https://m.workers.dev&т=tok-a1"});
    await пауза(300);
    const $ = id => d.getElementById(id);
    тест("кнопка «Зчитати кольори з портрета» є, ручний шлях під розкривачем", !!$("кол-зчитати") && !!$("кол-копія"), null);
    $("кол-зчитати").click(); await пауза(200);
    тест("без портрета — каже додати портрет, модель не кличе", /портрет/.test($("кол-стан").textContent), $("кол-стан").textContent);
    await w.eval("писатиКв(ключФото('портрет'), 'портрет-заглушка')");
    w.блобВБазу = async () => ({тип:"image/jpeg", дані:"AAAA", ширина:1568, висота:1176, якість:0.85});
    let викликів = 0, отримано = null;
    w.модельП = async (промпт, фото) => { викликів++; отримано = {промпт, фото};
      return "шкіра 1 #f2d6c4\nшкіра 2 #efd0bc\nволосся 1 #4a4644\nочі #6b8cae\nосвітлення: нейтральне\nслово шкіра: світла\nслово волосся: темне\nслово очі: середні"; };
    $("кол-зчитати").click(); await пауза(400);
    тест("з портретом: один виклик моделі з ПРОМПТ_КОЛІР і фото; кольори застосовано; свотчі намальовано",
         викликів === 1 && отримано.фото && отримано.фото.дані === "AAAA" && /ЇЇ ВЛАСНІ кольори/.test(отримано.промпт)
         && w.eval("КОЛІР.шкіра") === "#f2d6c4" && w.eval("КОЛІР.очі") === "#6b8cae"
         && d.querySelectorAll("#кол-свотчі .св").length === 4 && /Прочитано/.test($("кол-стан").textContent),
         [викликів, w.eval("JSON.stringify(КОЛІР)"), $("кол-стан").textContent]);
    w.модельП = async () => "не читається: обличчя менше чверті кадру";
    $("кол-зчитати").click(); await пауза(300);
    тест("відмова моделі доходить словами", /відмовилась/.test($("кол-стан").textContent) && /чверті/.test($("кол-стан").textContent),
         $("кол-стан").textContent);
    тест("без винятків", помилки.length === 0, помилки);
  }

  console.log("2г. ФОТО ЗМЕНШУЄТЬСЯ ПЕРЕД ВІДПРАВКОЮ (413 на першому прогоні)");
  {
    const {w, d} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html"});
    await пауза(300);
    /* jsdom не має createImageBitmap і canvas.toDataURL — підставляємо їх так,
       щоб перевірити АРИФМЕТИКУ зменшення, а не растеризацію браузера */
    let малювали = null;
    w.createImageBitmap = async () => ({width:4000, height:3000, close(){}});
    w.HTMLCanvasElement.prototype.getContext = function(){ return {drawImage: (бм, x, y, ш, в) => { малювали = [ш, в]; }}; };
    let якості = [];
    w.HTMLCanvasElement.prototype.toDataURL = function(тип, я){ якості.push(я);
      /* «важке» фото: перші дві якості вище стелі, третя — під нею */
      const n = я >= 0.85 ? 400000 : (я >= 0.7 ? 300000 : 100000);
      return "data:image/jpeg;base64," + "A".repeat(n); };
    const р = await w.eval("блобВБазу(new Blob(['x'], {type:'image/jpeg'}))");
    тест("довга сторона 4000 → 1568, пропорції збережено (1568×1176)",
         р.ширина === 1568 && р.висота === 1176 && малювали[0] === 1568 && малювали[1] === 1176, малювали);
    тест("якість знижується, поки не влізе під стелю (0.85 → 0.7 → 0.55), тип jpeg",
         JSON.stringify(якості) === "[0.85,0.7,0.55]" && р.якість === 0.55 && р.тип === "image/jpeg"
         && р.дані.length === 100000, [якості, р.якість, р.дані.length]);
    /* легке фото — одна ітерація */
    якості = [];
    w.HTMLCanvasElement.prototype.toDataURL = function(тип, я){ якості.push(я);
      return "data:image/jpeg;base64," + "A".repeat(50000); };
    const р2 = await w.eval("блобВБазу(new Blob(['x'], {type:'image/jpeg'}))");
    тест("легке фото — одна ітерація, якість 0.85", JSON.stringify(якості) === "[0.85]" && р2.якість === 0.85, якості);
    /* канвас недоступний → фолбек `_блобВБазуЯкЄ`. Сам FileReader у jsdom
       примхливий до Blob, тому перевіряємо не байти, а те, що фолбек
       ВИКЛИКАЄТЬСЯ і зменшення не ковтає помилку мовчки. */
    w.createImageBitmap = async () => { throw new Error("нема"); };
    let фолбек = 0;
    w.eval("window._старий = _блобВБазуЯкЄ;");
    w._блобВБазуЯкЄ_перехоплення = () => { фолбек++; return Promise.resolve({тип:"image/jpeg", дані:"ЯКЄ"}); };
    w.eval("_блобВБазуЯкЄ = (б)=>window._блобВБазуЯкЄ_перехоплення(б);");
    const р3 = await w.eval("блобВБазу(new window.Blob([new Uint8Array([1,2,3])], {type:'image/jpeg'}))");
    тест("без createImageBitmap — фото йде як є через фолбек (не тиша)",
         фолбек === 1 && р3.дані === "ЯКЄ" && !р3.ширина, [фолбек, р3]);
  }

  console.log("2д. ЧЕРГА ВИКЛИКІВ: не більше двох у польоті, з паузою (429 на прогоні 17:33)");
  {
    const {w} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html#міст=https://m.workers.dev&т=tok-a1"});
    await пауза(300);
    let уПольоті = 0, максимум = 0;
    const старти = [];
    /* під ІНШИМ іменем: `_дзвінокП` — властивість window, і підміна на себе
       дала б ту саму рекурсію, що вбила прогін 15:22 */
    w._заглушкаДзвінка = async () => {
      старти.push(Date.now()); уПольоті++; максимум = Math.max(максимум, уПольоті);
      await new Promise(р=>setTimeout(р, 300));
      уПольоті--;
      return {ok:true, status:200, headers:{get:()=>null, forEach:()=>{}},
              json: async () => ({content:[{type:"text", text:"ок"}], usage:{}, stop_reason:"end_turn"})};
    };
    w.eval("_дзвінокП = (...а)=>window._заглушкаДзвінка(...а);");
    const t0 = Date.now();
    await w.eval("Promise.all([1,2,3,4,5,6].map(()=>модельП('промпт', null)))");
    const всього = (Date.now() - t0) / 1000;
    тест("шість викликів: у польоті не більше двох одночасно", максимум <= 2 && старти.length === 6, [максимум, старти.length]);
    /* Конструкція — не «один за одним», а «пара кожні 2.5 с»: більше двох у
       польоті нема, і в жодне двосекундне вікно не влазить понад два старти.
       Саме сплеск із ЧОТИРЬОХ 32-тисячних промптів дав 429 о 17:33. */
    const у_вікні = старти.map((т, i) => старти.filter(x => x >= т && x < т + 2000).length);
    тест("у жодне 2-секундне вікно не влазить понад два старти", Math.max(...у_вікні) <= 2, у_вікні);
    тест("черга не вішає: шість викликів пройшли за розумний час", всього < 20 && всього >= 4, всього.toFixed(1));
  }

  console.log("2е. МІСТ ДО PYTHON: без спільного стану між паралельними викликами (гонка 18:45)");
  {
    const {w} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html"});
    await пауза(300);
    /* заглушка Pyodide: пам'ятає КОД кожного виклику; «виконує» його з
       затримкою, щоб виклики перекривались, як у чотирьох рук */
    const коди = [];
    /* `pyodideП` — `let` у скрипті, не властивість window: підставляємо через eval */
    w._заглушкаPy = { runPythonAsync: async (код) => { коди.push(код); await new Promise(р=>setTimeout(р, 50));
      return JSON.stringify({луна: код.length}); } };
    w.eval("pyodideП = window._заглушкаPy; підняти_міст_показу = async () => pyodideП;");
    const дані = ["A","B","C","D"].map(х => ({хто: х, вага: "я".repeat(50000 + х.charCodeAt(0))}));
    await w.eval("Promise.all(" + JSON.stringify(дані) + ".map(д => містП('запити', д)))");
    тест("чотири паралельні виклики — чотири різні коди, кожен із СВОЇМИ даними всередині (літерал, не глобальна)",
         коди.length === 4 && дані.every((д, i) => коди[i].includes(JSON.stringify(JSON.stringify(д)).slice(1, 60)))
         && !коди.some(к => /__ВХІД_МОСТА|from js import/.test(к)), коди.map(к => к.slice(0, 40)));
  }

  console.log("3. СПРАВЖНІЙ ПАКЕТ У ХЕШІ — КАРТКИ МАЛЮЮТЬСЯ");
  {
    const пакет = {в: "ПОКАЗ-V1", збірка: "тест-пакет", каталог: "каталог_стенд.xml · 639 речей", профіль: "Оля",
      розклад: "3142", картки: [
        {рука: "1", текст: "Сукня міді.\nСВІДОМО: пояс поверх жакета\nОБРАЗ: ж-00003@gepur.com, ж-00010@gepur.com",
         речі: [{id: "ж-00003@gepur.com", назва: "Чорна сукня", ціна: 6999, фото: "https://img.example/1.jpg", урл: "https://gepur.com/x", слот: "сукня"}],
         мітки: ["довжина"], знахідки: []},
        {рука: "4", текст: "Проза без каталогу", речі: [], мітки: []}]};
    const байти = new TextEncoder().encode(JSON.stringify(пакет));
    const ст = new Uint8Array(await new Response(new Blob([байти]).stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer());
    const б64 = Buffer.from(ст).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    const {w, d, помилки} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html#" + б64});
    await пауза(500);
    const $ = id => d.getElementById(id);
    тест("без винятків", помилки.length === 0, помилки);
    тест("дві картки", d.querySelectorAll("#картки .картка").length === 2, d.querySelectorAll("#картки .картка").length);
    тест("екрани введення сховано", $("е-профіль").style.display === "none" && $("ніг").style.display === "none", null);
    тест("шапка несе збірку й каталог пакета", /тест-пакет/.test($("ш-рядок").textContent) && /639/.test($("ш-рядок").textContent), $("ш-рядок").textContent);
    const текст = $("к-0").querySelector(".текст-образу").textContent;
    тест("людині — без «ОБРАЗ:» і без id", !/ОБРАЗ:/.test(текст) && !/ж-000/.test(текст), текст);
    тест("«Як це носити» винесено окремо", /пояс поверх жакета/.test($("к-0").querySelector(".задум").textContent), null);
    тест("фото речі з посиланням у магазин", $("к-0").querySelector(".річ img").src === "https://img.example/1.jpg"
         && /gepur/.test($("к-0").querySelector(".річ a[href*='gepur']").href), null);
    тест("кнопка «Приміряти на себе» на кожній картці", !!$("прмк-0") && !!$("прмк-1"), null);
  }

  console.log("4. ЛЕГКА ЗБІРКА (без фіду): старий шлях лишається");
  {
    const {w, d, помилки} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html", фід: "", підпис: "без каталогу"});
    await пауза(300);
    const $ = id => d.getElementById(id);
    тест("без винятків", помилки.length === 0, помилки);
    тест("ЄДИНА_СТОРІНКА=false: картка переходу видно, збирання сховано",
         !w.eval("ЄДИНА_СТОРІНКА") && $("перехід").style.display === "block" && $("зб-картка").style.display === "none", null);
    w.eval("екран(3)"); $("н-далі").click(); await пауза(300);
    тест("«Далі» веде старим шляхом і теж каже, чого бракує", /Спершу додайте/.test($("п-стан").textContent), $("п-стан").textContent);
    w.eval("зібратиОбразиП()"); await пауза(100);
    тест("пряме збирання відмовляється без фіду словами", /без каталогу/.test($("зб-статус").textContent), $("зб-статус").textContent);
  }

  console.log("5. ПАРСЕР КОЛЬОРІВ (перенесено з тест_парсера.js — той читав неіснуючий файл)");
  {
    const {w} = сторінка({url: "https://mightyrochy.github.io/kod-shi-data/показ.html"});
    await пауза(200);
    const р = т => w.eval("розібратиКолір(" + JSON.stringify(т) + ")");
    const a = р("шкіра 1 #C9937B шкіра 2 #D09D84 шкіра 3 #CE987F волосся 1 #B4956F волосся 2 #C5AE80 волосся 3 #7A5B4D очі #7F8C82 кільце #5F6259 освітлення: теплий жовто-оранжевий відтінок нейтралізовано приблизно на 8–10% у бік нейтрального денного світла слово шкіра: середня слово волосся: світле слово очі: світлі");
    тест("одним абзацом: 3 шкіри, 3 волосся, око, кільце, слова", a.шкіра.length === 3 && a.волосся.length === 3
         && a.очі === "#7f8c82" && a.кільце === "#5f6259" && a.безмітки === 0
         && a.слова.шкіра === "середня" && a.слова.волосся === "світле" && a.слова.очі === "світлі", a);
    тест("освітлення чисте", a.освітлення && a.освітлення.indexOf("теплий") === 0 && a.освітлення.indexOf("слово") < 0, a.освітлення);
    const b = р("шкіра 1 #f2d6c4\nшкіра 2 #efd0bc\nволосся 1 #4a4644\nочі #6b8cae\nосвітлення: нейтральне\nслово шкіра: світла");
    тест("по рядках", b.шкіра.length === 2 && b.волосся.length === 1 && b.очі === "#6b8cae" && b.слова.шкіра === "світла", b);
    const c = р("**шкіра 1** — `#F2D6C4`, **шкіра 2** — `#EFD0BC`\n* волосся: #4A4644\n* очі: #6B8CAE");
    тест("маркдаун не з'їдає ґратку", c.шкіра.length === 2 && c.волосся.length === 1 && c.очі === "#6b8cae", c);
    const d2 = р("шкіра: #f2d6c4, #efd0bc, #eccdb8; волосся: #4a4644, #55504e; очі: #6b8cae");
    тест("мітка успадковується", d2.шкіра.length === 3 && d2.волосся.length === 2 && d2.очі === "#6b8cae", d2);
    const e = р("не читається: обличчя менше чверті кадру");
    тест("відмова", e.відмова === "обличчя менше чверті кадру", e.відмова);
    тест("щабель слова", w.eval("[щабель('дуже темна'), щабель('світле'), щабель('середні'), щабель('х')].join()") === "0,3,2,", null);
    const [опис, задум] = w.eval("людською(" + JSON.stringify("ПІДПИС: тест\nНавмисно — рукав закочено\nЖакет ж-07826@dolcedonna.com.ua і #412·29 у тоні #4a4644 .\nОБРАЗ: ж-1, ж-2") + ")");
    тест("людською: без ПІДПИС/ОБРАЗ/id/пар/hex, задум окремо",
         !/ПІДПИС|ОБРАЗ|ж-07826|#412|#4a4644/.test(опис) && задум[0] === "рукав закочено", [опис, задум]);
  }

  console.log(провалів ? ("ВПАЛО " + провалів) : "ПОКАЗ: усе зелене");
  process.exit(провалів ? 1 : 0);
})().catch(e => { console.error("тест не запустився:", e); process.exit(2); });
