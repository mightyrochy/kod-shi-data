/* ФОТО-513: опис образу отримував чуже фото речі. Воркер для Gemini викидає з запиту кадр, що не
   завантажився, — решта кадрів зсувається, а `photos` речі лічить кадри ПОЗА ЧЕРГОЮ («номери зображень
   перед цим обʼєктом»). Проба шле через справжній воркер образ з трьох речей (сумка 1–2, ремінь 3–4,
   сережки 5) і мертвим кадром №3 та друкує пари «річ → кадр, який побачить модель».
   ДО — воркер і сторінка origin/main (кадри голими блоками), ПІСЛЯ — робоче дерево (`підписатиКадри`).
   Запуск із теки `джерела`: node проби/опис_кадр_речі.js */
const fs = require("fs"), { execFileSync } = require("child_process");
const git = ф => execFileSync("git", ["show", "origin/main:джерела/" + ф], { encoding: "utf8", maxBuffer: 1 << 28 });
const модуль = async (код, ім) => { const ш = "/tmp/_кадр_" + ім + ".mjs";
  fs.writeFileSync(ш, код.replace(/export\s*\{\s*worker_default as default\s*\}\s*;?/, "const М = worker_default;").replace(/^export default/m, "const М =") + "\nexport {М};");
  return (await import(ш)).М; };
const РЕЧІ = [["сумка", [1, 2]], ["ремінь", [3, 4]], ["сережки", [5]]];
const УРЛИ = [1, 2, 3, 4, 5].map(i => (i === 3 ? "https://dead.example/" : "https://img.example/") + i + ".jpg");
const пнг = new Uint8Array(2048); пнг.set([137, 80, 78, 71, 13, 10, 26, 10]);
const хтмл = ф => fs.readFileSync(__dirname + "/../" + ф, "utf8");
const підписати = (() => { const м = хтмл("показ.html").match(/function підписатиКадри[\s\S]*?\n}\n/);
  return м ? new Function(м[0] + "; return підписатиКадри;")() : null; })();
(async () => {
  const вихідні = [];
  globalThis.fetch = async (u, o) => /dead\./.test(String(u)) ? new Response("нема", { status: 404 })
    : /img\./.test(String(u)) ? new Response(пнг, { status: 200, headers: { "content-type": "image/png" } })
    : (вихідні.push(JSON.parse(o.body)), new Response(JSON.stringify({ candidates: [{ content: { parts: [{ text: "ок" }] }, finishReason: "STOP" }] })));
  const env = { ALLOWED_ORIGINS: "https://o.example", TESTER_TOKENS: "t", GEMINI_API_KEY: "k" };
  for (const [мітка, воркер, блоки] of [
    ["ДО   ", await модуль(git("worker.js"), "до"), УРЛИ.map(u => ({ type: "image", source: { type: "url", url: u } }))],
    ["ПІСЛЯ", await модуль(хтмл("worker.js"), "після"), підписати && підписати(УРЛИ.map(u => ({ type: "image", source: { type: "url", url: u } })))]]) {
    if (!блоки) { console.log(мітка, "— `підписатиКадри` у показ.html ще нема"); continue; }
    await воркер.fetch(new Request("https://w.workers.dev/", { method: "POST", headers: { "content-type": "application/json", Origin: "https://o.example", "x-lyusterko-token": "t" },
      body: JSON.stringify({ model: "gemini-flash-latest", messages: [{ role: "user", content: [...блоки, { type: "text", text: "{}" }] }] }) }), env);
    const ч = вихідні.pop().contents[0].parts, бачить = {};
    // ДО модель лічить зображення по черзі; ПІСЛЯ — за підписом «Photo N», що стоїть перед кадром
    ч.forEach((p, i) => { if (/^Photo (\d+)/.test(p.text || "")) бачить[RegExp.$1] = ч[i + 1] && ч[i + 1].inline_data ? "кадр " + RegExp.$1 : "нема (не дійшов)"; });
    const зображення = ч.filter(p => p.inline_data).map((_, i) => i);
    console.log(мітка, "кадрів у запиті:", ч.filter(p => p.inline_data).length, "з", УРЛИ.length);
    for (const [р, н] of РЕЧІ) console.log("   ", р.padEnd(8), "→", н.map(k => /^ДО/.test(мітка)
      ? (зображення[k - 1] === undefined ? "нема зображення №" + k : "зображення №" + k + " = кадр " + УРЛИ.map((u, j) => /dead/.test(u) ? 0 : j + 1).filter(Boolean)[k - 1])
      : бачить[k]).join(", "));
  }
})();
