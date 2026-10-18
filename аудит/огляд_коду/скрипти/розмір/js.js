const fs=require('fs'),acorn=require(process.env.SP+'/node_modules/acorn');
const f=process.argv[2];const s=fs.readFileSync(f,'utf8');
let blocks=[];
if(f.endsWith('.html')){const re=/<script\b([^>]*)>([\s\S]*?)<\/script>/g;let m;while(m=re.exec(s)){if(/src=/.test(m[1])&&!m[2].trim())continue;blocks.push({off:m.index+m[0].indexOf('>')+1,src:m[2]});}}
else blocks.push({off:0,src:s});
const lineOf=(o)=>s.slice(0,o).split('\n').length;
let fns=[],top=[],tot=0,ev=[],cnt={};
const rep=(k,l)=>{(cnt[k]=cnt[k]||[]).push(l)};
for(const b of blocks){
 let ast;try{ast=acorn.parse(b.src,{ecmaVersion:'latest',allowReturnOutsideFunction:true,locations:true,onComment:()=>{}});}catch(e){console.log('PARSE FAIL block at line',lineOf(b.off),e.message);continue}
 const base=lineOf(b.off)-1;
 tot+=b.src.split('\n').length;
 for(const n of ast.body){
  if(n.type==='VariableDeclaration')for(const d of n.declarations)top.push([n.kind,d.id.name||'{destr}',n.loc.start.line+base,n.loc.end.line-n.loc.start.line+1,d.init?d.init.type:'']);
  else if(n.type==='FunctionDeclaration')top.push(['function',n.id.name,n.loc.start.line+base,n.loc.end.line-n.loc.start.line+1,'']);
 }
 (function walk(n,name){
  if(!n||typeof n.type!=='string')return;
  if(/Function/.test(n.type)){fns.push({name:n.id?n.id.name:name||'(anon)',l:n.loc.start.line+base,len:n.loc.end.line-n.loc.start.line+1,top:false});}
  if(n.type==='CallExpression'||n.type==='NewExpression'){
    const c=n.callee;const txt=b.src.slice(c.start,c.end).slice(0,60);
    const L=n.loc.start.line+base;
    if(/addEventListener$/.test(txt))rep('addEventListener',L);
    if(/^fetch$|\.fetch$/.test(txt))rep('fetch',L);
    if(/runPython/.test(txt))rep('runPython',L);
    if(/pyodide|loadPyodide|\.pyimport|toPy|\.globals\.get/.test(txt))rep('pyodide*',L);
    if(/localStorage|sessionStorage/.test(txt))rep('storage-call',L);
    if(/indexedDB/.test(txt))rep('indexedDB',L);
    if(/Worker$/.test(txt)&&n.type==='NewExpression')rep('new Worker',L);
    if(/postMessage$/.test(txt))rep('postMessage',L);
  }
  if(n.type==='MemberExpression'){const t=b.src.slice(n.start,n.end);if(/^(window\.)?(localStorage|sessionStorage)$/.test(t))rep('localStorage/sessionStorage ref',n.loc.start.line+base);if(/^(window\.)?indexedDB$/.test(t))rep('indexedDB ref',n.loc.start.line+base);}
  if(n.type==='AssignmentExpression'&&n.left.type==='MemberExpression'&&n.left.property.name&&/^on[a-z]+$/.test(n.left.property.name))rep('on*= handler',n.loc.start.line+base);
  for(const k in n){if(k==='loc')continue;const v=n[k];if(Array.isArray(v))v.forEach(x=>walk(x,(n.type==='VariableDeclarator'&&n.id)?n.id.name:name));else if(v&&typeof v.type==='string'){walk(v,(n.type==='VariableDeclarator'&&n.id&&k==='init')?n.id.name:(n.type==='Property'&&k==='value'&&n.key)?(n.key.name||n.key.value):(n.type==='AssignmentExpression'&&k==='right')?b.src.slice(n.left.start,n.left.end).slice(-40):name)}}
 })(ast,null);
}
console.log('JS lines',tot,'functions(all incl. nested/arrow)',fns.length);
const named=fns.filter(f=>f.name!=='(anon)');
console.log('longest 15:');fns.sort((a,b)=>b.len-a.len).slice(0,15).forEach(f=>console.log(f.len,f.name,f.l));
console.log('>100 lines',fns.filter(f=>f.len>100).length,'>200',fns.filter(f=>f.len>200).length);
console.log('top-level decls',top.length,' vars:',top.filter(t=>t[0]!=='function').length,'funcs:',top.filter(t=>t[0]==='function').length);
console.log('top-level let/var:',top.filter(t=>t[0]==='let'||t[0]==='var').length,'const:',top.filter(t=>t[0]==='const').length);
fs.writeFileSync(process.env.SP+'/js_top_'+require('path').basename(f)+'.json',JSON.stringify({top,fns:fns.slice(0,400),cnt}));
for(const k in cnt)console.log(k,cnt[k].length,'lines:',cnt[k].slice(0,12).join(','));
