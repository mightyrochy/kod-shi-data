/* Зіставляє всі сцени двох артефактів replay без повторного запуску продукту. */
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const assert = require('node:assert/strict');
const {ключЗапиту} = require('../../проби/записаний_обмін.js');

function розбіжності(а, б, шлях = '') {
  if (typeof а === 'string' && typeof б === 'string') {
    let ліва, права;
    try { ліва = JSON.parse(а); права = JSON.parse(б); } catch (_) { return а === б ? [] : [шлях]; }
    return розбіжності(ліва, права, шлях + ':json');
  }
  if (а && б && typeof а === 'object' && typeof б === 'object')
    return [...new Set([...Object.keys(а), ...Object.keys(б)])].flatMap(
      к => розбіжності(а[к], б[к], шлях + '.' + к));
  return а === б ? [] : [шлях];
}

function виміряти(тека) {
  const читати = файл => JSON.parse(fs.readFileSync(файл, 'utf8'));
  const сцени = [], докази = [];
  for (const артефакт of fs.readdirSync(тека).filter(ім => ім.startsWith('replay-')).sort()) {
    const корінь = path.join(тека, артефакт);
    for (const рядок of читати(path.join(корінь, 'підсумок.json'))) {
      const місце = path.join(корінь, рядок.сцена.replace(/[/\\:]/g, '_'));
      const голова = читати(path.join(місце, 'звірки.json'));
      const база = читати(path.join(місце, 'вимір-бази.json'));
      const запитГолови = читати(path.join(місце, 'знімки/помилка_відтворення.json'));
      const запитБази = читати(path.join(місце, 'main/знімки/помилка_відтворення.json'));
      assert.equal(голова.застарілий.вхід, ключЗапиту(запитГолови.запит));
      assert.equal(база.застарілий.вхід, ключЗапиту(запитБази.запит));
      const однаковийВиклик = голова.застарілий.виклик === база.застарілий.виклик;
      const однаковийЗапит = голова.застарілий.вхід === база.застарілий.вхід;
      сцени.push({сцена: рядок.сцена, артефакт, стан: рядок.стан, регресій: рядок.регресії.length,
        голова: голова.застарілий, база: база.застарілий, однаковийВиклик, однаковийЗапит,
        розбіжності: розбіжності(запитБази.запит, запитГолови.запит)});
      докази.push({сцена: рядок.сцена, голова, база, запитГолови, запитБази});
    }
  }
  const результат = {сцен: сцени.length,
    однакові: сцени.filter(с => с.однаковийВиклик && с.однаковийЗапит).length,
    інший_виклик: сцени.filter(с => !с.однаковийВиклик).length,
    інший_запит: сцени.filter(с => !с.однаковийЗапит).length, сцени};
  fs.writeFileSync(path.join(__dirname, 'артефакти.json'), JSON.stringify(результат, null, 1) + '\n');
  fs.writeFileSync(path.join(__dirname, 'артефакти-докази.json.gz'), zlib.gzipSync(JSON.stringify(докази)));
  console.log(JSON.stringify(результат, null, 1));
}

if (require.main === module) виміряти(path.resolve(process.argv[2]));
