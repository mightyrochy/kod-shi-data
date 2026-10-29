/* Завершений автоживий на голові main сам стає новою датованою базою записів (наряд автоживий-нова-база).

   Запуск — останній крок шаблону `аудит/наряди/автоживий.md`, до коміту звіту:
     node аудит/проби/нова_база.js аудит/проби/<наряд> [--main origin/main]
   Кожна тека сцени з `повтор.json` і `результат.json` (`записати_сцену.py`) переноситься в
   `аудит/проби/нічні/<РРРРММДД>/<сцена>` (друга база дня — `<РРРРММДД>T<ГГХХ>`) з `база.json`, коли:
   - SHA живого коду — предок `--main`, а живий шлях (`джерела/`, стенд і його місцеві залежності) після нього не
     змінювався: інакше запис застарілий уже при народженні;
   - живий вимір завершено (rc 0 чи 1, доказ доведено);
   - кожна червона звірка має номер дошки з попередньої бази тієї самої сцени: нова червона — «ЗНАХІДКА», не база.
   Підсумок — `НОВА_БАЗА.md` у теці наряду. Код: 0 — є нова база й нема знахідок; 4 — є знахідка; 3 — бази нема. */
const fs = require('fs'), path = require('path');
const {spawnSync} = require('child_process');
const {записатиБазу, вікДіб} = require('./приймання_записів.js');

const НІЧНІ = 'аудит/проби/нічні';

function git(корінь, аргументи) {
  const р = spawnSync('git', аргументи, {cwd: корінь, encoding: 'utf8'});
  if (р.error) throw р.error;
  return р;
}

/* Місцеві модулі й файли стенда транзитивно: їхня зміна міняє запис так само, як зміна продукту. Звіт збірки
   `джерела/аудит/ДОСЯЖНІСТЬ.md` коміт «збірка:» CI перегенеровує щоразу — він не вхід стенда (той самий виняток —
   у `zbirka.yml`), інакше жоден штамп `build.txt` не став би базою (11220). */
const НЕ_ВХІД = ':(exclude)джерела/аудит/ДОСЯЖНІСТЬ.md';

function живийШлях(корінь) {
  const проби = path.join(корінь, 'аудит/проби');
  const бачено = new Set(), черга = ['рв6_стенд.js'];
  while (черга.length) {
    const файл = черга.pop();
    if (бачено.has(файл) || !fs.existsSync(path.join(проби, файл))) continue;
    бачено.add(файл);
    const код = fs.readFileSync(path.join(проби, файл), 'utf8');
    if (!файл.endsWith('.js')) continue;
    for (const м of код.matchAll(/(?:require\(|path\.join\(__dirname, *)'(?:\.\/)?([^'/]+\.(?:js|py|txt|json))'/g)) черга.push(м[1]);
  }
  return ['джерела', 'аудит/проби/жінки', ...[...бачено].sort().map(ф => 'аудит/проби/' + ф), НЕ_ВХІД];
}

function датаЗапису(результат) {
  const час = Date.parse(результат.початок || результат.початок_utc || результат.кінець || результат.кінець_utc || '');
  if (!Number.isFinite(час)) throw new Error('Нема часу початку живого запису');
  return new Date(час);
}

function назваДати(дата) { return дата.toISOString().slice(0, 10).replace(/-/g, ''); }

function перенести(корінь, тека, сцена, main, шлях, попередні) {
  const результат = JSON.parse(fs.readFileSync(path.join(тека, 'результат.json'), 'utf8'));
  const sha = String(результат.sha || '');
  if (!/^[0-9a-f]{40}$/.test(sha)) return {не: 'нема SHA живого коду в результат.json'};
  if (![0, 1].includes(результат.rc)) return {не: 'стенд не завершився (rc=' + результат.rc + ')'};
  for (const файл of ['повтор.json', 'лог.txt', 'знімки/доказ.json', 'VIDPOVIDI/обмін'])
    if (!fs.existsSync(path.join(тека, файл))) return {не: 'нема ' + файл};
  if (git(корінь, ['merge-base', '--is-ancestor', sha, main]).status !== 0)
    return {не: sha + ' не предок ' + main};
  const зміни = git(корінь, ['-c', 'core.quotepath=false', 'diff', '--name-only', sha, main, '--', ...шлях]);
  if (зміни.status !== 0) throw new Error('git diff: ' + зміни.stderr);
  if (зміни.stdout.trim())
    return {не: 'живий шлях змінено після ' + sha + ': ' + зміни.stdout.trim().split('\n').slice(0, 3).join(', ')};
  const попередня = попередні.бази.get(сцена) || null;
  const номери = new Map((попередня?.база.звірки || []).filter(з => !з.зелена).map(з => [з.ід, з.вада]));
  const дата = датаЗапису(результат);
  const є = відносна => попередні.теки.has(відносна) || fs.existsSync(path.join(корінь, відносна));
  let відносна = НІЧНІ + '/' + назваДати(дата) + '/' + сцена;
  if (є(відносна)) відносна = НІЧНІ + '/' + назваДати(дата) + 'T' + дата.toISOString().slice(11, 16).replace(':', '') + '/' + сцена;
  if (є(відносна)) return {не: 'тека бази вже є: ' + відносна};
  if (попередня && попередня.шлях.localeCompare(відносна) >= 0) return {не: 'новіша база вже є: ' + попередня.шлях};
  const куди = path.join(корінь, відносна);
  if (fs.existsSync(path.join(тека, 'база.json'))) return {не: 'база.json уже є в записі наряду'};
  // Спершу перенос, потім база: збій переносу нічого не лишає, нова червона повертає запис назад доказом (11222).
  fs.mkdirSync(path.dirname(куди), {recursive: true});
  try { fs.renameSync(тека, куди); }
  catch (помилка) {
    if (!fs.readdirSync(path.dirname(куди)).length) fs.rmdirSync(path.dirname(куди));
    return {не: 'перенос не вдався (' + помилка.code + '), запис лишився без бази: ' + помилка.message};
  }
  try { записатиБазу(куди, номери); }
  catch (помилка) {
    fs.rmSync(path.join(куди, 'база.json'), {force: true});
    fs.renameSync(куди, тека);
    if (!fs.readdirSync(path.dirname(куди)).length) fs.rmdirSync(path.dirname(куди));
    return /номер\S* дошки/.test(помилка.message)
      ? {знахідка: 'червона звірка без номера в попередній базі ' + (попередня ? попередня.шлях : '(нема)')}
      : {не: помилка.message};
  }
  const замінює = попередня ? попередня.шлях : null;
  const вік = попередня ? вікДіб(попередня.шлях, дата.getTime()) : null;
  fs.writeFileSync(path.join(куди, 'походження.json'), JSON.stringify({
    шлях_запису: path.relative(корінь, тека), код_живого: sha, main: git(корінь, ['rev-parse', main]).stdout.trim(),
    живий_шлях: шлях, замінює, вік_заміненої_діб: вік, відомі_червоні: [...номери.values()]}, null, 1) + '\n');
  return {база: відносна, замінює, вік};
}

/* Попередні бази — з дерева main, а не з диска: копія наряду обгортки не викладає великих тек-архівів (sparse). */
function базиMain(корінь, main) {
  const р = git(корінь, ['-c', 'core.quotepath=false', 'ls-tree', '-r', '--name-only', main, '--', НІЧНІ]);
  if (р.status !== 0) throw new Error('git ls-tree: ' + р.stderr);
  const файли = р.stdout.split('\n').filter(Boolean);
  const бази = new Map();
  for (const файл of файли.filter(ф => ф.endsWith('/база.json')).sort((а, б) => а.localeCompare(б))) {
    const шлях = path.posix.dirname(файл);
    const показ = git(корінь, ['show', main + ':' + файл]);
    if (показ.status !== 0) throw new Error('git show: ' + показ.stderr);
    бази.set(path.posix.basename(шлях), {шлях, база: JSON.parse(показ.stdout)});
  }
  return {бази, теки: new Set(файли.map(ф => ф.split('/').slice(0, 5).join('/')))};
}

function виконати(аргументи, корінь = path.resolve(__dirname, '../..')) {
  const [відносна, ...решта] = аргументи;
  const тека = відносна && path.resolve(відносна);
  const і = решта.indexOf('--main');
  const main = і >= 0 ? решта[і + 1] : 'origin/main';
  if (!тека || !fs.existsSync(тека)) throw new Error('Вжиток: node нова_база.js <тека наряду> [--main origin/main]');
  if (git(корінь, ['rev-parse', '--verify', '-q', main + '^{commit}']).status !== 0) throw new Error('Нема ' + main);
  const шлях = живийШлях(корінь);
  const попередні = базиMain(корінь, main);
  const рядки = [];
  let баз = 0, знахідок = 0;
  for (const вузол of fs.readdirSync(тека, {withFileTypes: true}).sort((а, б) => а.name.localeCompare(б.name))) {
    const сцена = path.join(тека, вузол.name);
    if (!вузол.isDirectory() || !fs.existsSync(path.join(сцена, 'повтор.json'))) continue;
    if (!fs.existsSync(path.join(сцена, 'результат.json'))) { рядки.push(`- ${вузол.name}: не база — нема результат.json`); continue; }
    const р = перенести(корінь, сцена, вузол.name, main, шлях, попередні);
    if (р.база) {
      баз++;
      рядки.push(`НОВА БАЗА: ${р.база} замінює ${р.замінює || '(нема попередньої)'}` +
        (р.вік === null ? '' : ` (вік заміненої ${р.вік} діб)`) + ' — завершений автоживий на голові main');
    } else if (р.знахідка) {
      знахідок++;
      рядки.push(`ЗНАХІДКА: ${вузол.name} — ${р.знахідка}; запис лишається в ${path.relative(корінь, сцена)}`);
    } else рядки.push(`- ${вузол.name}: не база — ${р.не}`);
  }
  if (!рядки.length) рядки.push('- сцен із повтор.json і результат.json нема: бази нема');
  fs.writeFileSync(path.join(тека, 'НОВА_БАЗА.md'), '# Нова база записів\n\n' + рядки.join('\n') + '\n');
  console.log(рядки.join('\n'));
  return знахідок ? 4 : баз ? 0 : 3;
}

if (require.main === module) {
  try { process.exitCode = виконати(process.argv.slice(2)); }
  catch (помилка) { console.error(помилка.message); process.exitCode = 2; }
}
module.exports = {виконати, живийШлях};
