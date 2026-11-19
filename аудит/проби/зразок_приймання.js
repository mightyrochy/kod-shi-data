/* Ізолює зразки приймання від набору нічних записів, який постійно оновлюється. */
const fs = require('fs'), path = require('path');

function створитиЗразок(тека, сцени, джерело = __dirname) {
  const проби = path.join(тека, 'зразок/аудит/проби');
  fs.mkdirSync(проби, {recursive: true});
  for (const ім of ['приймання_записів.js', 'храповик_записів.js', 'записаний_обмін.js', 'живий_після_CI.js'])
    fs.copyFileSync(path.join(джерело, ім), path.join(проби, ім));
  fs.writeFileSync(path.join(проби, 'рв6_стенд.js'), '/* Дочірній браузер замінено виходами зразка. */\n');
  for (const {id, база} of сцени) {
    const місце = path.join(проби, 'нічні/20261112', id);
    fs.mkdirSync(path.join(місце, 'VIDPOVIDI/обмін'), {recursive: true});
    fs.writeFileSync(path.join(місце, 'повтор.json'), JSON.stringify({версія: 1, жінка: {імʼя: id}, змінні: {}, сід: 3}));
    fs.writeFileSync(path.join(місце, 'база.json'), JSON.stringify(база));
  }
  return проби;
}

module.exports = {створитиЗразок};
