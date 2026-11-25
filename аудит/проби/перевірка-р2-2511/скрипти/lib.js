const fs=require('fs'),crypto=require('crypto');
const {chromium}=require('playwright');
const URL0='http://localhost/';
exports.URL0=URL0;
exports.sha=f=>crypto.createHash('sha256').update(fs.readFileSync(f)).digest('hex');
exports.start=async(html,{w=390,h=844,scale=1,touch=true,file=false,fake={}}={})=>{
  const br=await chromium.launch({args:['--no-sandbox']});
  const ctx=await br.newContext({viewport:{width:w,height:h},deviceScaleFactor:scale,hasTouch:touch,isMobile:touch,reducedMotion:'reduce'});
  const log={allowed:[],blocked:[]};
  const body=fs.readFileSync(html);
  // транспорт закрито ДО навігації: усе, крім самої сторінки, abort; журнал усіх запитаних URL
  await ctx.route('**/*',r=>{const u=r.request().url();
    if(u===URL0){log.allowed.push(u);return r.fulfill({contentType:'text/html; charset=utf-8',body});}
    if(u.startsWith('file:')||u.startsWith('data:')||u.startsWith('blob:')){return r.continue();}
    if(fake[u]){log.allowed.push('(локальна підстановка) '+u);return r.fulfill({contentType:'image/png',body:fake[u]});}
    log.blocked.push(u);return r.abort();});
  ctx.on('request',q=>{const u=q.url(); if(!u.startsWith('data:')&&!u.startsWith('blob:')) (log.all??=[]).push(u);});
  const open=async()=>{const p=await ctx.newPage();p.errs=[];p.on('pageerror',e=>p.errs.push(String(e)));await p.goto(file?'file://'+require('path').resolve(html):URL0);await p.waitForFunction(()=>window.MirrorRoom?.available(),null,{timeout:90000});return p;};
  return {br,ctx,log,open};
};
