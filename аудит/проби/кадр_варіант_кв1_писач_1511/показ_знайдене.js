/* Ізолює незмінений розділ 1е батареї для відтворення знахідки поза нарядом. Без мережі й моделей. */
const fs = require('fs');
const path = require('path');
const Module = require('module');
const {execFileSync} = require('child_process');
const корінь = path.resolve(__dirname, '../../..');
const база = process.argv[2] || '7683d07e38eb757762afe3c2b3c4008aec77f3d1';
const шлях = 'джерела/тест_показу.js';
execFileSync('git', ['diff', '--exit-code', база, 'HEAD', '--',
  шлях, 'джерела/показ.html', 'джерела/показ', 'джерела/package-lock.json'], {cwd: корінь});
const текст = execFileSync('git', ['show', `${база}:${шлях}`], {cwd: корінь, encoding: 'utf8'});
const вступ = текст.indexOf('(async () => {');
const початок = текст.indexOf('  розділ("1е.');
const кінець = текст.indexOf('\n  розділ(', початок + 1);
if (вступ < 0 || початок < вступ || кінець < початок) throw new Error('Розділ 1е не знайдений');
console.log('Джерело батареї:', база, '; файли показу тотожні цій базі');
process.argv = [process.argv[0], path.join(корінь, шлях)];
const програма = текст.slice(0, вступ) + '(async () => { батареяПочалась = true;\n' +
  текст.slice(початок, кінець) + '\nдійшлоДоКінця = true;\n' +
  'console.log("Звірок:", виконано, "впало:", провалів); process.exit(провалів ? 1 : 0);\n' +
  '})().catch(e => { console.error(e); process.exit(2); });';
const модуль = new Module(path.join(корінь, шлях), module);
модуль.filename = path.join(корінь, шлях);
модуль.paths = Module._nodeModulePaths(path.join(корінь, 'джерела'));
модуль._compile(програма, модуль.filename);
