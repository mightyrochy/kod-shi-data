/* Синтаксичний граф Е2: області імен, виклики, події та передані замикання. */
'use strict';
const fs = require('node:fs'), vm = require('node:vm'), zlib = require('node:zlib'), crypto = require('node:crypto');
const модуль = {exports: {}};
vm.runInNewContext(zlib.gunzipSync(fs.readFileSync(__dirname + '/річ_запис_дані/acorn.cjs.gz')).toString('utf8'),
  {exports: модуль.exports, module: модуль});
const acorn = модуль.exports;
const частини = JSON.parse(fs.readFileSync(0, 'utf8'));
const функції = [], виклики = [], події = [], змінні = [], вузли = new WeakMap(), слухачі = new Map(), додаткові = [];
const глобальна = {батько: null, імена: new Map()};
const вузолВиклику = new WeakMap();
const подіяЛюдини = /^(?:click|dblclick|auxclick|contextmenu|change|input|beforeinput|submit|reset|keydown|keyup|keypress|toggle|focus|blur|focusin|focusout|paste|cut|copy|drop|drag\w*|pointer\w*|touch\w*|mouse\w*|wheel|select)$/;
const цеФункція = в => /^(?:FunctionDeclaration|FunctionExpression|ArrowFunctionExpression)$/.test(в.type);
function діти(в){
  return Object.entries(в).filter(([к])=>к !== 'loc').flatMap(([, з])=>Array.isArray(з) ? з : [з])
    .filter(д=>д && typeof д.type === 'string');
}
function назва(в){
  if (!в) return '';
  if (в.type === 'Identifier') return в.name;
  if (в.type === 'Literal') return String(в.value);
  if (в.type === 'BinaryExpression' && в.operator === '+' && в.left.type === 'Literal' && в.right.type === 'Literal')
    return String(в.left.value + в.right.value);
  if (в.type === 'ChainExpression') return назва(в.expression);
  if (в.type === 'MemberExpression') return назва(в.object) + '.' + назва(в.property);
  return '';
}
function ключ(в){
  if (!в) return в;
  if (Array.isArray(в)) return в.map(ключ);
  if (typeof в !== 'object') return typeof в === 'bigint' ? String(в) : в;
  return Object.fromEntries(Object.entries(в).filter(([к])=>!['start','end','loc','raw'].includes(к)).map(([к, з])=>[к, ключ(з)]));
}
function місце(в, ф){ return {файл: ф.файл, рядок: ф.рядок + в.loc.start.line - 1, стовпець: в.loc.start.column}; }
function реєструвати(в, о, ф, власник, батько){
  let тут = власник, область = о;
  if (цеФункція(в) || в.type === 'Program'){
    const ім = (в.id && в.id.name) || (батько && батько.type === 'VariableDeclarator' && назва(батько.id)) || '';
    тут = {ід: функції.length, ...місце(в, ф), назва: ім, код: ф.код.slice(в.start, в.end),
      відбиток: crypto.createHash('sha256').update(JSON.stringify(ключ(в))).digest('hex'),
      ребра: [], аргументи: [], параметри: (в.params || []).map(назва),
      записи: [], виклики: [], потоки: [], дом_записи: [], повернення: [], приймачі: [], батько: власник && власник.ід};
    функції.push(тут);
    область = в.type === 'Program' ? о : {батько: о, імена: new Map()};
    if (ім) о.імена.set(ім, {значення: new Set([тут.ід])});
    for (const п of в.params || []) if (п.type === 'Identifier'){
      const комірка = {значення: new Set()}; область.імена.set(п.name, комірка); тут.аргументи.push(комірка);
    } else тут.аргументи.push({значення: new Set()});
  }
  вузли.set(в, {о: область, ф, власник: тут});
  if (в.type === 'VariableDeclarator' && в.id.type === 'Identifier' && в.init){
    const комірка = {значення: new Set(), вираз: в.init};
    о.імена.set(в.id.name, комірка); змінні.push({комірка, о, вираз: в.init});
  }
  for (const д of діти(в)) реєструвати(д, область, ф, тут, в);
}
function знайти(ім, о){
  for (; о; о = о.батько) if (о.імена.has(ім)) return о.імена.get(ім);
  return null;
}
function значення(в, о){
  if (!в) return new Set();
  if (цеФункція(в)) return new Set([вузли.get(в).власник.ід]);
  if (в.type === 'ChainExpression') return значення(в.expression, о);
  if (в.type === 'Identifier' || в.type === 'MemberExpression'){
    const ім = назва(в), комірка = знайти(ім, о) || (/^window\./.test(ім) && знайти(ім.slice(7), о));
    return комірка ? комірка.значення : new Set();
  }
  if (в.type === 'ConditionalExpression') return new Set([...значення(в.consequent, о), ...значення(в.alternate, о)]);
  return new Set();
}
function елемент(в, о, бачені = new Set()){
  if (!в) return '';
  if (в.type === 'CallExpression' && ['$', 'document.getElementById'].includes(назва(в.callee)) && в.arguments[0]?.type === 'Literal')
    return '#' + в.arguments[0].value;
  if (в.type === 'Identifier'){
    const к = знайти(в.name, о);
    if (к && к.вираз && !бачені.has(к)){ бачені.add(к); return елемент(к.вираз, о, бачені); }
  }
  return '';
}
function залежності(в){
  if (!в) return [];
  if (цеФункція(в)) return [];
  if (в.type === 'Identifier') return [в.name];
  if (в.type === 'CallExpression' || в.type === 'NewExpression'){
    const к = вузолВиклику.get(в);
    // Результат функції не дорівнює її входу; передавання крізь обгортку
    // доводить міжпроцедурний потік, стандартні перетворення зберігають дані.
    const ім = назва(в.callee);
    const прозорий = /^(?:Object\.(?:assign|entries|values|fromEntries)|JSON\.stringify|String|Number|Boolean)$/.test(ім)
      || /\.(?:map|slice|filter|join|trim|concat)$/.test(ім);
    return [...(к ? ['@' + к.ід] : []), ...(прозорий ? в.arguments.flatMap(залежності) : [])];
  }
  if (в.type === 'MemberExpression') return залежності(в.object);
  if (в.type === 'Property') return залежності(в.value);
  return діти(в).flatMap(залежності);
}
function поля(в){
  if (!в || цеФункція(в)) return [];
  return [...(в.type === 'Property' ? [назва(в.key)] : []), ...діти(в).flatMap(поля)];
}
function оглянути(в){
  const {о, ф, власник} = вузли.get(в);
  const розмітка = в.type === 'Literal' && typeof в.value === 'string' ? в.value
    : в.type === 'TemplateLiteral' ? в.quasis.map(ч=>ч.value.cooked || ч.value.raw).join('null') : '';
  if (розмітка.includes('<')) for (const збіг of розмітка.matchAll(/\b(on\w+)\s*=\s*(["'])([\s\S]*?)\2/g)){
    const дод = {файл: ф.файл, рядок: місце(в, ф).рядок + розмітка.slice(0, збіг.index).split('\n').length - 1,
      код: '__html__.' + збіг[1] + ' = function(event){' + збіг[3] + '};'};
    const дерево = acorn.parse(дод.код, {ecmaVersion: 'latest', locations: true});
    реєструвати(дерево, о, дод, власник, null); оглянути(дерево); додаткові.push(дерево);
  }
  if (в.type === 'AssignmentExpression'){
    const ім = назва(в.left), власт = в.left.type === 'MemberExpression' ? назва(в.left.property) : '';
    власник.записи.push({ціль: ім || ф.код.slice(в.left.start, в.left.end), код: ф.код.slice(в.start, в.end)});
    if (подіяЛюдини.test(власт.slice(2)) && власт.startsWith('on'))
      події.push({в, обробник: в.right, о, ф, власник, подія: власт});
    else if (ім){
      let к = знайти(ім, о);
      if (!к){ к = {значення: new Set()}; (ім.startsWith('window.') ? глобальна : о).імена.set(ім, к); }
      змінні.push({комірка: к, о, вираз: в.right});
    }
  }
  if (в.type === 'CallExpression' || в.type === 'NewExpression'){
    const ім = назва(в.callee), власт = в.callee.type === 'MemberExpression' ? назва(в.callee.property) : '';
    const цеПодія = власт === 'addEventListener' && в.arguments.length >= 2;
    const к = {ід: виклики.length, в, о, ф, власник, ім, цеПодія};
    виклики.push(к);
    вузолВиклику.set(в, к);
    к.запис = {ід: к.ід, назва: ім, ...місце(в, ф), аргументи: в.arguments.map(а=>ф.код.slice(а.start, а.end)),
      поля: в.arguments.map(поля)};
    власник.виклики.push(к.запис);
    if (цеПодія && в.arguments[0].type === 'Literal' && подіяЛюдини.test(в.arguments[0].value))
      події.push({в, обробник: в.arguments[1], о, ф, власник, подія: в.arguments[0].value});
    // Нелітеральна подія теж лишається в інвентарі: класифікатор мусить її розглянути.
    if (цеПодія && в.arguments[0].type !== 'Literal')
      події.push({в, обробник: в.arguments[1], о, ф, власник, подія: '<динамічна>'});
    if (власт === 'setAttribute' && в.arguments[0]?.type === 'Literal' && /^on/.test(в.arguments[0].value)
        && в.arguments[1]?.type === 'Literal' && typeof в.arguments[1].value === 'string'){
      const дод = {файл: ф.файл, рядок: місце(в, ф).рядок,
        код: '__html__.' + в.arguments[0].value + ' = function(event){' + в.arguments[1].value + '};'};
      const дерево = acorn.parse(дод.код, {ecmaVersion: 'latest', locations: true});
      реєструвати(дерево, о, дод, власник, null); оглянути(дерево); додаткові.push(дерево);
    }
  }
  for (const д of діти(в)) оглянути(д);
}
for (const ф of частини){
  const дерево = acorn.parse(ф.код, {ecmaVersion: 'latest', sourceType: 'module', locations: true,
    allowReturnOutsideFunction: true});
  реєструвати(дерево, глобальна, ф, null, null);
  ф.дерево = дерево;
}
for (const ф of частини) оглянути(ф.дерево);
function додати(куди, звідки){ let зміна = false; for (const і of звідки) if (!куди.has(і)){ куди.add(і); зміна = true; } return зміна; }
let зміна = true;
while (зміна){
  зміна = false;
  for (const з of змінні) зміна = додати(з.комірка.значення, значення(з.вираз, з.о)) || зміна;
  for (const к of виклики) for (const і of значення(к.в.callee, к.о)){
    const ф = функції[і];
    к.в.arguments.forEach((а, н)=>{ if (ф.аргументи[н]) зміна = додати(ф.аргументи[н].значення, значення(а, к.о)) || зміна; });
  }
}
for (const п of події){
  if (п.в.type !== 'AssignmentExpression') continue;
  const дом = елемент(п.в.left.object, п.о);
  if (дом){
    if (!слухачі.has(дом)) слухачі.set(дом, new Set());
    додати(слухачі.get(дом), значення(п.обробник, п.о));
  }
}
for (const к of виклики){
  const ребра = new Set(значення(к.в.callee, к.о));
  if (к.в.callee.type === 'MemberExpression' && /^(?:click|onclick)$/.test(назва(к.в.callee.property)))
    додати(ребра, слухачі.get(елемент(к.в.callee.object, к.о)) || []);
  // Колекції, обіцянки й таймери виконують callback; реєстрація UI — ні.
  if (!к.цеПодія && /^(?:.*\.)?(?:forEach|map|filter|find|some|every|reduce|sort|then|catch|finally|setTimeout|setInterval|queueMicrotask)$/.test(к.ім))
    for (const а of к.в.arguments) додати(ребра, значення(а, к.о));
  к.власник.ребра.push(...ребра);
  к.запис.цілі = [...ребра];
  к.запис.вхід = к.в.arguments.map(залежності);
}
function потоки(в){
  const {власник, о} = вузли.get(в);
  if (в.type === 'ArrowFunctionExpression' && в.body.type !== 'BlockStatement')
    власник.повернення.push(...залежності(в.body));
  if (в.type === 'VariableDeclarator' && в.init)
    власник.потоки.push({ціль: назва(в.id), з: залежності(в.init)});
  if (в.type === 'AssignmentExpression')
    власник.потоки.push({ціль: назва(в.left).split('.')[0], з: залежності(в.right)});
  if (в.type === 'AssignmentExpression' && в.left.type === 'MemberExpression' && /^(?:value|checked)$/.test(назва(в.left.property))){
    const дом = елемент(в.left.object, о);
    if (дом) власник.дом_записи.push({елемент: дом.slice(1), з: залежності(в.right)});
  }
  if (в.type === 'ReturnStatement') власник.повернення.push(...залежності(в.argument));
  if (в.type === 'CallExpression' && /^(?:window\.)?ЧАТ_П\.push$/.test(назва(в.callee)))
    власник.приймачі.push(...в.arguments.flatMap(залежності));
  for (const д of діти(в)) потоки(д);
}
for (const ф of частини) потоки(ф.дерево);
for (const дерево of додаткові) потоки(дерево);
const обробники = [];
for (const п of події){
  const цілі = [...значення(п.обробник, п.о)];
  for (const і of цілі.length ? цілі : [null]){
    const ц = і === null ? null : функції[і];
    обробники.push({...місце(п.в, п.ф), подія: п.подія, функція: п.власник.назва,
      ціль: і, код: ц ? ц.код : п.ф.код.slice(п.обробник.start, п.обробник.end),
      передано: ц && ц.файл !== п.ф.файл || ц && (ц.рядок < п.ф.рядок + п.обробник.loc.start.line - 1 || ц.рядок > п.ф.рядок + п.обробник.loc.end.line - 1),
      реєстрація: п.ф.код.slice(п.в.start, п.в.end)});
  }
}
for (const ф of функції){ ф.ребра = [...new Set(ф.ребра)]; delete ф.аргументи; }
process.stdout.write(JSON.stringify({функції, обробники}));
