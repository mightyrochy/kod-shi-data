const fs=require('fs'),assert=require('assert'),path=require('path');
const out=__dirname;
const read=n=>JSON.parse(fs.readFileSync(path.join(out,n),'utf8'));
const groups=[['final-v2-native',8],['final-v3-remaining',12],['unknown-slot-native',1]];
const cases=[],runs=[];
for(const [base,wanted] of groups){
 const r=read(base+'.json'),log=fs.readFileSync(path.join(out,base+'.log'),'utf8');
 const passed=[...log.matchAll(/^PASS (\S+) (\S+) changed/gm)].map(x=>x[1]+'/'+x[2]);
 assert.equal(passed.length,wanted,base+': число завершених PASS');
 const set=new Set(passed),ok=r.cases.filter(c=>set.has(c.choice+'/'+c.name));
 assert.equal(ok.length,wanted);
 assert.equal(r.head,'b722c8867f671c612e71c5f5828f8befbf642111');
 assert.equal(r.artifactSHA256,'1c376f922b1a2c10492d710b6b1e98200dcab9a0aeab99ec7b9fbf2536f821df');
 assert.equal(r.errors.length,0);
 assert.equal(r.requests.filter(q=>q.method==='POST').length,0);
 for(const c of ok){
   const beforeChoices=JSON.parse(c.before.choices),afterChoices=c.choices;
   for(const k of new Set([...Object.keys(beforeChoices),...Object.keys(afterChoices)])) if(k!==String(c.pos)) assert.equal(JSON.stringify(beforeChoices[k]),JSON.stringify(afterChoices[k]),base+'/'+c.name+': інші вибори');
   assert.equal(JSON.stringify(c.saved.знімок),c.before.snapshot,base+'/'+c.name+': знімок IndexedDB');
   for(let i=0;i<c.cards.length;i++) if(i!==c.pos){
     assert.equal(c.cards[i],c.before.cards[i]);
     assert.equal(JSON.stringify(c.saved.картки[i]),c.before.cards[i]);
   }
   assert(c.otherDOMExact&&c.otherCardsExact&&c.savedOtherCardsExact&&c.fixedItemsExact&&c.nodesSame.every(Boolean));
   assert.equal(c.verdicts,0);
   if(!c.name.startsWith('late-')) assert.equal(c.pager,c.before.pager,base+'/'+c.name+': пейджер');
   cases.push({source:base+'.json',choice:c.choice,name:c.name,position:c.pos,changed:c.changed,modelCalls:c.calls.length,otherCardJSONByteExact:true,otherDOMByteExact:true,otherIDBCardJSONByteExact:true,otherChoicesByteExact:true,savedSnapshotExact:true,fixedItemsExact:c.fixedItemsExact,stageSavedExact:c.stageSavedExact,stale:c.stage?.застаріло,verdictCount:c.verdicts,domBaseline:c.navBaselineDOM?'після стабілізації навігації, перед release відповіді':'до дотику'});
 }
 runs.push({file:base+'.json',pid:r.pid,started:r.startedAt,finished:r.finishedAt,passed:wanted,chromium:r.chromium,pyodide:r.pyodide,modelPOSTs:r.requests.filter(q=>q.method==='POST').length,failedAttempt:r.failure||null});
}
assert.equal(cases.length,21);assert.equal(new Set(cases.map(c=>c.choice+'/'+c.name)).size,21);
const header=read('header-native.json');assert(!header.failure);assert.equal(header.cases.length,1);assert.equal(header.cases[0].calls.length,1);assert.equal(header.modelPOSTs,0);assert.equal(header.headerAfterReset.display,'none');assert.equal(header.reset.marks.length,0);
const identity=read('final-source-identity.json');const fullPath=read('full-path-check-v2.json');
const summary={head:identity.head,artifactSHA256:identity.artifactSHA256,grade:'CONTENT PASS / PENDING CI',functionalDistinctCases:cases.length,headerVisualExtraCapture:1,sourceModulesExact:identity.sourceModulesExact,sourceTemplateExact:identity.htmlTemplateExact,CSSExactToBase:identity.CSSExactToBase,ARIALiteralsExactToBase:identity.ARIALiteralsExactToBase,catalogueRows:identity.catalogueRows,fullAssemblySourceUnchanged:fullPath.fullAssemblyHtmlSuffixExact,runs,cases,headerProof:{file:'header-native.json',before:header.headerBeforeReset,after:header.headerAfterReset,modelCalls:1,modelPOSTs:0},scope:'Синтетичні лише відповіді модельП, початковий стан — явна фікстура. Реальні артефакт/Chromium/Pyodide/міст/IndexedDB. Семантику живої моделі й фото не оцінено.'};
fs.writeFileSync(path.join(out,'aggregate.json'),JSON.stringify(summary,null,2)+'\n');
console.log(JSON.stringify({grade:summary.grade,cases:cases.length,headerExtra:1,modelPOSTs:0,runs:runs.map(({file,passed,chromium,pyodide})=>({file,passed,chromium,pyodide}))},null,2));
