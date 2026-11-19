/* Обгортка перевірки (не код продукту): той самий рв6_стенд.js, плюс знімок 390×844 у мить,
   коли ЗБ.картки вже має картку руки 1, а ЗБ.готово ще false (руки 2–4 ще йдуть). */
const pw = require('playwright');
const ВИХІД = process.env.RUKA1_ZNIMOK;
const ориг = pw.chromium.launch.bind(pw.chromium);
pw.chromium.launch = async (...а) => {
  const б = await ориг(...а);
  const nc = б.newContext.bind(б);
  б.newContext = async (...к) => {
    const кн = await nc(...к);
    const np = кн.newPage.bind(кн);
    кн.newPage = async (...п) => {
      const с = await np(...п);
      (async () => {
        try {
          await с.waitForFunction(() => typeof ЗБ !== 'undefined' && ЗБ && Array.isArray(ЗБ.картки)
            && ЗБ.картки.some(к => к && String(к.рука) === '1') && !ЗБ.готово, null, {timeout: 1200000, polling: 100});
          const мить = await с.evaluate(() => ({
            мс_від_почато: Date.now() - ЗБ.почато, готові_мс: ЗБ.готові_мс, готово: ЗБ.готово,
            руки_готові: ЗБ.картки.map(к => к ? String(к.рука) : null),
            режим: (window.Екран && Екран.стан) ? Екран.стан.режим : null,
            П_карток: (typeof П !== 'undefined' && П && П.картки) ? П.картки.map(к => String(к.рука)) : null,
            П_прогін: (typeof П !== 'undefined' && П) ? П.прогін : null}));
          await new Promise(р => setTimeout(р, 600));
          const було = с.viewportSize();
          await с.setViewportSize({width: 390, height: 844});
          await new Promise(р => setTimeout(р, 400));
          await с.screenshot({path: ВИХІД});
          const після = await с.evaluate(() => ({режим: (window.Екран && Екран.стан) ? Екран.стан.режим : null,
            готово: ЗБ.готово, руки_готові: ЗБ.картки.map(к => к ? String(к.рука) : null),
            текст: document.body.innerText.slice(0, 1500)}));
          if (було) await с.setViewportSize(було);
          console.log('ПЕРЕВІРКА: мить руки 1 ' + JSON.stringify(мить));
          console.log('ПЕРЕВІРКА: на знімку ' + JSON.stringify(після));
          if (process.env.DIYA === '2'){
            /* вона відкриває свій щойно показаний образ з «Усіх образів» тією ж дією плитки, поки йдуть руки 2–4 */
            const відкр = await с.evaluate(async () => { await оновитиБібліотеку(); const пр = String(П.прогін);
              const н = БІБЛІОТЕКА_П.плитки.findIndex(пл => String(пл.ід).startsWith(пр + '#'));
              return {н, плиток_прогону: БІБЛІОТЕКА_П.плитки.filter(пл => String(пл.ід).startsWith(пр + '#')).length,
                      відкрито: н >= 0 ? відкритиОбразБібліотекиП(н) : null, готово: ЗБ.готово, пр}; });
            console.log('ПЕРЕВІРКА: відкрила свій образ з бібліотеки ' + JSON.stringify(відкр));
            await с.waitForFunction(() => ЗБ && ЗБ.готово, null, {timeout: 1200000, polling: 200});
            await new Promise(р => setTimeout(р, 2000));
            const кін = await с.evaluate(async (пр) => { await оновитиБібліотеку();
              return {готово: ЗБ.готово, успіх: ЗБ.успіх, П_прогін: П.прогін, П_карток: П.картки.map(к => String(к.рука)),
                      ЗБ_карток: ЗБ.картки.map(к => к ? String(к.рука) : null),
                      плиток_прогону: БІБЛІОТЕКА_П.плитки.filter(пл => String(пл.ід).startsWith(пр + '#')).length,
                      діагноз: ЗБ.діагноз.filter(д => /late_hands|early/.test(д))}; }, відкр.пр);
            console.log('ПЕРЕВІРКА: після кінця рук ' + JSON.stringify(кін));
            if (було) await с.setViewportSize(було);
          }
          if (process.env.DIYA === '1'){
            /* дія жінки на картці руки 1 до кінця рук 2–4: вердикт дотиком і слова в полі */
            await с.setViewportSize({width: 390, height: 844});
            await с.getByText('вдягну як є', {exact: true}).first().click({timeout: 10000});
            await с.locator('textarea[placeholder^="Наприклад"]').first().fill('слова перевірки до кінця рук', {timeout: 10000});
            await с.evaluate(() => window.scrollTo(0, 900));
            const до = await с.evaluate(() => ({готово: ЗБ.готово, В0: JSON.stringify(В[0] || null).slice(0, 300), scrollY,
              вибр: [...document.querySelectorAll('.вибр, [aria-pressed="true"], [aria-checked="true"]')].map(е => е.textContent.trim()).slice(0, 8),
              поле: (document.querySelector('textarea[placeholder^="Наприклад"]') || {}).value}));
            console.log('ПЕРЕВІРКА: дія до кінця рук ' + JSON.stringify(до));
            await с.screenshot({path: ВИХІД.replace('.png', '_дія.png')});
            await с.waitForFunction(() => ЗБ && ЗБ.готово, null, {timeout: 1200000, polling: 200});
            await new Promise(р => setTimeout(р, 1500));
            const після2 = await с.evaluate(() => ({готово: ЗБ.готово, режим: Екран.стан.режим, В0: JSON.stringify(В[0] || null).slice(0, 300), scrollY,
              вибр: [...document.querySelectorAll('.вибр, [aria-pressed="true"], [aria-checked="true"]')].map(е => е.textContent.trim()).slice(0, 8),
              поле: (document.querySelector('textarea[placeholder^="Наприклад"]') || {}).value,
              П_карток: П.картки.map(к => String(к.рука))}));
            console.log('ПЕРЕВІРКА: після кінця рук ' + JSON.stringify(після2));
            await с.screenshot({path: ВИХІД.replace('.png', '_після_кінця.png')});
            if (було) await с.setViewportSize(було);
          }
        } catch (е) { console.log('ПЕРЕВІРКА: знімок руки 1 не вдався: ' + String(е).slice(0, 200)); }
      })();
      return с;
    };
    return кн;
  };
  return б;
};
const стенд = process.argv[2];
process.argv.splice(2, 1);
require(стенд);
