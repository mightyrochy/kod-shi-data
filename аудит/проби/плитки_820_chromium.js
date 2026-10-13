// ОЦІНКА-Ж16: #820 у справжньому Chromium на зібраній сторінці (код 964c637a0601 = 9ad76ee2, пачка 25): плитки відчуття «Коли й погода»,
// ошатність «Свято» без місця, паспорт К7, рядок речей без анімації. Аргумент — тека з index.html.
// Збірка: cd джерела && python3 build_артефакт.py . /tmp/с25/index.html показ-повний (на дереві 9ad76ee2);
// запуск: NODE_PATH=$(npm root -g) node аудит/проби/плитки_820_chromium.js /tmp/с25
const {chromium} = require("playwright");
(async () => {
  const b = await chromium.launch({executablePath: "/opt/pw-browsers/chromium"});
  const p = await b.newPage({viewport: {width: 390, height: 844}});
  const помилки = []; p.on("pageerror", e => помилки.push(String(e)));
  await p.goto("file://" + process.argv[2] + "/index.html");
  await p.waitForFunction(() => typeof застосуватиПаспортДоЕкрана === "function" && document.getElementById("сц-нагода"), null, {timeout: 60000});
  const r = await p.evaluate(() => {
    const $ = і => document.getElementById(і), вих = {};
    const вето = {типи: [], тканини: [], принти: [], кольори: [], зони: []};
    const паспорт = о => { ПАСПОРТ_П = Object.assign({джерело: "модель", джерело_полів: {}, вето}, о); ВИПАДОК_ЗМІНЕНО_П = false; застосуватиПаспортДоЕкрана(ПАСПОРТ_П); };
    const плитки = () => Array.from(document.querySelectorAll("#сц-відчуття-плитки .плитка"));
    $("сц-нагода").value = "свято"; малюватиКарткуСценарію(); вих["3250 свято без місця"] = $("зн-дрес").textContent; $("сц-нагода").value = "";
    паспорт({подія: "робота", нагода: "робота", місце: "прогулянка", погода_відчуття: "frost", джерело_полів: {місце: "розмова"}});
    $("сц-нагода").value = "робота"; малюватиКарткуСценарію();
    вих["3252 К7"] = [$("зн-дрес").textContent, $("зн-коли").textContent];
    вих["3251 плитки"] = плитки().map(п => п.textContent + (п.classList.contains("вибр") ? "✔" : "")).join(",");
    плитки().find(п => п.textContent === "холодно").click();
    вих["3251 дотик «холодно»"] = {картка: $("зн-коли").textContent, вхід: зібратиВхід().сценарій.погода_відчуття, шов: ПАСПОРТ_П.погода_відчуття, темп: ПАСПОРТ_П.темп_c};
    const річ = Array.from(document.styleSheets).flatMap(с => { try { return Array.from(с.cssRules); } catch (е) { return []; } })
      .find(р => р.selectorText === ".річ");
    вих["3463 .річ"] = річ ? (річ.style.animationName || "без анімації") : "правила нема";
    return вих;
  });
  console.log(JSON.stringify(r, null, 1)); console.log("помилки сторінки:", помилки.length, помилки.slice(0, 3));
  await b.close();
})();
