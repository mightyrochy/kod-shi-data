/* ФОТО-513 (стенд): адаптери живої моделі в `аудит/проби/рв6_стенд.js` (LM Studio, `ZHYVA`) мають класти
   на місце кадру, що не дійшов, той самий текст, що воркер («(image not delivered)»), — інакше стенд міряє
   не те, що шле справжній міст. Проба бере ЦИКЛИ кадрів обох адаптерів із файлу стенда (ДО — origin/main,
   ПІСЛЯ — робоче дерево), дає їм образ із підписами «Photo N:» і мертвим кадром 3 і друкує, що піде моделі.
   Запуск із теки `джерела`: node проби/опис_кадр_адаптер.js */
const fs = require("fs"), { execFileSync } = require("child_process");
const ФАЙЛ = "аудит/проби/рв6_стенд.js", ТУТ = fs.readFileSync(__dirname + "/../../" + ФАЙЛ, "utf8"),
  ДО = execFileSync("git", ["show", "origin/main:" + ФАЙЛ], { encoding: "utf8", maxBuffer: 1 << 28 });
const ВХІД = [1, 2, 3].flatMap(i => [{ type: "text", text: "Photo " + i + ":" },
  { type: "image", source: { type: "url", url: (i === 3 ? "https://dead.example/" : "https://img.example/") + i + ".jpg" } }]);
const цикл = (код, початок, кінець) => { const а = код.indexOf(початок), б = код.indexOf(кінець, а);
  if (а < 0 || б < 0) throw new Error("не знайдено цикл: " + початок); return код.slice(а, б + кінець.length); };
const адаптери = {
  "LM Studio": [`for (const б of м.content){\n      if (б.type !== 'image'){ зміст.push`, "\n    }", "зміст", u => ({ type: "image_url", image_url: { url: u } })],
  "ZHYVA   ": [`for (const б of м.content){\n      if (б.type !== 'image'){ блоки.push`, "\n    }", "блоки", u => ({ type: "image", url: u })]};
for (const [ім, [поч, кін, зм, обгортка]] of Object.entries(адаптери)) for (const [мітка, код] of [["ДО   ", ДО], ["ПІСЛЯ", ТУТ]]) {
  const тіло = цикл(код, поч, кін), вихід = [];
  new Function("м", "кадрБазою", "клодКадром", зм, "фотоНеДійшло", `(async () => { ${тіло} })()`)
    ({ content: ВХІД }, async u => /dead/.test(u) ? null : u, обгортка, вихід, 0);
  setTimeout(() => console.log(ім, мітка, вихід.map(б => б.text || (б.url || б.image_url.url).split("/").pop()).join(" | ")), 0);
}
