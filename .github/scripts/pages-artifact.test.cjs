const {test} = require('node:test');
const assert = require('node:assert/strict');
const опублікувати = require('./pages-artifact.cjs');

function стенд(стани) {
  const виклики = [], вихід = {};
  let час = 0;
  return {виклики, вихід, аргументи: {
    artifactId: '24680', context: {repo: {owner: 'власник', repo: 'сайт'}, sha: 'перевірений-коміт'},
    core: {getIDToken: async () => 'тестовий-oidc', info() {}, warning() {}, setOutput: (к, з) => { вихід[к] = з; }},
    тепер: () => час, чекати: async мс => { час += мс; }, таймаут: 15000,
    github: {request: async (шлях, дані) => {
      виклики.push({шлях, дані});
      if (шлях === 'POST /repos/{owner}/{repo}/pages/deployments')
        return {data: {id: 'новий-випуск', page_url: 'https://example.test/'}};
      if (шлях.endsWith('/cancel')) return {data: {}};
      assert.equal(шлях, 'GET /repos/{owner}/{repo}/pages/deployments/{deployment_id}', 'каталог артефактів не читається');
      const наступний = стани.shift() || 'in_progress';
      if (наступний instanceof Error) throw наступний;
      return {data: {status: наступний}};
    }}
  }};
}

test('публікується переданий ID, успіх — лише після завершення саме цього випуску', async () => {
  const с = стенд(['queued', 'in_progress', 'succeed']);
  await опублікувати(с.аргументи);
  assert.deepEqual(с.виклики[0].дані, {owner: 'власник', repo: 'сайт', artifact_id: 24680,
    pages_build_version: 'перевірений-коміт', oidc_token: 'тестовий-oidc'});
  assert.ok(с.виклики.slice(1).every(в => в.дані.deployment_id === 'новий-випуск'));
  assert.deepEqual(с.вихід, {page_url: 'https://example.test/', status: 'succeed'});
});

test('відсутній ID не запускає розгортання', async () => {
  const с = стенд([]);
  await assert.rejects(опублікувати({...с.аргументи, artifactId: ''}), /коректного ID/);
  assert.equal(с.виклики.length, 0);
});

test('помилка вмісту не видається за успіх', async () => {
  const с = стенд(['deployment_content_failed']);
  await assert.rejects(опублікувати(с.аргументи), /deployment_content_failed/);
  assert.deepEqual(с.вихід, {});
  assert.equal(с.виклики.length, 2);
});

test('тимчасовий збій читання не створює повторного випуску', async () => {
  const с = стенд([Object.assign(new Error('тимчасово'), {status: 502}), 'succeed']);
  await опублікувати(с.аргументи);
  assert.equal(с.виклики.filter(в => в.шлях.startsWith('POST')).length, 1);
  assert.equal(с.вихід.status, 'succeed');
});

test('таймаут скасовує незавершений випуск', async () => {
  const с = стенд([]);
  await assert.rejects(опублікувати(с.аргументи), /відведений час/);
  assert.ok(с.виклики.at(-1).шлях.endsWith('/cancel'));
  assert.deepEqual(с.вихід, {});
});

test('відмова доступу не приховується повторними запитами', async () => {
  const с = стенд([Object.assign(new Error('доступ заборонено'), {status: 403})]);
  await assert.rejects(опублікувати(с.аргументи), /доступ заборонено/);
  assert.ok(с.виклики.at(-1).шлях.endsWith('/cancel'));
  assert.equal(с.виклики.length, 3);
});
