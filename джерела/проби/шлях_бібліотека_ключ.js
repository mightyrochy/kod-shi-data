/* Проба Л-7: ДВА ЗБОРИ З ОДНАКОВИМ РОЗКЛАДОМ — ДВА ЗАПИСИ, ВЕРДИКТИ КОЖНОГО СВОЇ.
   До правки ключ бібліотеки був `збірка·розклад·профіль`, а `розклад` — одна з 24
   перестановок рук: другий збір затирав перший (`put` за тим самим ключем), а його
   вердикти сідали на плитки нового. Проба міряє обидва числа на живій сторінці —
   «до» рахується тим самим старим ключем на тих самих записах, «після» — тим, що
   справді лежить у сховищі.
   Запуск із теки `джерела`: NODE_PATH=<тека з jsdom і fake-indexeddb> node проби/шлях_бібліотека_ключ.js */
const fs = require("fs"), path = require("path");
const { JSDOM } = require("jsdom"), { IDBFactory, IDBKeyRange } = require("fake-indexeddb");
const ФАЙЛ = process.argv[2] ? path.resolve(process.argv[2]) : path.join(__dirname, "..", "показ.html");
const КАРТКА = підпис => ({рука: "1", ітерацій: 1, викликів: 1, текст: підпис, опис: підпис, підпис,
  речі: [{id: "ж-1@g.com", назва: "Сукня", ціна: 3000, слот: "сукня"}], мітки: [], знахідки: [], питання: [],
  етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null, різноманітність: null, мова: [], мова_спроб: 0});

(async () => {
  const html = fs.readFileSync(ФАЙЛ, "utf8")
    .replace("__МОДУЛІ_ПОКАЗУ__", "ЗАГЛУШКА").replace(/__ЗБІРКА_ПОКАЗУ__/g, "проба-л7")
    .replace("__ВІДБИТОК__", "abc").replace("__ФІД_ПОКАЗУ__", "каталог_brief.xml")
    .replace("__КАТАЛОГ_ПОКАЗУ__", "каталог_стенд.xml").replace("__ДОВІДНИК_ПОКАЗУ__", '{"нагоди":[],"місця":[],"коди":[]}')
    .replace(/const МОДУЛІ_ПОКАЗУ = "[^"]*";/, 'const МОДУЛІ_ПОКАЗУ = "ЗАГЛУШКА";')
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, "<script>window.loadPyodide=null;</script>");
  const пакет = {в: "ПОКАЗ-V1", збірка: "проба-л7", каталог: "каталог_стенд.xml", профіль: "Оля",
                 розклад: "1234", пул: 100, картки: [КАРТКА("прогін А")]};
  const ст = new Uint8Array(await new Response(new Blob([new TextEncoder().encode(JSON.stringify(пакет))])
    .stream().pipeThrough(new CompressionStream("gzip"))).arrayBuffer());
  const хеш = Buffer.from(ст).toString("base64").replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  const w = new JSDOM(html, {runScripts: "dangerously", pretendToBeVisual: true,
    url: "https://mightyrochy.github.io/kod-shi-data/показ.html#" + хеш,
    beforeParse(w) { w.indexedDB = new IDBFactory(); w.IDBKeyRange = IDBKeyRange;
      w.fetch = () => Promise.reject(new Error("мережі в пробі нема")); w.scrollTo = () => {};
      w.Element.prototype.scrollIntoView = () => {}; w.Blob = Blob; w.Response = Response;
      w.TextEncoder = TextEncoder; w.TextDecoder = TextDecoder;
      w.CompressionStream = CompressionStream; w.DecompressionStream = DecompressionStream; }}).window;
  await new Promise(р => setTimeout(р, 800));
  w.eval("містП = async () => [];");
  /* ДВА ЗБОРИ, ОДНАКОВИЙ РОЗКЛАД: другий — те саме, що робить шов збирання (новий
     ід, ті самі збірка/розклад/профіль), і вердикт жінки на картці кожного. */
  const судити = async верд => { w.eval("відповідь(0).верд = '" + верд + "'; відповідь(0).річ = 'так, це вона';");
                                 await w.eval("записати(0)"); };
  await судити("вдягну як є");
  w.eval("П = JSON.parse(JSON.stringify(П)); П.прогін = (typeof новийІдПрогону === 'function' ? новийІдПрогону() : П.прогін);"
       + "П.картки[0].підпис = 'прогін Б'; П.картки[0].опис = 'прогін Б'; рендер();");
  await new Promise(р => setTimeout(р, 200));
  await судити("не вдягну");
  /* Сховище читаємо через `дб()`, а не через `усіОбрази` показу: ту саму пробу
     мусить прогнати й ЗБІРКА ДО ПРАВКИ (`git show origin/main:джерела/показ.html`),
     а там читача назовні не виставлено — і «до» лишилось би на слово. */
  const ОБРАЗИ = "дб().then(d => new Promise(r => { const q = d.transaction('образи').objectStore('образи').getAll();"
    + " q.onsuccess = () => r(q.result || []); }))";
  const факт = JSON.parse(await w.eval("Promise.all([" + ОБРАЗИ + ", усіВердикти()]).then(([о, в]) => JSON.stringify({"
    + "записів: о.length, ключі: о.map(з => з.ключ),"
    + "старий: [...new Set(в.map(з => [з.збірка||'?', з.розклад ?? '?', з.профіль||''].join('·')))],"
    + "вердикти: в.map(з => ({прогін: з.прогін || null, верд: з.вердикт_людини}))}))"));
  const наПлитках = JSON.parse(await w.eval("оновитиБібліотеку().then(() => JSON.stringify("
    + "[...document.querySelectorAll('#біб-список .біб-образ em')].map(е => е.textContent)))"));
  let провалів = 0;
  const проба = (н, ок, що) => { if (ок) console.log("ок      " + н);
    else { провалів++; console.log("ПОЛОМКА " + н + "  →  " + JSON.stringify(що)); } };
  проба("два збори — ДВА записи бібліотеки (до правки був 1: старий ключ у них один)",
        факт.записів === 2 && факт.старий.length === 1, [факт.записів, факт.ключі, факт.старий]);
  проба("кожен вердикт несе ід свого прогону, і ці іди різні",
        факт.вердикти.length === 2 && факт.вердикти.every(в => в.прогін)
        && факт.вердикти[0].прогін !== факт.вердикти[1].прогін, факт.вердикти);
  проба("на плитці кожного прогону — ОДИН вердикт, і саме його (до правки — два на обох)",
        наПлитках.length === 2 && наПлитках.filter(т => /вдягну як є/.test(т)).length === 1
        && наПлитках.filter(т => /^не вдягну/.test(т)).length === 1 && !наПлитках.some(т => /записи/.test(т)),
        наПлитках);
  /* «ДО» — НЕ З ПАМ'ЯТІ, А ПОРАХОВАНЕ НА ЦИХ САМИХ ДАНИХ: скільки комірок дав би
     старий ключ на цих двох прогонах (стільки ж було б і записів у бібліотеці). */
  console.log("\nдо:    комірок за старим ключем " + факт.старий.length + " на 2 прогони ("
    + факт.старий.join(" | ") + ") — стільки ж було б і записів"
    + "\nпісля: записів " + факт.записів + " · ключі " + факт.ключі.join(" | ")
    + "\nплитки «Усіх образів»: " + наПлитках.join(" | "));
  process.exit(провалів ? 1 : 0);
})().catch(e => { console.error("проба не запустилась:", e); process.exit(2); });
