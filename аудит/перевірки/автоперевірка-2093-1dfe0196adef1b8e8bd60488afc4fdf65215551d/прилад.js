const fs=require('fs'),path=require('path'),vm=require('vm'),{spawnSync}=require('child_process');
const repo=process.argv[2],src=path.join(repo,'джерела');
const newer=require(path.join(repo,'аудит/проби/записи_шару.js'));
const oldSource=spawnSync('git',['show','bd628bb29a90637ae18833c92eceb8230bd9b995:аудит/проби/записи_шару.js'],{cwd:repo,encoding:'utf8'});
if(oldSource.status)throw Error(oldSource.stderr);
const oldModule={exports:{}};vm.runInNewContext(oldSource.stdout,{module:oldModule});
const message=i=>({kind:'card_unchecked',statements:[{code:'scarf_size_unknown',values:{item:{free_text:'Шарф',lang:'uk'},item_id:i}}]});
function context(){
  const c=vm.createContext({console,Date,МОДЕЛЬ_МОВИ_П:'контроль',безМашинногоСліду:t=>t});
  c.містП=async (_,d)=>{
    const r=spawnSync('python',['-X','utf8','-c','import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as M;print(M.мова(sys.stdin.read()))',src],
      {input:JSON.stringify(d),encoding:'utf8',maxBuffer:4000000});
    if(r.status)throw Error(r.stderr);return JSON.parse(r.stdout);
  };
  vm.runInContext(fs.readFileSync(path.join(src,'показ/мовний_шар.js'),'utf8'),c);return c;
}
(async()=>{
  const results=[];
  for(const name of ['українські відповіді','чужомовний текст','немає відповіді на друге','порожня відповідь на друге']){
    const c=context();let calls=0,firstKey;
    c.модельМовиП=async p=>{calls++;const rows=JSON.parse(p.split('ПОВІДОМЛЕННЯ:\n')[1]);
      if(calls===1)firstKey=rows[0].key;
      if(calls>1 && (name.startsWith('немає')||name.startsWith('порожня')))return '{}';
      return JSON.stringify(Object.fromEntries(rows.filter(r=>!name.startsWith('немає')||r.key===firstKey).map(r=>
        [r.key,name.startsWith('порожня')&&r.key!==firstKey?'':name.startsWith('чужомовний')?'The scarf size is unknown.':'Розміру цього шарфа я не знаю.'])));};
    const r=await c.повідомленнямП({'питання.0':message('а'),'питання.1':message('б')},'hand_1.code_unknowns');
    const item={випадок:name,викликів:calls,старий:oldModule.exports.питаньЗВідповіддю(r.записи),
      доставка:newer.питаньЗВідповіддю(r.записи,false),переклад:newer.питаньЗВідповіддю(r.записи),записи:r.записи};
    results.push(item); console.log(JSON.stringify({...item,записи:undefined}));
  }
})().catch(e=>{console.error(e);process.exitCode=1;});
