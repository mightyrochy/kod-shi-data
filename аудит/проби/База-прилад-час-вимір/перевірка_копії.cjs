/* Самоперевірка з копіюванням фікстури Python: штатний fs.cpSync аварійно завершує Node 22 у цьому середовищі.
   Аргументи та перевірки приладу ті самі; це допоміжний доказ, окремий від штатного запуску. */
const fs = require('fs'), path = require('path'), cp = require('child_process'), Module = require('module');
fs.cpSync = (from, to, options) => {
  if (!options?.recursive) throw new Error('Очікується копіювання дерева фікстури');
  const result = cp.spawnSync(process.env.PYTHON_FOR_COPY || 'python',
    ['-c', 'import shutil,sys; shutil.copytree(sys.argv[1],sys.argv[2],dirs_exist_ok=True)', from, to], {encoding: 'utf8'});
  if (result.status !== 0) throw new Error(result.stderr || result.error?.message || 'Копіювання не завершено');
};
if (process.argv[2]) {
  const original = path.resolve(__dirname, '../нова_база.js'), read = Module._extensions['.js'];
  Module._extensions['.js'] = (m, filename) => filename === original
    ? m._compile(fs.readFileSync(process.argv[2], 'utf8'), filename) : read(m, filename);
}
require(path.join(__dirname, '../перевірити_нову_базу.js'));
