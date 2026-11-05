/* Повторює записані відповіді Е3 через JS шару та справжній Python-суд злиття.
   Запуск із кореня; аргумент — SHA джерела ДО або поточний робочий код. Без мережі й моделі. */
const fs = require('fs');
const path = require('path');
const vm = require('vm');
const {execFileSync} = require('child_process');
const корінь = process.cwd();
const файл = 'джерела/показ/мовний_шар.js';
const код = process.argv[2]
  ? execFileSync('git', ['show', process.argv[2] + ':' + файл], {encoding: 'utf8'})
  : fs.readFileSync(файл, 'utf8');
const тека = 'аудит/проби/б1/ПІСЛЯ-Е3';
const сцени = fs.readdirSync(тека).filter(с => /^(01|03|08|15|21|22)_/.test(с));
const результати = [];
(async () => {
  for (const сцена of сцени){
    const дані = JSON.parse(fs.readFileSync(path.join(тека, сцена, 'вердикти.txt'), 'utf8'));
    for (const прогін of дані.прогони){
      for (const в of прогін.вердикти.filter(в => ['1', '2'].includes(в.рука))){
        const записи = (в.мова_шару || []).filter(з => Object.keys(з.вхід || {}).some(к => /^свідомі\./.test(к)));
        if (!записи.length) continue;
        let розмітка = [], переклад = {};
        const контекст = vm.createContext({console, setTimeout, clearTimeout,
          ЧАТ_П: [], П: {картки: []}, ОЦ: null, МОДЕЛЬ_МОВИ_П: 'запис-Е3',
          містП: async (_ім, д) => {
            const р = JSON.parse(execFileSync('python', ['-c',
              'import sys,мовний_шар; print(мовний_шар.мова(sys.stdin.read()))'], {
              cwd: path.join(корінь, 'джерела'), input: JSON.stringify(д), encoding: 'utf8',
              env: {...process.env, PYTHONUTF8: '1', PYTHONIOENCODING: 'utf-8'},
            }));
            if (д.тексти) розмітка = р.розмітка;
            return р;
          },
          модель: () => JSON.stringify(Object.fromEntries(розмітка.map(р => [р.н, переклад[р.ключ] || '']))),
        });
        vm.runInContext(код, контекст);
        vm.runInContext('модельМовиП = async () => модель();', контекст);
        контекст.картка = {речі: в.речі_образу || []};
        const відповіді = [];
        for (const з of записи){
          контекст.вхід = з.вхід;
          переклад = з.вихід;
          відповіді.push(await vm.runInContext("мовоюП(вхід, 'запис-Е3', undefined, речіШаруП(картка), undefined, undefined, true)", контекст));
        }
        контекст.відповіді = відповіді;
        const разом = await vm.runInContext('злитиВідповідіШаруП(відповіді)', контекст);
        for (const [ключ, текст] of Object.entries(разом.тексти || {})){
          if (!/^свідомі\./.test(ключ)) continue;
          результати.push({сцена, рука: в.рука, ключ, текст,
            без_тексту: текст === '— без тексту',
            шаблон: текст === vm.runInContext('НАПИС_БЕЗ_ШАРУ_П.card_without_description', контекст)});
        }
      }
    }
  }
  console.log(JSON.stringify({джерело: process.argv[2] || 'робочий код',
    ходів: результати.length, без_тексту: результати.filter(р => р.без_тексту).length,
    шаблонів: результати.filter(р => р.шаблон).length, результати}, null, 2));
})().catch(п => {console.error(п); process.exitCode = 1;});
