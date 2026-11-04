const fs = require('fs'), path = require('path');
const root = process.cwd();
const dir = path.join(root, 'аудит/проби/Е1-нічний-живий-20261104/б1_концерт_стримано');
const {результатСтенда} = require(path.join(root, 'аудит/проби/приймання_записів.js'));
const result = JSON.parse(fs.readFileSync(path.join(dir, 'результат.json'), 'utf8'));
const checks = результатСтенда(dir, result.rc);
fs.writeFileSync(path.join(dir, 'звірки.json'), JSON.stringify(checks, null, 1) + '\n');
console.log(JSON.stringify({звірок:checks.звірки.length, червоні:checks.звірки.filter(x=>!x.зелена)}, null, 1));
