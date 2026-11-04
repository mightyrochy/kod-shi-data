/* Прилад сцени ж7: псує лише дані в пам'яті воркера, натискає справжню кнопку,
   записує видиму відмову й відновлює дані перед звичайним проходом стенда. */
const Module = require('module'), fs = require('fs'), path = require('path');
const load = Module._load, seen = new WeakSet();
const out = process.env.VIDPOVIDI && path.dirname(process.env.VIDPOVIDI);
Module._load = function (...args) {
  const result = load.apply(this, args), chromium = result && result.chromium;
  if (!chromium || seen.has(chromium) || process.env.SCENA !== 'ж7_збій_правил_без_підборів') return result;
  seen.add(chromium);
  const launch = chromium.launch.bind(chromium);
  chromium.launch = async function (...args) {
    const browser = await launch(...args), newContext = browser.newContext.bind(browser);
    browser.newContext = async function (...args) {
      const context = await newContext(...args), newPage = context.newPage.bind(context);
      context.newPage = async function (...args) {
        const page = await newPage(...args), click = page.click.bind(page);
        let done = false;
        page.click = async function (selector, ...args) {
          if (selector === '#зб-зібрати' && !done) {
            done = true;
            const results = [];
            try {
              for (const field of ['каблук_см', 'сезон_тканини']) {
                const mutation = await page.evaluate(async field => JSON.parse(await приладМостуП({}, `
import json, copy, фід_каталог as Ф, profile as П, пакет_моделі as М, bridge as Б
_живий_поле = ${JSON.stringify(field)}
_живий_каталог = [c for v in Ф.КЕШ_БАЗИ.values() for c in v[1]['каталог']]
if _живий_поле == 'каблук_см':
    _живий_річ = next(c for c in _живий_каталог if c.get('слот') == 'взуття' and not c.get('каблук') and not c.get('каблук_є') and not П._каблук_за_типом(c))
else:
    _живий_річ = next(c for c in _живий_каталог if c.get('слот') == 'верх')
_живий_до = copy.deepcopy(_живий_річ)
_живий_річ[_живий_поле] = 'бите' if _живий_поле == 'каблук_см' else ['бите', 25]
Б._КЕШ_ПАКЕТА.clear()
_живий_вето = П.сенсорний_збіг('підбори', dict(_живий_річ, тип='човники', каблук_см='бите')) if _живий_поле == 'каблук_см' else None
json.dumps({'поле': _живий_поле, 'id': _живий_річ.get('id'), 'до': _живий_до.get(_живий_поле), 'після': _живий_річ[_живий_поле], 'інший_доказ_вето': _живий_вето}, ensure_ascii=False)
`)), field);
                mutation.паспорт = await page.evaluate(() => ПАСПОРТ_П);
                console.log('Ж7: пошкоджено дані ' + JSON.stringify(mutation));
                await click(selector, ...args);
                await page.waitForFunction(() => ЗБ && (ЗБ.готово || ЗБ.діагноз.some(x => x.startsWith('build · failed:'))) && !document.getElementById('зб-зібрати').disabled, null, {timeout: 600000});
                const visible = await page.evaluate(() => ({режим: РЕЖИМ, статус: document.getElementById('зб-статус').textContent,
                  діагноз: ЗБ.діагноз, карток: ЗБ.картки.length, готово: ЗБ.готово, успіх: ЗБ.успіх}));
                visible.очікуваний_збій = visible.діагноз.some(x => x.includes(field === 'каблук_см' ? 'sensory_limit_unreadable' : 'fabric_band_unreadable'));
                await page.screenshot({path: path.join(out, 'збій_' + field + '.png'), fullPage: true});
                results.push({...mutation, ...visible});
                await page.evaluate(async () => приладМостуП({}, "_живий_річ.clear()\n_живий_річ.update(_живий_до)\nБ._КЕШ_ПАКЕТА.clear()\n'відновлено'"));
                console.log('Ж7: результат ' + JSON.stringify({поле: field, очікуваний_збій: visible.очікуваний_збій, статус: visible.статус}));
              }
            } catch (error) {
              results.push({помилка_приладу: String(error.stack || error)});
              console.log('Ж7: пошкодження не перевірено: ' + String(error.message || error));
            } finally {
              fs.writeFileSync(path.join(out, 'пошкоджені_поля.json'), JSON.stringify(results, null, 2));
              await page.evaluate(async () => приладМостуП({}, "if '_живий_до' in globals():\n    _живий_річ.clear()\n    _живий_річ.update(_живий_до)\n    Б._КЕШ_ПАКЕТА.clear()\n'відновлено'"));
            }
          }
          return click(selector, ...args);
        };
        return page;
      };
      return context;
    };
    return browser;
  };
  return result;
};
