/* VM одержує лише підготовлені відповіді моста й фікстури, без мережі та моделі. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const набір = JSON.parse(fs.readFileSync(0, 'utf8'));
const шлях = path.join(__dirname, '../../../джерела/показ/мовний_шар.js');
let спроб = 0, викликів_моста = 0, повторів_письма = 0;
const мова = vm.createContext({
  МОДЕЛЬ_МОВИ_П: 'фікстура',
  ПАСПОРТ_П: {},
  ЧАТ_П: [],
  async містП(імʼя, вхід) {
    assert.equal(імʼя, 'мова');
    const і = Math.floor(викликів_моста / 2);
    const крок = набір.кроки[і];
    assert.ok(крок, 'зайвий виклик моста');
    const запит = викликів_моста++ % 2 === 0;
    assert.deepEqual(JSON.parse(JSON.stringify(вхід)), запит ? крок.запит : крок.вихід);
    return запит ? крок.промпт : крок.результат;
  },
  async фікстура(промпт) {
    const крок = набір.кроки[спроб++];
    assert.ok(крок, 'зайва спроба перекладу');
    assert.equal(промпт, крок.промпт.промпт);
    return крок.вихід.відповідь_моделі;
  },
  async забороненийПереклад() {
    ++повторів_письма;
    throw new Error('зайвий запит на виправлення письма');
  },
});
vm.runInContext(набір.код || fs.readFileSync(шлях, 'utf8'), мова);
vm.runInContext('модельМовиП = фікстура; мовоюП = забороненийПереклад;', мова);

мова.реплікоюП(набір.репліка, 'chat', набір.запрошення).then(вихід => {
  assert.equal(спроб, набір.кроки.length);
  assert.equal(викликів_моста, 2 * спроб);
  assert.equal(повторів_письма, 0);
  assert.ok(!(вихід.запис.причина || '').startsWith('layer_failed'));
  process.stdout.write(JSON.stringify({...вихід, спроб}));
}).catch(помилка => {
  console.error(помилка);
  process.exitCode = 1;
});
