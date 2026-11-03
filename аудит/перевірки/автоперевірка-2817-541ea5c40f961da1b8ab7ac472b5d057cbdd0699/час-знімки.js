const fs=require('fs'), path=require('path'), Module=require('module');
const root=process.argv[2], out=process.argv[3], code=path.join(root,'джерела');
process.argv=process.argv.slice(0,2);
const test=path.join(code,'тест_показу.js'), source=fs.readFileSync(test,'utf8');
const mod=new Module(test); mod.filename=test; mod.paths=Module._nodeModulePaths(code);
mod._compile(source.slice(0,source.indexOf('(async () => {'))+'\nmodule.exports={сторінка};',test);
const values=JSON.parse(fs.readFileSync(path.join(out,'час-перевірка.json'),'utf8').replace(/^\uFEFF/,''));
const {chromium}=require(path.join(code,'node_modules/playwright'));
(async()=>{
 const browser=await chromium.launch({headless:true,args:['--disable-gpu']});
 try { for (const value of values) {
  const {дом,w,d}=mod.exports.сторінка({url:'https://example.test/'});
  await new Promise(resolve=>w.addEventListener('load',resolve));
  w.__п=value.паспорт; w.__ш=value.шматки;
  w.eval("ПАСПОРТ_П=window.__п; застосуватиПаспортДоЕкрана(ПАСПОРТ_П); режим('сценарій'); малюватиКарткуСценарію();");
  const text=d.getElementById('зн-коли').textContent;
  if (/\d\d:\d\d/.test(text)) throw Error('Година на картці: '+text);
  for (const script of d.querySelectorAll('script')) script.remove();
  const html=дом.serialize(); w.close();
  const page=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  await page.route('**/*',route=>route.abort()); await page.setContent(html);
  await page.locator('#сц-картка').scrollIntoViewIfNeeded();
  await page.screenshot({path:path.join(out,value.код+'.png'),animations:'disabled'});
  console.log(JSON.stringify({пора:value.код,текст:text,ширина:await page.evaluate(()=>document.documentElement.scrollWidth)}));
  await page.close();
 }} finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1});
