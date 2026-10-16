/* Рядок 6222: «Як носити» в промпті примірки — мовою опису, не українські рядки картки. Функцією в Chromium на
   зібраних сторінках ДО і ПІСЛЯ: картка з англійським «Як носити» → `мовоюКарткуП` (переклад підставний) →
   `приміряти`; `містП('приміряння')` перехоплено, друкується його `як_носити` (= `how_to_wear` промпту).
   Запуск (з теки джерела): NODE_PATH=node_modules node ../аудит/проби/як_носити_6222.js <тека ДО> <тека ПІСЛЯ> */
const { chromium } = require('playwright');
(async () => {
  const б = await chromium.launch({executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
  for (const [назва, сайт] of [['ДО', process.argv[2]], ['ПІСЛЯ', process.argv[3]]]) {
    const с = await б.newPage({viewport: {width: 390, height: 844}});
    await с.route(/^https?:/, р => р.abort());
    await с.goto('file://' + сайт + '/index.html#model_mova=mamaylm-gemma-3-12b-it-v2.0');
    await с.waitForFunction(() => typeof мовоюКарткуП === 'function' && typeof приміряти === 'function', null, {timeout: 60000});
    const р = await с.evaluate(async () => {
      мовоюП = async (т) => ({тексти: Object.fromEntries(Object.entries(т).map(([к, v]) =>
        [к, к.startsWith('як_носити') ? 'верх заправити спереду' : 'Спокійний образ на кожен день.'])), записи: [{де: 'test'}]});
      питаннямиП = async () => ({});
      const к = {рука: 1, текст: '', опис: 'A calm everyday look.', як_носити: ['tuck the top in at the front'],
                 речі: [{id: '1', назва: 'Блуза', слот: 'верх', фото: null}, {id: '2', назва: 'Річ', слот: 'щось', фото: null}]};
      await мовоюКарткуП(к, 'test');
      П = {картки: [к]};
      for (const ід of ['прм-0', 'прмк-0']) { const е = document.createElement('div'); е.id = ід; document.body.appendChild(е); }
      читатиКв = async () => new Blob([new Uint8Array([255, 216, 255, 217])], {type: 'image/jpeg'});
      блобВБазу = async () => 'data:image/jpeg;base64,AA=='; фотоДоСторониП = async (x) => x;
      let вх = null; містП = async (е, в) => { if (е === 'приміряння') { вх = в; throw new Error('стоп'); } return {}; };
      await приміряти(0);
      return {шар: МОДЕЛЬ_МОВИ_П, картка: к.як_носити, how_to_wear: вх && вх.як_носити};
    });
    const кир = JSON.stringify(р.how_to_wear || []).match(/[А-Яа-яІіЇїЄєҐґ]/g) || [];
    console.log(назва, 'шар', р.шар, 'картка:', JSON.stringify(р.картка), '· how_to_wear у промпт:', JSON.stringify(р.how_to_wear), '· кирилиці', кир.length);
    await с.close();
  }
  await б.close();
})();
