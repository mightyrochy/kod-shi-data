"""Форма входу шару — мапа, як відповідь (рядок 6752): replay записів `*мовний_шар.txt` з блоком ТЕКСТИ живого прогону.
Без моделі друкує по запису, скільки текстів, чи вхід нового промпта — мапа «н → текст», і записану відповідь через
`прийняти`: перекладено / без відповіді, віддзеркалений вхід (`input_form_read`). З MODEL_URL і MODEL_MOVA (LM Studio)
шле новий промпт і друкує те саме для живої відповіді плюс тексти з латиницею поза назвами (англійська жінці).
Запуск: [MODEL_URL=http://127.0.0.1:1234/v1 MODEL_MOVA=…] python3 проби/мова_форма_мапою_6752.py <тека прогону>"""
import sys, os, re, json, glob, urllib.request
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import мовний_шар as МШ

URL, М = os.environ.get("MODEL_URL"), os.environ.get("MODEL_MOVA")
ЛАТИНИЦЯ = re.compile(r"\b[A-Za-z]{3,}(?:\s+[A-Za-z]{3,}){3,}")   # чотири англійські слова поспіль — не назва бренду
підсумок = dict.fromkeys(("записів", "мапа", "текстів", "записано_перекладено", "записано_віддзеркалено",
                          "живо_перекладено", "живо_віддзеркалено", "живо_англійською"), 0)

def лічба(розм, відповідь, хто):
    п = МШ.прийняти(розм, відповідь)
    підсумок[хто + "_перекладено"] += len(розм) - len(п["без_відповіді"])
    підсумок[хто + "_віддзеркалено"] += МШ.ФОРМА_ВХОДУ in п["нотатки"] and bool(п["без_відповіді"])
    return п
for ф in sorted(glob.glob(os.path.join(sys.argv[1], "**", "*мовний_шар.txt"), recursive=True)):
    т = open(ф, encoding="utf8").read()
    if "\nТЕКСТИ:\n[" not in т or '"виправ"' in т:
        continue
    вхід, _ = json.JSONDecoder().raw_decode(т.split("\nТЕКСТИ:\n", 1)[1])
    розм = МШ.розмітити({str(х["н"]): х["текст"] for х in вхід})
    пр = МШ.промпт(розм)
    мапа = isinstance(json.loads(пр.split("ТЕКСТИ:\n", 1)[1]), dict)
    п = лічба(розм, т.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1], "записано")
    підсумок.update(записів=підсумок["записів"] + 1, мапа=підсумок["мапа"] + мапа, текстів=підсумок["текстів"] + len(розм))
    рядок = "%s · текстів %d · вхід мапою %s · записано без відповіді %d" % (
        os.path.relpath(ф, sys.argv[1]), len(розм), мапа, len(п["без_відповіді"]))
    if URL and М:
        з = urllib.request.Request(URL.rstrip("/") + "/chat/completions", headers={"Content-Type": "application/json"},
                                   data=json.dumps(dict(model=М, messages=[{"role": "user", "content": пр}], **МШ.ВИБІРКА)).encode())
        ж = лічба(розм, json.load(urllib.request.urlopen(з, timeout=600))["choices"][0]["message"]["content"], "живо")
        англ = [к for к, в in ж["тексти"].items() if ЛАТИНИЦЯ.search(в)]
        підсумок["живо_англійською"] += len(англ)
        рядок += " · живо без відповіді %d · англійською %s" % (len(ж["без_відповіді"]), англ)
    print(рядок)
print("ПІДСУМОК:", json.dumps(підсумок, ensure_ascii=False))
