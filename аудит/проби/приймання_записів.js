/* Усі зареєстровані живі сцени проходять той самий браузерний стенд із відповідями з диска. */
const fs = require('fs'), path = require('path');
const {spawnSync} = require('child_process');
const {знімок, звіритиБазу, порівняти, затягнутиЗелені} = require('./храповик_записів.js');
const {ключЗапиту} = require('./записаний_обмін.js');
const корінь = path.resolve(__dirname, '../..');

function серіяДва() {
  const текст = fs.readFileSync(path.join(__dirname, 'б1_доречність.md'), 'utf8');
  const блок = текст.match(/```\r?\n(б1_[\s\S]*?)\r?\n```/);
  if (!блок) throw new Error('Нема переліку серії 2');
  return блок[1].split(/\r?\n/).map((рядок, і) => {
    const [назва, жінка, запит, змінні] = рядок.split('|');
    if (!назва || !жінка || !запит || змінні) throw new Error('Не прочитано сцену: ' + рядок);
    return {назва: String(і + 1).padStart(2, '0') + '_' + назва,
      записи: path.join(__dirname, 'б1/ДО-2710', String(і + 1).padStart(2, '0') + '_' + назва, 'VIDPOVIDI'),
      змінні: {CHAT_TEXT: запит, ZHINKA: path.join(__dirname, 'жінки', жінка + '.json'),
        MODEL: 'qwen/qwen3.5-9b', MODEL_MOVA: 'mamaylm-gemma-3-12b-it-v2.0', OTSINKA: '0', FOTO: '0'}, сід: 3};
  });
}

function новіЗаписи(тека) {
  if (!fs.existsSync(тека)) return [];
  return fs.readdirSync(тека, {withFileTypes: true}).flatMap(вузол => {
    const файл = path.join(тека, вузол.name);
    if (вузол.isDirectory()) return новіЗаписи(файл);
    if (вузол.name !== 'повтор.json') return [];
    const паспорт = JSON.parse(fs.readFileSync(файл, 'utf8'));
    if (паспорт.версія !== 1 || !паспорт.жінка || !паспорт.змінні || !Number.isInteger(паспорт.сід))
      throw new Error('Неповний паспорт прогону: ' + файл);
    return [{назва: path.relative(корінь, тека), id: path.basename(тека), тека,
      обмін: path.join(тека, 'VIDPOVIDI/обмін'), ...паспорт}];
  });
}

function свіжіЗаписи(тека) {
  const останні = new Map();
  for (const сцена of новіЗаписи(тека).sort((а, б) => а.тека.localeCompare(б.тека))) останні.set(сцена.id, сцена);
  return [...останні.values()];
}

function перелік(архів = false) {
  const сцени = архів ? серіяДва() : свіжіЗаписи(path.join(__dirname, 'нічні'));
  if (!сцени.length) throw new Error('Порожній набір записів');
  for (const сцена of сцени) if (!fs.existsSync(сцена.записи || сцена.обмін))
    throw new Error('Нема записів сцени: ' + сцена.назва);
  return сцени;
}

function прочитатиJSON(файл) {
  return fs.existsSync(файл) ? JSON.parse(fs.readFileSync(файл, 'utf8')) : null;
}

function результатСтенда(тека, rc) {
  const помилка = прочитатиJSON(path.join(тека, 'знімки/помилка_відтворення.json'));
  const застарілий = rc === 3 && помилка?.код === 'REPLAY_STALE' && Number.isInteger(помилка.виклик)
    ? {виклик: помилка.виклик, причина: помилка.причина,
      ...(помилка.запит ? {вхід: ключЗапиту(помилка.запит)} : {})} : null;
  return знімок(fs.readFileSync(path.join(тека, 'лог.txt'), 'utf8'),
    прочитатиJSON(path.join(тека, 'знімки/доказ.json')), rc, застарілий);
}

function записатиБазу(тека, номери) {
  const результат = прочитатиJSON(path.join(тека, 'результат.json'));
  if (!результат || !/^[0-9a-f]{40}$/.test(результат.sha)) throw new Error('Нема SHA живого запису');
  const база = результатСтенда(тека, результат.rc);
  const червоні = база.звірки.filter(з => !з.зелена);
  if (червоні.length !== номери.length) throw new Error('Кожній червоній звірці потрібний окремий номер дошки');
  червоні.forEach((з, і) => { з.вада = Number(номери[і]); });
  звіритиБазу(база);
  база.sha = результат.sha;
  fs.writeFileSync(path.join(тека, 'база.json'), JSON.stringify(база, null, 1) + '\n', {flag: 'wx'});
  console.log('База: ' + база.звірки.length + ' звірок, відомих червоних ' + червоні.length);
}

function виконати() {
  if (process.argv[2] === '--записати-базу') {
    записатиБазу(path.resolve(process.argv[3]), process.argv.slice(4)); return;
  }
  const [збірка, кеш, вихід, частина = '0', частин = '1'] = process.argv.slice(2);
  const всі = перелік(process.env.REPLAY_ARCHIVE === '1');
  // Незмінені записи попереднього main теж перевіряються, коли PR приносить нову ніч.
  if (process.env.REPLAY_BASE_ROOT) {
    const попередні = свіжіЗаписи(path.join(process.env.REPLAY_BASE_ROOT, 'аудит/проби/нічні'));
    for (const сцена of попередні) {
      сцена.назва = path.relative(process.env.REPLAY_BASE_ROOT, сцена.тека);
      const і = всі.findIndex(с => с.назва === сцена.назва);
      if (і >= 0) всі[і] = сцена; else всі.push(сцена);
    }
  }
  if (збірка === '--перелік') { console.log(JSON.stringify(всі, null, 1)); return; }
  if (!збірка || !кеш || !вихід || !Number.isInteger(+частин) || +частин < 1 ||
      !Number.isInteger(+частина) || +частина < 0 || +частина >= +частин)
    throw new Error('Вжиток: node приймання_записів.js <збірка> <кеш Pyodide> <вихід> [частина=0] [частин=1]');
  const сцени = всі.filter((_, і) => і % +частин === +частина);
  fs.mkdirSync(вихід, {recursive: true});
  const підсумок = [];
  for (const сцена of сцени) {
    if (process.env.REPLAY_ARCHIVE !== '1') {
      const база = прочитатиJSON(path.join(сцена.тека, 'база.json'));
      if (!база) throw new Error('Нема бази живого запису: ' + сцена.назва);
      звіритиБазу(база);
    }
    const тека = path.join(вихід, сцена.назва.replace(/[/\\:]/g, '_'));
    // Старий доказ чи помилка не можуть стати результатом нового запуску.
    fs.mkdirSync(тека, {recursive: false});
    const середовище = {...process.env};
    // Режими батьківського живого прогону не змінюють записаний сценарій.
    const код = fs.readFileSync(path.join(__dirname, 'рв6_стенд.js'), 'utf8');
    for (const м of код.matchAll(/process\.env\.([\p{Lu}_][\p{Lu}\d_]*)/gu))
      if (!['CHROMIUM', 'NODE_PATH', 'HTTPS_PROXY'].includes(м[1])) delete середовище[м[1]];
    Object.assign(середовище, сцена.змінні, {ZNIMKY: path.join(тека, 'знімки')});
    if (сцена.жінка) {
      const файл = path.join(тека, 'жінка.json');
      fs.writeFileSync(файл, JSON.stringify(сцена.жінка));
      середовище.ZHINKA = path.resolve(файл);
    }
    середовище[сцена.обмін ? 'REPLAY_EXCHANGE' : 'REPLAY_RECORDINGS'] = сцена.обмін || сцена.записи;
    const початок = Date.now();
    const лог = fs.openSync(path.join(тека, 'лог.txt'), 'w');
    let результат;
    try {
      результат = spawnSync(process.execPath, [path.join(__dirname, 'рв6_стенд.js'),
        'http://127.0.0.1:8765', path.resolve(збірка), path.resolve(кеш), String(сцена.сід)],
      {cwd: корінь, env: середовище, stdio: ['ignore', лог, лог], timeout: 600000, windowsHide: true});
    } finally { fs.closeSync(лог); }
    const rc = результат.status === null ? 2 : результат.status;
    const після = результатСтенда(тека, rc);
    let звіт;
    if (process.env.REPLAY_ARCHIVE === '1') звіт = {стан: 'архів', регресії: []};
    else {
      let база = прочитатиJSON(path.join(сцена.тека, 'база.json'));
      if (!база) throw new Error('Нема бази живого запису: ' + сцена.назва);
      звіритиБазу(база);
      let вимірБази = null;
      if (process.env.REPLAY_BASE_BUILD) {
        const текаБази = path.join(тека, 'main');
        fs.mkdirSync(текаБази, {recursive: true});
        const логБази = fs.openSync(path.join(текаБази, 'лог.txt'), 'w');
        let до;
        try {
          до = spawnSync(process.execPath, [path.join(__dirname, 'рв6_стенд.js'),
            'http://127.0.0.1:8765', path.resolve(process.env.REPLAY_BASE_BUILD), path.resolve(кеш), String(сцена.сід)],
          {cwd: корінь, env: {...середовище, ZNIMKY: path.join(текаБази, 'знімки')},
            stdio: ['ignore', логБази, логБази], timeout: 600000, windowsHide: true});
        } finally { fs.closeSync(логБази); }
        вимірБази = результатСтенда(текаБази, до.status === null ? 2 : до.status);
        fs.writeFileSync(path.join(тека, 'вимір-бази.json'), JSON.stringify(вимірБази, null, 1) + '\n');
        if (вимірБази.застарілий) console.log('База main: ' + вимірБази.застарілий.причина);
        else база = затягнутиЗелені(база, вимірБази);
      }
      звіт = порівняти(база, після, вимірБази);
      fs.writeFileSync(path.join(тека, 'база-порівняння.json'), JSON.stringify(база, null, 1) + '\n');
    }
    підсумок.push({сцена: сцена.назва, rc, секунд: (Date.now() - початок) / 1000,
      помилка: результат.error ? результат.error.message : null, ...звіт});
    fs.writeFileSync(path.join(тека, 'звірки.json'), JSON.stringify(після, null, 1) + '\n');
    fs.writeFileSync(path.join(вихід, 'підсумок.json'), JSON.stringify(підсумок, null, 1) + '\n');
    const рядок = сцена.назва + ': ' + звіт.стан + (після.застарілий ? ' на виклику ' + після.застарілий.виклик : '') +
      '; rc стенда=' + rc + '; регресій=' + звіт.регресії.length;
    console.log(рядок);
    const потрібенЖивий = звіт.стан === 'запис застарів';
    if (потрібенЖивий) {
      console.log('ЖИВИЙ ПІСЛЯ: ' + сцена.id + ' — перезаписати змінений вхід моделі');
    }
    if (після.застарілий && process.env.GITHUB_ACTIONS)
      console.log('::warning::' + рядок);
    if (process.env.GITHUB_STEP_SUMMARY) fs.appendFileSync(process.env.GITHUB_STEP_SUMMARY,
      '- ' + рядок + (потрібенЖивий ? '\n  ЖИВИЙ ПІСЛЯ: ' + сцена.id + ' — перезаписати змінений вхід моделі' : '') + '\n');
  }
  if (підсумок.some(р => р.стан === 'регрес')) process.exitCode = 1;
  if (!сцени.length) {
    console.log('Частина без сцен: ' + частина + '/' + частин);
    fs.writeFileSync(path.join(вихід, 'підсумок.json'), '[]\n');
  }
}

if (require.main === module) {
  try { виконати(); } catch (помилка) { console.error(помилка); process.exitCode = 2; }
}
module.exports = {перелік, серіяДва, свіжіЗаписи, результатСтенда, записатиБазу};
