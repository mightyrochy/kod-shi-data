/* Вставляє крок даних перед першим збиранням лише у процесі цієї сцени.
   Файл стенда й артефакт збірки залишаються незміненими. */
const Module = require('module'), fs = require('fs'), path = require('path');
if (process.env.SCENA === 'ж7_збій_правил_без_підборів') {
  const попередня = Module._extensions['.js'];
  Module._extensions['.js'] = function(модуль, файл) {
    if (path.basename(файл) === 'записаний_обмін.js') {
      попередня(модуль, файл);
      const записати = модуль.exports.записатиОбмін;
      модуль.exports.записатиОбмін = function(тека, ...решта) {
        // Очікувані відмови — окремі первинні докази. База містить звичайний
        // шлях до повного збирання після відновлення, без зайвих обмінів.
        const місце = global.__ж7_внесення
          ? path.resolve(тека, '../..', 'пошкоджені_обміни', global.__ж7_внесення) : тека;
        return записати(місце, ...решта);
      };
      return;
    }
    if (path.basename(файл) !== 'рв6_стенд.js') return попередня(модуль, файл);
    const код = fs.readFileSync(файл,'utf8');
    const мітка = "  await стор.click('#зб-зібрати', { noWaitAfter: true });";
    if (!код.includes(мітка)) throw Error('Нема точки внесення даних перед збиранням');
    const крок = '  await require(' + JSON.stringify(path.join(__dirname,'внести_збій.cjs')) + ')(стор);\n';
    модуль._compile(код.replace(мітка,крок+мітка),файл);
  };
}
