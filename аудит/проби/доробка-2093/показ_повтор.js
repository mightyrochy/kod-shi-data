/* Функції показу → справжній читач і суддя Е2; записана відповідь замінює лише модель. */
const fs = require('fs'), path = require('path'), vm = require('vm'), {spawnSync} = require('child_process');
const джерела = process.env.E2_SOURCES || path.resolve(__dirname, '../../../джерела');
const середовище = vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П: 'запис', ПАСПОРТ_П: null, ЧАТ_П: []});
середовище.містП = async (ім, дані) => {
  if (ім !== 'мова') throw Error(ім);
  const р = spawnSync('python', ['-X', 'utf8', '-c',
    'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as М;print(М.мова(sys.stdin.read()))', джерела],
    {input: JSON.stringify(дані), encoding: 'utf8', maxBuffer: 4000000});
  if (р.status) throw Error(р.stderr);
  return JSON.parse(р.stdout);
};
for (const файл of ['мовний_шар.js', 'оцінка.js'])
  vm.runInContext(fs.readFileSync(path.join(джерела, 'показ', файл), 'utf8'), середовище);

async function main(){
  let помилок = 0;
  const звірити = (випадок, пройдено, дані) => {
    console.log(JSON.stringify({випадок, пройдено, дані})); помилок += !пройдено;
  };
  let викликів = 0;
  середовище.модельМовиП = async () => JSON.stringify(++викликів === 1
    ? {'1': 'Коротке повідомлення для тебе.'} : {'1': null});
  const текст = await середовище.мовоюП({а: 'A short message for you.', б: 'Another short message for you.'}, 'проба');
  звірити('прямий переклад: невдалий повтор не стирає сусіднє', викликів === 2
    && текст.тексти.а === 'Коротке повідомлення для тебе.' && текст.тексти.б === '— без тексту', текст.тексти);

  викликів = 0;
  середовище.модельМовиП = async п => {
    викликів++;
    const заяви = JSON.parse(п.split('\nПОВІДОМЛЕННЯ:\n')[1]);
    return JSON.stringify(Object.fromEntries(заяви.filter(з => викликів === 2 || з.item_ids[0] === 'а')
      .map(з => [з.key, з.item_ids[0] === 'а' ? 'Перша сукня.' : 'Друга сукня.'])));
  };
  const повідомлення = await середовище.повідомленнямП({рядок: {kind: 'card_occasion', statements: ['а', 'б'].map(ід => ({
    code: 'mourning_colour_word_only', item_ids: [ід], choice: 'her', recipient: 'woman', source: 'catalogue',
    rank: {position: 1, rare: false}, values: {item: {free_text: 'Сукня', lang: 'uk'}}}))}}, 'проба');
  звірити('заяви: часткові відповіді дають обидві сукні', викликів === 2
    && повідомлення.тексти.рядок === 'Перша сукня. Друга сукня.', повідомлення.тексти);

  викликів = 0;
  середовище.модельМовиП = async () => JSON.stringify(++викликів === 1
    ? {'1': 'Тобі пасує цей образ.'} : {'1': null});
  const картка = {відповідь: 'This look suits you.', вдало: [{текст: 'The colour suits you.'}], змінити: []};
  await середовище.мовоюКарткуОцінкиП(картка, 'review');
  звірити('оцінка: невдалий повтор зберігає прийняту відповідь', викликів === 2
    && картка.відповідь === 'Тобі пасує цей образ.', картка.відповідь);
  for (const виправлено of [false, true]){
    середовище.модельМовиП = async () => JSON.stringify(виправлено ? {'1': 'Тобі пасує цей образ.'} : {});
    const запис = {};
    const чат = await середовище.латинкаЧатуП('Тобі пасує цей образ. Макіяж planуєш?', запис);
    звірити('чат: заміну обирає той самий суддя', чат === 'Тобі пасує цей образ.'
      && запис.латиниця_повтор.вихід === (виправлено ? 'clean' : 'cut'), {чат, виправлено});
  }
  const міст = середовище.містП;
  середовище.містП = async (ім, дані) => {
    if (дані.відповіді_шару) throw Error('немає транспорту судді');
    return міст(ім, дані);
  };
  викликів = 0;
  середовище.модельМовиП = async () => JSON.stringify(++викликів === 1
    ? {'1': 'Коротке повідомлення для тебе.'} : {});
  const відмова = await середовище.мовоюП({а: 'A short message for you.', б: 'Another short message for you.'}, 'проба');
  звірити('збій транспорту судді: прийняте доступне, причина видима',
    відмова.тексти.а === 'Коротке повідомлення для тебе.'
    && відмова.записи.some(з => з.де === 'merge' && /layer_failed/.test(з.причина)), відмова.тексти);
  process.exitCode = помилок ? 1 : 0;
}
main().catch(помилка => {console.error(помилка); process.exitCode = 1;});
