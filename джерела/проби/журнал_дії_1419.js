/* Справжні DOM-події між читаннями журналу; новий writer — ревізія, старий — focus. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {JSDOM}=require('jsdom'),{indexedDB,IDBObjectStore}=require('fake-indexeddb');
const html=fs.readFileSync(path.join(__dirname,'..','показ.html'),'utf8');
const slice=(a,b)=>html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
const code=slice('function tx(d,','async function пристрій_Id(')+slice('const КЛЮЧ_РЕВІЗІЇ_ЖУРНАЛУ_П','/* ── ПОВТОРНЕ ВИВАНТАЖЕННЯ')+slice('function копіяРозборуП(','function розібратиПоле(');
const dom=new JSDOM('<button id="читати">Журнал</button><button id="записати">Вердикт</button><output id="стан"></output>');
let reads=0;const getAll=IDBObjectStore.prototype.getAll;
IDBObjectStore.prototype.getAll=function(...a){if(this.name==='вердикти')reads++;return getAll.apply(this,a)};
(async()=>{
 const db=await new Promise((ok,no)=>{const r=indexedDB.open('журнал-дії-1419',3);r.onupgradeneeded=()=>{r.result.createObjectStore('вердикти',{autoIncrement:true});r.result.createObjectStore('кв')};r.onsuccess=()=>ok(r.result);r.onerror=()=>no(r.error)});
 const api=new Function('дб','window',code+';return {tx,усіВердикти};')(async()=>db,dom.window);
 await api.tx(db,'вердикти','readwrite',s=>{s.add({рука:1,етапи:'а'.repeat(1500000)});s.add({рука:2,етапи:'б'.repeat(2200000)})});
 let pending,rows;const doc=dom.window.document;
 doc.getElementById('читати').onclick=()=>pending=api.усіВердикти().then(r=>{rows=r;doc.getElementById('стан').textContent=r.length});
 doc.getElementById('записати').onclick=()=>pending=api.tx(db,'вердикти','readwrite',s=>s.add({рука:'оцінка',етапи:'{}'}));
 const click=async id=>{doc.getElementById(id).click();await pending};
 for(let i=0;i<16;i++){doc.getElementById('читати').dispatchEvent(new dom.window.KeyboardEvent('keydown',{key:'Tab',bubbles:true}));await click('читати')}
 assert.equal(reads,1,'16 DOM-команд читання не скидають незмінний знімок');assert.equal(doc.getElementById('стан').textContent,'2');
 await click('записати');await click('читати');assert.equal(rows.length,3);assert.equal(reads,2,'новий writer змінює ревізію');
 const old=db.transaction('вердикти','readwrite');old.objectStore('вердикти').put({рука:1,етапи:'старий writer'},1);await new Promise(ok=>old.oncomplete=ok);
 dom.window.dispatchEvent(new dom.window.Event('focus'));await click('читати');assert.equal(rows[0].етапи,'старий writer');assert.equal(reads,3);
 dom.window.dispatchEvent(new dom.window.Event('pagehide'));await click('читати');assert.equal(reads,4);
 db.close();dom.window.close();console.log('DOM: 16 команд → 1 повне читання; новий запис за ревізією, старий writer після focus, pagehide — пройдено');
})().catch(e=>{dom.window.close();console.error(e);process.exitCode=1});
