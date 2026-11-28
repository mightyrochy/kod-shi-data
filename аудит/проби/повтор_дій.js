/* Записані дії знайомства v5 у «Парі» проходять через відповідні видимі аркуші профілю. */
async function знайомствоПовтору(стор, мітка){
  if (!await стор.locator('#mirror-studio').count()) return null;
  const профіль = стор.locator('[data-ux="pair-profile-done"]');
  const готово = стор.locator('#аркуш-готово');
  const закрити = async () => { if (await готово.isVisible()) await готово.click(); };
  const відкрити = async (аркуш, селектор) => {
    if (!await стор.locator('#аркуш-тіло #' + аркуш).count()){
      await закрити();
      if (!await стор.locator(селектор).first().isVisible()) await стор.locator('#mirror-person').click();
      await стор.locator(селектор + ':visible').first().click();
    }
  };
  const поле = (селектор) => ({лок: стор.locator(селектор)});
  const щеБезПрофілю = !await стор.evaluate(() => ПРОФІЛЬ_СТВОРЕНО);
  if (щеБезПрофілю){
    if (/Нема портрета під рукою|Інший шлях/.test(мітка)){
      await відкрити('кол-блок', '[data-аркуш="кол-блок"]');
      const розкривач = стор.locator('#кол-блок details.розкривач');
      if (await розкривач.getAttribute('open') === null) await розкривач.locator('summary').click();
      return {виконано: true};
    }
    if (/Встав відповідь чату|Застосувати кольори/.test(мітка)){
      await відкрити('кол-блок', '[data-аркуш="кол-блок"]');
      const розкривач = стор.locator('#кол-блок details.розкривач');
      if (await розкривач.getAttribute('open') === null) await розкривач.locator('summary').click();
      return поле(мітка.includes('Застосувати') ? '#кол-читати' : '#кол-відповідь');
    }
    if (/Ім['ʼ’]я або псевдонім|Дозволяю записати/.test(мітка)){
      await відкрити('проф-блок', '[data-ux="pair-name"]');
      return поле(мітка.includes('Дозволяю') ? '#пр-згода' : '[id="пр-імʼя"]');
    }
    const мірки = {'Зріст': 'зріст', 'Плечі': 'плечі', 'Груди': 'груди', 'Талія': 'талія', 'Стегна': 'стегна'};
    const мірка = Object.keys(мірки).find(назва => мітка.startsWith('поле: ' + назва + ' '));
    if (мірка){
      await відкрити('мір-блок', '[data-аркуш="мір-блок"]');
      return поле('#мр-' + мірки[мірка]);
    }
    if (мітка === 'кнопка: Далі'){
      await закрити();
      return {виконано: true};
    }
    if (мітка === 'кнопка: Готово'){
      await закрити();
      if (!await профіль.isVisible()) await стор.locator('#mirror-person').click();
      return поле('[data-ux="pair-profile-done"]');
    }
  }
  if (/Напиши, як подрузі|Напиши стилістці|^кнопка: Надіслати$/.test(мітка)){
    if (await профіль.isVisible()) await профіль.click();
    if (!await стор.locator('#чат-поле').isVisible()) await стор.locator('#pair-handle').click();
    return поле(мітка === 'кнопка: Надіслати' ? '#чат-слати' : '#чат-поле');
  }
  return null;
}

const кнопкаУмов = '[data-ux="pair-summary"]:visible';

async function відкритиУмови(стор){
  await згорнутиРозмовуПари(стор);
  const підсумок = стор.locator(кнопкаУмов).first();
  if (!await підсумок.isVisible()) await стор.locator('[data-ux="features"]:visible').first().click();
  await підсумок.click();
  await згорнутиРозмовуПари(стор);
}

async function умовиПовтору(стор, мітка){
  if (!await стор.locator('#mirror-studio').count()) return null;
  const кнопка = селектор => ({лок: стор.locator(селектор).first()});
  if (мітка === 'кнопка: ← До сценарію' && await стор.locator('#е-палітра').isVisible())
    return кнопка(кнопкаУмов);
  const поле = [
    [/^кнопка: Нагода /, 'нагода'],
    [/^кнопка: Де /, 'місце'],
    [/^кнопка: Ошатність /, 'дрес'],
    [/^кнопка: (Коли й погода|Погода) /, 'коли'],
    [/^кнопка: Макіяж /, 'макіяж'],
    [/^кнопка: Прикраси /, 'прикраси'],
    [/^кнопка: Мета /, 'мета'],
  ].find(([назва]) => назва.test(мітка))?.[1];
  const палітра = /^кнопка: Палітра /.test(мітка);
  if (!поле && !палітра) return null;
  const умови = стор.locator('.pair-conditions');
  if (!await умови.isVisible()) await відкритиУмови(стор);
  if (палітра) return кнопка('[data-ux="pair-palette"]:visible');
  if (поле === 'нагода') {
    const редактор = '[data-ux="pair-edit"][data-value="нагода"]:visible';
    return кнопка(await стор.locator(редактор).count() ? редактор : '[data-ux="pair-occasion"]:visible');
  }
  if (await умови.getAttribute('open') === null) await умови.locator('summary').click();
  return кнопка('[data-ux="pair-edit"][data-value="' + поле + '"]:visible');
}

async function кнопкаЗборуПовтору(стор){
  if (!await стор.locator('#mirror-studio').count()) return стор.locator('#зб-зібрати');
  const готово = стор.locator('#аркуш-готово');
  if (await готово.isVisible()) await готово.click();
  await згорнутиРозмовуПари(стор);
  const кнопка = стор.locator('#mirror-work [data-ux="pair-build"]:visible').first();
  if (!await кнопка.isVisible()) await відкритиУмови(стор);
  return кнопка;
}

const {станЗбору, новийЗбір, чекатиЗбір, початиЗбір, згорнутиРозмовуПари} = require('./потік_стенда.js');

async function зібратиВПовторі(стор, до){
  const timeout = 900000;
  const дотик = async () => {
    const кнопка = await кнопкаЗборуПовтору(стор);
    if (!новийЗбір(до, await станЗбору(стор))) await кнопка.click({noWaitAfter: true, timeout});
  };
  const старт = await початиЗбір(стор, до, дотик, timeout);
  if (старт.відмова) return старт;
  const готовий = await чекатиЗбір(стор, до, 'картки', timeout);
  return {...готовий, розмова: !!старт.розмова};
}

module.exports = {знайомствоПовтору, умовиПовтору, зібратиВПовторі};
