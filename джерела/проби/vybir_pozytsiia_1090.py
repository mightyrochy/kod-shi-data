"""ПОРЯДОК-1090: чи вибір образа тягне позиція. Дані справжніх промптів ВИБІР_V1 із вивантажених вердиктів, ті самі
образи (`ід`) крутимо циклічно (кожен стає першим рівно раз), промпт збираємо ПОТОЧНИМ збирачем, кличемо `claude -p`. Друкує: частку «обрано першого»
(0.20 — позиція нічого не важить, 1.00 — вибирає лише місце) і частку модального ід (1.00 — вибір не залежить від порядку).
Запуск: python3 проби/vybir_pozytsiia_1090.py <вердикти.gz>… [-n промптів] [-r ротацій]"""
import gzip, json, subprocess, sys, tempfile, collections, concurrent.futures as cf, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import збирач_промптів as ЗП, повнота_образу as ПО, дріт_моделі as Д
SYS = ("You are the model behind a mobile styling app. The user message is the application prompt, verbatim. Do exactly what it asks "
       "and output only the answer it asks for: raw JSON, no code fence, no preamble, no tools.")
def промпти(файли, ліміт):
    for ф in файли:
        for в in json.loads(gzip.open(ф, "rt").read())["прогони"][0]["вердикти"]:
            for к in (в.get("етапи") or {}).get("виклики", []):
                if к.get("крок") == "choice" and len((к["запит"].get("порядок") or {}).get("образи", [])) == 5 and ліміт[0] > 0:
                    ліміт[0] -= 1; yield "%s·р%s" % (os.path.basename(os.path.dirname(ф))[:18], в["рука"]), {x: y for x, y in json.loads(к["запит"]["текст"]).items() if x not in ("version", "task")}
def крутити(т, k):
    т = json.loads(json.dumps(т)); т["verdict"] = т["verdict"][k:] + т["verdict"][:k]; return т
def виклик(т):
    if hasattr(Д, "_ремарки_за_кодом"):    # після 1090 знахідки образів їдуть картою за кодом (як у мосту)
        т = dict(т); ремарки = {}
        for о in т["verdict"]: Д._ремарки_за_кодом(о, ремарки)
        т["remarks_by_code"] = ремарки
    т = ЗП.зібрати(ПО.ВИБІР, т, мова_тексту="English")
    p = subprocess.run(["claude", "-p", "--model", os.environ.get("MODEL", "sonnet"), "--tools", "", "--strict-mcp-config", "--no-session-persistence",
                        "--system-prompt", SYS], input=json.dumps(т, ensure_ascii=False, separators=(",", ":")), capture_output=True, text=True,
                       cwd=tempfile.mkdtemp(), timeout=600)
    try: return json.loads(p.stdout[p.stdout.index("{"):p.stdout.rindex("}") + 1])["chosen"]
    except Exception: return None
a = sys.argv[1:]; n = int(a[a.index("-n") + 1]) if "-n" in a else 8; R = int(a[a.index("-r") + 1]) if "-r" in a else 5
файли = [x for x in a if x.endswith(".gz")]; ліміт = [n]; завд = []
for ім, т in промпти(файли, ліміт):
    for k in range(R): завд.append((ім, k, крутити(т, k), крутити(т, k)["verdict"][0]["your_outfit"]["id"]))
with cf.ThreadPoolExecutor(6) as ex: рез = list(ex.map(lambda z: (z[0], z[3], виклик(z[2])), завд))
перші = [r[2] == r[1] for r in рез if r[2]]; по = collections.defaultdict(list)
for ім, п, о in рез:
    if о: по[ім].append(о)
мод = [max(collections.Counter(x).values()) / len(x) for x in по.values()]
print("викликів %d, без відповіді %d · обрано ПЕРШОГО %.2f (навмання 0.20) · модальний ід %.2f (1.00 — порядок не важить)" % (
    len(рез), sum(1 for r in рез if not r[2]), sum(перші) / max(1, len(перші)), sum(мод) / max(1, len(мод))))
for ім, x in по.items(): print("  %-24s %s" % (ім, " ".join(x)))
