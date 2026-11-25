/* Погодження живого прогону під викликом збірки після злиття самозлиття (`workflow_call` від `workflow_run`):
   подія — не push і не PR, злиті цим запуском PR — у `ZLYTTIA_ZLYTI` ([{номер, коміт}]); погодження потрібне кожному. */
const fs = require('fs'), path = require('path'), os = require('os'), http = require('http');
const assert = require('node:assert/strict');
const {spawn} = require('child_process');

const A = 'a'.repeat(40), B = 'b'.repeat(40), РЕПО = 'mightyrochy/kod-shi-data';
const запит = (sha, тіло) => [{merged_at: '2026-11-25T12:00:00Z', merge_commit_sha: sha, base: {ref: 'main', repo: {full_name: РЕПО}},
  head: {repo: {full_name: РЕПО}}, user: {login: 'mightyrochy'}, body: тіло}];
const З_РЯДКОМ = 'Опис\n\nЖИВИЙ ПІСЛЯ: сцена_1 — чи тримається?', БЕЗ = 'Опис без рядка';

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
  const тіла = {[A]: БЕЗ, [B]: БЕЗ};
  const сервер = http.createServer((q, в) => {
    const sha = (q.url.match(/commits\/([0-9a-f]{40})\/pulls/) || [])[1];
    assert(sha && q.url.startsWith(`/repos/${РЕПО}/`), q.url);
    в.setHeader('content-type', 'application/json'); в.end(JSON.stringify(запит(sha, тіла[sha])));
  });
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  try {
    fs.mkdirSync(path.join(тека, 'вихід'));
    fs.writeFileSync(path.join(тека, 'вихід/підсумок.json'), JSON.stringify([{стан: 'запис застарів'}]));
    const подія = path.join(тека, 'подія.json');
    fs.writeFileSync(подія, JSON.stringify({workflow_run: {event: 'pull_request'}, repository: {full_name: РЕПО}}));
    const подіяМітки = path.join(тека, 'подія_мітки.json');
    // `pull_request_target` (мітка «злити» на PR B): подія несе PR B, а злито A — погодження беруться зі злитих.
    fs.writeFileSync(подіяМітки, JSON.stringify({action: 'labeled', pull_request: {number: 2, body: БЕЗ}, repository: {full_name: РЕПО}}));
    const подіяМіткиЗРядком = path.join(тека, 'подія_мітки_з_рядком.json');
    fs.writeFileSync(подіяМіткиЗРядком, JSON.stringify({action: 'labeled', pull_request: {number: 2, body: З_РЯДКОМ}, repository: {full_name: РЕПО}}));
    const середовище = list => ({GITHUB_EVENT_PATH: подія, ZLYTTIA_ZLYTI: JSON.stringify(list), GITHUB_TOKEN: 'x',
      GITHUB_API_URL: `http://127.0.0.1:${сервер.address().port}`});
    const лише = [{номер: 1, коміт: A}], обидва = [{номер: 1, коміт: A}, {номер: 2, коміт: B}];
    const код = async (список, a, b) => { тіла[A] = a; тіла[B] = b; return (await запуск(тека, середовище(список))); };
    assert.equal((await код(лише, БЕЗ, БЕЗ)).код, 1, 'лише A без рядка — відмова');
    assert.equal((await код(лише, З_РЯДКОМ, БЕЗ)).код, 0, 'лише A з рядком — як нині');
    assert.equal((await код(обидва, З_РЯДКОМ, З_РЯДКОМ)).код, 0, 'злито A потім B, обидва погоджено');
    const без_b = await код(обидва, З_РЯДКОМ, БЕЗ);
    assert.equal(без_b.код, 1, 'B без рядка — відмова'); assert(без_b.err.includes('#2') && !без_b.err.includes('#1'), без_b.err);
    const без_a = await код(обидва, БЕЗ, З_РЯДКОМ);
    assert.equal(без_a.код, 1, 'A без рядка — відмова: останній злитий PR не прикриває перший'); assert(без_a.err.includes('#1'), без_a.err);
    const міткаB = {GITHUB_EVENT_PATH: подіяМітки}, міткаBЗРядком = {GITHUB_EVENT_PATH: подіяМіткиЗРядком};
    тіла[A] = З_РЯДКОМ; тіла[B] = БЕЗ;
    assert.equal((await запуск(тека, {...середовище(лише), ...міткаB})).код, 0, 'мітка B (без рядка), злито A (з рядком) — 0, не 1');
    тіла[A] = БЕЗ; тіла[B] = З_РЯДКОМ;
    assert.equal((await запуск(тека, {...середовище(лише), ...міткаBЗРядком})).код, 1, 'мітка B (з рядком), злито A (без) — 1, не хибний пропуск');
    assert.equal((await запуск(тека, {...середовище(обидва), ...міткаBЗРядком})).код, 1, 'мітка B з рядком, злито A без і B — перелік головніший за подію');
    assert.equal((await запуск(тека, {...середовище(обидва), ZLYTTIA_ZLYTI: ''})).код, 1, 'без переліку подія workflow_run не погоджує');
    assert.equal((await запуск(тека, {...середовище(обидва), ZLYTTIA_ZLYTI: '[{"номер":1,"коміт":"x"}]'})).код, 1, 'хибний перелік — відмова');
    console.log('✔ погодження під викликом після злиття: лише A; A+B обидва; мітка B ↔ злито A (обидва напрямки); без рядка в B; без рядка в A; без переліку; хибний перелік');
  } finally {
    сервер.close(); fs.rmSync(тека, {recursive: true, force: true});
  }
})().catch(п => { console.error(п.message); process.exitCode = 1; });
