/* Записані хід і репліка обох сцен через справжній ендпойнт і функції показу. */
const fs = require('fs'), path = require('path'), vm = require('vm'), {spawnSync} = require('child_process');
const root = path.resolve(__dirname, '../..'), src = process.env.E2_SOURCES || path.join(root, 'джерела');
const scenes = JSON.parse(fs.readFileSync(path.join(root, 'аудит/проби/Е2-ремонт-шар/записи.json'), 'utf8'));
async function main(){
  let failed = 0;
  for (const scene of scenes){
    const prompts = [], calls = [];
    const bridge = async (_, data) => {
      calls.push(data);
      const r = spawnSync(process.env.PYTHON || 'python', ['-X', 'utf8', '-c',
        'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as М;print(М.мова(sys.stdin.read()))', src],
        {input: JSON.stringify(data), encoding:'utf8', maxBuffer: 4000000});
      if (r.status) throw Error(r.stderr);
      return JSON.parse(r.stdout);
    };
    const c = vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П:'запис', ПАСПОРТ_П:null, ЧАТ_П:[],
      містП:bridge, вхідМостаП:()=>({сценарій:{}}), текстРепліки:р=>р.текст});
    vm.runInContext(fs.readFileSync(path.join(src,'показ/мовний_шар.js'),'utf8'), c);
    let answer = Object.entries(scene.відповіді).find(([k])=>k.includes('seed3_01_'))[1].відповідь;
    c.модельМовиП = async prompt => {prompts.push(prompt);
      if(prompt.includes('РЕПЛІКА:\n')) JSON.parse(prompt.slice(prompt.lastIndexOf('РЕПЛІКА:')+8)); return answer;};
    c.латинкаЧатуП = async t => t;
    const turn = await c.ходомРозмовиП(scene.слова, [], 'chat');
    const p = await bridge('мова', {паспорт_з:turn.внутрішня, сценарій:{}, слова_розмови:[scene.слова], частини:turn.частини});
    c.ПАСПОРТ_П = p.паспорт;
    answer = Object.entries(scene.відповіді).find(([k])=>k.includes('seed3_02_'))[1].відповідь;
    const reply = await c.реплікоюП({recorded:p.записано, required:p.обовʼязкове}, 'chat', p.запрошення);
    const known = prompts.some(s=>s.includes('"passport"') && s.includes('"advice"') && s.includes('"code_data"'));
    const ok = known && !!p.запрошення && reply.текст.includes(p.запрошення);
    console.log(JSON.stringify({сцена:scene.сцена, повторів:turn.запис.повтор?1:0, контекст:known,
      подія:p.паспорт.подія, місце:p.паспорт.місце, порада:p.запрошення, теми:p.теми_поради, репліка:reply.текст, пройдено:ok}));
    failed += !ok;
  }
  process.exitCode = failed ? 1 : 0;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
