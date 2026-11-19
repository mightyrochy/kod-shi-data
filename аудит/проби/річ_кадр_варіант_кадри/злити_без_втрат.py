"""Злити новий вимір кадрів із попереднім без втрат: кадр, що мав колір (`lab`), а в новому прогоні не скачався
(`не скачалось: <urlopen error …>` — збій DNS посеред прогону — чи «лише ATR: чекає SAM» — ATR-прогін не взяв кадр, який раніше виміряв SAM), лишається зі старим записом.
Запуск: python злити_без_втрат.py <раніше.gz> <нове.gz> <вихід.gz>"""
import gzip, json, sys

def читати(ш):
    with gzip.open(ш, "rt", encoding="utf-8") as f:
        return json.load(f)

стар, нов = читати(sys.argv[1]), читати(sys.argv[2])
повернуто = 0
for ід, кадри in нов["записи"].items():
    A = {к.get("url"): к for к in стар["записи"].get(ід, [])}
    for і, к in enumerate(кадри):
        о = A.get(к.get("url"))
        if о and о.get("lab") and not к.get("lab") and str(к.get("чому", "")).startswith(("не скачалось", "лише ATR")):
            кадри[і] = о
            повернуто += 1
with gzip.open(sys.argv[3], "wt", encoding="utf-8") as f:
    json.dump(нов, f, ensure_ascii=False)
print("повернуто старих кадрів із кольором:", повернуто)
