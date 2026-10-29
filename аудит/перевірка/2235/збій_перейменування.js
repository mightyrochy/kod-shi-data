// Відтворення 11222: node збій_перейменування.js <корінь дерева з нова_база.js> <тека наряду з записом без база.json> [main, типово origin/main]
const fs = require('fs'), path = require('path');
const [корінь, наряд] = process.argv.slice(2, 4).map(р => path.resolve(р)), main = process.argv[4] || 'origin/main';
const {виконати} = require(path.join(корінь, 'аудит/проби/нова_база.js'));
fs.renameSync = () => { const е = new Error('EPERM: operation not permitted, rename'); е.code = 'EPERM'; throw е; };
try { process.exitCode = виконати([наряд, '--main', main], корінь); }
catch (е) { console.error('ВИНЯТОК:', е.message); process.exitCode = 2; }
