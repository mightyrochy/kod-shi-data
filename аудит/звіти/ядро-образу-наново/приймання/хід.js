/* Виконує дії ходу Н6 через кнопки сторінки й записує стан на кожному кроці. */
const fs = require('node:fs');
const path = require('node:path');
const {знімокРук, доЗавантажитиФото} = require('../../../проби/живий-як-людина-4/стенд/руки_зі_сторінки.js');

function записН6(файл){
  const план = JSON.parse(fs.readFileSync(файл, 'utf8'));
  const тека = path.dirname(файл);
  const записати = (ім, дані) => fs.writeFileSync(path.join(тека, ім), JSON.stringify(дані, null, 2) + '\n');
  const додати = (ім, дані) => fs.appendFileSync(path.join(тека, ім), JSON.stringify(дані) + '\n');
  const хід = (текст) => fs.appendFileSync(path.join(тека, 'хід.md'), текст + '\n');
  const лічба = {шлях: план.шлях, прохід: план.прохід, ситуація: план.номер, ід: план.ід, репліки: []};
  let репліка = null, обмінів = 0, початокЗбору = null, позиція = 0;

  for (const файл of ['обміни.jsonl', 'руки.jsonl']) fs.writeFileSync(path.join(тека, файл), '');
  хід('# Хід ' + план.номер + ', прохід ' + план.прохід + ', шлях ' + план.шлях);

  function початиОбмін(запит){
    const номер = ++обмінів, початок = Date.now(), чия = репліка;
    if (чия) чия.викликів++;
    return відповідь => {
      const тіло = typeof відповідь.body === 'string' ? відповідь.body : '{}';
      додати('обміни.jsonl', {номер, репліка: чия?.номер ?? null, час: new Date(початок).toISOString(),
        секунд: (Date.now() - початок) / 1000, статус: відповідь.status ?? 200, запит, відповідь: тіло});
    };
  }

  async function профіль(стор, вхід){
    await стор.evaluate(({skin, hair, eyes, ring, мірки}) => {
      const виміри = {плечі: 98, груди: 92, талія: 74, стегна: 99, зріст: 168, ...мірки};
      const {зріст, ...обхвати} = виміри;
      const колір = кольориПрофілюП({шкіра: skin, волосся: hair, очі: eyes, кільце: ring}, null, 'uncontrolled');
      return писатиКв('профіль:' + АКТИВНИЙ, {колір, створено: true, мірки: {зріст, обхвати}});
    }, вхід);
    await стор.evaluate(async () => { await читатиАктивний(); режим('сценарій'); });
  }

  async function пройти(стор, {передЗбором, післяЗбору, показатиКартку}){
    const таймаут = 900000;
    const натиснути = селектор => стор.locator(селектор).click({timeout: 15000});
    const чекати = (умова, аргумент) => стор.waitForFunction(умова, аргумент, {timeout: таймаут});
    const пара = Boolean(await стор.locator('#mirror-studio').count());
    const діяПари = (ім, значення = null) => `#mirror-work [data-ux="${ім}"]`
      + (значення === null ? '' : `[data-value="${значення}"]`) + ':visible';
    const кнопкаЗбору = пара ? діяПари('pair-build') : '#зб-зібрати';
    const slug = () => String(++позиція).padStart(3, '0');
    async function кадр(що){
      const ід = slug() + '.png';
      const знімок = 'знімки/' + ід;
      await стор.screenshot({path: path.join(тека, знімок), fullPage: false});
      const стан = await стор.evaluate(() => ({
        режим: Екран.стан.режим, прогін: П?.прогін ?? null, ситуація: typeof ситуаціяЯдраП === 'function' ? ситуаціяЯдраП() : null,
        паспорт: ПАСПОРТ_П ?? null, статус: document.getElementById('зб-статус')?.innerText ?? null,
        чат: ЧАТ_П.map(({хто, текст}) => ({хто, текст})), вироки: ЗБ?.ядро?.звіт ?? [],
        картки: (П?.картки ?? []).map(к => ({рука: к.рука, речі: к.речі, опис: к.опис,
          дія: к.дія_для_вибору ?? null, вирок: к.ядро?.вирок ?? к.вердикт ?? null, заміни: к.етапи?.заміни ?? []}))
      }));
      const руки = await знімокРук(стор);
      додати('руки.jsonl', {крок: позиція, що, знімок, ...(руки || {}), ...стан});
      хід('\n- ' + що + ' [' + знімок + '](' + знімок + ')');
      return стан;
    }

    async function сказати(слова){
      const поле = стор.locator('#чат-поле');
      if (пара){
        if (await стор.locator('#pair-handle').getAttribute('aria-expanded') !== 'true') await натиснути('#pair-handle');
      } else if (!await поле.isVisible()) await натиснути('#ші-пілюля');
      await поле.fill(слова);
      const до = await стор.evaluate(() => ЧАТ_П.length);
      репліка = {номер: лічба.репліки.length + 1, слова, викликів: 0};
      лічба.репліки.push(репліка);
      await натиснути('#чат-слати');
      const стан = await чекати(до => ЧАТ_П.length >= до + 2 && ЧАТ_П.at(-1).хто === 'ші' &&
        !document.getElementById('чат-поле').disabled, до);
      await стан.dispose();
      репліка = null;
      await кадр('Надіслати «' + слова + '»');
      if (пара && await стор.locator('#pair-handle').getAttribute('aria-expanded') === 'true')
        await натиснути('#pair-handle');
    }

    async function полеСценарію(тип, селектор, назва){
      if (пара){
        const умови = стор.locator('.pair-conditions');
        if (await умови.getAttribute('open') === null) await натиснути('.pair-conditions > summary');
        await натиснути(діяПари('pair-edit', тип));
      } else await натиснути('[data-редактор="ред-' + тип + '"]');
      await стор.locator(селектор).selectOption({label: назва}, {timeout: 15000});
      await натиснути('#аркуш-готово');
      await кадр('Обрано «' + назва + '»');
    }

    async function збір(кнопка, під_час = null){
      const попередній = await стор.evaluate(() => П?.прогін ?? null);
      початокЗбору ??= Date.now();
      const зараз = Date.now();
      const перша = стор.waitForFunction(попередній => {
        const картки = [...document.querySelectorAll('#картки .картка, #mirror-look-sides .pair-outfit')];
        return П?.прогін !== попередній && картки.some(к => к.getClientRects().length) ? Date.now() : null;
      }, попередній, {timeout: таймаут});
      // Під час збирання на очікування першої картки не блокуємо наступний дотик.
      перша.catch(() => {});
      await стор.locator(кнопка).first().click({timeout: 15000, noWaitAfter: true});
      if (під_час){
        await чекати(() => ЗБИРАННЯ_ЗАЙНЯТО_П);
        if (!пара) await натиснути('#знак');
        if (!await стор.evaluate(() => ЗБИРАННЯ_ЗАЙНЯТО_П)) throw Error('старий збір уже скінчився до зміни ситуації');
        await сказати(під_час);
        await чекати(() => !ЗБИРАННЯ_ЗАЙНЯТО_П);
        await кадр('Старий збір закінчився після зміни сценарію');
        if (await стор.locator(кнопкаЗбору).first().isVisible()) await стор.locator(кнопкаЗбору).first().click();
      }
      const першаКартка = await (await перша).jsonValue();
      await чекати(попередній => П?.прогін !== попередній && ЗБ?.готово && !ЗБИРАННЯ_ЗАЙНЯТО_П, попередній);
      лічба.до_першої_картки_с ??= (першаКартка - зараз) / 1000;
      лічба.до_карток_с ??= (Date.now() - зараз) / 1000;
      await післяЗбору();
      await доЗавантажитиФото(стор);
      await кадр('Образи після збирання');
      if (план.шлях === 'ядро'){
        if (пара) await стор.evaluate(() => MirrorRoom.pair.handlers['pair-test']());
        const карток = await стор.evaluate(() => П?.картки?.length ?? 0);
        for (let п = 0; п < карток; п++){
          await показатиКартку(п);
          await кадр('Картка ' + (п + 1));
        }
        if (карток) await показатиКартку(0);
      }
    }

    async function дія(рядок){
      const межа = рядок.indexOf(':');
      const ім = межа < 0 ? рядок : рядок.slice(0, межа);
      const слова = межа < 0 ? null : рядок.slice(межа + 1);
      switch (ім){
        case 'репліка':
          return сказати(слова);
        case 'офіс':
          return полеСценарію('місце', '#сц-місце', 'Офіс');
        case 'прохолодно':
          return полеСценарію('коли', '#сц-смуга', 'Прохолодно');
        case 'тріада':
          await натиснути(пара ? діяПари('pair-palette') : '#пал-кнопка');
          await стор.locator('#пал-схема .чип', {hasText: 'тріад'}).first().click({timeout: 600000});
          await кадр('Обрано схему «тріада»');
          await натиснути(пара ? діяПари('pair-summary') : '#пал-назад');
          return;
        case 'зібрати_ще':
          return збір('#зб-пуск');
        case 'коментар':
          await натиснути('#к-0 .чип[data-з="вдягну, якщо змінити одну річ"]');
          await стор.locator('#ком-0').fill(слова);
          await натиснути('#зап-0');
          await чекати(() => відповідь(0).записано && !відповідь(0).пише);
          return кадр('Записано коментар «' + слова + '»');
        case 'замінити_перший_прохід': {
          if (план.прохід !== 1) return;
          const до = await стор.evaluate(() => П.картки[0]?.етапи?.заміни?.length ?? 0);
          await стор.locator('#к-0 button.замін:not(.вибр)').first().click({timeout: 15000});
          await чекати(до => {
            const к = П.картки[0], з = к.етапи?.заміни || [];
            return з.length > до && !!з.at(-1).закінчено && !ЗАМІНИ_П.has(к);
          }, до);
          return кадр('Замінити біля однієї речі першої картки');
        }
        default:
          throw Error('Невідома дія: ' + ім);
      }
    }

    try {
      await кадр('Профіль готовий, сценарій порожній');
      await сказати(план.слова);
      let зміна = null;
      for (const крок of план.до){
        if (крок.startsWith('змінити_під_час_збирання:')) зміна = крок.slice(крок.indexOf(':') + 1);
        else await дія(крок);
      }
      if (план.номер === 'с7' && process.env.N6_NO_PORTRAIT === '1'){
        await стор.evaluate(async () => {
          const ключ = 'профіль:' + АКТИВНИЙ;
          await прибратиФотоП('портрет');
          const профіль = await читатиКв_(ключ);
          await писатиКв(ключ, {...профіль, колір: null});
          await читатиАктивний();
        });
        await кадр('У профілі випробування прибрано портрет і дані його кольорів після тапу');
      }
      await передЗбором();
      await збір(кнопкаЗбору, зміна);
      if (план.шлях === 'ядро'){
        for (const крок of план.після){
          await дія(крок);
          await чекати(() => !ЗБИРАННЯ_ЗАЙНЯТО_П && (П?.картки ?? []).every(к => !ЗАМІНИ_П.has(к)));
        }
      }
      await кадр('Кінець ходу');
      лічба.закінчено = true;
    } catch (помилка){
      лічба.збій = String(помилка);
      throw помилка;
    } finally {
      лічба.викликів = обмінів;
      лічба.до_кінця_с = початокЗбору === null ? null : (Date.now() - початокЗбору) / 1000;
      записати('числа.json', лічба);
      try {
        const вироки = await стор.evaluate(async () => ({
          відгуки: await усіВердикти(), ядро: ЗБ?.ядро?.звіт ?? [],
          картки: (П?.картки ?? []).map(к => ({рука: к.рука, вирок: к.ядро?.вирок ?? к.вердикт ?? null,
            заміни: к.етапи?.заміни ?? [], діагноз: к.етапи?.діагноз_прогону ?? []}))
        }));
        записати('вироки.json', вироки);
      } catch (помилка){
        записати('вироки.json', {збій: String(помилка)});
        if (лічба.закінчено) throw помилка;
      }
    }
  }
  return {початиОбмін, профіль, пройти};
}

module.exports = {записН6};
