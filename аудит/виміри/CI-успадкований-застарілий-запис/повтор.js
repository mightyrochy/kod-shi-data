/* Повторює незмінений продукт голови й main, перевіряє погодження без рядка PR. */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const {spawnSync} = require('child_process');
const assert = require('node:assert/strict');
const корінь = path.resolve(__dirname, '../../..');

function виконати() {
  const [збірка, кеш, вихід] = process.argv.slice(2).map(ш => path.resolve(ш));
  const середовище = {...process.env, REPLAY_BASE_BUILD: збірка, REPLAY_BASE_ROOT: корінь,
    REPLAY_ARCHIVE: '', GITHUB_ACTIONS: 'true', GITHUB_STEP_SUMMARY: path.join(вихід, 'резюме.md')};
  const підсумки = [], докази = [], коди = [];
  fs.mkdirSync(вихід, {recursive: true});
  for (const частина of [0, 1]) {
    const місце = path.join(вихід, String(частина));
    const р = spawnSync(process.execPath, [path.join(корінь, 'аудит/проби/приймання_записів.js'),
      збірка, кеш, місце, String(частина), '2'],
    {env: середовище, encoding: 'utf8', windowsHide: true, maxBuffer: 16 * 1024 * 1024});
    fs.writeFileSync(path.join(__dirname, 'повтор-' + частина + '.txt.gz'), zlib.gzipSync(р.stdout + '\n' + р.stderr));
    console.log(р.stdout);
    assert.equal(р.status, 0, р.stderr || р.error?.message);
    const подія = path.join(вихід, 'подія.json');
    fs.writeFileSync(подія, JSON.stringify({pull_request: {body: ''}}));
    const погодження = spawnSync(process.execPath, [path.join(корінь, 'аудит/проби/живий_після_CI.js'), місце],
      {env: {...середовище, GITHUB_EVENT_PATH: подія}, encoding: 'utf8', windowsHide: true});
    assert.equal(погодження.status, 0, погодження.stderr);
    коди.push({частина, приймання: р.status, погодження_без_рядка: погодження.status});
    const рядки = JSON.parse(fs.readFileSync(path.join(місце, 'підсумок.json'), 'utf8'));
    for (const рядок of рядки) {
      const сцена = path.join(місце, рядок.сцена.replace(/[/\\:]/g, '_'));
      const голова = JSON.parse(fs.readFileSync(path.join(сцена, 'звірки.json'), 'utf8'));
      const база = JSON.parse(fs.readFileSync(path.join(сцена, 'вимір-бази.json'), 'utf8'));
      assert.equal(рядок.стан, 'застарів у main');
      assert.equal(голова.застарілий.виклик, база.застарілий.виклик);
      assert.equal(голова.застарілий.вхід, база.застарілий.вхід);
      assert.equal(рядок.регресії.length, 0);
      підсумки.push({...рядок, голова: голова.застарілий, база: база.застарілий});
      докази.push({сцена: рядок.сцена, голова, база});
    }
    assert(!р.stdout.includes('ЖИВИЙ ПІСЛЯ'));
    assert.equal((р.stdout.match(/СПІЛЬНИЙ ПРОГІН:/g) || []).length, рядки.length);
    console.log('✔ частина ' + частина + ': приймання=0; погодження без рядка=0');
  }
  assert.equal(підсумки.length, 10);
  fs.writeFileSync(path.join(__dirname, 'повтор.json'), JSON.stringify({коди, сцени: підсумки}, null, 1) + '\n');
  fs.writeFileSync(path.join(__dirname, 'повтор-докази.json.gz'), zlib.gzipSync(JSON.stringify(докази)));
  fs.copyFileSync(середовище.GITHUB_STEP_SUMMARY, path.join(__dirname, 'повтор-резюме.md'));
}

if (require.main === module) виконати();
