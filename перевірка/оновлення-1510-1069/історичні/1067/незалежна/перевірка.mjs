import fs from 'node:fs';
import assert from 'node:assert/strict';
const valid=fs.readFileSync(new URL('./valid.webp',import.meta.url));
const invalid=new TextEncoder().encode('<html>Не картинка</html>'.repeat(100));
const env={ALLOWED_ORIGINS:'https://qa.example',TESTER_TOKENS:'qa',GEMINI_API_KEY:'local-test',ANTHROPIC_API_KEY:'local-test',GEMINI_THINKING:'as-is'};
const images=['https://fixture.example/valid.webp?sig=5634','https://fixture.example/notimage?sig=5634'];
const cases=[
 ['WebP/200/відсутній MIME',valid,{},200,true],
 ['WebP/200/порожній MIME',valid,{'content-type':''},200,true],
 ['WebP/200/пробіли MIME',valid,{'content-type':'   '},200,true],
 ['HTML/200/відсутній MIME',invalid,{},200,false],
 ['WebP/200/image-webp',valid,{'content-type':'image/webp'},200,true],
 ['HTML/200/image-webp',invalid,{'content-type':'image/webp'},200,false],
 ['WebP/200/text-html',valid,{'content-type':'text/html'},200,false],
 ['WebP/404/відсутній MIME',valid,{},404,false],
 ['WebP/200/замалий',valid.subarray(0,100),{},200,false],
 ['WebP/200/завеликий declared',valid,{'content-length':String(4*1024*1024+1)},200,false],
];
for(const stage of ['before','after']) {
 const {default:worker}=await import('./worker-'+stage+'.mjs');
 for(const [name,bytes,headers,status,accepted] of cases) {
  const sent=[];let imageCalls=0;
  globalThis.fetch=async(url,options)=>{
   if(String(url)===images[0]) {imageCalls++;const r=new Response(bytes,{status,headers});if(!Object.keys(headers).some(x=>x==='content-type'))assert.equal(r.headers.get('content-type'),null);return r;}
   assert.match(String(url),/^https:\/\/generativelanguage.googleapis.com\//);sent.push(JSON.parse(options.body));
   return Response.json({candidates:[{content:{parts:[{text:'є'}]},finishReason:'STOP'}]});
  };
  const body={model:'gemini-test',messages:[{role:'user',content:[{type:'image',source:{type:'url',url:images[0]}}]}]};
  const response=await worker.fetch(new Request('https://worker.example/',{method:'POST',headers:{Origin:'https://qa.example','x-lyusterko-token':'qa','content-type':'application/json'},body:JSON.stringify(body)}),env);
  const expected=accepted && (stage==='after'||name==='WebP/200/image-webp');
  assert.equal(response.status,200);assert.equal(imageCalls,1);assert.equal(sent.length,1);assert.equal(response.headers.get('x-images-dropped'),expected?'0':'1');
  const part=sent[0].contents[0].parts[0];
  if(expected){assert.equal(part.inline_data.mime_type,'image/webp');assert.deepEqual(Buffer.from(part.inline_data.data,'base64'),valid);}
  else {assert.equal(part.inline_data,undefined);assert.equal(part.text,'(image not delivered)');}
  console.log(stage,name,'→',expected?'прийнято точні байти':'відкинуто');
 }
 for(const status of [200,400]) {
  const sent=[];const content=images.map(url=>({type:'image',source:{type:'url',url}}));
  globalThis.fetch=async(url,options)=>{assert.equal(String(url),'https://api.anthropic.com/v1/messages');sent.push(JSON.parse(options.body));return Response.json(status===200?{content:[{type:'text',text:'є'}],usage:{}}:{error:{message:'Відмова фото провайдером'}},{status});};
  const response=await worker.fetch(new Request('https://worker.example/',{method:'POST',headers:{Origin:'https://qa.example','x-lyusterko-token':'qa','content-type':'application/json'},body:JSON.stringify({model:'claude-test',messages:[{role:'user',content}]})}),env);
  assert.equal(response.status,status);assert.equal(sent.length,1);assert.deepEqual(sent[0].messages[0].content,content);assert.equal(response.headers.get('x-images-dropped'),'0');
  if(status===400)assert.match(await response.text(),/Відмова фото провайдером/);
  console.log(stage,'Anthropic: обидва URL без змін, без локального fetch; видимий HTTP',status);
 }
}
console.log('Усі 24 цільові перевірки пройшли; мережевих/API викликів нема.');
