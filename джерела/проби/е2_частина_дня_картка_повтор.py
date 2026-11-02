"""Корінь Е2-частина-дня, крок 2 (ґ): записані репліки перекладача (`аудит/**/VIDPOVIDI/*_мовний_шар_репліка.txt`)
крізь суд підтвердження картки без моделі — скільки реплік прийнято й які з годиною словами чи годинником.
argv[1] — корінь дерева коду (типово — це); друкує «файл · прийнято · чому» і підсумок."""
import sys, os, json, glob, re, warnings
warnings.filterwarnings("ignore")
ТУТ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(sys.argv[1] if len(sys.argv) > 1 else ТУТ, "джерела"))
import мовний_шар as М

ГОДИНА = re.compile(r"\d{1,2}:\d\d|\bо\s+\w+(?:ій|ої)\s+(?:\w+\s+)?(?:вечора|дня|ранку|ночі)\b", re.I)
лічба = dict(всього=0, прийнято=0, з_годиною=0, з_годиною_прийнято=0)
for ф in sorted(glob.glob(os.path.join(ТУТ, "аудит/**/VIDPOVIDI/*_мовний_шар_репліка.txt"), recursive=True)):
    т = open(ф, encoding="utf8", errors="replace").read()
    try:
        репліка = json.loads(т.split("РЕПЛІКА:", 1)[1].split("── ВІДПОВІДЬ", 1)[0].strip())
        в = т.split("── ВІДПОВІДЬ", 1)[1]
        текст = json.loads(в[в.find("{"):в.rfind("}") + 1])["text"]
    except Exception:
        continue
    прийнято, чому = М.суд_репліки(текст, репліка)
    година = bool(ГОДИНА.search(текст))
    лічба["всього"] += 1
    лічба["прийнято"] += bool(прийнято)
    лічба["з_годиною"] += година
    лічба["з_годиною_прийнято"] += година and bool(прийнято)
    print("%s · %s · %s · %s" % (os.path.relpath(ф, ТУТ)[:110], "так" if прийнято else "ні",
                                ",".join(sorted({ч.get("чому", "?") for ч in чому})) or "-", текст[:90].replace("\n", " ")))
print("ПІДСУМОК", json.dumps(лічба, ensure_ascii=False))
