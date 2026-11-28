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
  const подія = path.join(тека, 'подія.json');
  fs.writeFileSync(подія, JSON.stringify({pull_request: {body: 'ЖИВИЙ ПІСЛЯ: зразок_а — перевірити запит'}}));
  for (const [назва, варіант, продукт, стани, коди, кодПідсумку, очікування] of [
    ['усі застарілі в main', {}, 'false', ['застарів у main', 'застарів у main'], [0, 0, 0], 0,
      'порівняних сцен 0 з 2: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)'],
    ['одна порівняна', {завершена: 'зразок_б'}, 'true', ['застарів у main', 'без регресу'], [0, 0, 0], 0,
      'порівняно 1 з 2; застаріло 1'],
    ['регрес', {завершена: 'зразок_б', регрес: 'зразок_б'}, 'true',
      ['застарів у main', 'регрес'], [0, 1, 0], 1,
      'порівняно 1 з 2; застаріло 1'],
    ['PR змінив запит', {іншийВхід: true}, 'true', ['запис застарів', 'запис застарів'], [0, 0, 0], 0,
      'порівняних сцен 0 з 2: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)'],
    ['зіпсований запис без зміни продукту', {іншийВхід: true}, 'false',
      ['запис застарів', 'запис застарів'], [0, 0, 0], 1,
      'порівняних сцен 0 з 2: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)'],
    ['зміна запиту не доведена', {безВходу: true}, 'true', ['запис застарів', 'запис застарів'], [0, 0, 0], 1,
      'порівняних сцен 0 з 2: відтворення нічого не виміряло; потрібні свіжі записи (нічний набір)'],
  ]) {
    const резюме = path.join(тека, назва + '.md');
    const звіти = коди.map((код, частина) => {
      const вихід = path.join(тека, `${назва}-${частина}`);
      const звіт = вихід + '.json';
      const приймання = spawnSync(process.execPath, ['--require', стенд,
        path.join(проби, 'приймання_записів.js'), path.join(тека, 'збірка-голови'), тека, вихід,
        String(частина), String(коди.length)], {
        encoding: 'utf8', env: {...process.env, RATCHET_PROBE: JSON.stringify({виклик: 7, ...варіант}),
          REPLAY_BASE_BUILD: path.join(тека, 'збірка-бази'), REPLAY_BASE_ROOT: '', REPLAY_ARCHIVE: '',
          REPLAY_MATRIX_SUMMARY: звіт, GITHUB_STEP_SUMMARY: ''},
      });
      assert.ifError(приймання.error);
      assert.equal(приймання.status, код, приймання.stderr);
      assert.deepEqual(JSON.parse(fs.readFileSync(звіт, 'utf8')).map(р => р.стан), стани.slice(частина, частина + 1));
      if (код === 0) {
        const погодження = spawnSync(process.execPath, [path.join(проби, 'живий_після_CI.js'), вихід], {
          encoding: 'utf8', env: {...process.env, GITHUB_EVENT_PATH: подія, ZLYTTIA_ZLYTI: ''},
        });
        assert.ifError(погодження.error);
        assert.equal(погодження.status, 0, погодження.stderr);
      }
      return звіт;
    });
    const підсумок = spawnSync(process.execPath, [скрипт, ...звіти], {
      encoding: 'utf8', env: {...process.env, GITHUB_STEP_SUMMARY: резюме, REPLAY_PRODUCT: продукт},
    });
    assert.ifError(підсумок.error);
    assert.equal(підсумок.status, кодПідсумку, підсумок.stderr);
    assert.equal(підсумок.stdout.split('\n')[0], очікування, підсумок.stderr);
    assert.equal(fs.readFileSync(резюме, 'utf8'), підсумок.stdout);
    for (const [і, id] of ['зразок_а', 'зразок_б'].entries()) {
      const неВиміряно = стани[і] === 'застарів у main' || (продукт === 'true' && варіант.іншийВхід === true);
      assert.equal(підсумок.stdout.includes(`${id} — не виміряно`), неВиміряно);
    }
    assert.equal(підсумок.stdout.includes('messages.0.content: зразок_а → зразок_а змінено'), !!варіант.іншийВхід);
    assert.equal(підсумок.stdout.includes('застарілий запис у PR без зміни продукту'),
      продукт === 'false' && стани.includes('запис застарів'));
    console.log(`✔ ${назва}: частини ${коди.join(', ')} → підсумок ${кодПідсумку}; ${очікування}`);
  }
} finally {
  fs.rmSync(тека, {recursive: true, force: true});
}
