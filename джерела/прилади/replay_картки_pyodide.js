/* Ті самі проби у локальному Pyodide, без мережі.
   node прилади/replay_картки_pyodide.js <кеш Pyodide> <архів від replay_картки.py --архів> */
const fs = require('fs'), path = require('path');
const [кеш, архів] = process.argv.slice(2);
(async () => {
  const {loadPyodide} = require(path.resolve(кеш, 'pyodide.js'));
  const пд = await loadPyodide({indexURL: path.resolve(кеш) + '/'});
  const байти = fs.readFileSync(архів);
  пд.unpackArchive(байти.buffer.slice(байти.byteOffset, байти.byteOffset + байти.byteLength),
    'zip', {extractDir: '/card'});
  console.log('Рушій: Pyodide ' + пд.version);
  await пд.runPythonAsync(`
import os, sys, runpy
os.chdir('/card')
sys.path.insert(0, '/card')
runpy.run_path('/card/проби/картка_події.py', run_name='__main__')
runpy.run_path('/card/проби/картка_replay.py', run_name='__main__')
`);
})().catch(помилка => { console.error(помилка); process.exitCode = 1; });
