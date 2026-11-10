/* Лічба доповнення доходить до етапу звіту без втрат. argv[2] — коміт ДО. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const корінь = path.resolve(__dirname, '../..');
const файл = 'джерела/показ/звіти.js';
const код = process.argv[2]
  ? require('child_process').execFileSync('git', ['show', process.argv[2] + ':' + файл], {cwd: корінь, encoding:'utf8'})
  : fs.readFileSync(path.join(корінь, файл), 'utf8');
const початок = код.indexOf('function етапВиклику(');
const кінець = код.indexOf('/* Останнє слово коду', початок);
if (початок < 0 || кінець < 0) throw Error('Нема функції етапу звіту');
const етап = vm.runInNewContext(код.slice(початок, кінець) + '; етапВиклику', {
  КРОК_П:{ремонт_повноти:'completeness_repair'}, _числаСтадії:()=>({}), _запитЕтапу:()=>null
});
const лічба = {ходів:3, прийнято:2, не_з_вітрини:['#999·99']};
const звіт = JSON.parse(JSON.stringify(етап({спроба_повноти:1}, {доповнення:лічба}, {}, null)));
const рівність = JSON.stringify(звіт.доповнення) === JSON.stringify(лічба);
console.log('Лічба доповнення в етапі звіту дослівно: ' + рівність);
if (!process.argv[2] && !рівність) process.exitCode = 1;
