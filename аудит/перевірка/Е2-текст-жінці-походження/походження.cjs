/* Перевіряє носій походження, відмову мосту й відсутність винятку за самою мовою входу. */
const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const код = fs.readFileSync('джерела/показ/мовний_шар.js', 'utf8');
(async () => {
  let звірок = 0;
  for (const збій of [false, true]){
    for (const [тип, дозволено] of [['каталог', true], ['копія', false], ['модель', false], ['крамниця', false], ['поле', false]]){
      const текст = 'Сумка Gucci підкреслює лінії образу і створює колірний акцент.';
      const с = vm.createContext({setTimeout, clearTimeout, ЧАТ_П: [], П: null, ОЦ: null,
        МОДЕЛЬ_МОВИ_П: 'заглушка',
        містП: async (_ім, д) => {
          if (д.тексти) return {промпт: 'п', розмітка: [{н: 1, ключ: 'свідомі.0', текст: д.тексти['свідомі.0']}]};
          if (д.відповіді_шару && збій) return {помилка: 'збій-судді'};
          return {тексти: {'свідомі.0': текст}};
        },
      });
      vm.runInContext(код, с);
      с.тип = тип;
      vm.runInContext(`модельМовиП = async () => '{}';
        const картка = {речі: [{назва: 'Сумка', бренд: 'Gucci',
          вигадана: ['модель', 'крамниця'].includes(тип), крамниця: тип === 'крамниця' ? 'Gucci' : ''}]};
        let речі = тип === 'поле' ? [{назва: 'Gucci', свої_шару: ['gucci']}] : речіШаруП(картка);
        if (тип === 'копія') речі = JSON.parse(JSON.stringify(речі));`, с);
      const р = await vm.runInContext(`(async () => {
        const р = await мовоюП({'свідомі.0': 'The Gucci bag adds an accent and supports the outfit.'},
          'перевірка', undefined, речі, undefined, undefined, true);
        return злитиВідповідіШаруП([р]);
      })()`, с);
      assert.equal(р.тексти['свідомі.0'], дозволено ? текст
        : vm.runInContext('НАПИС_БЕЗ_ШАРУ_П.card_without_description', с), `${тип}, збій=${збій}`);
      звірок++;
    }
  }
  const с = vm.createContext({ЧАТ_П: [], П: null, ОЦ: null});
  vm.runInContext(код, с);
  for (const вхід of ['Сумка Gucci пасує до образу.', 'The Gucci bag goes with the outfit.']){
    с.вхід = вхід;
    assert.equal(vm.runInContext("своїВходуП(вхід, new Set(['gucci'])).has('gucci')", с), true);
    assert.equal(vm.runInContext("своїВходуП(вхід).has('gucci')", с), false);
    звірок += 2;
  }
  console.log(`Звірок: ${звірок}, провалів: 0`);
})().catch(п => {console.error(п); process.exitCode = 1;});
