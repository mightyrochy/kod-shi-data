/* VM викликає штатний Python-міст через локальний процес. Модель підставна, мережі немає. */
const assert = require('node:assert/strict');
const {spawn} = require('node:child_process');
const fs = require('node:fs');
const path = require('node:path');
const readline = require('node:readline');
const vm = require('node:vm');

const набір = JSON.parse(fs.readFileSync(0, 'utf8'));
const шлях = path.join(__dirname, '../../../джерела/показ/мовний_шар.js');
const міст = spawn('python3', ['-B', path.join(__dirname, 'проба.py'), '--міст', ...(набір.до ? ['--до'] : [])],
  {stdio: ['pipe', 'pipe', 'inherit']});
const рядки = readline.createInterface({input: міст.stdout})[Symbol.asyncIterator]();
let спроб = 0, викликів_моста = 0, повторів_письма = 0;
let промптМоста, причинаПовтору;
const мова = vm.createContext({
  МОДЕЛЬ_МОВИ_П: 'фікстура',
  ПАСПОРТ_П: {},
  ЧАТ_П: [],
  async містП(імʼя, вхід) {
    assert.equal(імʼя, 'мова');
    const і = Math.floor(викликів_моста / 2);
    assert.ok(і < набір.відповіді.length, 'зайвий виклик моста');
    const запит = викликів_моста++ % 2 === 0;
    const очікуване = {репліка: набір.репліка, паспорт: {}, запрошення: набір.запрошення};
    if (запит && і) очікуване.помилка_формату = причинаПовтору;
    if (!запит) {
      очікуване.відповідь_моделі = набір.відповіді[і];
      if (і) очікуване.перша_відповідь = набір.відповіді[0];
    }
    assert.deepEqual(JSON.parse(JSON.stringify(вхід)), очікуване);
    міст.stdin.write(JSON.stringify(вхід) + '\n');
    const рядок = await рядки.next();
    assert.ok(!рядок.done, 'міст завершився без відповіді');
    const вихід = JSON.parse(рядок.value);
    if (запит) {
      промптМоста = вихід.промпт;
      const зміст = JSON.parse(промптМоста.split('РЕПЛІКА:\n')[1]);
      assert.deepEqual(зміст.item_verdicts, набір.репліка.item_verdicts);
      if (і) assert.match(промптМоста, /Розбіжність попередньої відповіді:/);
    } else {
      assert.equal(typeof вихід.текст, 'string');
      причинаПовтору = вихід.причина;
    }
    return вихід;
  },
  async фікстура(промпт) {
    assert.ok(спроб < набір.відповіді.length, 'зайва спроба перекладу');
    assert.equal(промпт, промптМоста);
    return набір.відповіді[спроб++];
  },
  async забороненийПереклад() {
    ++повторів_письма;
    throw new Error('зайвий запит на виправлення письма');
  },
});
vm.runInContext(набір.код || fs.readFileSync(шлях, 'utf8'), мова);
vm.runInContext('модельМовиП = фікстура; мовоюП = забороненийПереклад;', мова);

мова.реплікоюП(набір.репліка, 'chat', набір.запрошення).then(вихід => {
  assert.equal(спроб, набір.відповіді.length);
  assert.equal(викликів_моста, 2 * спроб);
  assert.equal(повторів_письма, 0);
  assert.ok(!(вихід.запис.причина || '').startsWith('layer_failed'));
  process.stdout.write(JSON.stringify({...вихід, спроб}));
}).catch(помилка => {
  console.error(помилка);
  process.exitCode = 1;
}).finally(() => міст.stdin.end());
