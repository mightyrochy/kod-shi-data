/* Вставляє крок даних перед першим збиранням лише у процесі цієї сцени.
   Файл стенда й артефакт збірки залишаються незміненими. */
const Module = require('module'), fs = require('fs'), path = require('path');
if (process.env.SCENA === 'ж7_збій_правил_без_підборів') {
  const попередня = Module._extensions['.js'];
  Module._extensions['.js'] = function(модуль, файл) {
    if (path.basename(файл) !== 'рв6_стенд.js') return попередня(модуль, файл);
    const код = fs.readFileSync(файл,'utf8');
    const мітка = "  await стор.click('#зб-зібрати', { noWaitAfter: true });";
    if (!код.includes(мітка)) throw Error('Нема точки внесення даних перед збиранням');
    const крок = '  await require(' + JSON.stringify(path.join(__dirname,'внести_збій.cjs')) + ')(стор);\n';
    модуль._compile(код.replace(мітка,крок+мітка),файл);
  };
}
