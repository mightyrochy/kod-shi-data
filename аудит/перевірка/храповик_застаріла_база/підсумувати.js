/* Зберігає перевірювані ДО → ПІСЛЯ на виходах справжнього браузерного стенда. */
const assert = require('node:assert/strict');
const fs = require('fs'), path = require('path');
const crypto = require('crypto');
const корінь = path.resolve(__dirname, '../../..');
const докази = path.resolve(process.argv[2]);
const {результатСтенда} = require(path.join(корінь, 'аудит/проби/приймання_записів.js'));
const після = require(path.join(корінь, 'аудит/проби/храповик_записів.js'));
const до = require(path.join(докази, 'до/аудит/проби/храповик_записів.js'));
const погодженняДо = require(path.join(докази, 'до/аудит/проби/живий_після_CI.js'));
const погодженняПісля = require(path.join(корінь, 'аудит/проби/живий_після_CI.js'));
const база = JSON.parse(fs.readFileSync(path.join(корінь,
  'аудит/проби/нічні/20261027/б1_концерт_стримано/база.json'), 'utf8'));

function прочитати(назва) {
  const тека = path.join(докази, назва);
  const результат = JSON.parse(fs.readFileSync(path.join(тека, 'результат.json'), 'utf8'));
  const вимір = результатСтенда(тека, результат.rc);
  const збірка = path.join(докази, 'збірки', результат.sha);
  const паспортЗбірки = {обʼєкти: JSON.parse(fs.readFileSync(path.join(збірка, 'входи.json'), 'utf8')),
    html_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(збірка, 'index.html'))).digest('hex')};
  const вихід = path.join(__dirname, 'докази', назва);
  fs.mkdirSync(вихід, {recursive: true});
  fs.writeFileSync(path.join(вихід, 'вимір.json'), JSON.stringify({sha: результат.sha,
    збірка: паспортЗбірки, ...вимір}, null, 1) + '\n');
  fs.writeFileSync(path.join(вихід, 'лог.txt'), fs.readFileSync(path.join(тека, 'лог.txt'), 'utf8')
    .split(докази).join('<докази>').split(корінь).join('<репозиторій>'));
  return {sha: результат.sha, ...вимір};
}

async function виконати() {
  const виміри = [];
  const контрприклади = [];
  for (const номер of [2109, 2124, 2118]) {
    const голова = прочитати(номер + '-голова'), вимірБази = прочитати(номер + '-база');
    const раніше = до.порівняти(до.затягнутиЗелені(база, вимірБази), голова);
    const тепер = після.порівняти(після.затягнутиЗелені(база, вимірБази), голова, вимірБази);
    const подія = {pull_request: {body: ''}};
    fs.writeFileSync(path.join(докази, 'підсумок.json'), JSON.stringify([раніше]));
    await assert.rejects(() => погодженняДо.перевірити(докази, подія), /ЖИВИЙ ПІСЛЯ/);
    fs.writeFileSync(path.join(докази, 'підсумок.json'), JSON.stringify([тепер]));
    await погодженняПісля.перевірити(докази, подія);
    assert.equal(тепер.стан, 'запис застарів на базі');
    виміри.push({PR: номер, голова: голова.sha, база: вимірБази.sha,
      виклик_голови: голова.застарілий.виклик, вхід_голови: голова.застарілий.вхід,
      виклик_бази: вимірБази.застарілий.виклик, вхід_бази: вимірБази.застарілий.вхід,
      ДО: {...раніше, CI: 'блок без ЖИВИЙ ПІСЛЯ'}, ПІСЛЯ: {...тепер, CI: 'проходить без ЖИВИЙ ПІСЛЯ'}});
    if (номер === 2109) for (const [назва, застарілий] of [
      ['раніше за базу', {...голова.застарілий, виклик: 6}],
      ['інший виклик', {...голова.застарілий, виклик: 8}],
      ['інший вхід', {...голова.застарілий, вхід: 'b'.repeat(64)}],
    ]) {
      const змінений = {...голова, застарілий};
      for (const [механізм, перевірка] of [[до, погодженняДо], [після, погодженняПісля]]) {
        const стан = механізм.порівняти(база, змінений, вимірБази);
        assert.equal(стан.стан, 'запис застарів');
        fs.writeFileSync(path.join(докази, 'підсумок.json'), JSON.stringify([стан]));
        await assert.rejects(() => перевірка.перевірити(докази, подія), /ЖИВИЙ ПІСЛЯ/);
      }
      контрприклади.push({назва, ДО: 'блок', ПІСЛЯ: 'блок'});
    }
  }
  const старий = прочитати('main-старий-запис'), новий = прочитати('main-новий-запис');
  const новаБаза = JSON.parse(fs.readFileSync(path.join(корінь,
    'аудит/проби/нічні/20261028/б1_концерт_стримано/база.json'), 'utf8'));
  assert.equal(старий.застарілий.виклик, 7);
  assert.equal(після.порівняти(новаБаза, новий).стан, 'без регресу');
  assert.equal(новий.завершено, true);
  const обмін = JSON.parse(fs.readFileSync(path.join(докази, 'main-новий-запис/лог.txt'), 'utf8')
    .match(/^ВІДТВОРЕННЯ: (\{.+\})\r?$/m)[1]);
  assert.deepEqual(обмін, {взято: 39, записів: 39});
  const звіт = {PR: виміри, контрприклади, запис_main: {sha: новий.sha, ДО: старий.застарілий,
    ПІСЛЯ: {стан: 'без регресу', завершено: новий.завершено, звірок: новий.звірки.length,
      червоні: новий.звірки.filter(з => !з.зелена), ...обмін}},
    зайвих_блокувань: {ДО: 3, ПІСЛЯ: 0}};
  fs.writeFileSync(path.join(__dirname, 'докази/підсумок.json'), JSON.stringify(звіт, null, 1) + '\n');
  console.log(JSON.stringify(звіт, null, 1));
}

виконати().catch(помилка => { console.error(помилка); process.exitCode = 1; });
