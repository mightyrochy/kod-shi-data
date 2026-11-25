/* Підставні прямокутники й події видимої області. Запуск: node тест_вікна_вердикту.js [шлях до вердикт.js]. */
const assert = require('node:assert/strict');
const {EventEmitter} = require('node:events');
const {readFileSync} = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const подіїВікна = new EventEmitter();
const подіїОбласті = new EventEmitter();
const кадри = [];
const прокрутки = [];
let підгонок = 0;
const область = {offsetTop: 90, height: 400, addEventListener: подіїОбласті.on.bind(подіїОбласті)};
const форма = {
  closest: () => null,
  style: {setProperty(){ підгонок++; }},
  lastElementChild: {getBoundingClientRect: () => ({bottom: низКнопки})}
};
let низКнопки = 490;
const поле = {closest: селектор => селектор === '.форма-вердикту' ? форма : поле};
const документ = {activeElement: поле, querySelectorAll: () => [форма]};
const вікно = {
  visualViewport: область,
  addEventListener: подіїВікна.on.bind(подіїВікна),
  getComputedStyle: () => ({display: 'grid', getPropertyValue: () => '0px'}),
  requestAnimationFrame(кадр){ кадри.push(кадр); return кадри.length; },
  scrollBy({top}){
    прокрутки.push(top);
    низКнопки -= top;
    подіїОбласті.emit('scroll');
  }
};
const джерело = process.argv[2] || path.join(__dirname, 'показ', 'екран', 'вердикт.js');
vm.runInNewContext(readFileSync(джерело, 'utf8'), {
  window: вікно, document: документ, Екран: {змінити(){}, малювач(){}, дія(){}}, НЕМА_ЩО_ЗАПИСАТИ_П: ''
});

подіїОбласті.emit('resize');
кадри.shift()();
assert.equal(підгонок, 1);
assert.deepEqual(прокрутки, []);

область.offsetTop = 0;
подіїОбласті.emit('scroll');
подіїОбласті.emit('scroll');
assert.equal(кадри.length, 1, 'зміна offsetTop без resize планує один кадр');
кадри.shift()();
assert.equal(підгонок, 2);
assert.deepEqual(прокрутки, [90]);
assert.equal(кадри.length, 0, 'подія під час програмної прокрутки не продовжує цикл');
подіїОбласті.emit('scroll');
assert.equal(кадри.length, 0, 'пізня подія з тим самим offsetTop теж не створює нового кадру');

документ.activeElement = null;
область.offsetTop = 45;
подіїОбласті.emit('scroll');
assert.equal(кадри.length, 0, 'без активного поля прокрутка не рухає вердикт');
assert.equal(подіїОбласті.listenerCount('scroll'), 1);
assert.equal(подіїОбласті.listenerCount('resize'), 1);
console.log('10 контролів пройшли: scroll без resize, спільний кадр, відсутність циклу, межа фокусу.');
