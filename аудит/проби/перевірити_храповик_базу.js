/* Перевіряє приймання й погодження через CLI на зразках, без живих записів і браузера. */
const assert = require('node:assert/strict');
const fs = require('fs'), path = require('path'), os = require('os');
const {spawnSync} = require('child_process');
const {знімок} = require('./храповик_записів.js');

if (process.env.RATCHET_PROBE) {
  require('child_process').spawnSync = (_команда, аргументи, параметри) => {
    const базовий = аргументи[2] === process.env.REPLAY_BASE_BUILD;
    const варіант = JSON.parse(process.env.RATCHET_PROBE);
    const тека = параметри.env.ZNIMKY;
    const id = path.basename(path.dirname(path.dirname(параметри.env.REPLAY_EXCHANGE)));
    fs.mkdirSync(тека, {recursive: true});
    const завершено = базовий && варіант.нова;
    const запит = базовий ? {model: 'зразок', messages: [{content: id, role: 'user'}]}
      : {messages: [{role: 'user', content: варіант.іншийВхід ? id + ' змінено' : id}], model: 'зразок'};
    if (завершено)
      fs.writeFileSync(path.join(тека, 'доказ.json'), JSON.stringify({вердикт: {доведено: true}}));
    else
      fs.writeFileSync(path.join(тека, 'помилка_відтворення.json'), JSON.stringify({
        код: 'REPLAY_STALE', виклик: базовий ? 7 : варіант.виклик, причина: 'запис застарів',
        ...(!(базовий ? варіант.безВходуБази : варіант.безВходу) ? {запит} : {})}));
    const лог = (!базовий && варіант.регрес ? '  ✗ зелена зразкова звірка' : '  ✔ зелена зразкова звірка') +
      '\n  ✗ відома червона звірка\n';
    fs.writeSync(параметри.stdio[1], лог);
    return {status: завершено ? 1 : 3};
  };
} else if (require.main === module) {
  const джерело = process.argv[2] ? path.resolve(process.argv[2]) : __dirname;
  const до = джерело !== __dirname;
  const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'храповик-база-'));
  try {
    const проби = path.join(тека, 'аудит/проби');
    fs.mkdirSync(проби, {recursive: true});
    for (const ім of ['приймання_записів.js', 'храповик_записів.js', 'записаний_обмін.js', 'живий_після_CI.js'])
      fs.copyFileSync(path.join(джерело, ім), path.join(проби, ім));
    fs.writeFileSync(path.join(проби, 'рв6_стенд.js'), '/* Дочірній браузер замінено виходами зразка. */\n');
    const база = знімок('  ✔ зелена зразкова звірка\n  ✗ відома червона звірка\n', {вердикт: {доведено: true}}, 1);
    база.звірки[1].вада = 1;
    for (const id of ['зразок_а', 'зразок_б']) {
      const місце = path.join(проби, 'нічні/20261112', id);
      const обмін = path.join(місце, 'VIDPOVIDI/обмін');
      fs.mkdirSync(обмін, {recursive: true});
      fs.writeFileSync(path.join(місце, 'повтор.json'), JSON.stringify({версія: 1, жінка: {імʼя: id}, змінні: {}, сід: 3}));
      fs.writeFileSync(path.join(місце, 'база.json'), JSON.stringify(база));
    }
    const рядок = 'ЖИВИЙ ПІСЛЯ: зразок_а — перезаписати змінений вхід';
    let перевірок = 0;
    for (const [назва, варіант, стан, безРядка, зРядком] of [
      ['успадкована', {виклик: 7}, до ? 'запис застарів на базі' : 'застарів у main', 0, 0],
      ['нова', {виклик: 7, нова: true}, 'запис застарів', 1, 0],
      ['раніший виклик', {виклик: 6}, 'запис застарів', 1, 0],
      ['пізніший виклик', {виклик: 8}, 'запис застарів', 1, 0],
      ['інший запит', {виклик: 7, іншийВхід: true}, 'запис застарів', 1, 0],
      ['нема запиту голови', {виклик: 7, безВходу: true}, 'запис застарів', 1, 0],
      ['нема запиту бази', {виклик: 7, безВходуБази: true}, 'запис застарів', 1, 0],
      ['нема виміру main', {виклик: 7, безБази: true}, 'запис застарів', 1, 0],
      ['регрес перед успадкованістю', {виклик: 7, регрес: true}, 'регрес', 1, 1],
      ['регрес перед новою застарілістю', {виклик: 7, нова: true, регрес: true}, 'регрес', 1, 1],
    ]) {
      const вихід = path.join(тека, назва), резюме = path.join(тека, назва + '.md');
      const середовище = {...process.env, RATCHET_PROBE: JSON.stringify(варіант),
        REPLAY_BASE_BUILD: варіант.безБази ? '' : path.join(тека, 'збірка-бази'), REPLAY_BASE_ROOT: '', REPLAY_ARCHIVE: '',
        GITHUB_ACTIONS: 'true', GITHUB_STEP_SUMMARY: резюме};
      const приймання = spawnSync(process.execPath, ['--require', __filename,
        path.join(проби, 'приймання_записів.js'), path.join(тека, 'збірка-голови'), тека, вихід],
      {encoding: 'utf8', windowsHide: true, env: середовище});
      assert.equal(приймання.status, стан === 'регрес' ? 1 : 0, приймання.stderr);
      const підсумок = JSON.parse(fs.readFileSync(path.join(вихід, 'підсумок.json'), 'utf8'));
      assert.equal(підсумок.length, 2);
      assert(підсумок.every(р => р.стан === стан), приймання.stdout);
      for (const [опис, rc] of [['', безРядка], [рядок, зРядком]]) {
        const подія = path.join(тека, 'подія.json');
        fs.writeFileSync(подія, JSON.stringify({pull_request: {body: опис}}));
        const погодження = spawnSync(process.execPath, [path.join(проби, 'живий_після_CI.js'), вихід],
          {encoding: 'utf8', windowsHide: true, env: {...середовище, GITHUB_EVENT_PATH: подія}});
        assert.equal(погодження.status, rc, погодження.stderr);
        перевірок++;
      }
      if (назва === 'успадкована') {
        for (const текст of [приймання.stdout, fs.readFileSync(резюме, 'utf8')]) {
          assert(!текст.includes('ЖИВИЙ ПІСЛЯ'));
          for (const id of ['зразок_а', 'зразок_б']) assert.equal(текст.includes('СПІЛЬНИЙ ПРОГІН: ' + id), !до);
        }
        assert.equal((приймання.stdout.match(/::warning::/g) || []).length, 2);
        const безПодії = spawnSync(process.execPath, [path.join(проби, 'живий_після_CI.js'), вихід],
          {encoding: 'utf8', windowsHide: true, env: {...середовище, GITHUB_EVENT_PATH: ''}});
        assert.equal(безПодії.status, 0, безПодії.stderr);
        console.log('✔ рядків спільного прогону=' + (до ? 0 : 2) + '; погодження без події=0');
      }
      console.log('✔ ' + назва + ': ' + стан + '; без рядка=' + безРядка + '; з рядком=' + зРядком);
    }
    console.log('✔ ' + перевірок + ' кодів виходу погодження; 10 варіантів приймання; 2 зразкові сцени');
  } finally {
    assert.equal(path.dirname(path.resolve(тека)), path.resolve(os.tmpdir()));
    fs.rmSync(тека, {recursive: true, force: true});
  }
}
