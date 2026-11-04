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
        const scenario = async () => {
          await page.evaluate(() => режим('сценарій'));
          await page.waitForSelector('#зб-зібрати', {state: 'visible'});
        };
        page.click = async function (selector, ...args) {
          if (selector === '#зб-зібрати' && !done) {
            done = true;
            const results = [];
            try {
              for (const field of ['каблук_см', 'сезон_тканини']) {
                const passport = await page.evaluate(() => ПАСПОРТ_П);
                if (field === 'каблук_см' && !(passport.вето?.типи || []).includes('підбори')) {
                  results.push({поле: field, пропущено: 'у фактичному паспорті немає вето підборів', паспорт: passport});
                  console.log('Ж7: підбори не перевірено — немає вето у фактичному паспорті');
                  continue;
                }
                const mutation = await page.evaluate(async field => JSON.parse(await приладМостуП({}, `
import json, copy, фід_каталог as Ф, profile as П, пакет_моделі as М, bridge as Б
_живий_поле = ${JSON.stringify(field)}
_живий_п = json.loads(${JSON.stringify(JSON.stringify(ПАСПОРТ_П))})
_живий_вхід = json.loads(${JSON.stringify(JSON.stringify(вхідМостаП()))})
_живий_шлях, _живий_кеш = Ф.каталог_із(_живий_вхід)
Ф.база_прогону(_живий_шлях, int(_живий_вхід.get('ліміт_фото') or 0), _живий_кеш)
_живий_каталог = [c for v in Ф.КЕШ_БАЗИ.values() for c in v[1]['каталог']]
_живий_річ = None
_живий_маркер = 'sensory_limit_unreadable' if _живий_поле == 'каблук_см' else 'fabric_band_unreadable'
for _живий_к in _живий_каталог:
    if _живий_к.get('слот') != ('взуття' if _живий_поле == 'каблук_см' else 'верх'):
        continue
    _живий_проба = dict(_живий_к)
    _живий_проба[_живий_поле] = 'бите' if _живий_поле == 'каблук_см' else ['бите', 25]
    try:
        М.жорстке_відсічення(_живий_проба, темп_c=_живий_п.get('темп_c'), вето=_живий_п.get('вето'))
    except ValueError as _живий_збій:
        if _живий_маркер in str(_живий_збій):
            _живий_річ = _живий_к
            break
if _живий_річ is None:
    raise ValueError('не знайдено речі, на якій бите поле читається раніше за інші відсічення')
_живий_до = copy.deepcopy(_живий_річ)
_живий_річ[_живий_поле] = 'бите' if _живий_поле == 'каблук_см' else ['бите', 25]
Б._КЕШ_ПАКЕТА.clear()
_живий_вето = П.сенсорний_збіг('підбори', dict(_живий_річ, тип='човники', каблук_см='бите')) if _живий_поле == 'каблук_см' else None
_живий_вето_пул = М.жорстке_відсічення(dict(_живий_річ, тип='човники', каблук_см='бите'), вето={'типи': ['підбори']}) if _живий_поле == 'каблук_см' else None
json.dumps({'поле': _живий_поле, 'id': _живий_річ.get('id'), 'до': _живий_до.get(_живий_поле), 'після': _живий_річ[_живий_поле], 'інший_доказ_вето': _живий_вето, 'інший_доказ_відсічення': _живий_вето_пул, 'речей_каталогу': len(_живий_каталог)}, ensure_ascii=False)
`)), field);
                mutation.паспорт = await page.evaluate(() => ПАСПОРТ_П);
                console.log('Ж7: пошкоджено дані ' + JSON.stringify(mutation));
                await scenario();
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
              await scenario();
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
