/* Записує і віддає обмін на межі моделі, без заглушки та повторного використання відповіді. */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const {spawnSync} = require('child_process');

function канон(значення) {
  if (Array.isArray(значення)) return значення.map(канон);
  if (значення && typeof значення === 'object') return Object.fromEntries(
    Object.keys(значення).sort().map(ключ => [ключ, канон(значення[ключ])]));
  return значення;
}

function ключЗапиту(тіло) {
  return crypto.createHash('sha256').update(JSON.stringify(канон(тіло))).digest('hex');
}

function імТипу(тип) {
  return тип.replace(/[^\p{L}\d]+/gu, '_').slice(0, 40);
}

class ЗаписанийОбмін {
  constructor(тека) {
    this.тека = тека;
    this.взято = new Set();
    this.помилки = [];
    this.записи = fs.readdirSync(тека).filter(ім => /^\d+\.json$/.test(ім)).sort().map(ім => {
      const запис = JSON.parse(fs.readFileSync(path.join(тека, ім), 'utf8'));
      if (запис.версія !== 1 || !запис.запит || !запис.відповідь ||
          !Number.isInteger(запис.відповідь.status) || typeof запис.відповідь.body !== 'string')
        throw new Error('Неповний запис обміну: ' + ім);
      return {ім, ключ: ключЗапиту(запис.запит), ...запис};
    });
    if (!this.записи.length) throw new Error('Нема записів обміну: ' + тека);
  }

  взяти(тіло) {
    const ключ = ключЗапиту(тіло);
    const запис = this.записи.find(з => з.ключ === ключ && !this.взято.has(з.ім));
    if (!запис) {
      const причина = 'Нема невзятої відповіді для запиту sha256=' + ключ;
      this.помилки.push(причина);
      throw new Error(причина);
    }
    this.взято.add(запис.ім);
    return запис.відповідь;
  }

  завершити() {
    const лишилось = this.записи.filter(з => !this.взято.has(з.ім)).map(з => з.ім);
    if (лишилось.length || this.помилки.length) throw new Error(
      'Неповне відтворення: взято ' + this.взято.size + '/' + this.записи.length +
      '; невзято: ' + лишилось.join(', ') + '; помилки: ' + this.помилки.join('; '));
    return {взято: this.взято.size, записів: this.записи.length};
  }
}

class ТекстовіВідповіді {
  constructor(тека) {
    this.взято = new Set();
    this.помилки = [];
    const доповнення = path.join(тека, '..', 'доповнення');
    this.доповнення = fs.existsSync(доповнення) ? new ЗаписанийОбмін(доповнення) : null;
    this.точніПовтори = new Map();
    this.повторів = 0;
    const підготовка = spawnSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
      [path.join(__dirname, 'сумісність_записів.py'), path.join(тека, '..', 'вердикти.txt')],
      {encoding: 'utf8', windowsHide: true, timeout: 60000, maxBuffer: 32 * 1024 * 1024,
        env: {...process.env, PYTHONIOENCODING: 'utf-8'}});
    if (підготовка.status !== 0) throw new Error('Не підготовлено старий протокол: ' + (підготовка.stderr || підготовка.error));
    const сумісні = JSON.parse(підготовка.stdout);
    const лог = fs.readFileSync(path.join(тека, '..', 'лог.txt'), 'utf8');
    const стеля = new Set([...лог.matchAll(/↔ модель #(\d+) [^\n]*УПЕРЛОСЬ У СТЕЛЮ ВИВОДУ/g)].map(м => Number(м[1])));
    this.записи = fs.readdirSync(тека).filter(ім => /^seed\d+_\d+_.*\.txt$/.test(ім)).sort().map(ім => {
      const текст = fs.readFileSync(path.join(тека, ім), 'utf8').replace(/\r\n/g, '\n');
      const м = /^── ПРОМПТ \(\d+ симв\.\) ──\n([\s\S]*)\n\n── ВІДПОВІДЬ \([^\n]*HTTP (\d+)[^\n]*\) ──\n([\s\S]*)\n$/.exec(текст);
      if (!м) throw new Error('Не прочитано старий запис: ' + ім);
      const номер = Number(/^seed\d+_(\d+)_/.exec(ім)[1]);
      const статус = Number(м[2]);
      const ід = crypto.createHash('sha256').update(м[3]).digest('hex');
      const варіанти = сумісні[ід] || [];
      if (варіанти.length > 1) throw new Error('Неоднозначна архівна розмітка: ' + ім);
      const сумісний = варіанти[0];
      return {ім, тип: /^seed\d+_\d+_(.*)\.txt$/.exec(ім)[1],
        промпт: сумісний ? сумісний.промпт : м[1], перенумеровано: !!сумісний,
        сирий_промпт: м[1], сирий_текст: м[3],
        відповідь: {status: статус, contentType: 'application/json',
        body: JSON.stringify(статус === 200 ? {content: [{type: 'text', text: сумісний ? сумісний.відповідь : м[3]}],
          usage: {input_tokens: 0, output_tokens: 0}, stop_reason: стеля.has(номер) ? 'max_tokens' : 'end_turn'}
          : {error: {message: м[3]}})}};
    });
    if (!this.записи.length) throw new Error('Нема текстових відповідей: ' + тека);
  }

  взяти(тіло, промпт, тип) {
    const ключТіла = ключЗапиту(тіло);
    if (this.доповнення && this.доповнення.записи.some(з => з.ключ === ключТіла)) {
      console.log('   точний живий запис доповнення · sha256=' + ключТіла);
      return this.доповнення.взяти(тіло);
    }
    const ключ = ключЗапиту(промпт);
    if (this.точніПовтори.has(ключ)) {
      this.повторів++;
      console.log('   точний повтор того самого промпту · sha256=' + ключ);
      return this.точніПовтори.get(ключ);
    }
    const кандидати = this.записи.filter(з => з.тип === імТипу(тип) && !this.взято.has(з.ім));
    const зіставлення = spawnSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
      [path.join(__dirname, 'схожість_промптів.py')], {encoding: 'utf8', windowsHide: true, timeout: 30000,
        env: {...process.env, PYTHONIOENCODING: 'utf-8'},
        input: JSON.stringify({промпт, кандидати: кандидати.map(з => з.промпт)})});
    if (зіставлення.status !== 0) throw new Error('Не зіставлено промпти: ' + (зіставлення.stderr || зіставлення.error));
    const оцінки = JSON.parse(зіставлення.stdout);
    const запис = кандидати.map((з, і) => ({...з, схожість: оцінки[і]}))
      .sort((а, б) => б.схожість - а.схожість)[0];
    if (!запис) {
      const причина = 'Нема невзятої текстової відповіді; тип=' + тип + '; sha256=' + ключЗапиту(промпт);
      this.помилки.push(причина);
      throw new Error(причина);
    }
    this.взято.add(запис.ім);
    const перейменування = spawnSync(process.env.PYTHON || (process.platform === 'win32' ? 'python' : 'python3'),
      [path.join(__dirname, 'сумісність_записів.py'), '--виклик'], {encoding: 'utf8', windowsHide: true, timeout: 60000,
        env: {...process.env, PYTHONIOENCODING: 'utf-8'}, maxBuffer: 32 * 1024 * 1024,
        input: JSON.stringify({було: запис.сирий_промпт, тепер: промпт, відповідь: запис.сирий_текст})});
    if (перейменування.status !== 0) throw new Error('Не зіставлено ключі: ' + (перейменування.stderr || перейменування.error));
    const відповідь = {...запис.відповідь};
    const тілоВідповіді = JSON.parse(відповідь.body);
    if (відповідь.status === 200) {
      тілоВідповіді.content[0].text = JSON.parse(перейменування.stdout);
      відповідь.body = JSON.stringify(тілоВідповіді);
    }
    this.точніПовтори.set(ключ, відповідь);
    console.log('   запис ' + запис.ім + ' · схожість промпту ' + запис.схожість.toFixed(4)
      + (запис.перенумеровано ? ' · нумерація з продукту, тексти незмінні' : ''));
    return відповідь;
  }

  завершити() {
    if (this.помилки.length) throw new Error(this.помилки.join('; '));
    if (this.доповнення) this.доповнення.завершити();
    return {взято: this.взято.size, записів: this.записи.length,
      точних_повторів: this.повторів,
      невикористано: this.записи.filter(з => !this.взято.has(з.ім)).map(з => з.ім)};
  }
}

function записатиОбмін(тека, номер, запит, відповідь) {
  fs.mkdirSync(тека, {recursive: true});
  const файл = path.join(тека, String(номер).padStart(5, '0') + '.json');
  fs.writeFileSync(файл, JSON.stringify({версія: 1, запит, відповідь}, null, 1) + '\n', {flag: 'wx'});
}

module.exports = {ЗаписанийОбмін, ТекстовіВідповіді, записатиОбмін, ключЗапиту, імТипу};
