/* Виконує справжній ЗЛІПОК_DOM у Node на збереженому дереві, без браузера й мережі.
 * Acorn додає позначки до операцій у пам'яті; вихідний JS жнив не змінюється.
 * DOM тут структурний: textContent і innerText мають текст збереженого HTML.
 * Властивості верстки, мережеві API й невідомі селектори завершують прогін помилкою.
 */
'use strict';
const fs = require('node:fs');
const vm = require('node:vm');
const acorn = require('./річ_запис_дані/acorn.cjs');

class Рядок {
  constructor(значення, джерела) { this.значення = значення; this.джерела = [...new Set(джерела)]; }
  toString() { return this.значення; }
  valueOf() { return this.значення; }
}
const чисте = з => з instanceof Рядок ? з.значення : з;
const мітки = з => з instanceof Рядок ? з.джерела : [];
const підпис = (з, д) => typeof з === 'string' && з && д.length ? new Рядок(з, д) :
  Array.isArray(з) ? з.map(ч => підпис(ч, д)) : з;

function перетворити(код) {
  const дерево = acorn.parse('(' + код + ')', {ecmaVersion: 2022, locations: true});
  const текст = '(' + код + ')';
  function пройти(в) {
    if (!в || typeof в.type !== 'string') return '';
    if (в.type === 'MemberExpression') {
      return `п.поле(${пройти(в.object)},${в.computed ? пройти(в.property) : JSON.stringify(в.property.name)},${в.loc.start.line})`;
    }
    if (в.type === 'CallExpression') {
      const арг = '[' + в.arguments.map(ч => пройти(ч)).join(',') + ']';
      if (в.callee.type === 'MemberExpression') {
        const ч = в.callee;
        return `п.виклик(${пройти(ч.object)},${ч.computed ? пройти(ч.property) : JSON.stringify(ч.property.name)},${арг},${в.loc.start.line})`;
      }
      return `п.функція(${пройти(в.callee)},${арг})`;
    }
    if (в.type === 'NewExpression') return `п.новий(${пройти(в.callee)},[${в.arguments.map(пройти).join(',')}])`;
    if (в.type === 'BinaryExpression') return `п.бінарна(${JSON.stringify(в.operator)},${пройти(в.left)},${пройти(в.right)})`;
    if (в.type === 'LogicalExpression') return `п.логічна(${JSON.stringify(в.operator)},()=>(${пройти(в.left)}),()=>(${пройти(в.right)}))`;
    if (в.type === 'UnaryExpression' && в.operator === '!') return `(!п.чисте(${пройти(в.argument)}))`;
    if (в.type === 'ConditionalExpression') return `(п.чисте(${пройти(в.test)})?(${пройти(в.consequent)}):(${пройти(в.alternate)}))`;
    // Частини, які є цілями присвоєння чи ++, лишаються звичайними lvalue.
    const діти = [];
    for (const [ключ, з] of Object.entries(в)) {
      if (['loc', 'start', 'end'].includes(ключ)) continue;
      for (const ч of Array.isArray(з) ? з : [з]) if (ч && typeof ч.type === 'string') {
        if ((в.type === 'AssignmentExpression' && ключ === 'left') ||
            (в.type === 'UpdateExpression' && ключ === 'argument') ||
            (в.type === 'Property' && ключ === 'key' && !в.computed)) continue;
        діти.push(ч);
      }
    }
    діти.sort((а, б) => а.start - б.start);
    let вих = '', початок = в.start;
    for (const ч of діти) {
      if (ч.start < початок) continue; // shorthand Property має один і той самий Identifier двічі
      вих += текст.slice(початок, ч.start);
      const з = пройти(ч);
      вих += ['IfStatement', 'WhileStatement', 'ForStatement'].includes(в.type) && ч === в.test ? `п.чисте(${з})` : з;
      початок = ч.end;
    }
    return вих + текст.slice(початок, в.end);
  }
  const селектори = new Set();
  function рядки(в) {
    if (!в || typeof в.type !== 'string') return;
    if (в.type === 'CallExpression' && в.callee.type === 'MemberExpression' &&
        ['querySelector', 'querySelectorAll', 'closest'].includes(в.callee.property.name) &&
        в.arguments[0]?.type === 'Literal' && typeof в.arguments[0].value === 'string') селектори.add(в.arguments[0].value);
    for (const з of Object.values(в)) for (const ч of Array.isArray(з) ? з : [з]) if (ч && ч.type) рядки(ч);
  }
  рядки(дерево);
  return {код: пройти(дерево), селектори: [...селектори]};
}

function виконати(вхід) {
  const читання = [];
  const індекс = new Map();
  class Вузол {
    constructor(д, батько = null, мапа = індекс) {
      this.дані = д; this.parentElement = батько; this.мапа = мапа;
      this.tagName = д.тег.toUpperCase();
      this.childNodes = (д.діти || []).map(ч => typeof ч === 'string' ? ч : new Вузол(ч, this, мапа));
      мапа.set(д.ід, this);
    }
    get children() { return this.childNodes.filter(ч => ч instanceof Вузол); }
    get textContent() { return this.childNodes.map(ч => ч instanceof Вузол ? ч.textContent : ч).join(''); }
    get innerText() { return this.textContent; }
    get title() { return this.дані.атр.title || ''; }
    get className() { return this.дані.атр.class || ''; }
    get dataset() {
      return Object.fromEntries(Object.entries(this.дані.атр).filter(([к]) => к.startsWith('data-')).map(([к, з]) =>
        [к.slice(5).replace(/-([a-z])/g, (_, л) => л.toUpperCase()), з]));
    }
    get src() { return this.адреса(this.дані.атр.src); }
    get currentSrc() { return this.src; }
    get srcset() { return this.дані.атр.srcset || ''; }
    get href() { return this.адреса(this.дані.атр.href); }
    get disabled() { return Object.hasOwn(this.дані.атр, 'disabled'); }
    адреса(з) { return з ? new URL(з, вхід.url).href : ''; }
    querySelectorAll(сел) {
      if (!Object.hasOwn(вхід.селектори, сел)) throw new Error('непідтриманий селектор: ' + сел);
      const свої = new Set();
      const пройти = в => { for (const д of в.children) { свої.add(д.дані.ід); пройти(д); } };
      пройти(this);
      return вхід.селектори[сел].filter(ід => свої.has(ід)).map(ід => this.мапа.get(ід));
    }
    querySelector(сел) { return this.querySelectorAll(сел)[0] || null; }
    closest(сел) {
      if (!Object.hasOwn(вхід.селектори, сел)) throw new Error('непідтриманий closest: ' + сел);
      let в = this;
      while (в) { if (вхід.селектори[сел].includes(в.дані.ід)) return в; в = в.parentElement; }
      return null;
    }
    getAttribute(ім) { return this.дані.атр[ім] ?? null; }
    cloneNode(глибоко) {
      if (!глибоко) throw new Error('очікується глибокий клон');
      return new Вузол(this.дані, null, new Map());
    }
    remove() { if (this.parentElement) this.parentElement.childNodes = this.parentElement.childNodes.filter(ч => ч !== this); }
  }
  const документ = new Вузол(вхід.дерево);
  документ.body = документ.querySelector('body');
  const document = new Proxy(документ, {get(об, к) {
    if (к === 'title') return документ.querySelector('title')?.textContent || '';
    return об[к];
  }});
  function джерело(в, ключ, рядок) {
    const д = {файл: 'zhnyvarka/виконавець.py', рядок: вхід.рядок + рядок - 1,
      вузол: в.дані.шлях + '@' + ключ, порушення: в.дані.порушення,
      причина: в.дані.причина || ''};
    читання.push(д);
    return JSON.stringify(д);
  }
  const п = {
    чисте,
    поле(об, ключ, рядок) {
      ключ = чисте(ключ);
      const з = чисте(об)[ключ];
      if (об instanceof Вузол && ['textContent', 'innerText', 'title'].includes(ключ)) return підпис(з, [джерело(об, ключ, рядок)]);
      return підпис(з, мітки(об));
    },
    виклик(об, ім, арг, рядок) {
      const сирий = чисте(об), метод = сирий[ім];
      // Масиви, callbacks і DOM лишають мітки на своїх елементах.
      if (сирий instanceof Вузол) {
        const з = метод.apply(сирий, арг.map(чисте));
        return ім === 'getAttribute' ? підпис(з, [джерело(сирий, чисте(арг[0]), рядок)]) : з;
      }
      if (Array.isArray(сирий) && ім !== 'join') return метод.apply(сирий, арг);
      let з = метод.apply(сирий, арг.map(чисте));
      let д = мітки(об);
      if (Object.prototype.toString.call(сирий) === '[object RegExp]') д = арг.flatMap(мітки);
      if (Array.isArray(сирий) && ім === 'join') {
        з = сирий.map(чисте).join(...арг.map(чисте)); д = сирий.flatMap(мітки);
      }
      return підпис(з, д);
    },
    функція(ф, арг) {
      if (ф === String) return підпис(String(чисте(арг[0])), мітки(арг[0]));
      return ф(...арг);
    },
    новий(ф, арг) {
      if (ф === Set) {
        const унікальні = new Map();
        for (const ч of арг[0]) if (!унікальні.has(чисте(ч))) унікальні.set(чисте(ч), ч);
        return new Set(унікальні.values());
      }
      return new ф(...арг.map(чисте));
    },
    логічна(вид, ліве, праве) {
      const а = ліве();
      return вид === '&&' ? (чисте(а) ? праве() : а) : вид === '||' ? (чисте(а) ? а : праве()) : (чисте(а) == null ? праве() : а);
    },
    бінарна(вид, ліве, праве) {
      const а = чисте(ліве), б = чисте(праве);
      const дії = {'+': () => а + б, '-': () => а - б, '*': () => а * б, '/': () => а / б,
        '<': () => а < б, '>': () => а > б, '<=': () => а <= б, '>=': () => а >= б,
        '===': () => а === б, '!==': () => а !== б, '==': () => а == б, '!=': () => а != б};
      if (!дії[вид]) throw new Error('непідтриманий оператор: ' + вид);
      return підпис(дії[вид](), [...мітки(ліве), ...мітки(праве)]);
    },
  };
  const контекст = {п, document, location: new URL(вхід.url), URL, String, Array, Math, Set, RegExp};
  const результат = vm.runInNewContext('(' + перетворити(вхід.код).код + ')()', контекст, {timeout: 10000});
  const походження = [];
  function розпакувати(з, шлях=[]) {
    if (з instanceof Рядок) { походження.push({шлях, джерела: з.джерела.map(JSON.parse)}); return з.значення; }
    if (Array.isArray(з)) return з.map((ч, і) => розпакувати(ч, [...шлях, і]));
    if (з && typeof з === 'object') return Object.fromEntries(Object.entries(з).map(([к, ч]) => [к, розпакувати(ч, [...шлях, к])]));
    return з;
  }
  const dom = розпакувати(результат);
  const звичайний = vm.runInNewContext('(' + вхід.код + ')()', контекст, {timeout: 10000});
  if (JSON.stringify(dom) !== JSON.stringify(звичайний)) throw new Error('позначки змінили значення JS-зліпка');
  return {dom, походження, читання};
}

if (require.main === module) {
  const вхід = JSON.parse(fs.readFileSync(0, 'utf8'));
  const вихід = вхід.лише_селектори ? перетворити(вхід.код).селектори : виконати(вхід);
  process.stdout.write(JSON.stringify(вихід));
}
module.exports = {перетворити, виконати};
