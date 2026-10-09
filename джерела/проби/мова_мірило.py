"""ОЦІНКА-МОВА (рядки 1431–1434): мовні вади на теці живих прогонів стенда (підтеки з картки.txt,
текст_екранів.txt, відповіді.tar.gz). Друкує лічбу: биті знаки й «ы э ё ъ» у видимому; слова двох абеток у
відповідях шару; антиприклади шаблону; мова лічильника зауважень; wear_with_change без «change»; шкала
ошатності числами. Запуск: python3 проби/мова_мірило.py <тека> (розбір 02.10 — аудит/перевірки/rozbir_0210)"""
import sys, os, re, tarfile, collections
БИТІ = re.compile(r"[†�]|[ыэёъЫЭЁЪ]"); СЛОВО = re.compile(r"[A-Za-zА-ЯҐЄІЇа-яґєії'’ʼ]+")
ЛІЧИЛЬНИК = re.compile(r"(кількість|вагу) зауважень|зауваження зникн|нове зауваження|(усі|всі|решта) зауважен|знайшла клітинка|"
                       r"(number|weight) of (the )?(findings|remarks|issues)|fewer (findings|remarks)|(findings|remarks) "
                       r"(disappear|go away)|new (small |minor )?(finding|remark)|(all|every) (the )?(findings|remarks)", re.I)
ШКАЛА = re.compile(r"ошатн\w*[^.]{0,40}\b(з|від) \d+ (до|на) \d+", re.I)
мішане = lambda т: [с for с in СЛОВО.findall(re.sub(r"\\[nrtu]", " ", т))
                    if re.search("[A-Za-z]", с) and re.search("[а-яґєіїА-ЯҐЄІЇ]", с)]
лік, прогони = collections.Counter(), collections.defaultdict(set)
def додати(к, n, прогін):
    if n: лік[к] += n; прогони[к].add(прогін)
корінь = sys.argv[1]
for прогін in sorted(os.listdir(корінь)):
    д = os.path.join(корінь, прогін)
    if not os.path.isfile(os.path.join(д, "відповіді.tar.gz")): continue
    видиме = "".join(open(os.path.join(д, ф), encoding="utf-8", errors="replace").read()
                     for ф in ("картки.txt", "текст_екранів.txt") if os.path.exists(os.path.join(д, ф)))
    додати("биті знаки й «ыэёъ» у видимому", len(БИТІ.findall(видиме)), прогін)
    додати("шкала ошатності числами у видимому", len(ШКАЛА.findall(видиме)), прогін)
    додати("мова лічильника у видимому", len(ЛІЧИЛЬНИК.findall(видиме)), прогін)
    додати("«зауважен» у видимому (усе)", len(re.findall(r"зауважен", видиме, re.I)), прогін)
    with tarfile.open(os.path.join(д, "відповіді.tar.gz")) as тар:
        for ч in тар.getmembers():
            if not ч.isfile(): continue
            т = тар.extractfile(ч).read().decode("utf-8", "replace"); в = т.split("── ВІДПОВІДЬ", 1)[-1] if "── ВІДПОВІДЬ" in т else ""
            if "мовний_шар" in ч.name:
                додати("слова двох абеток у відповідях шару", len(мішане(в)), прогін)
                додати("антиприклади шаблону у відповідях шару", len(re.findall(r"personally|spідниц", в, re.I)), прогін)
            if "ОЦІНКА_відповідь" in ч.name:
                додати("мова лічильника у відповідях оцінки", len(ЛІЧИЛЬНИК.findall(в)), прогін)
                додати("wear_with_change без change", int('"wear_with_change"' in в and bool(re.search(r'"change"\s*:\s*\[\s*\]', в))), прогін)
for к in sorted(лік):
    print("%-42s %4d у %2d прогонах" % (к, лік[к], len(прогони[к])))
print("прогонів у теці:", len([п for п in os.listdir(корінь) if os.path.isfile(os.path.join(корінь, п, "відповіді.tar.gz"))]))
