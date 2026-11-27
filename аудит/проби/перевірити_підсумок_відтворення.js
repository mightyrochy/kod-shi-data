/* Перевіряє вердикт CI за звітами, які CLI приймання пише для окремих частин. */
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const {знімок} = require('./храповик_записів.js');
const {створитиЗразок} = require('./зразок_приймання.js');

const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'підсумок-відтворення-'));
try {
  const база = знімок('  ✔ зелена зразкова звірка\n  ✗ відома червона звірка\n', {вердикт: {доведено: true}}, 1);
  база.звірки[1].вада = 1;
  const проби = створитиЗразок(тека, ['зразок_а', 'зразок_б'].map(id => ({id, база})));
  const стенд = path.join(__dirname, 'перевірити_храповик_базу.js');
  const скрипт = path.join(__dirname, 'підсумок_відтворення.js');
  for (const [назва, завершена, регрес, стани, коди, кодПідсумку, очікування] of [
    ['усі застарілі', null, null, ['застарів у main', 'застарів у main'], [0, 0, 0], 1,
      'порівняних сцен 0 з 2: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)'],
    ['одна порівняна', 'зразок_б', null, ['застарів у main', 'без регресу'], [0, 0, 0], 0,
      'порівняно 1 з 2; застаріло 1'],
    ['регрес', 'зразок_б', 'зразок_б', ['застарів у main', 'регрес'], [0, 1, 0], 1,
      'порівняно 1 з 2; застаріло 1'],
  ]) {
    const резюме = path.join(тека, назва + '.md');
    const звіти = коди.map((код, частина) => {
      const вихід = path.join(тека, `${назва}-${частина}`);
      const звіт = вихід + '.json';
      const приймання = spawnSync(process.execPath, ['--require', стенд,
        path.join(проби, 'приймання_записів.js'), path.join(тека, 'збірка-голови'), тека, вихід,
        String(частина), String(коди.length)], {
        encoding: 'utf8', env: {...process.env, RATCHET_PROBE: JSON.stringify({виклик: 7, завершена, регрес}),
          REPLAY_BASE_BUILD: path.join(тека, 'збірка-бази'), REPLAY_BASE_ROOT: '', REPLAY_ARCHIVE: '',
          REPLAY_MATRIX_SUMMARY: звіт, GITHUB_STEP_SUMMARY: ''},
      });
      assert.ifError(приймання.error);
      assert.equal(приймання.status, код, приймання.stderr);
      assert.deepEqual(JSON.parse(fs.readFileSync(звіт, 'utf8')).map(р => р.стан), стани.slice(частина, частина + 1));
      if (код === 0) {
        const погодження = spawnSync(process.execPath, [path.join(проби, 'живий_після_CI.js'), вихід], {
          encoding: 'utf8', env: {...process.env, GITHUB_EVENT_PATH: '', ZLYTTIA_ZLYTI: ''},
        });
        assert.ifError(погодження.error);
        assert.equal(погодження.status, 0, погодження.stderr);
      }
      return звіт;
    });
    const підсумок = spawnSync(process.execPath, [скрипт, ...звіти], {
      encoding: 'utf8', env: {...process.env, GITHUB_STEP_SUMMARY: резюме},
    });
    assert.ifError(підсумок.error);
    assert.equal(підсумок.status, кодПідсумку, підсумок.stderr);
    assert.equal(підсумок.stdout.trim(), очікування, підсумок.stderr);
    assert.equal(fs.readFileSync(резюме, 'utf8'), очікування + '\n');
    console.log(`✔ ${назва}: частини ${коди.join(', ')} → підсумок ${кодПідсумку}; ${очікування}`);
  }
} finally {
  fs.rmSync(тека, {recursive: true, force: true});
}
