"""Лічба службових слів у реченнях жінці з логу стенда (рядки «→» після «· <місце>: {json}»): місце → слово → скільки.
Аргументи: лог.txt… Слова — ті, що жінки назвали у вадах 3 і 10 (аудит/проби/живий-як-людина-1/вади.md) і ключі ядра."""
import re, sys, collections, json
СЛОВА = re.compile(r"маківк|підборідд|\bпах[уаи]?\b|похибк|анкет|заявлен\w* колон|колон[аиу]|структур\w* світлот|"
                   r"нейтрал\w* однієї світлот|правил[оауіа]?\b|\bсхем\w*|рівноцінн|шаблон\w* тіла|\w+_\w+", re.I)
к = collections.Counter(); рядків = collections.Counter(); всього = 0
for ф in sys.argv[1:]:
    місце = None
    for р in open(ф, encoding="utf-8", errors="replace"):
        м = re.match(r"\s+· (\S+) · (\S+?): (\{.*)", р)
        if м:
            місце = м.group(2).split(".")[0]
            код = ",".join(dict.fromkeys(re.findall(r'"code":"([a-z_]+)"', м.group(3)))) or "?"
            continue
        м = re.match(r"\s+→ (.*)", р)
        if м and місце:
            всього += 1
            for с in СЛОВА.findall(м.group(1)):
                к[(місце, код, с.lower())] += 1; рядків[(місце, код)] += 1
for (м, код, с), n in sorted(к.items(), key=lambda x: -x[1]): print(n, м, код, с)
print("РАЗОМ речень", всього, "службових слів", sum(к.values()))
