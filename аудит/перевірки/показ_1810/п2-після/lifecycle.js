const fs=require('fs'), {chromium}=require('playwright'), assert=require('node:assert/strict');
(async()=>{
 const b=await chromium.launch({executablePath:process.env.CHROMIUM,headless:true,args:['--no-sandbox']});
 const c=await b.newContext({viewport:{width:390,height:844}});
 await c.route('http://p2.local/**',r=>r.fulfill({contentType:'text/html',body:'<!doctype html><title>П2</title>'}));
 const p=await c.newPage(); await p.goto('http://p2.local/');
 const s=fs.readFileSync('/workspace/work/p2/джерела/показ.html','utf8');
 await p.evaluate(s.slice(s.indexOf('let зʼєднанняДбП'),s.indexOf('\nfunction tx(')));
 const facts=await p.evaluate(async()=>{
  let opens=0, blockedEvents=0; const warn=console.warn; console.warn=(...a)=>{blockedEvents++;warn(...a)}; const original=indexedDB.open.bind(indexedDB); indexedDB.open=(...a)=>{opens++;return original(...a)};
  const old=await new Promise((res,rej)=>{const r=original('показ',2);r.onsuccess=()=>res(r.result);r.onerror=()=>rej(r.error)});
  let blocked=false; const close=old.close.bind(old); old.onversionchange=()=>{blocked=true; setTimeout(close,100)};
  const all=await Promise.all(Array.from({length:109},()=>дб()));
  const shared=all.every(d=>d===all[0]), first=opens;
  const d=all[0], t=d.transaction('кв','readwrite');t.objectStore('кв').put('дані','p2');
  await new Promise((res,rej)=>{t.oncomplete=res;t.onerror=()=>rej(t.error)});
  const abort=d.transaction('кв','readwrite');abort.objectStore('кв').put('не зберігати','p2');abort.abort();await new Promise(res=>abort.onabort=res);
  d.close(); const next=await дб();
  const r=next.transaction('кв').objectStore('кв').get('p2');const value=await new Promise(res=>r.onsuccess=()=>res(r.result));
  const upgrade=original('показ',4); const v4=await new Promise((res,rej)=>{upgrade.onsuccess=()=>res(upgrade.result);upgrade.onerror=()=>rej(upgrade.error)});v4.close();
  let errors=0;for(let i=0;i<2;i++)try{await дб()}catch(e){if(e.name==='VersionError')errors++}
  return {first,shared,blocked,blockedEvents,value,errors,opens,viewport:[innerWidth,innerHeight]};
 });
 assert.equal(facts.first,1);assert(facts.shared&&facts.blocked);assert.equal(facts.blockedEvents,1);assert.equal(facts.value,'дані');assert.equal(facts.errors,2);assert.equal(facts.opens,4);
 console.log(JSON.stringify(facts));await b.close();
})().catch(e=>{console.error(e);process.exitCode=1});
