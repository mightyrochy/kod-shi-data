/* Усі зареєстровані живі сцени проходять той самий браузерний стенд із відповідями з диска. */
const fs = require('fs'), path = require('path'), os = require('os');
const {spawnSync} = require('child_process');
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
    return [{назва: path.relative(корінь, тека), обмін: path.join(тека, 'VIDPOVIDI/обмін'), ...паспорт}];
  });
}

function перелік() {
  const сцени = [...серіяДва(), ...новіЗаписи(path.join(__dirname, 'нічні'))];
  if (!сцени.length) throw new Error('Порожній набір записів');
  for (const сцена of сцени) if (!fs.existsSync(сцена.записи || сцена.обмін))
    throw new Error('Нема записів сцени: ' + сцена.назва);
  return сцени;
}

function виконати() {
  const [збірка, кеш, вихід, частина = '0', частин = '1'] = process.argv.slice(2);
  const всі = перелік();
  if (збірка === '--перелік') { console.log(JSON.stringify(всі, null, 1)); return; }
  if (!збірка || !кеш || !вихід || !Number.isInteger(+частин) || +частин < 1 ||
      !Number.isInteger(+частина) || +частина < 0 || +частина >= +частин)
    throw new Error('Вжиток: node приймання_записів.js <збірка> <кеш Pyodide> <вихід> [частина=0] [частин=1]');
  const сцени = всі.filter((_, і) => і % +частин === +частина);
  if (!сцени.length) throw new Error('Порожня частина набору');
  fs.mkdirSync(вихід, {recursive: true});
  const підсумок = [];
  for (const сцена of сцени) {
    const тека = path.join(вихід, сцена.назва.replace(/[/\\:]/g, '_'));
    fs.mkdirSync(тека, {recursive: true});
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
    підсумок.push({сцена: сцена.назва, rc, секунд: (Date.now() - початок) / 1000,
      помилка: результат.error ? результат.error.message : null});
    fs.writeFileSync(path.join(вихід, 'підсумок.json'), JSON.stringify(підсумок, null, 1) + '\n');
    console.log((rc ? '✗ ' : '✔ ') + сцена.назва + ': rc=' + rc);
  }
  if (підсумок.some(р => р.rc)) process.exitCode = 1;
}

if (require.main === module) {
  try { виконати(); } catch (помилка) { console.error(помилка); process.exitCode = 2; }
}
module.exports = {перелік, серіяДва};
