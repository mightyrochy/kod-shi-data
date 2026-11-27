import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import vm from "node:vm";

const snapshot=JSON.parse(readFileSync(0,"utf8"));
const bytes=new TextEncoder().encode(JSON.stringify(snapshot));
const engines=process.argv.slice(2).map(path=>{
  const window={};
  vm.runInNewContext(readFileSync(path,"utf8"),{
    window, TextDecoder, fetch:async()=>({ok:true,arrayBuffer:async()=>bytes.buffer})
  });
  return window.MirrorIndex;
});
const [before,after]=engines;
const limit=snapshot.перша_сторінка, openings=200;
const slots=[...new Set(snapshot.rows.map(row=>row[2]))].sort();
const ids=result=>result.results.map(row=>row.id);
const output={};
for(const slot of [undefined,...slots]){
  const initial=await before.search("",{slot,limit});
  const visible=new Set();
  for(let seed=1;seed<=openings;seed++){
    for(const id of ids(await after.search("",{slot,limit,seed}))) visible.add(id);
  }
  output[slot ?? "усі"]={усього:initial.total,до:initial.results.length,після:visible.size,
    очікувано:Math.round(initial.total*(1-(1-initial.results.length/initial.total)**openings))};
}
const slot="dress", seed=1, page=await after.search("",{slot,limit,seed});
const ordered=[];
for(let offset=0;offset<page.total;offset+=limit){
  ordered.push(...ids(await after.search("",{slot,limit,seed,offset})));
}
assert.equal(ordered.length,page.total);
assert.equal(new Set(ordered).size,page.total);
assert.deepEqual([...ids(page)],[...ordered.slice(0,limit)]);
for(const [query,options] of [["сукня",{}],["до 1000",{}],["",{slot,availableOnly:true}]]){
  assert.equal(JSON.stringify(await before.search(query, options)),JSON.stringify(await after.search(query,{...options,seed})));
}
console.log(JSON.stringify(output));
