const fs=require('fs'),cp=require('child_process'),vm=require('vm'),crypto=require('crypto'),assert=require('assert');
const ROOT='/workspace/replace4945',HEAD='0a664f440b208a4023cbeb9a01bc4461ae37ab84',MAIN='16a13b727f35aec508bf01d7fc6070049481a785',OLD='b722c8867f671c612e71c5f5828f8befbf642111';
const get=ref=>cp.execFileSync('git',['-C',ROOT,'show',ref+':джерела/показ.html'],{maxBuffer:8e6}).toString();
const current=get(HEAD),main=get(MAIN),old=get(OLD),sha=x=>crypto.createHash('sha256').update(x).digest('hex');
function extract(text,name){
 const start=text.search(new RegExp('^(?:async )?function '+name+'\\(', 'm'));assert(start>=0,name+' відсутня');
 for(let at=text.indexOf('}',start);at>=0;at=text.indexOf('}',at+1)){
  const s=text.slice(start,at+1);try{new vm.Script('('+s+')');return s;}catch(e){if(!(e instanceof SyntaxError))throw e;}
 }
 throw Error('Неможливо виділити '+name);
}
const names=['станВиборуП','оголоситиЗбиранняП','оголоситиВідмовуЗбиранняП','малюватиПоступП','зібратиОбразиП','чипРяд','чипП','плитка','позначитиВідчуттяП','малюватиДрап','малюватиОцінкуП','оновитиПолеВердиктуП','відновитиСтанКарткиП','малюватиЧатП'];
const rows=names.map(name=>{const a=extract(current,name),b=extract(main,name);assert.strictEqual(a,b,name+': main змінено');return{name,exact:MAIN,bytes:Buffer.byteLength(a),sha256:sha(a)};});
for(const name of ['замінитиРічП','малюватиНеЦяП','рядокПідПереліком','виглядКнопкиЗаміниП']){const a=extract(current,name),b=extract(old,name);assert.strictEqual(a,b);rows.push({name,exact:OLD,bytes:Buffer.byteLength(a),sha256:sha(a)});}
const css=t=>[...t.matchAll(/<style[^>]*>([\s\S]*?)<\/style>/g)].map(m=>m[1]);assert.deepStrictEqual(css(current),css(main));
const scripts=[...current.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]);for(const s of scripts)new vm.Script(s);
const result={head:HEAD,mainWholeFunctionsExact:names.length,localReplacementFunctionsExact:4,cssExactMain:true,scriptCompile:scripts.length,rows};
fs.writeFileSync(__dirname+'/function-identity.json',JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify({...result,rows:undefined}));
