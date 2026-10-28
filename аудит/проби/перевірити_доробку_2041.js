/* Вимірює погодження push та виправлення нових звірок на записаному журналі концерту. */
const fs = require('fs'), path = require('path'), os = require('os');
const assert = require('node:assert/strict');
const процеси = require('child_process');

// Підставляються лише відповіді GitHub та виходи дочірнього браузера; приймання виконується цілим.
if (process.env.E1_2041_FIXTURE) {
  const дані = JSON.parse(fs.readFileSync(process.env.E1_2041_FIXTURE, 'utf8'));
  global.fetch = async () => ({ok: !дані.помилкаAPI, status: дані.помилкаAPI ? 503 : 200,
    json: async () => дані.prs || []});
  if (дані.лог) процеси.spawnSync = (_команда, аргументи, параметри) => {
    const тека = параметри.env.ZNIMKY;
    fs.mkdirSync(тека, {recursive: true});
    fs.writeFileSync(path.join(тека, 'доказ.json'), JSON.stringify({вердикт: {доведено: true}}));
    fs.writeSync(параметри.stdio[1], аргументи[2] === дані.збіркаБази ? дані.логБази : дані.лог);
    return {status: 1};
  };
} else if (require.main === module) {
  const корінь = path.resolve(process.argv[2] || path.join(__dirname, '../..'));
  const проби = path.join(корінь, 'аудит/проби');
  const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'Е1-2041-'));
  const результати = [];
  function виконати(назва, файл, аргументи, дані, подія, очікувано) {
    const місце = path.join(тека, String(результати.length));
    fs.mkdirSync(місце);
    const фікстура = path.join(місце, 'fixture.json'), подіяФайл = path.join(місце, 'event.json');
    fs.writeFileSync(фікстура, JSON.stringify(дані));
    fs.writeFileSync(подіяФайл, JSON.stringify(подія));
    const вихід = path.join(місце, 'out');
    if (файл === 'живий_після_CI.js') {
      fs.mkdirSync(вихід);
      fs.writeFileSync(path.join(вихід, 'підсумок.json'), JSON.stringify(дані.підсумок || [{стан: 'запис застарів'}]));
    }
    const результат = процеси.spawnSync(process.execPath, ['--require', __filename,
      path.join(проби, файл), ...аргументи(вихід)], {cwd: корінь, encoding: 'utf8', windowsHide: true,
      env: {...process.env, E1_2041_FIXTURE: фікстура, GITHUB_EVENT_PATH: подіяФайл,
        GITHUB_EVENT_NAME: подія.pull_request ? 'pull_request' : 'push',
        GITHUB_REPOSITORY: 'mightyrochy/kod-shi-data', GITHUB_API_URL: 'https://api.github.com', GITHUB_TOKEN: '',
        REPLAY_BASE_BUILD: дані.збіркаБази || '', REPLAY_BASE_ROOT: '', REPLAY_ARCHIVE: ''}});
    результати.push({проба: назва, rc: результат.status, очікувано,
      ...(результат.status !== очікувано ? {помилка: результат.stderr.trim()} : {})});
  }
  try {
    const sha = 'a'.repeat(40), інший = 'b'.repeat(40);
    const рядок = 'ЖИВИЙ ПІСЛЯ: б1_концерт_стримано — перезаписати вхід моделі';
    const push = {ref: 'refs/heads/main', after: sha, repository: {full_name: 'mightyrochy/kod-shi-data'},
      head_commit: {id: sha, message: 'Злиття PR'}};
    const pr = {number: 2041, body: рядок, merged_at: '2026-10-28T09:00:00Z', merge_commit_sha: sha,
      user: {login: 'mightyrochy'}, base: {ref: 'main', repo: {full_name: 'mightyrochy/kod-shi-data'}},
      head: {repo: {full_name: 'mightyrochy/kod-shi-data'}}};
    for (const [назва, подія, дані, rc] of [
      ['PR з погодженням', {pull_request: {body: рядок}}, {}, 0],
      ['PR без погодження', {pull_request: {body: ''}}, {}, 1],
      ['push з погодженого PR', push, {prs: [pr]}, 0],
      ['push без погодження', push, {prs: [{...pr, body: ''}]}, 1],
      ['push з рядком у коміті злиття', {...push, head_commit: {id: sha, message: рядок}}, {}, 0],
      ['push: відкритий PR не є погодженням', push, {prs: [{...pr, merged_at: null}]}, 1],
      ['push: погодження іншої голови', push, {prs: [{...pr, merge_commit_sha: інший}]}, 1],
      ['push: PR з форка', push, {prs: [{...pr, head: {repo: {full_name: 'чужий/форк'}}}]}, 1],
      ['push: API недоступний', push, {помилкаAPI: true}, 1],
      ['push: справжній регрес з погодженням', push, {prs: [pr], підсумок: [{стан: 'регрес'}]}, 1],
      ['push: точний запис без погодження', push, {підсумок: [{стан: 'без регресу'}]}, 0],
    ]) виконати(назва, 'живий_після_CI.js', в => [в], дані, подія, rc);

    const лог = fs.readFileSync(path.join(проби, 'нічні/20261027/б1_концерт_стримано/лог.txt'), 'utf8');
    const зелений = лог + '\n  ✔ с1.нова_звірка\n';
    const червоний = лог.replace(/^ВПАЛО 1 ·/m, 'ВПАЛО 2 ·') + '\n  ✗ с1.нова_звірка  →  не виконано\n';
    const посилений = лог.replace(/^  ✔ /m, '  ✗ ').replace(/^ВПАЛО 1 ·/m, 'ВПАЛО 2 ·');
    const стала = лог.match(/^  ✔ (.+)$/m)[1].replace(/\r$/, '');
    const перейменувати = колір => лог.replace('  ✔ ' + стала,
      '  ІД ЗВІРКИ: ' + JSON.stringify({назва: 'Оновлений опис', стала}) + '\n  ' + колір + ' Оновлений опис');
    for (const [назва, логБази, логГолови, rc] of [
      ['нова червона на main, зелена на голові', червоний, зелений, 0],
      ['посилена червона на main, зелена на голові', посилений, лог, 0],
      ['нова червона на голові й main', червоний, червоний, 1],
      ['нова червона лише на голові', лог, червоний, 1],
      ['нова зелена main стала червоною', зелений, червоний, 1],
      ['виправлена 10231 на main знову червона', лог.replace('  ✗ ', '  ✔ ').replace(/^ВПАЛО 1 ·/m, 'ВПАЛО 0 ·'), лог, 1],
      ['перейменована зелена', лог, перейменувати('✔'), 0],
      ['перейменована червона', лог, перейменувати('✗'), 1],
    ]) виконати(назва, 'приймання_записів.js', в => [тека, тека, в, '0', '1'],
      {лог: логГолови, логБази, збіркаБази: path.join(тека, 'base')}, {}, rc);
    console.log(JSON.stringify(результати, null, 1));
    if (!process.argv.includes('--до')) assert(результати.every(р => р.rc === р.очікувано), 'Мірила доробки не пройдено');
  } finally {
    assert.equal(path.dirname(path.resolve(тека)), path.resolve(os.tmpdir()));
    fs.rmSync(тека, {recursive: true, force: true});
  }
}
