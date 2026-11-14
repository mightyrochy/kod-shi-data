/* Аргументи: дерево ДО з node_modules, дерево ПІСЛЯ, фото №17, тека виходу. FOTO=1. */
const fs=require('fs'),path=require('path'),Module=require('module');
const [R,H,photoFile,out]=process.argv.slice(2).map(p=>path.resolve(p));
const {chromium}=require(path.join(R,'джерела/node_modules/playwright'));
function htmlFor(root){
 const src=path.join(root,'джерела'),file=path.join(src,'тест_показу.js'),code=fs.readFileSync(file,'utf8');
 const mod=new Module(file);mod.filename=file;mod.paths=Module._nodeModulePaths(src);
 const argv=process.argv;process.argv=argv.slice(0,2);
 try{mod._compile(code.slice(0,code.indexOf('(async () => {'))+'\nmodule.exports={сторінка};',file)}
 finally{process.argv=argv}
 const {дом,w,d}=mod.exports.сторінка({url:'https://example.test/'});
 w.__photo='data:image/jpeg;base64,'+fs.readFileSync(photoFile).toString('base64');
 w.eval(`П={картки:[{рука:'1',текст:'Образ',опис:'Образ із мереживною спідницею.',як_носити:['Доповни зручним взуттям.'],
 речі:[{id:'ж-06015@rito.ua',назва:'Бавовняна мереживна спідниця з аплікаціями',слот:'низ',фото:window.__photo}],
 мітки:[],знахідки:[],питання:[],етапи:{},свідомі:[],фото_не_ті:[],дібрав_код_слоти:[]}]};`);
 for(const screen of d.querySelectorAll('.екран'))screen.style.display='none';
 d.getElementById('е-образи').style.display='block';
 d.getElementById('е-образи').appendChild(w.eval('рендерКартку(0)'));
 for(const script of d.querySelectorAll('script'))script.remove();
 const html=дом.serialize();w.close();return html;
}
(async()=>{
 const browser=await chromium.launch({headless:true,
   ...(process.platform==='win32'?{executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'}:{}),args:['--disable-gpu']});
 try{
  for(const [name,root] of [['до',R],['після',H]]){
   const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
   await page.route(/^https?:/,route=>route.abort());
   await page.setContent(htmlFor(root),{waitUntil:'load'});
   await page.locator('#к-0').scrollIntoViewIfNeeded();
   const photos=await page.locator('#к-0 img').evaluateAll(imgs=>imgs.map(x=>({loaded:x.complete&&x.naturalWidth>0,width:x.naturalWidth})));
   await page.screenshot({path:path.join(out,name+'-390x844.png'),animations:'disabled'});
   console.log(JSON.stringify({name,viewport:'390x844',FOTO:process.env.FOTO,photos,width:await page.evaluate(()=>document.documentElement.scrollWidth)}));
   await page.close();
  }
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
