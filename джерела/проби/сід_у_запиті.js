/* Рядок 4108: чи доходять сід і температура стенда до тіла запиту до MODEL_MOVA — з коду стенда (`живоюМоделлю`),
   крізь справжній проксі (:1236, підробний lms). Запуск: `node джерела/проби/сід_у_запиті.js`. */
const fs = require('fs'), path = require('path'), vm = require('vm'), http = require('http'), cp = require('child_process');
const кор = path.join(__dirname, '..', '..', 'аудит');
const код = fs.readFileSync(path.join(кор, 'проби', 'рв6_стенд.js'), 'utf8');
const шматок = код.slice(код.indexOf('const http_ = require'), код.indexOf('/* ФОТО РЕЧЕЙ ПРИХОДЯТЬ'))
  + код.slice(код.indexOf('async function живоюМоделлю'), код.indexOf('/* ── ОДИН ВИКЛИК МОДЕЛІ ЧЕРЕЗ `claude -p`'));
const спіймано = [];
const верх = http.createServer((q, в) => { const ч = []; q.on('data', д => ч.push(д)); q.on('end', () => {
  спіймано.push(JSON.parse(Buffer.concat(ч))); в.end(JSON.stringify({choices: [{message: {content: 'ок'}}]})); }); }).listen(0, '127.0.0.1', () => {
  const проксі = cp.spawn('node', [path.join(кор, 'ноутбук_стенд_2', 'проксі_почергове.js')],
    {env: Object.assign({}, process.env, {PORT: 1236, UP_PORT: верх.address().port, LMS_BIN: 'true'})});
  проксі.stdout.once('data', async () => {
    const ВИБІРКА_ЗАПИТУ = require(path.join(кор, 'проби', 'вибірка_запиту.js'));
    for (const сід of [5, 4]) {
      const ctx = {require, console, Buffer, URL, ВИБІРКА_ЗАПИТУ, ЖУРНАЛ_МОДЕЛІ: [], КЛОД_ШВОМ: false, ПРАВИЛА_РЕЧЕННЯМИ: false,
        МОДЕЛЬ_МОВИ_СТЕНДУ: 'mamay', МОДЕЛЬ_ЖИВА: 'styl', ШАР_ВИМКНЕНО: false, ТЕМПЕРАТУРА: null, ТЕМПЕРАТУРА_МОВИ: 0.7,
        СІД: сід, АДРЕСА_МОДЕЛІ: 'http://127.0.0.1:1236/v1', process, ЧЕКАЄ_JSON: () => false, setTimeout, Date, Promise};
      vm.createContext(ctx); vm.runInContext(шматок + '\nthis.f = живоюМоделлю;', ctx);
      for (const тип of ['мовний шар', 'ПАКЕТ_V1→ОБРАЗИ_V1']) {
        await ctx.f({messages: [{role: 'user', content: 'x'}], temperature: 0}, тип);
        const т = спіймано.pop();
        console.log(`сід ${сід} · ${тип.padEnd(18)} → model=${т.model} seed=${т.seed} temperature=${т.temperature}`);
      }
    }
    проксі.kill(); верх.close();
  });
});
