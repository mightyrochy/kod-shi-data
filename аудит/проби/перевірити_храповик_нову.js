/* Вимірює приймання нової умовної звірки на записаному журналі концерту. */
const fs = require('fs'), path = require('path'), os = require('os');
const assert = require('node:assert/strict');
const процеси = require('child_process');
const {знімок, порівняти} = require('./храповик_записів.js');
const сцена = path.join(__dirname, 'нічні/20261027/б1_концерт_стримано');

// Дочірній браузер замінено його записаними виходами; саме приймання виконується без підмін.
if (process.env.E1_PROBE_LOG) {
  процеси.spawnSync = (_команда, _аргументи, параметри) => {
    const тека = параметри.env.ZNIMKY;
    fs.mkdirSync(тека, {recursive: true});
    fs.copyFileSync(path.join(сцена, 'знімки/доказ.json'), path.join(тека, 'доказ.json'));
    fs.writeSync(параметри.stdio[1], fs.readFileSync(process.env.E1_PROBE_LOG));
    return {status: 1};
  };
} else if (require.main === module) {
  const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'Е1-нова-звірка-'));
  try {
    const лог = fs.readFileSync(path.join(сцена, 'лог.txt'), 'utf8');
    const база = JSON.parse(fs.readFileSync(path.join(сцена, 'база.json'), 'utf8'));
    const доказ = JSON.parse(fs.readFileSync(path.join(сцена, 'знімки/доказ.json'), 'utf8'));
    const виміри = [];
    for (const [назва, текст, очікувано] of [
      ['відома 10231', лог, 0],
      ['нова зелена', лог + '\n  ✔ с1.не_взято\n', 0],
      ['нова червона', лог.replace(/^ВПАЛО 1 ·/m, 'ВПАЛО 2 ·') + '\n  ✗ с1.не_взято  →  не відсічено\n', 1],
    ]) {
      const файл = path.join(тека, назва + '.log');
      fs.writeFileSync(файл, текст);
      const звіт = порівняти(база, знімок(текст, доказ, 1));
      const результат = процеси.spawnSync(process.execPath, ['--require', __filename,
        path.join(__dirname, 'приймання_записів.js'), тека, тека, path.join(тека, назва), '0', '1'],
      {env: {...process.env, E1_PROBE_LOG: файл, REPLAY_BASE_BUILD: '', REPLAY_BASE_ROOT: '', REPLAY_ARCHIVE: ''},
        encoding: 'utf8', windowsHide: true});
      виміри.push({проба: назва, стан: звіт.стан, регресії: звіт.регресії, rc: результат.status});
      if (!process.argv.includes('--до')) assert.equal(результат.status, очікувано, результат.stderr);
    }
    console.log(JSON.stringify(виміри, null, 1));
  } finally {
    assert.equal(path.dirname(path.resolve(тека)), path.resolve(os.tmpdir()));
    fs.rmSync(тека, {recursive: true, force: true});
  }
}
