/* Проба рядка 5813: обрив `fetch` сторінки закриває запит до сервера моделі (заглушка тримає відповідь). */
const {chromium} = require('playwright'), http = require('http'), path = require('path');
const {постЖСОН, стежитиЗаОбривом} = require(path.join(__dirname, 'обрив_моста.js'));
(async () => {
  let закрито = null, прийшло = 0;
  const сервер = http.createServer((з, в) => { прийшло++; з.on('close', () => { закрито = Date.now(); }); /* відповіді нема */ });
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  const адреса = 'http://127.0.0.1:' + сервер.address().port + '/v1/chat/completions';
  const б = await chromium.launch({executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium'});
  const стор = await б.newPage(), мапа = new Map();
  стежитиЗаОбривом(стор, мапа, () => {});
  await стор.route('http://міст.тест/**', async route => {
    const д = {}; мапа.set(route.request(), д);
    await постЖСОН(адреса, {x: 1}, д); мапа.delete(route.request());
    await route.abort().catch(() => {});
  });
  await стор.goto('about:blank');
  const т0 = Date.now();
  await стор.evaluate(() => { window.ак = new AbortController(); window.п = fetch('http://міст.тест/міст', {method: 'POST', signal: ак.signal}).catch(e => e.name); });
  await new Promise(р => setTimeout(р, 500));
  const обірвано = Date.now();
  await стор.evaluate(() => ак.abort());
  await new Promise(р => setTimeout(р, 1000));
  console.log(JSON.stringify({запит_дійшов_до_сервера: прийшло, сервер_закрив_з_мс: закрито ? закрито - обірвано : null}));
  console.log(закрито && прийшло === 1 ? 'ОБРИВ ДІЙШОВ ДО СЕРВЕРА' : 'ОБРИВ НЕ ДІЙШОВ');
  await б.close(); сервер.close(); process.exit(закрито ? 0 : 1);
})();
