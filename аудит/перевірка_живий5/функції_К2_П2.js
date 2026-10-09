// К2 і П2 — функції в справжньому Chromium на зібраній сторінці (Pyodide), без моделі
const { chromium } = require('playwright'); const fs = require('fs'), path = require('path');
const [,, КОРІНЬ, PYO] = process.argv; const БАЗА = 'http://127.0.0.1:8765';
(async () => {
  const br = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM });
  const p = await (await br.newContext()).newPage();
  p.on('pageerror', e => console.log('pageerror', String(e).slice(0, 200)));
  await p.route(u => u.origin === new URL(БАЗА).origin, r => r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(path.join(КОРІНЬ, 'index.html')) }));
  await p.route('https://cdn.jsdelivr.net/pyodide/**', r => { const ім = new URL(r.request().url()).pathname.split('/').pop(); const f = path.join(PYO, ім);
    const t = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    return fs.existsSync(f) ? r.fulfill({ status: 200, contentType: t, body: fs.readFileSync(f) }) : r.fulfill({ status: 404, body: '' }); });
  await p.route(u => !u.href.startsWith(БАЗА) && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), r => r.abort());
  await p.goto(БАЗА + '/index.html', { waitUntil: 'load', timeout: 180000 });
  await p.waitForTimeout(8000);
  console.log('діагн:', JSON.stringify(await p.evaluate(() => ({режим: typeof РЕЖИМ, py: (()=>{try{return typeof pyodide_показу}catch(e){return 'ERR '+e.message}})(), далі: !!(document.getElementById('н-далі')||{}).onclick, збірка: (()=>{try{return ЗБІРКА_ПОКАЗУ}catch(e){return 'ERR'}})()}))));
  await p.evaluate(async () => { await підняти_міст_показу(); return 1; });
  console.log('збірка:', await p.evaluate(() => ЗБІРКА_ПОКАЗУ), '· UA:', (await p.evaluate(() => navigator.userAgent)).slice(0, 80));
  const py = код => p.evaluate(async к => String(await pyodide_показу.runPythonAsync(к)), код);
  console.log('=== К2 (K-KOH-05, код cocktail; E — стан «надворі» / «у приміщенні»)');
  console.log(await py(`
import json, формальність as Ф
def е(ід, слот, тип): return dict(річ=ід, слот=слот, тип=тип, площа=1, lab=(50, 0, 0))
def є(E): return any(з["правило"] == "K-KOH-05" and "просить" in з.get("суть", "") for з in Ф.вимоги_коду(E, "cocktail"))
надворі = [е("тренч", "верхній_шар", "тренч"), е("туфлі", "взуття", "туфлі")]
у_приміщенні = [е("туфлі", "взуття", "туфлі")]
з_сукнею = [е("сукня", "сукня", "сукня_без_уточнення"), е("туфлі", "взуття", "туфлі")]
без_шару_без_сукні = [е("блуза", "верх", "блуза"), е("спідниця", "низ", "спідниця"), е("туфлі", "взуття", "туфлі")]
"\\n".join([
 "К1 (шар ховає сукню надворі): знахідка K-KOH-05 «сукня від коліна до міді» = %s (очікуємо False)" % є(надворі),
 "К2 контроль (шар знято, сукні нема): = %s (очікуємо True)" % є(у_приміщенні),
 "К2 контроль (без шару, блуза+спідниця, сукні нема): = %s (очікуємо True)" % є(без_шару_без_сукні),
 "      (з сукнею без шару): = %s (очікуємо False)" % є(з_сукнею)])`));
  console.log('=== П2 (тональна: «вийшла» лише коли тон на великих речах)');
  console.log(await py(`
import palettes as PAL, colorspace as cs, суд_від_моделі as СВ, brief as Б
дуга = (160.0, 184.0)
сп = {с: dict(роль=р, L=[5, 95], C=[14.0, 34.0], дуга_тону=дуга) for с, р in (("верх", "домінанта"), ("низ", "секундант"), ("взуття", "секундант"), ("сумка", "акцент"))}
сп["_схема"] = "тональна"
річ = lambda і, сл, L, C, h: {"id": і, "слот": сл, "lab": list(СВ._lab_з(L, C, h))}
сумка_лише = [річ("v", "верх", 85, 2, 80), річ("n", "низ", 25, 2, 260), річ("b", "сумка", 50, 30, 172)]
тон_на_верху = [річ("v", "верх", 70, 20, 170), річ("n", "низ", 45, 18, 175), річ("b", "сумка", 50, 30, 172)]
хустка_лише = [річ("v", "верх", 85, 2, 80), річ("n", "низ", 25, 2, 260), річ("s", "хустка", 50, 30, 172)]
out = []
for назва, речі in (("нейтральні верх+низ, сумка тону", сумка_лише), ("нейтральні верх+низ, хустка тону", хустка_лише), ("верх і низ тону", тон_на_верху)):
    т = PAL.тон_тональної(речі, сп); зн = PAL.обіцянка_схеми(речі, сп); пов = PAL.повідомлення_схеми_жінці(речі, сп)
    out.append("%s: великих на тоні %s/%s · K-COL-03 %s · вийшла=%s" % (назва, т and т["великих_на_тоні"], т and т["великих_виміряно"], [з["заяви"][0]["code"] for з in зн] or "—", "так" if not пов else "ні"))
out.append("сумка сама дає «вийшла»? %s (очікуємо False)" % (not PAL.повідомлення_схеми_жінці(сумка_лише, сп)))
out.append("тон на верху дає «вийшла»? %s (очікуємо True)" % (not PAL.повідомлення_схеми_жінці(тон_на_верху, сп)))
ціль, _ = Б.колір_слота(dict(L=[2, 18], C=[14.0, 34.0], дуга_тону=(110.0, 134.0)))
L, C, h = cs.lch(cs.hx(ціль))
out.append("ціль верху темної «хвої» (L 2–18, C 14–34): %s — L* %.0f C* %.0f (ДО #181d0e: C* 10)" % (ціль, L, C))
"\\n".join(out)`));
  await br.close();
})().catch(e => { console.log('ВПАЛО', e.message.slice(0, 400)); process.exit(1); });
