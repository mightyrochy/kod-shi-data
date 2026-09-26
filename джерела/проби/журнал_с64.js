/* Приймальна проба С-64: журнал вердиктів ЕКСПОРТУЄТЬСЯ з новими полями.
   §9 `тест_показу.js` міряє шапку й текст функції `записати`; це — інше
   твердження: чотири руки справді записані і ВИВЕДЕНІ в TSV, а дев'ять
   колонок Т-11 несуть значення, а не порожні стовпчики. Поломку й контроль
   дає живий `bridge.запити`, не літерал: рядок журналу мусить витримати те,
   що приїде з мосту на прогоні.
   Запуск із теки `джерела`: node проби/журнал_с64.js [зібраний.html] */
const fs = require("fs"), path = require("path"), { execSync } = require("child_process");
const { JSDOM } = require("jsdom"), { IDBFactory, IDBKeyRange } = require("fake-indexeddb");
const ДЖ = path.join(__dirname, "..");
const ФАЙЛ = process.argv[2] ? path.resolve(process.argv[2]) : path.join(ДЖ, "показ.html");

/* живий вихід мосту: саме він наповнює `поломка`, `різних_правил`, `пул_спільних` */
const міст = JSON.parse(execSync('python3 -c "import json, bridge as B;'
  + ' r = json.loads(B.виклик(\'запити\', open(\'стенд_вх.json\').read()));'
  + ' print(json.dumps({\'поломка\': r.get(\'поломка\'), \'контроль\': (r.get(\'мета\') or {}).get(\'контроль\'),'
  + ' \'довжини\': sorted((r.get(\'мета\') or {}).get(\'довжини\') or {})}, ensure_ascii=False))"',
  {cwd: ДЖ, encoding: "utf8"}).trim().split("\n").pop());

const КАРТКА = (рука, n) => ({рука, ітерацій: рука === "1" || рука === "2" ? 2 : 1, викликів: рука <= "2" ? 3 : 1,
  текст: "Сукня міді.\nСВІДОМО: пояс поверх жакета", підпис: "рука " + рука,
  речі: [{id: "ж-0000" + n + "@gepur.com", назва: "Сукня", ціна: 6999, слот: "сукня"}], мітки: [], знахідки: [],
  свідомі: ["пояс поверх жакета"], невиконано: рука === "3" ? ["з-о1-2"] : [],
  різноманітність: {ок: рука !== "4", групи: рука === "4" ? [["о2", "о5"]] : []}});

(async () => {
  let html = fs.readFileSync(ФАЙЛ, "utf8")
    .replace("__МОДУЛІ_ПОКАЗУ__", "ЗАГЛУШКА").replace(/__ЗБІРКА_ПОКАЗУ__/g, "проба")
    .replace("__ВІДБИТОК__", "abc").replace("__ФІД_ПОКАЗУ__", "каталог_brief.xml")
    .replace("__КАТАЛОГ_ПОКАЗУ__", "каталог_стенд.xml").replace("__ДОВІДНИК_ПОКАЗУ__", '{"нагоди":[],"місця":[],"коди":[]}')
    .replace(/const МОДУЛІ_ПОКАЗУ = "[^"]*";/, 'const МОДУЛІ_ПОКАЗУ = "ЗАГЛУШКА";')
    .replace(/<script src="https:\/\/cdn\.jsdelivr\.net[^"]*"><\/script>/, "<script>window.loadPyodide=null;</script>");
  const пакет = {в: "ПОКАЗ-V1", збірка: "проба-с64", каталог: "каталог_стенд.xml", профіль: "Оля", розклад: "1234",
                 пул: 208, картки: ["1", "2", "3", "4"].map(КАРТКА)};
  const ст = new Uint8Array(await new Response(new Blob([new TextEncoder().encode(JSON.stringify(пакет))])
    .stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer());
  const хеш = Buffer.from(ст).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const дом = new JSDOM(html, {runScripts: "dangerously", pretendToBeVisual: true,
    url: "https://mightyrochy.github.io/kod-shi-data/показ.html#" + хеш,
    beforeParse(w) {
      w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange;
      w.fetch = () => Promise.reject(new Error("мережі в пробі нема"));
      w.scrollTo = () => {}; w.Element.prototype.scrollIntoView = () => {};
      w.Blob = Blob; w.Response = Response; w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
      w.CompressionStream = CompressionStream; w.DecompressionStream = DecompressionStream;
    }});
  const w = дом.window;
  await new Promise(р => setTimeout(р, 700));
  /* стан збирання: те, що на прогоні лишає по собі виклик 0 і `запити` */
  w._міст = міст;
  w.eval("ЗБ = {картки:[], стадії:[], етап:[], діагноз:[], ключ:null, готово:true,"
       + " поломка: window._міст.поломка, контроль: window._міст.контроль, чат:[{хто:'людина',текст:'побачення'},{хто:'ші',текст:'де саме?'}]};"
       + "ПАСПОРТ_П = {джерело:'модель', нагода:'побачення'}; ВИПАДОК_ПАСПОРТА_П = 'побачення, ресторан';"
       /* знімок прогону (ділянка 6/8): вхід вердикта читається з нього, як у шві */
       + "ЗБ.паспорт = ПАСПОРТ_П; ЗБ.випадок = ВИПАДОК_ПАСПОРТА_П; П.знімок = знімокПрогонуП(ЗБ);");
  for (let п = 0; п < 4; п++) {
    w.eval("відповідь(" + п + ").верд = 'вдягну як є'; відповідь(" + п + ").річ = 'так, це вона';");
    await w.eval("записати(" + п + ")");
  }
  const рядки = JSON.parse(await w.eval("усіВердикти().then(в => JSON.stringify("
    + "[ШАПКА.join('\\t')].concat(в.map(з => ШАПКА.map(к => чисто(з[к])).join('\\t')))))"));
  const шапка = рядки[0].split("\t"), тіло = рядки.slice(1).map(р => р.split("\t"));
  const НОВІ = ["поломка", "різних_правил", "пул_спільних", "викликів",
                "паспорт_джерело", "чат_повідомлень", "свідомі", "виконано", "різноманітність"];
  const зн = (р, к) => р[шапка.indexOf(к)];
  let провалів = 0;
  const проба = (н, ок, що) => { if (ок) console.log("ок      " + н);
    else { провалів++; console.log("ПОЛОМКА " + н + "  →  " + JSON.stringify(що)); } };
  проба("міст дав живу поломку руки 2", !!(міст.поломка || {}).назва, міст.поломка);
  проба("чотири руки записані й вивантажені", тіло.length === 4 && тіло.every(р => зн(р, "рука")), тіло.map(р => зн(р, "рука")));
  проба("жоден рядок не з'їхав по колонках", тіло.every(р => р.length === шапка.length), тіло.map(р => р.length));
  /* поломка — лише в руки 2, решта вісьмох колонок мусять бути в КОЖНОМУ рядку */
  проба("`поломка` стоїть у руки 2 і називає, що саме змінено",
        /.+: .+/.test(зн(тіло[1], "поломка")) && тіло.filter((_, і) => і !== 1).every(р => зн(р, "поломка") === ""),
        тіло.map(р => зн(р, "поломка")));
  for (const к of НОВІ.filter(к => к !== "поломка"))
    проба("колонка «" + к + "» несе значення в усіх чотирьох руках",
          тіло.every(р => зн(р, к) !== ""), тіло.map(р => зн(р, к)));
  console.log("\nшапка: " + шапка.length + " колонок, нових " + НОВІ.length);
  for (const р of тіло) console.log("рука " + зн(р, "рука") + " · " + НОВІ.map(к => к + "=" + (зн(р, к) || "—")).join(" · "));
  process.exit(провалів ? 1 : 0);
})().catch(e => { console.error("проба не запустилась:", e); process.exit(2); });
