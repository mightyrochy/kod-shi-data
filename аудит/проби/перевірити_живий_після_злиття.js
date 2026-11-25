/* Погодження живого прогону під викликом збірки після злиття самозлиття (`workflow_call` від `workflow_run`):
   подія — не push і не PR, коміт злиття — у `ZLYTTIA_SHA`; погодження беруть зі злитого PR цього коміту. */
const fs = require('fs'), path = require('path'), os = require('os'), http = require('http');
const assert = require('node:assert/strict');
const {spawn} = require('child_process');

const SHA = 'a'.repeat(40), РЕПО = 'mightyrochy/kod-shi-data';
const запит = тіло => [{merged_at: '2026-11-25T12:00:00Z', merge_commit_sha: SHA, base: {ref: 'main', repo: {full_name: РЕПО}},
  head: {repo: {full_name: РЕПО}}, user: {login: 'mightyrochy'}, body: тіло}];

function запуск(тека, середовище) {
  return new Promise(resolve => {
    const дитина = spawn(process.execPath, [path.join(__dirname, 'живий_після_CI.js'), path.join(тека, 'вихід')],
      {env: {...process.env, GITHUB_REPOSITORY: РЕПО, ...середовище}});
    let err = '';
    дитина.stderr.on('data', д => { err += д; });
    дитина.on('close', код => resolve({код, err}));
  });
}

(async () => {
  const тека = fs.mkdtempSync(path.join(os.tmpdir(), 'живий-після-злиття-'));
  let тіло = '';
  const сервер = http.createServer((q, в) => {
    assert(q.url.startsWith(`/repos/${РЕПО}/commits/${SHA}/pulls`), q.url);
    в.setHeader('content-type', 'application/json'); в.end(JSON.stringify(запит(тіло)));
  });
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  try {
    fs.mkdirSync(path.join(тека, 'вихід'));
    fs.writeFileSync(path.join(тека, 'вихід/підсумок.json'), JSON.stringify([{стан: 'запис застарів'}]));
    const подія = path.join(тека, 'подія.json');
    fs.writeFileSync(подія, JSON.stringify({workflow_run: {event: 'pull_request'}, repository: {full_name: РЕПО}}));
    const середовище = {GITHUB_EVENT_PATH: подія, ZLYTTIA_SHA: SHA, GITHUB_TOKEN: 'x',
      GITHUB_API_URL: `http://127.0.0.1:${сервер.address().port}`};
    тіло = 'Опис без рядка';
    assert.equal((await запуск(тека, середовище)).код, 1, 'без рядка ЖИВИЙ ПІСЛЯ у злитому PR — відмова');
    тіло = 'Опис\n\nЖИВИЙ ПІСЛЯ: сцена_1 — чи тримається?';
    const з = await запуск(тека, середовище);
    assert.equal(з.код, 0, з.err);
    assert.equal((await запуск(тека, {...середовище, ZLYTTIA_SHA: ''})).код, 1, 'без sha подія workflow_run не погоджує');
    console.log('✔ погодження під викликом після злиття: без рядка=1; з рядком=0; без sha=1');
  } finally {
    сервер.close(); fs.rmSync(тека, {recursive: true, force: true});
  }
})().catch(п => { console.error(п.message); process.exitCode = 1; });
