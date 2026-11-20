/* Незалежна проба шляху збою оцінки фото (`збійОцінкиП`) на голові PR #4407 при HTTP 402 credits_exhausted. */
const fs = require('fs'), path = require('path'), vm = require('vm');
const root = path.resolve(process.argv[2]), src = path.join(root, 'джерела');
const shown = [];
const context = vm.createContext({console,
  показатиСтанФотоОцінки: (місце, код, вид) => shown.push({місце, код, вид: вид || null}),
  записатиЗбійОцінкиП: async () => {},
  повідомленнямП: async () => ({тексти: {}, записи: []}),
});
vm.runInContext(fs.readFileSync(path.join(src, 'показ', 'мовний_шар.js'), 'utf8'), context);
vm.runInContext(fs.readFileSync(path.join(src, 'показ', 'оцінка.js'), 'utf8'), context);
(async () => {
  vm.runInContext('ОЦ.етапи = {мова_шару: []}', context);
  const err = new Error('model · http=402 · body={"error":{"type":"credits_exhausted","message":"кредити скінчились"}}');
  await vm.runInContext('збійОцінкиП(err)', Object.assign(context, {err}));
  console.log(JSON.stringify({
    спільний_розпізнавач: vm.runInContext('кредитиСкінчилисьП(err)', context),
    стан_оцінки: shown,
    текст_на_екрані_оцінки: vm.runInContext('НАПИС_ЗБОЮ_ОЦІНКИ_П', context),
    очікуваний_шаблон_кредитів: vm.runInContext('ШАБЛОНИ_ЗБОЮ_П.credits_exhausted', context),
    журнал_збоїв_жінці: vm.runInContext('ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П', context)
  }, null, 2));
})().catch(e => {console.error(e); process.exitCode = 1;});
