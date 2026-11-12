/* Два повні повтори десяти записаних сцен; порівнює всі байти першого запиту. */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const assert = require('assert/strict');
const {spawnSync} = require('child_process');
const корінь = path.resolve(__dirname, '../../..');
const приймання = path.join(корінь, 'аудит/проби/приймання_записів.js');
const {ключЗапиту} = require('../../проби/записаний_обмін.js');
const {перелік} = require('../../проби/приймання_записів.js');

function розбіжності(а, б, шлях = '') {
  if (typeof а === 'string' && typeof б === 'string') {
    try { return розбіжності(JSON.parse(а), JSON.parse(б), шлях + ':json'); } catch (_) {}
  }
  if (а && б && typeof а === 'object' && typeof б === 'object')
    return [...new Set([...Object.keys(а), ...Object.keys(б)])].flatMap(
      к => розбіжності(а[к], б[к], шлях + '.' + к));
  return а === б ? [] : [шлях];
}

function виконати() {
  const [мітка, збірка, кеш, вихід] = process.argv.slice(2);
  assert(['до', 'після'].includes(мітка));
  const всіЗапити = [], журнали = [], пари = new Map();
  const записи = new Map(перелік().map(с => [с.назва, с.обмін]));
  const середовище = {...process.env};
  for (const к of Object.keys(середовище)) if (к.startsWith('REPLAY_')) delete середовище[к];
  for (let повтор = 1; повтор <= 2; повтор++) {
    const тека = path.resolve(вихід, мітка + '-' + повтор);
    const р = spawnSync(process.execPath, [приймання, path.resolve(збірка), path.resolve(кеш), тека],
      {cwd: корінь, env: середовище, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024,
        windowsHide: true});
    assert.equal(р.status, 0, р.stderr || р.error?.message);
    журнали.push(р.stdout, р.stderr);
    const підсумок = JSON.parse(fs.readFileSync(path.join(тека, 'підсумок.json'), 'utf8'));
    assert.equal(підсумок.length, 10);
    for (const сцена of підсумок) {
      assert.equal(сцена.rc, 3);
      const папка = path.join(тека, сцена.сцена.replace(/[/\\:]/g, '_'));
      const помилка = JSON.parse(fs.readFileSync(path.join(папка, 'знімки/помилка_відтворення.json'), 'utf8'));
      assert.equal(помилка.код, 'REPLAY_STALE');
      assert.equal(помилка.виклик, 1);
      assert(помилка.запит);
      всіЗапити.push({сцена: сцена.сцена, повтор, запит: помилка.запит});
      журнали.push(fs.readFileSync(path.join(папка, 'лог.txt'), 'utf8'));
      if (!пари.has(сцена.сцена)) пари.set(сцена.сцена, []);
      пари.get(сцена.сцена).push(помилка.запит);
    }
    console.log(мітка + ': завершено повтор ' + повтор + ', сцен ' + підсумок.length);
  }
  const сцени = [...пари].map(([сцена, [а, б]]) => {
    const тека = записи.get(сцена);
    const файл = fs.readdirSync(тека).filter(ім => /^\d+\.json$/.test(ім)).sort()[0];
    const запис = JSON.parse(fs.readFileSync(path.join(тека, файл), 'utf8'));
    return {сцена,
      побайтно_однакові: Buffer.from(JSON.stringify(а)).equals(Buffer.from(JSON.stringify(б))),
      sha256: [ключЗапиту(а), ключЗапиту(б)], розбіжності: розбіжності(а, б),
      розбіжності_із_записом: розбіжності(запис.запит, а)};
  });
  const результат = {сцен: сцени.length,
    розбіжностей: сцени.filter(с => !с.побайтно_однакові).length,
    застарілих_повторів: всіЗапити.length, сцени};
  fs.writeFileSync(path.join(__dirname, 'вимір-' + мітка + '.json'), JSON.stringify(результат, null, 1) + '\n');
  fs.writeFileSync(path.join(__dirname, 'запити-' + мітка + '.json.gz'), zlib.gzipSync(JSON.stringify(всіЗапити)));
  fs.writeFileSync(path.join(__dirname, 'стенд-' + мітка + '.txt.gz'), zlib.gzipSync(журнали.join('\n')));
  console.log('Розбіжностей: ' + результат.розбіжностей + ' з ' + результат.сцен);
  if (мітка === 'після') assert.equal(результат.розбіжностей, 0);
}

if (require.main === module) виконати();
