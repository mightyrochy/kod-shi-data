// Відтворення сцени ж1_213_теракотова_сукня без моделі. NICHNI=<тека нічні/20261120>, NODE_PATH=<playwright>, PYODIDE=<кеш>.
// вжиток: node run.js <кореньБазиПроб> <збірка> <вихідТека> [стенд]
const path=require('path'),fs=require('fs');
const [,, кор, збірка, вих, стендАрг]=process.argv;
const П=require(path.join(кор,'аудит/проби/приймання_записів.js'));
const сцени=П.свіжіЗаписи(process.env.NICHNI).filter(с=>с.id==='ж1_213_теракотова_сукня');
const с=сцени[0]; fs.rmSync(вих,{recursive:true,force:true});
const стенд=стендАрг||path.join(кор,'аудит/проби/рв6_стенд.js');
const сер=П.середовищеСцени(с,вих,стенд);
const р=П.запуститиСтенд(збірка,process.env.PYODIDE||'/tmp/pyodide',с.сід,сер,вих,стенд);
const rc=р.status===null?2:р.status;
console.log('rc',rc, р.error?р.error.message:'');
const після=П.результатСтенда(вих,rc);
console.log(JSON.stringify(після.звірки.map(з=>[з.назва.slice(0,60),з.зелена]),null,0), після.застарілий);
