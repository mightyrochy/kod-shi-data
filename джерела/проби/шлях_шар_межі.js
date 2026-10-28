/* Вимір єдиного повтору вхідних перекладів і прямих перекладів тексту. */
const fs=require('fs'), path=require('path'), vm=require('vm'), {spawnSync}=require('child_process');
const src=process.env.E2_SOURCES || path.resolve(__dirname,'..');
const c=vm.createContext({console, Date, МОДЕЛЬ_МОВИ_П:'запис', ПАСПОРТ_П:null});
c.містП=async (_,d)=>{
  const r=spawnSync(process.env.PYTHON || 'python',['-X','utf8','-c',
    'import sys;sys.path.insert(0,sys.argv[1]);import мовний_шар as М;print(М.мова(sys.stdin.read()))',src],
    {input:JSON.stringify(d),encoding:'utf8',maxBuffer:4000000});
  if(r.status) throw Error(r.stderr); return JSON.parse(r.stdout);
};
vm.runInContext(fs.readFileSync(path.join(src,'показ/мовний_шар.js'),'utf8'),c);
async function main(){
  let failures=0;
  for(const [kind,bad,good] of [
    ['question',{question_about:'bad'},{question_about:'look'}],
    ['verdict_comment',{wear:'bad'},{wear:'as_is'}],
    ['review_items_fix',{actions:[{item:'r1'}]},{actions:[{op:'remove',item:'r1'}]}]]){
    let calls=0;
    c.модельМовиП=async p=>{JSON.parse(p);return JSON.stringify(++calls===1?bad:good);};
    const r=await c.перекластиП(kind,'її слова',{},'проба');
    const ok=calls===2 && Object.keys(r.внутрішня).length>0;
    console.log(JSON.stringify({межа:kind,викликів:calls,дані:r.внутрішня,пройдено:ok}));failures+=!ok;
  }
  for(const repaired of [false,true]){
    let calls=0;
    c.модельМовиП=async p=>{JSON.parse(p.slice(p.lastIndexOf('ТЕКСТИ:')+7));
      return (++calls===1 || !repaired)?'{}':'{"1":"Коротке повідомлення для тебе."}';};
    const r=await c.мовоюП({рядок:'A short message for you.'},'try_on');
    const ok=calls===2 && r.тексти.рядок===(repaired?'Коротке повідомлення для тебе.':'A short message for you.');
    console.log(JSON.stringify({межа:'тексти',виправлено:repaired,викликів:calls,дані:r.тексти,пройдено:ok}));failures+=!ok;
  }
  process.exitCode=failures?1:0;
}
main().catch(e=>{console.error(e);process.exitCode=1;});
