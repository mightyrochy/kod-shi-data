// Прогін прототипу в Pyodide 0.26.4 (та сама версія, що в показ.html) у Node 22.
// Запуск поза деревом: npm i pyodide@0.26.4 && node pyodide_прогін.mjs <шлях до прототип/>
// Лише CPU; жодних мережевих викликів, крім завантаження пакета npm.
import { loadPyodide } from "pyodide";
import fs from "fs";
const dir = process.argv[2];
const py = await loadPyodide();
py.FS.mkdirTree("/proto");
for (const f of ["ядро.py", "шаблони.py", "заміри.py", "перевірки.py", "приклади.py"]) {
  py.FS.writeFile("/proto/" + f, fs.readFileSync(dir + "/" + f, "utf8"));
}
let out = "";
py.setStdout({ batched: (s) => { out += s + "\n"; } });
await py.runPythonAsync(`
import os, sys
os.chdir("/proto"); sys.path.insert(0, "/proto")
import platform
print("runtime:", platform.python_implementation(), sys.version.split()[0], sys.platform)
import заміри
for k, v in заміри.main(20261008).items():
    print("%-32s %s" % (k, v))
import перевірки
print("I1", перевірки.i1_soundness(20261008, 60))
print("I2", перевірки.i2_incremental(20261008, 60))
`);
console.log(out);
