// Рядок 4371: код кольору hex без її слова (`мовний_шар._код_кольору` → `palettes._назва`) у справжньому Chromium на
// зібраній сторінці — hex знахідки й речі каталогу (JSON [{id, крамниця, lab, назва}]), Python — pyodide самої сторінки.
// Збірка: cd джерела && LYUSTERKO_CATALOG=повний python3 build_артефакт.py . <тека>/index.html показ-повний
// Запуск: NODE_PATH=джерела/node_modules node аудит/проби/лимонний_4371_chromium.js <тека> <тека pyodide> <речі.json>
const {chromium} = require("playwright"), fs = require("fs"), path = require("path");
const [КОРІНЬ, PYO, РЕЧІ] = process.argv.slice(2), БАЗА = "http://127.0.0.1:8765";
const HEX = ["FFF44F", "FAFA33", "ECDA6E", "DFDC8E", "F4E87C", "FFD700"];
(async () => {
  const b = await chromium.launch({executablePath: "/opt/pw-browsers/chromium"});
  const p = await b.newPage({viewport: {width: 390, height: 844}});
  const помилки = []; p.on("pageerror", e => помилки.push(String(e)));
  await p.route(u => u.origin === БАЗА, r => {
    const ф = path.join(КОРІНЬ, decodeURIComponent(new URL(r.request().url()).pathname).slice(1) || "index.html");
    return fs.existsSync(ф) ? r.fulfill({status: 200, contentType: "text/html; charset=utf-8", body: fs.readFileSync(ф)}) : r.fulfill({status: 404});
  });
  await p.route("https://cdn.jsdelivr.net/pyodide/**", r => {
    const ім = new URL(r.request().url()).pathname.split("/").pop(), ф = path.join(PYO, ім);
    const тип = ім.endsWith(".wasm") ? "application/wasm" : /\.m?js$/.test(ім) ? "application/javascript" : "application/octet-stream";
    return fs.existsSync(ф) ? r.fulfill({status: 200, contentType: тип, body: fs.readFileSync(ф)}) : r.fulfill({status: 404});
  });
  await p.route(u => u.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), r => r.abort());
  await p.goto(БАЗА + "/index.html");
  await p.waitForFunction(() => typeof підняти_міст_показу === "function", null, {timeout: 60000});
  const вих = await p.evaluate(async ([hex, речі]) => {
    const пі = await підняти_міст_показу();
    return JSON.parse(await пі.runPythonAsync("import json, palettes as PS, colorspace as cs, мовний_шар as МШ\n" +
      "json.dumps(dict(hex={h: [МШ._код_кольору(h), PS._назва(cs.hx('#' + h))[0]] for h in " + JSON.stringify(hex) + "},\n" +
      "  речі=[[р['id'], р['крамниця'], PS._hex(tuple(р['lab'])), PS._назва(tuple(р['lab']))[0]] for р in json.loads(" +
      JSON.stringify(JSON.stringify(речі)) + ")]), ensure_ascii=False)"));
  }, [HEX, JSON.parse(fs.readFileSync(РЕЧІ, "utf8"))]);
  console.log(JSON.stringify(вих)); console.log("помилки сторінки:", помилки.length, помилки.slice(0, 3));
  await b.close();
})();
