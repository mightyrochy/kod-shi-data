const fs=require('fs'),path=require('path'),Module=require('module');
const root=process.argv[2],out=process.argv[3];process.argv=process.argv.slice(0,2);
const code=path.join(root,'джерела'),test=path.join(code,'тест_показу.js'),s=fs.readFileSync(test,'utf8');
const mod=new Module(test);mod.filename=test;mod.paths=Module._nodeModulePaths(code);
mod._compile(s.slice(0,s.indexOf('(async () => {'))+'\nmodule.exports={сторінка};',test);
const data=JSON.parse(fs.readFileSync(path.join(out,'каталог-після.json'),'utf8'));
const {chromium}=require(path.join(code,'node_modules/playwright'));
(async()=>{
 const {дом,w,d}=mod.exports.сторінка({url:'https://example.test/'});
 await new Promise(r=>w.addEventListener('load',r));
 w.__cards=data.показ[0];w.__passport=data.паспорт[0].паспорт;
 w.eval("ПАСПОРТ_П=window.__passport; П={картки:[{рука:'1',речі:window.__cards,опис:'',як_носити:[],питання:[]}],випадок_шматки:[{ключ:'пора',текст:'ввечері'}]};рендер();");
 for(const script of d.querySelectorAll('script'))script.remove();
 const html=дом.serialize();w.close();
 const browser=await chromium.launch({headless:true,args:['--disable-gpu']});
 try{
  const p=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  await p.setContent(html,{waitUntil:'load',timeout:60000});
  const photos=await p.locator('#к-0 img').evaluateAll(xs=>xs.map(x=>({url:x.currentSrc,loaded:x.complete&&x.naturalWidth>0})));
  console.log(JSON.stringify({фото:photos}));
  await p.screenshot({path:path.join(out,'каталог-верх.png'),animations:'disabled'});
  await p.locator('#к-0').screenshot({path:path.join(out,'каталог-картка.png'),animations:'disabled'});
  await p.getByText(data.показ[0][0].назва,{exact:true}).scrollIntoViewIfNeeded();
  await p.screenshot({path:path.join(out,'каталог-назва.png'),animations:'disabled'});
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1});
