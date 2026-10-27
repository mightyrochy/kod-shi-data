/* Записує і віддає обмін на межі моделі, без заглушки та повторного використання відповіді. */
const fs = require('fs'), path = require('path'), crypto = require('crypto');

function канон(значення) {
  if (Array.isArray(значення)) return значення.map(канон);
  if (значення && typeof значення === 'object') return Object.fromEntries(
    Object.keys(значення).sort().map(ключ => [ключ, канон(значення[ключ])]));
  return значення;
}

function ключЗапиту(тіло) {
  return crypto.createHash('sha256').update(JSON.stringify(канон(тіло))).digest('hex');
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

function записатиОбмін(тека, номер, запит, відповідь) {
  fs.mkdirSync(тека, {recursive: true});
  const файл = path.join(тека, String(номер).padStart(5, '0') + '.json');
  fs.writeFileSync(файл, JSON.stringify({версія: 1, запит, відповідь}, null, 1) + '\n', {flag: 'wx'});
}

module.exports = {ЗаписанийОбмін, записатиОбмін, ключЗапиту};
