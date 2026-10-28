const fs=require('fs'),path=require('path'),vm=require('vm'),{spawnSync}=require('child_process');
const src=process.argv[2] || path.resolve(__dirname,'../../../джерела');
const c=vm.createContext({Date,console,МОДЕЛЬ_МОВИ_П:'запис',ПАСПОРТ_П:null,ЧАТ_П:[],
  вхідМостаП:()=>({сценарій:{}})});
c.містП=async (_,d)=>{
  const r=spawnSync('python',['-X','utf8','-c',
    'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as M;print(M.мова(sys.stdin.read()))',src],
    {input:JSON.stringify(d),encoding:'utf8',maxBuffer:4000000});
  if(r.status)throw Error(r.stderr); return JSON.parse(r.stdout);
};
vm.runInContext(fs.readFileSync(path.join(src,'показ/мовний_шар.js'),'utf8'),c);
async function main(){
  const results=[];
  for(const [name,words,bad,good,scenario] of [
    ['плитки: невідомий ключ','',{update:{formality:'neat',part_of_dai:'evening'}},
      {update:{formality:'neat',part_of_day:'evening'}},{нагода:'театр',година:19}],
    ['список: виправлення другого коду','Класично й мінімалістично',
      {update:{registers:{quote:'класично й мінімалістично',value:['classic','minimalist']}},need:'build',text:'Записала стиль.'},
      {update:{registers:{quote:'класично й мінімалістично',value:['classic','minimalism']}},need:'build',text:'Записала стиль.'},{}],
  ]){
    let calls=0; const prompts=[];
    c.вхідМостаП=()=>({сценарій:scenario});
    c.модельМовиП=async p=>{prompts.push(p);return JSON.stringify(++calls===1?bad:good);};
    const r=await c.ходомРозмовиП(words,[],'chat');
    const control=await c.містП('мова',{розмова:{нове:words},сценарій:scenario,відповідь_моделі:JSON.stringify(good)});
    const item={випадок:name,викликів:calls,перша:bad,друга:good,внутрішня:r.внутрішня,контроль_виправленої:control.внутрішня,запис:r.запис};
    results.push(item); console.log(JSON.stringify(item));
  }
}
main().catch(e=>{console.error(e);process.exitCode=1;});
