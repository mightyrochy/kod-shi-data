/* Відмова моделі на повторі після відхилення першого перекладу. */
const fs = require('fs'), path = require('path'), vm = require('vm'), {spawnSync} = require('child_process');
const root = process.argv[2];
const sources = path.join(root, 'джерела');
async function check(mode) {
  const context = vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П: 'запис', ПАСПОРТ_П: null, ЧАТ_П: []});
  context.містП = async (name, data) => {
    const p = spawnSync('python', ['-X','utf8','-c',
      'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as М;print(М.мова(sys.stdin.read()))',sources],
      {input:JSON.stringify(data),encoding:'utf8',maxBuffer:4000000});
    if(p.status) throw Error(p.stderr);
    return JSON.parse(p.stdout);
  };
  vm.runInContext(fs.readFileSync(path.join(sources,'показ/мовний_шар.js'),'utf8'),context);
  let calls = 0;
  context.модельМовиП = async prompt => {
    calls++;
    if (calls === 2) throw Error('контрольована відмова моделі');
    const statements = JSON.parse(prompt.split('\nПОВІДОМЛЕННЯ:\n')[1]);
    return JSON.stringify(Object.fromEntries(statements.map(s=>[s.key,
      mode==='foreign' ? 'This dress suits you.' : 'Ця сукня тобі пасує dress.'])));
  };
  const input = {рядок:{kind:'card_occasion',statements:[{
    code:'mourning_colour_word_only',item_ids:['а'],choice:'her',recipient:'woman',source:'catalogue',
    rank:{position:1,rare:false},values:{item:{free_text:'Сукня',lang:'uk'}}
  }]}};
  const result = await context.повідомленнямП(input,'проба');
  const firstCalls = calls;
  const again = await context.повідомленнямП(input,'проба');
  console.log(JSON.stringify({mode,root,calls:firstCalls,cached_calls:calls-firstCalls,cached_text:again.тексти.рядок,text:result.тексти.рядок,
    statements:result.заяви.map(s=>({state:s.стан,text:s.текст})),
    records:result.записи.map(r=>({reason:r.причина,rejected:r.чужою}))}));
}
(async()=>{await check('foreign');await check('latin');})().catch(e=>{console.error(e);process.exitCode=1});
