/* Показ → справжня схема Е2 → злиття → показ і повторний показ із кешу. Модель замінено записом. */
const fs = require('fs'), path = require('path'), vm = require('vm'), {spawnSync} = require('child_process');
const джерела = process.env.E2_SOURCES || path.resolve(__dirname, '../../../джерела');

function показ(){
  const с = vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П: 'запис', ПАСПОРТ_П: null, ЧАТ_П: []});
  с.містП = async (ім, дані) => {
    if (ім !== 'мова') throw Error(ім);
    const р = spawnSync('python', ['-X', 'utf8', '-c',
      'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as М;print(М.мова(sys.stdin.read()))', джерела],
      {input: JSON.stringify(дані), encoding: 'utf8', maxBuffer: 4000000});
    if (р.status) throw Error(р.stderr);
    return JSON.parse(р.stdout);
  };
  vm.runInContext(fs.readFileSync(path.join(джерела, 'показ/мовний_шар.js'), 'utf8'), с);
  return с;
}

async function main(){
  const факти = [];
  const звірити = (випадок, пройдено, дані) => {
    факти.push(!!пройдено); console.log(JSON.stringify({випадок, пройдено: !!пройдено, дані}));
  };
  const заява = ід => ({code: 'mourning_colour_word_only', item_ids: [ід], choice: 'her', recipient: 'woman',
    source: 'catalogue', rank: {position: 1, rare: false}, values: {item: {free_text: 'Сукня', lang: 'uk'}}});
  for (const текст of ['This dress suits you.', 'Ця сукня тобі пасує dress.']){
    const с = показ(); let викликів = 0;
    с.модельМовиП = async п => {
      if (++викликів % 2 === 0) throw Error('контрольована відмова моделі');
      const заяви = JSON.parse(п.split('\nПОВІДОМЛЕННЯ:\n')[1]);
      return JSON.stringify(Object.fromEntries(заяви.map(з => [з.key, текст])));
    };
    const вхід = {рядок: {kind: 'card_occasion', statements: [заява('а')]}};
    const перший = await с.повідомленнямП(вхід, 'відмова повтору');
    const другий = await с.повідомленнямП(вхід, 'повторний показ');
    const кеш = vm.runInContext('[ТЕКСТИ_ЗА_КЛЮЧЕМ_П.size, ПАМ_ЯТЬ_ПОВІДОМЛЕНЬ_П.size]', с);
    const шаблон = vm.runInContext('НАПИС_БЕЗ_ШАРУ_П.card_occasion || НАПИС_БЕЗ_ТЕКСТУ_П', с);
    звірити('2116: відмова моделі на повторі: ' + текст, перший.тексти.рядок === шаблон
      && другий.тексти.рядок === шаблон && викликів === 4 && кеш.every(к => к === 0),
      {перший: перший.тексти, другий: другий.тексти, стани: перший.заяви.map(з => з.стан), викликів, кеш});
  }
  for (const [назва, текст] of [['відмова англійською', 'I cannot translate this request.'],
    ['латинка', 'Ця сукня тобі пасує, але planуєш вечір.'], ['порожнє', null], ['об’єкт замість рядка', {text: 'Сукня.'}]]){
    const с = показ(); let викликів = 0;
    с.модельМовиП = async () => JSON.stringify(++викликів % 2 ? {} : {'1': текст});
    const вхід = {рядок: {kind: 'card_occasion', statements: [заява('а')]}};
    const перший = await с.повідомленнямП(вхід, 'проба');
    const післяПершого = викликів;
    const другий = await с.повідомленнямП(вхід, 'повторний показ');
    const кеш = vm.runInContext('({заКлючем: ТЕКСТИ_ЗА_КЛЮЧЕМ_П.size, повідомлень: ПАМ_ЯТЬ_ПОВІДОМЛЕНЬ_П.size})', с);
    const шаблон = vm.runInContext('НАПИС_БЕЗ_ШАРУ_П.card_occasion || НАПИС_БЕЗ_ТЕКСТУ_П', с);
    звірити(назва + ': шаблон, без кешування', перший.тексти.рядок === шаблон && другий.тексти.рядок === шаблон
      && перший.заяви.every(з => з.стан !== 'translated') && післяПершого === 2 && викликів === 4
      && кеш.заКлючем === 0 && кеш.повідомлень === 0, {перший: перший.тексти, другий: другий.тексти,
        стани: перший.заяви.map(з => з.стан), викликів, кеш});
  }
  for (const збій of [false, true]){
    const с = показ(); let викликів = 0;
    const міст = с.містП;
    с.містП = async (ім, дані) => {
      if (збій && дані.відповіді_шару) throw Error('немає транспорту');
      return міст(ім, дані);
    };
    с.модельМовиП = async п => {
      викликів++;
      const заяви = JSON.parse(п.split('\nПОВІДОМЛЕННЯ:\n')[1]);
      return JSON.stringify(Object.fromEntries(заяви.filter(з => викликів > 1 || з.item_ids[0] === 'а')
        .map(з => [з.key, з.item_ids[0] === 'а' ? 'Перша сукня.' : 'I cannot translate this request.'])));
    };
    const р = await с.повідомленнямП({рядок: {kind: 'card_occasion', statements: [заява('а'), заява('б')]}}, 'часткова');
    звірити('прийнятий сусід і відхилений повтор; транспорт=' + !збій,
      р.тексти.рядок === 'Перша сукня. — без тексту' && р.заяви[0].стан === 'translated'
      && р.заяви[1].стан !== 'translated', {тексти: р.тексти, стани: р.заяви.map(з => з.стан)});
  }
  const с = показ(); let викликів = 0;
  с.модельМовиП = async () => JSON.stringify(++викликів === 1 ? {} : {'1': 'Ця сукня тобі пасує.'});
  const вхід = {рядок: {kind: 'card_occasion', statements: [заява('а')]}};
  const р = await с.повідомленнямП(вхід, 'придатна заміна');
  const кеш = await с.повідомленнямП(вхід, 'повторний показ');
  звірити('придатне виправлення проходить і кешується', викликів === 2 && р.тексти.рядок === 'Ця сукня тобі пасує.'
    && кеш.тексти.рядок === р.тексти.рядок && р.заяви[0].стан === 'translated', {тексти: р.тексти, викликів});
  console.log(JSON.stringify({усього: факти.length, пройдено: факти.filter(Boolean).length}));
  process.exitCode = факти.every(Boolean) ? 0 : 1;
}
main().catch(помилка => {console.error(помилка); process.exitCode = 1;});
