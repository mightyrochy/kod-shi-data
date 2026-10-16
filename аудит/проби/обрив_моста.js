/* РЯДОК 5813: обрив з браузера доходить до LM Studio. Показ рве `fetch` через `AbortController`
   (`ланцюгПерелікуП`, `_дзвінокП`); Playwright-маршрут моста цього не знав, і запит до моделі
   доїдав своє. Тут: `постЖСОН` з ручкою (`держак.скасувати()` рве з'єднання з моделлю) і
   `стежитиЗаОбривом` — коли запит сторінки скасовано, ручка натискається і подія йде в журнал. */
const http_ = require('http');
/* Власний POST без таймаута (див. рв6_стенд.js: undici відрізає 300 с). `держак` — {} або нічого. */
function постЖСОН(адреса, тіло, держак){
  return new Promise(рез => {
    const у = new URL(адреса), дані = Buffer.from(JSON.stringify(тіло), 'utf8');
    const зап = http_.request({hostname: у.hostname, port: у.port, path: у.pathname + у.search,
      method: 'POST', agent: false,
      headers: {'Content-Type': 'application/json', 'Content-Length': дані.length}},
      від => { const шм = []; від.on('data', д => шм.push(д));
               від.on('end', () => рез({статус: від.statusCode, сире: Buffer.concat(шм).toString('utf8')})); });
    зап.setTimeout(0);
    зап.on('error', е => рез({статус: 599, сире: JSON.stringify({error: {message: String(е)}})}));
    if (держак) держак.скасувати = () => { держак.обірвано_о = Date.now(); зап.destroy(new Error('клієнт обірвав запит')); };
    зап.end(дані);
  });
}
/* `мапа`: Playwright Request → держак. `подія(запит, держак)` викликається після обриву. */
function стежитиЗаОбривом(стор, мапа, подія){
  стор.on('requestfailed', з => {
    const д = мапа.get(з); if (!д || д.обірвано_о) return;
    д.скасувати(); мапа.delete(з);
    if (подія) подія(з, д);
  });
}
module.exports = {постЖСОН, стежитиЗаОбривом};
