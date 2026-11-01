/* Проба справжнього писача знімка: початкові позначки переживають збереження картки. */
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert');
const код = fs.readFileSync(path.resolve('джерела/показ/звіти.js'), 'utf8');
const поч = код.indexOf('function знімокПрогонуП(');
const кін = код.indexOf('function безКольорівБезЗгодиП(', поч);
const первісні = {не_ця: {'1':['неприйнятна-раніше']}, вже_були:['попередній-збір']};
const знімок = vm.runInNewContext(код.slice(поч, кін) + '\nзнімокПрогонуП(вхід)',
  {вхід:{вхід_рук:первісні}, ДРАП:{білий:null, метал:null, нейтралі:[], барви:[]}});
const збережений = JSON.parse(JSON.stringify(знімок));
assert.deepStrictEqual(збережений.не_ця_прогону, первісні.не_ця);
assert.deepStrictEqual(збережений.вже_були_прогону, первісні.вже_були);
console.log('✔ знімок зберігає початкові не_ця та вже_були, зокрема непорожні');
