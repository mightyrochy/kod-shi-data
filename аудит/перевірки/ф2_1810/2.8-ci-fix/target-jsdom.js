const fs=require('fs'),path=require('path'),Module=require('module');
const filename=path.resolve('джерела/тест_показу.js');
const prefix=fs.readFileSync(filename,'utf8').split('\n(async () => {')[0];
process.argv[2]=path.resolve('work/index-jsdom.html');
const probe=String.raw`
(async()=>{
 const {дом,w}=сторінка({url:'https://mightyrochy.github.io/kod-shi-data/показ.html#міст=http://localhost:8787&т=tok-a1&модель_мови=нема'});
 const errors=[];w.console.error=(...args)=>errors.push(String(args[0]));
 try{
  const descriptor=Object.getOwnPropertyDescriptor(w,'містП');
  console.log('accessor_after_global_function:',typeof descriptor.get==='function');
  const state=await w.eval("містП('стан_сценарію', {сценарій:{нагода:'робота',опади:'ні'}})");
  if(typeof state.є_сценарій!=='boolean')throw new Error('немає проєкції Python');
  console.log('стан_сценарію:',JSON.stringify(state));
  w._transport=async(name,raw)=>{const data=JSON.parse(raw);await пауза(data.мс);return JSON.stringify(data);};
  w.eval('транспортМостуП=(...args)=>window._transport(...args)');
  const results=await w.eval("Promise.allSettled([містП('мова',{мс:40,мітка:'стара'},{ключ:'перевірка'}),містП('мова',{мс:1,мітка:'нова'},{ключ:'перевірка'})])");
  if(results[0].status!=='rejected'||!results[0].reason.застаріло||results[1].value.мітка!=='нова')throw new Error('втрачено третій аргумент/покоління');
  console.log('third_arg_generation: stale rejected / latest fulfilled');
  w._scene=async(...args)=>args;
  w.eval('містП=(...args)=>window._scene(...args)');
  const args=await w.eval("містП('помади',{мітка:1},{ключ:'помада'})");
  if(args.length!==3||args[2].ключ!=='помада')throw new Error('аргументи не дійшли заглушці сцени');
  console.log('scene_assignment: accessor preserved, 3 args forwarded');
  const again=await w.eval("містП('стан_сценарію',{сценарій:{}})");
  if(typeof again.є_сценарій!=='boolean')throw new Error('сцена перехопила preflight');
  console.log('preflight_after_scene_assignment: Python projection preserved');
  console.log('PASS target jsdom seam');
 }catch(e){console.error('FAIL target jsdom seam:',e.stack);process.exitCode=1;}
 finally{дом.window.close();}
})();`;
const mod=new Module(filename,module);mod.filename=filename;mod.paths=Module._nodeModulePaths(path.dirname(filename));mod._compile(prefix+probe,filename);
