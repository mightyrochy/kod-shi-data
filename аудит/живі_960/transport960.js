const http = require('http'), fs = require('fs'), path = require('path');
const dir = process.argv[2]; fs.mkdirSync(dir, {recursive:true});
let n = 0;
http.createServer((req,res)=>{
  const body = []; req.on('data',x=>body.push(x)); req.on('end',()=>{
    const payload = Buffer.concat(body); let request = {};
    try { request = JSON.parse(payload); } catch (e) { request.parse_error = e.message; }
    const id = ++n, started = Date.now(), at = new Date().toISOString();
    const up = http.request({host:'127.0.0.1',port:1235,path:req.url,method:req.method,
      headers:req.headers,agent:false}, r=>{
      const chunks=[]; res.writeHead(r.statusCode,r.headers);
      r.on('data',x=>{chunks.push(x);res.write(x);});
      r.on('end',()=>{
        const raw=Buffer.concat(chunks).toString('utf8');
        let result; try { result=JSON.parse(raw); } catch(e) { result={raw,parse_error:e.message}; }
        fs.writeFileSync(path.join(dir,String(id).padStart(3,'0')+'.json'),JSON.stringify({
          at,seconds:(Date.now()-started)/1000,status:r.statusCode,model:request.model,
          max_tokens:request.max_tokens,seed:request.seed,result},null,2)); res.end();
      });
      r.on('error',e=>res.destroy(e));
    });
    up.on('error',e=>{res.writeHead(502);res.end(String(e));}); up.end(payload);
  });
}).listen(1236,'127.0.0.1',()=>console.log('telemetry :1236 -> sequential proxy :1235'));
