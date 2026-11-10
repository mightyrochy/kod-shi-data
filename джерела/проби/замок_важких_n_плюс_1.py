# Замок важких кроків: N тримачів беруть слоти; чекачі A (Python) і B (Node) ідуть у черзі за приходом; смерть тримача звільняє слот; без змінної — без замка.
import os, subprocess, sys, tempfile, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import _замок_важких as З
if os.name != "nt": sys.exit(print("лише Windows: на інших ОС замок не діє (змінна не задається)"))
ДЖ = os.path.dirname(os.path.abspath(З.__file__)); тека = tempfile.mkdtemp(); N = З.межа()
сер = dict(os.environ, KODSHI_HEAVY_DIR=тека); сер.pop("KODSHI_HEAVY_HELD", None)
ПИ = "import sys,time; sys.path.insert(0, r'%s'); import _замок_важких as З; print(З.взяти('проба'), flush=True); time.sleep(600)" % ДЖ
НО = "console.log(require(String.raw`%s`).взяти('проба-node')); setTimeout(() => {}, 600000)" % os.path.join(ДЖ, "_замок_важких.js")
def пуск(cmd, ім):
    return subprocess.Popen(cmd, env=сер, stdout=open(os.path.join(тека, ім + ".out"), "w"), stderr=open(os.path.join(тека, ім + ".err"), "w"))
def рядок(ім, с, ф="out"):
    кінець = time.time() + с
    while time.time() < кінець:
        т = open(os.path.join(тека, ім + "." + ф), encoding="utf-8", errors="replace").read().strip()
        if т: return т.splitlines()[0]
        time.sleep(0.2)
    return ""
print("N з важкі.json:", N)
тримачі = [пуск([sys.executable, "-c", ПИ], "п%d" % i) for i in range(N)]
слоти = sorted(рядок("п%d" % i, 30) for i in range(N)); print("тримачі Python взяли слоти:", слоти)
а = пуск([sys.executable, "-c", ПИ], "а"); ча = рядок("а", 15, "err"); б = пуск(["node", "-e", НО], "б"); чб = рядок("б", 15, "err")
print("A чекає:", рядок("а", 2) == "", "|", ча); print("B чекає:", рядок("б", 2) == "", "|", чб)
тримачі[0].kill(); т0 = time.time(); ва = рядок("а", 30)
print("тримача 1 вбито → A взяв слот %s за %.1f с; B далі чекає: %s" % (ва, time.time() - т0, рядок("б", 3) == ""))
(тримачі[1] if N > 1 else а).kill(); т0 = time.time(); вб = рядок("б", 30)
print("ще один тримач умер → B (Node) взяв слот %s за %.1f с" % (вб, time.time() - т0))
сер.pop("KODSHI_HEAVY_DIR"); т0 = time.time()
без = subprocess.run([sys.executable, "-c", ПИ.replace("time.sleep(600)", "0")], env=сер, capture_output=True, text=True).stdout.strip()
print("без змінної: взяти() =", без, "за %.1f с" % (time.time() - т0))
for п in тримачі + [а, б]: п.kill()
ок = (слоти == [str(i) for i in range(1, N + 1)] and "чекаю замок" in ча and "у черзі 2-й" in чб and ва == "1"
      and вб == ("2" if N > 1 else "1") and без == "None")
print("ЗАМОК", "✓" if ок else "✗"); sys.exit(0 if ок else 1)
