/* Рядок 158: ЩО САМЕ ЙДЕ В ЗАПИТ ДО ПРОВАЙДЕРА, коли показ шле `temperature: 0`.
   До правки маршрут `gemini-` будував тіло нанову й це поле губив мовчки (grep на
   `temperature` у worker.js — 0 збігів), тобто модель шару відповідала з температурою
   провайдера за замовчуванням. Запуск: `cd джерела && node проби/темп_у_запиті.js`. */
const fs = require("fs"), path = require("path");
(async () => {
  const сир = fs.readFileSync(path.join(__dirname, "..", "worker.js"), "utf-8")
    .replace(/export\s*\{\s*worker_default as default\s*\}\s*;?/, "const М = worker_default;")
    .replace(/^export default/m, "const М =");
  fs.writeFileSync("/tmp/_темп_проба.mjs", сир + "\nexport {М};");
  const {М} = await import("/tmp/_темп_проба.mjs");
  const пішло = [];
  globalThis.fetch = async (url, opts) => { пішло.push({url:String(url), тіло:JSON.parse(opts.body)});
    return new Response(JSON.stringify({content:[{type:"text",text:"ок"}], stop_reason:"end_turn",
      candidates:[{content:{parts:[{text:"ок"}]}, finishReason:"STOP"}], usageMetadata:{}}), {status:200}); };
  const env = {ALLOWED_ORIGINS:"https://pokaz.example", TESTER_TOKENS:"tok-a1",
               ANTHROPIC_API_KEY:"sk-т", GEMINI_API_KEY:"AQ.т", GEMINI_THINKING:"як є"};
  for (const модель of ["claude-sonnet-5", "gemini-3.8-flash"]) {
    пішло.length = 0;
    const в = await М.fetch(new Request("https://w.workers.dev/", {method:"POST",
      headers:{"content-type":"application/json", "Origin":"https://pokaz.example", "x-lyusterko-token":"tok-a1"},
      /* рівно те тіло, що складає показ для мовного шару: `мовний_шар.ВИБІРКА` */
      body:JSON.stringify({model:модель, max_tokens:4000, temperature:0,
                           messages:[{role:"user", content:[{type:"text", text:"та сама репліка"}]}]})}), env);
    const т = пішло[0].тіло;
    const де = ("temperature" in т) ? "тіло.temperature = " + JSON.stringify(т.temperature)
             : (т.generationConfig && "temperature" in т.generationConfig)
               ? "generationConfig.temperature = " + JSON.stringify(т.generationConfig.temperature)
               : "НЕ ПІШЛА — провайдер візьме свою";
    console.log(модель.padEnd(17) + " → " + де.padEnd(46) + " x-temperature=" + в.headers.get("x-temperature"));
    if (!/temperature = 0$/.test(де)) { console.log("✗ температура 0 до провайдера не дійшла"); process.exit(1); }
  }
  console.log("обидва маршрути несуть temperature 0 — однакова репліка дає той самий паспорт");
})();
