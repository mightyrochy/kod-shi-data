/* МОДЕЛЬ ПРОТИ МОДЕЛІ НА ОДНОМУ Й ТОМУ САМОМУ ПРОМПТІ (наряд тестувальниці, крок 3).
   Повний прохід стенда на кожній моделі коштує десятки хвилин, а на 12B-моделях
   він на цьому ноутбуці просто не піднімається (див. звіт: контекст 61 440 для
   gemma-4-12b — 16.19 ГіБ проти 16.38 ГіБ картки). Щоб порівняння все ж стояло
   на тому самому вході, ця проба бере ПРОМПТ, який показ уже послав у живому
   прогоні (`VIDPOVIDI=<тека>` стенда), і шле його кожній моделі по черзі.

   Міряє рівно те, що просить наряд, і нічого понад:
     чи відповідь узагалі JSON (з ```-обгорткою чи без) · чи є ключ «образи» і
     скільки їх · скільки образів мають ≥5 речей і взуття+сумку (слот речі
     береться з ПУЛУ того самого промпта) · скільки речей повторюються між
     образами · час і токени · чи вперлось у стелю виводу.

   Запуск:
     node аудит/проби/модель_проти_моделі.js <файл_або_тека> <модель1,модель2,…> [стеля_токенів]
   Стеля типово 4000 — та сама, що `МАКС_ТОКЕНІВ_П` у показі. */
const fs = require('fs'), path = require('path'), http = require('http');
const АДРЕСА = process.env.MODEL_URL || 'http://127.0.0.1:1234/v1';
const [, , ШЛЯХ, МОДЕЛІ_, СТЕЛЯ_] = process.argv;
const МОДЕЛІ = (МОДЕЛІ_ || '').split(',').filter(Boolean);
const СТЕЛЯ = Number(СТЕЛЯ_ || 4000);
if (!ШЛЯХ || !МОДЕЛІ.length){ console.error('дай <файл_або_тека> <модель1,модель2,…>'); process.exit(2); }
const файли = fs.statSync(ШЛЯХ).isDirectory()
  ? fs.readdirSync(ШЛЯХ).filter(ф => /ПАКЕТ_V1/.test(ф)).map(ф => path.join(ШЛЯХ, ф)) : [ШЛЯХ];
const промптЗФайлу = ф => fs.readFileSync(ф, 'utf8').split('\n\n── ВІДПОВІДЬ')[0].replace(/^── ПРОМПТ[^\n]*\n/, '');
const пост = (тіло) => new Promise(рез => {
  const у = new URL(АДРЕСА + '/chat/completions'), дані = Buffer.from(JSON.stringify(тіло), 'utf8');
  const з = http.request({hostname: у.hostname, port: у.port, path: у.pathname, method: 'POST',
    headers: {'Content-Type': 'application/json', 'Content-Length': дані.length}},
    в => { const ш = []; в.on('data', д => ш.push(д));
           в.on('end', () => рез({статус: в.statusCode, сире: Buffer.concat(ш).toString('utf8')})); });
  з.setTimeout(0); з.on('error', е => рез({статус: 599, сире: String(е)})); з.end(дані);
});
/* слот кожного номера — з пулу самого промпта: інакше «взуття+сумка» довелось би вгадувати з назви */
function слотиПулу(промпт){
  const м = {}; let об = null; try { об = JSON.parse(промпт); } catch (_) { return м; }
  for (const [слот, речі] of Object.entries(об.пул || {})) for (const р of речі || []) м[р.н] = слот;
  return м;
}
/* назви пулу — щоб повтор називався річчю, а не номером (питання власника про
   скаргу тестувальниці «Ір»: «одні й ті самі кеди 3+ разів») */
function назвиПулу(промпт){
  const м = {}; let об = null; try { об = JSON.parse(промпт); } catch (_) { return м; }
  for (const речі of Object.values(об.пул || {})) for (const р of речі || []) м[р.н] = р.назва || '';
  return м;
}
(async () => {
  console.log('стеля виводу', СТЕЛЯ, '· моделей', МОДЕЛІ.length, '· промптів', файли.length);
  for (const ф of файли){
    const промпт = промптЗФайлу(ф), слоти = слотиПулу(промпт);
    console.log('\n══ ' + path.basename(ф) + ' · ' + промпт.length + ' симв. · пул ' + Object.keys(слоти).length + ' речей');
    for (const модель of МОДЕЛІ){
      const t0 = Date.now();
      const в = await пост({model: модель, max_tokens: СТЕЛЯ, stream: false, reasoning_effort: 'none',
        messages: [{role: 'user', content: [{type: 'text', text: промпт}]}]});
      const с = ((Date.now() - t0) / 1000).toFixed(1);
      let д = null; try { д = JSON.parse(в.сире); } catch (_) {}
      if (в.статус !== 200 || !д){ console.log('  ' + модель + ' · HTTP ' + в.статус + ' · ' + с + ' с · ' + в.сире.slice(0, 160)); continue; }
      const пов = ((д.choices || [{}])[0] || {}), текст = (пов.message || {}).content || '';
      const стеля = пов.finish_reason === 'length';
      /* VIDPOVIDI=<тека> — відповідь цілком у файл, щоб читати її очима, а не лише лічбу */
      if (process.env.VIDPOVIDI){
        fs.mkdirSync(process.env.VIDPOVIDI, {recursive: true});
        fs.writeFileSync(path.join(process.env.VIDPOVIDI, модель.replace(/[^\w.-]+/g, '_') + '__'
          + path.basename(ф)), текст, 'utf8');
      }
      const чистий = текст.replace(/^[\s\S]*?```(?:json)?/, '').replace(/```[\s\S]*$/, '').trim() || текст.trim();
      let об = null; try { об = JSON.parse(чистий); } catch (_) {}
      const образи = (об && (об.образи || об['обрazi'] || (Array.isArray(об) ? об : null))) || null;
      const сп = Array.isArray(образи) ? образи : (об && об.ід ? [об] : []);
      const речі = сп.map(о => (о.речі || []).map(String));
      const відомі = речі.map(р => р.filter(н => слоти[н]));
      const повних = речі.filter((р, і) => р.length >= 5
        && відомі[і].some(н => слоти[н] === 'взуття') && відомі[і].some(н => слоти[н] === 'сумка')).length;
      const усі = речі.flat(), повтори = усі.length - new Set(усі).size;
      const чужих = усі.filter(н => !слоти[н]).length;
      /* вхід у токенах — ЦІЄЇ моделі: той самий пакет у 120 000 символів qwen3.5-9b рахує як ~55 тис.,
         а qwen3-vl-8b — як 63.8–64.1 тис. (25.09), тож потрібний контекст залежить від токенізатора */
      console.log('  ' + модель + ' · ' + с + ' с · вхід ' + ((д.usage || {}).prompt_tokens || 0)
        + ' т. · вихід ' + ((д.usage || {}).completion_tokens || 0) + ' т.'
        + (стеля ? ' · СТЕЛЯ' : '') + ' · JSON ' + (об ? 'так' : 'НІ')
        + ' · образів ' + сп.length + ' · повних (взуття+сумка, ≥5) ' + повних
        + ' · речей поза пулом ' + чужих + ' · повторів між образами ' + повтори);
      /* ПОВТОРИ ПОІМЕННО (питання власника про скаргу «Ір»): скільки разів яка
         річ стоїть у десятьох образах однієї відповіді, і скільки різних речей
         узято в кожному слоті з того, що пропонував пул. */
      if (сп.length > 1){
        const назви = назвиПулу(промпт), лічба = {};
        for (const н of усі) лічба[н] = (лічба[н] || 0) + 1;
        const топ = Object.entries(лічба).sort((а, б) => б[1] - а[1]).filter(([, к]) => к > 1).slice(0, 5);
        console.log('     найчастіші речі: ' + (топ.map(([н, к]) => к + '× ' + н + ' «'
          + String(назви[н] || '(поза пулом)').slice(0, 40) + '»').join(' · ') || 'жодна не повторюється'));
        const заСлотом = {};
        for (const н of усі){ const с_ = слоти[н] || 'поза пулом';
          (заСлотом[с_] = заСлотом[с_] || new Set()).add(н); }
        console.log('     різних речей у слоті: ' + Object.entries(заСлотом)
          .map(([с_, м]) => с_ + ' ' + м.size).join(', '));
      }
    }
  }
})();
