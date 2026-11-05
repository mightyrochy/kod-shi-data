/* Виконати незмінений розділ 2в батареї окремо; база відрізняється лише трьома Python-модулями кроку. */
const fs=require('fs'), path=require('path'), Module=require('module');
const source=path.join(path.resolve(__dirname,'../../../..'),'джерела');
const file=path.join(source,'тест_показу.js'), text=fs.readFileSync(file,'utf8');
const start=text.indexOf('  розділ("2в. КОЛЬОРИ З ПОРТРЕТА');
const end=text.indexOf('\n  розділ(',start+10);
if(start<0 || end<0) throw Error('Не знайдено межі вихідного розділу 2в');
let prefix=text.slice(0,text.indexOf('(async () => {'));
if(process.env.PIDVYDY_BASE){
  const before="spawnSync('python3', ['-c', код, JSON.stringify(дані)]";
  const preamble='import sys;sys.path.insert(0,'+JSON.stringify(process.env.PIDVYDY_BASE)+');\n';
  if(!prefix.includes(before)) throw Error('Не знайдено виклик справжнього Python');
  prefix=prefix.replace(before,"spawnSync('python3', ['-c', "+JSON.stringify(preamble)+"+код, JSON.stringify(дані)]");
}
const mod=new Module(file);mod.filename=file;mod.paths=Module._nodeModulePaths(source);
mod._compile(prefix+'\n(async()=>{'+text.slice(start,end)
  +'\nconsole.log(JSON.stringify({звірок:виконано,відмов:провалів}));process.exit(провалів?1:0);'
  +'})().catch(error=>{console.error(error);process.exit(2);});',file);
