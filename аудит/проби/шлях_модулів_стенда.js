const os = require('os'), path = require('path');

/** Складає NODE_PATH для стенда в робочому дереві й у тимчасовому дереві штампа. */
function шляхМодулівСтенда(корінь, чинний = process.env.NODE_PATH) {
  const шляхи = (чинний || '').split(path.delimiter).filter(Boolean).map(шлях => path.resolve(корінь, шлях));
  шляхи.push(path.join(корінь, 'джерела', 'node_modules'),
    path.join(os.homedir(), 'kod-shi-test-node', 'node_modules'));
  return [...new Set(шляхи)].join(path.delimiter);
}

if (require.main === module) process.stdout.write(шляхМодулівСтенда(path.resolve(__dirname, '../..')));
module.exports = {шляхМодулівСтенда};
