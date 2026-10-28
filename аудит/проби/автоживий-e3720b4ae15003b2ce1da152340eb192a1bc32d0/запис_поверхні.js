/* Додатковий читач стану незміненого стенда. Входів і відповідей моделей не змінює. */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const launch = chromium.launch.bind(chromium);
chromium.launch = async (...args) => {
  const browser = await launch(...args), close = browser.close.bind(browser);
  const records = []; let previous = '', reading = false;
  async function capture() {
    if (reading) return;
    reading = true;
    try {
      for (const context of browser.contexts()) for (const page of context.pages()) {
        const state = await page.evaluate(() => {
          const item = x => ({ід: x.ід, назва: x.назва, слот: x.слот,
            колір: x.колір, рамка: x.рамка, вимір: x.вимір, вердикт: x.вердикт,
            колір_не_вимір: x.колір_не_вимір});
          return {режим: typeof РЕЖИМ === 'undefined' ? null : РЕЖИМ,
            речі: typeof ПАСПОРТ_П === 'undefined' ? [] : (ПАСПОРТ_П?.речі_з_фото || []).map(item),
            оцінка: typeof ОЦ === 'undefined' ? [] : (ОЦ.речі || []).map(item),
            репліки: [...document.querySelectorAll('#чат-стрічка .репліка')].map(x => x.textContent),
            картки: [...document.querySelectorAll('#картки .картка')].map(x => x.textContent)};
        });
        const value = JSON.stringify(state);
        if (value !== previous) {
          previous = value; records.push({час_utc: new Date().toISOString(), ...state});
          fs.writeFileSync(path.join(process.env.ZNIMKY, 'поверхня_стани.json'), JSON.stringify(records, null, 2));
        }
      }
    } catch (e) {
      if (!/closed|destroyed|navigation|Execution context/.test(String(e)))
        console.log('Додатковий запис поверхні: ' + e.message);
    } finally { reading = false; }
  }
  const timer = setInterval(capture, 2000); timer.unref();
  browser.close = async (...params) => {
    clearInterval(timer); await capture();
    return close(...params);
  };
  return browser;
};
const target = process.argv.splice(2, 1)[0];
require(target);
