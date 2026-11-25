/* Т34: та сама наскрізна нитка с5, що й `тест_ш_протокол.Ш_Протокол._нитка`, — у Pyodide (рушій сторінки).
   Запуск: node pyodide_нитка.js <тека Pyodide> <тека джерела>. Пише пакет `ядро/` і записаний прохід с5 у файлову
   систему Pyodide за тими самими відносними шляхами, що в репозиторії, і друкує JSON нитки одним останнім рядком. */
const fs = require('fs'), path = require('path');
const [ТЕКА_PYODIDE, ДЖЕРЕЛА] = process.argv.slice(2).map(п => path.resolve(п));
const КОРІНЬ = path.dirname(ДЖЕРЕЛА);
const ЗАПИС = 'аудит/проби/Живий-через-міст/стенд/службове/с5_весілля_сестри/обміни.jsonl';

function покласти(пд, відносний, дані){
  const куди = '/' + відносний;
  пд.FS.mkdirTree(path.posix.dirname(куди));
  пд.FS.writeFile(куди, дані);
}

function тека(пд, відносна){
  for (const е of fs.readdirSync(path.join(КОРІНЬ, відносна), {withFileTypes: true})){
    const в = path.posix.join(відносна, е.name);
    if (е.isDirectory() && е.name !== '__pycache__') тека(пд, в);
    else if (/\.(py|json)$/.test(е.name)) покласти(пд, в, fs.readFileSync(path.join(КОРІНЬ, в)));
  }
}

(async () => {
  const { loadPyodide } = require(path.join(ТЕКА_PYODIDE, 'pyodide.js'));
  const пд = await loadPyodide({indexURL: ТЕКА_PYODIDE + '/'});
  тека(пд, 'джерела/ядро');
  покласти(пд, ЗАПИС, fs.readFileSync(path.join(КОРІНЬ, ЗАПИС)));
  const вихід = пд.runPython(`
import json, sys
sys.path.insert(0, "/джерела")
from ядро.тести import обвязка as о
json.dumps(о.нитка_транспорту(), ensure_ascii=False)
`);
  console.log(вихід);
})().catch(е => { console.error(е); process.exit(1); });
