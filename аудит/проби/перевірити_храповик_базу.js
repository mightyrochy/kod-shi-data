/* Перевіряє весь ланцюг приймання: вимір бази → храповик → вимога живого прогону. */
const assert = require('node:assert/strict');
const fs = require('fs'), path = require('path'), os = require('os');
const процеси = require('child_process');
const сцена = path.join(__dirname, 'нічні/20261027/б1_концерт_стримано');

if (process.env.RATCHET_PROBE) {
  процеси.spawnSync = (_команда, _аргументи, параметри) => {
    const базовий = path.basename(path.dirname(параметри.env.ZNIMKY)) === 'main';
    const варіант = JSON.parse(process.env.RATCHET_PROBE);
    const виклик = базовий ? 7 : варіант.виклик;
    const тека = параметри.env.ZNIMKY;
    fs.mkdirSync(тека, {recursive: true});
    // Різний порядок ключів не змінює канонічний вхід.
    const запит = базовий ? {model: 'модель', messages: [{content: 'база', role: 'user'}]}
      : {messages: [{role: 'user', content: варіант.вхід}], model: 'модель'};
    fs.writeFileSync(path.join(тека, 'помилка_відтворення.json'), JSON.stringify({
      код: 'REPLAY_STALE', виклик, причина: 'запис застарів',
      ...(!варіант.безВходу ? {запит} : {})}));
    const лог = fs.readFileSync(path.join(сцена, 'лог.txt'), 'utf8');
    const звірка = лог.split(/\r?\n/).find(р => р.startsWith('  ✔ '));
    fs.writeSync(параметри.stdio[1], варіант.регрес && !базовий ? звірка.replace('✔', '✗') : звірка);
    return {status: 3};
  };
} else if (require.main === module) {
  (async () => {
    const {перевірити} = require('./живий_після_CI.js');
    const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'храповик-база-'));
    try {
      for (const [назва, варіант, стан, блокує] of [
        ['однаковий вхід', {виклик: 7, вхід: 'база'}, 'запис застарів на базі', false],
        ['раніше за базу', {виклик: 6, вхід: 'база'}, 'запис застарів', true],
        ['інший виклик', {виклик: 8, вхід: 'база'}, 'запис застарів', true],
        ['інший вхід', {виклик: 7, вхід: 'голова'}, 'запис застарів', true],
        ['нема входу', {виклик: 7, безВходу: true}, 'запис застарів', true],
        ['червона звірка', {виклик: 7, вхід: 'база', регрес: true}, 'регрес', true],
      ]) {
        const вихід = path.join(тека, назва), резюме = path.join(тека, назва + '.md');
        const результат = процеси.spawnSync(process.execPath, ['--require', __filename,
          path.join(__dirname, 'приймання_записів.js'), тека, тека, вихід, '0', '1'],
        {encoding: 'utf8', windowsHide: true, env: {...process.env,
          RATCHET_PROBE: JSON.stringify(варіант), REPLAY_BASE_BUILD: тека, REPLAY_BASE_ROOT: '', REPLAY_ARCHIVE: '',
          GITHUB_ACTIONS: 'true', GITHUB_STEP_SUMMARY: резюме}});
        assert.equal(результат.status, стан === 'регрес' ? 1 : 0, результат.stderr);
        const підсумок = JSON.parse(fs.readFileSync(path.join(вихід, 'підсумок.json'), 'utf8'));
        assert(підсумок.length > 0);
        assert(підсумок.every(р => р.стан === стан), результат.stdout);
        const дія = () => перевірити(вихід, {pull_request: {body: ''}});
        if (блокує) await assert.rejects(дія, /ЖИВИЙ ПІСЛЯ|регрес/);
        else {
          await дія();
          await перевірити(вихід, null);
          assert(!результат.stdout.includes('ЖИВИЙ ПІСЛЯ'));
          assert(!fs.readFileSync(резюме, 'utf8').includes('ЖИВИЙ ПІСЛЯ'));
          assert(результат.stdout.includes('::warning::' + підсумок[0].сцена));
        }
        if (стан === 'запис застарів')
          await перевірити(вихід, {pull_request: {body: 'ЖИВИЙ ПІСЛЯ: концерт — перезаписати вхід'}});
        console.log('✔ ' + назва + ': ' + стан + '; без погодження ' + (блокує ? 'блок' : 'проходить'));
      }
    } finally {
      assert.equal(path.dirname(path.resolve(тека)), path.resolve(os.tmpdir()));
      fs.rmSync(тека, {recursive: true, force: true});
    }
  })().catch(помилка => { console.error(помилка); process.exitCode = 1; });
}
