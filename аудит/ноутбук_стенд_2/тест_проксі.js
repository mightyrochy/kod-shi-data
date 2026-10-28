/* Підробний HTTP upstream і підробний lms; однакові проби на Windows та Linux. */
const http = require('http'), fs = require('fs'), os = require('os'), path = require('path');
const {spawn} = require('child_process'), assert = require('assert');
const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'proxy-'));
const flag = path.join(dir, 'fail'), лог = path.join(dir, 'lms.log'), lms = path.join(dir, 'lms.cjs');
// Node виконує цю фікстуру до розбору load/unload як імені файла; проксі проходить далі.
fs.writeFileSync(lms, `const fs=require('fs'),path=require('path');
if (['load','unload'].includes(path.basename(process.argv[1] || ''))) {
  fs.appendFileSync(${JSON.stringify(лог)}, path.basename(process.argv[1])+' '+process.argv.slice(2).join(' ')+'\\n');
  process.exit(path.basename(process.argv[1])==='load' && fs.existsSync(${JSON.stringify(flag)}) ? 1 : 0);
}`);
const free = () => new Promise(r => { const s = http.createServer().listen(0, '127.0.0.1', () => { const p = s.address().port; s.close(() => r(p)); }); });
const та = (p, мс = 10000) => new Promise((ok, no) => {
  const t = setTimeout(() => no(Error('Проба зависла')), мс);
  p.then(v => {clearTimeout(t); ok(v);}, e => {clearTimeout(t); no(e);});
});
const post = (port, model) => new Promise(r => {
  const q = http.request({host: '127.0.0.1', port, path: '/v1/chat/completions', method: 'POST'}, s => {
    let b = ''; s.on('data', d => b += d); s.on('end', () => r({код: s.statusCode, b}));
    s.on('aborted', () => r({код: s.statusCode, обрив: true})); s.on('error', () => r({код: s.statusCode, обрив: true}));
  }); q.on('error', () => r({код: 0})); q.end(JSON.stringify({model}));
});
async function проба(режим) {
  // Фікстура REST відбиває конфігурацію так само, як живий GET /api/v1/models.
  let інстанси = [], завантажень = 0, вивантажень = [], передано = 0;
  const up = http.createServer((q, s) => {
    let b = ''; q.on('data', d => b += d); q.on('end', () => {
      const дані = b ? JSON.parse(b) : {};
      const json = v => {s.setHeader('content-type', 'application/json'); s.end(JSON.stringify(v));};
      if (q.url === '/api/v1/models') return json({models: інстанси.map(i => ({key: i.model, loaded_instances: [i]}))});
      if (q.url === '/api/v1/models/load') {
        завантажень++;
        if (fs.existsSync(flag)) {s.statusCode = 500; return json({error: 'підробний збій load'});}
        assert.strictEqual(дані.parallel, 1); assert.strictEqual(дані.echo_load_config, true);
        const config = {context_length: дані.context_length, parallel: дані.model === 'wrong' ? 4 : 1};
        інстанси = [{id: дані.model + '-instance', model: дані.model, config}];
        return json({instance_id: інстанси[0].id, status: 'loaded', load_config: config});
      }
      if (q.url === '/api/v1/models/unload') {
        assert(інстанси.some(i => i.id === дані.instance_id));
        вивантажень.push(дані.instance_id); інстанси = інстанси.filter(i => i.id !== дані.instance_id);
        return json({instance_id: дані.instance_id});
      }
      передано++;
      if (дані.model === 'drop') {
        s.writeHead(200, {'content-length': 100}); s.write('часткова'); setTimeout(() => s.destroy(), 50);
      } else if (дані.model !== 'slow') json({ok: 1});
    });
  });
  const loads = () => режим === 'http' ? завантажень :
    (fs.existsSync(лог) ? fs.readFileSync(лог, 'utf8') : '').split('\n').filter(l => l.startsWith('load')).length;
  let pr;
  try {
    await new Promise(r => up.listen(0, '127.0.0.1', r));
    const PORT = await free();
    pr = spawn(process.execPath, [path.join(__dirname, 'проксі_почергове.js')], {
      env: {...process.env, PORT: String(PORT), UP_PORT: String(up.address().port), LMS_MODE: режим,
        LMS_BIN: process.execPath, NODE_OPTIONS: '--require ' + JSON.stringify(lms),
        CTX: JSON.stringify({a: 8192}), ТАЙМАУТ_МС: '1500'}, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe']});
    await та(new Promise((ok, no) => { pr.stdout.on('data', d => {if (d.toString().includes('проксі на')) ok();}); pr.on('error', no); }));
    const t = (н, у) => { assert(у, режим + ': ' + н); console.log('✔ ' + режим + ': ' + н); };
    t('щасливий запит', (await та(post(PORT, 'a'))).код === 200);
    if (режим === 'http') t('контекст із CTX і parallel=1', інстанси[0].config.context_length === 8192 && інстанси[0].config.parallel === 1);
    const кеш = loads();
    t('та сама модель без повторного load', (await та(post(PORT, 'a'))).код === 200 && loads() === кеш);
    fs.writeFileSync(flag, ''); const до = loads();
    t('load падає → 503', (await та(post(PORT, 'b'))).код === 503);
    t('дві спроби load', loads() - до === 2);
    fs.unlinkSync(flag); const до2 = loads();
    t('наступний запит відновлює load', (await та(post(PORT, 'b'))).код === 200 && loads() - до2 === 1);
    t('обрив відповіді', (await та(post(PORT, 'drop'))).обрив);
    t('після обриву черга жива', (await та(post(PORT, 'b'))).код === 200);
    t('тайм-аут → 504', (await та(post(PORT, 'slow'))).код === 504);
    t('після тайм-ауту черга жива', (await та(post(PORT, 'b'))).код === 200);
    const пара = await та(Promise.all([post(PORT, 'a'), post(PORT, 'b')]));
    t('два запити по черзі', пара.every(r => r.код === 200));
    if (режим === 'http') {
      const доПередано = передано;
      t('parallel=4 від сервера → 503', (await та(post(PORT, 'wrong'))).код === 503 && передано === доПередано);
      t('відновлення після невірної конфігурації', (await та(post(PORT, 'a'))).код === 200);
      інстанси[0].config.context_length = 4096; const доЗбою = loads();
      t('контекст 4096 після збою перезавантажується', (await та(post(PORT, 'a'))).код === 200 && loads() === доЗбою + 1);
      інстанси.push({id: 'чужий', model: 'стороння', config: {}});
      const доЧужого = loads(), доВивантаження = вивантажень.length;
      t('чужа модель → 503 без load/unload', (await та(post(PORT, 'b'))).код === 503 && loads() === доЧужого && вивантажень.length === доВивантаження);
      t('чужа модель блокує й кешовану свою', (await та(post(PORT, 'a'))).код === 503 && loads() === доЧужого && вивантажень.length === доВивантаження);
      t('чужий екземпляр збережено', інстанси.some(i => i.id === 'чужий'));
    }
  } finally {
    if (fs.existsSync(flag)) fs.unlinkSync(flag);
    if (pr && pr.exitCode === null) {const кінець = new Promise(r => pr.once('exit', r)); pr.kill(); await та(кінець);}
    up.closeAllConnections(); await new Promise(r => up.close(r));
  }
}
(async () => {await проба('lms'); await проба('http');})().catch(e => {console.error(e); process.exitCode = 1;});
