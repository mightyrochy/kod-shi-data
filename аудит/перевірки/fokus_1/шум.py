"""ФОКУС-1: знахідок на ідею в промпті ремонту (руки 1–2), найчастіші заяви, K-CRA-02 на кольорових образах
і що він велить (keep/quiet). Запуск із джерела/: python3 ../аудит/перевірки/fokus_1/шум.py <тека з ж*_*>"""
import json, gzip, glob, os, sys, collections as K
sys.path.insert(0, "."); import colorspace as cs, palettes as P
хр = lambda i: bool(i.get("hex")) and i.get("color") not in ("golden", "silvery", "pearly") and P._хроматична(cs.hx(i["hex"]))
кл = lambda s: s if isinstance(s, str) else next(iter(s))
ідей = зн = 0; З = K.Counter(); Ф = K.Counter()
for f in sorted(glob.glob(sys.argv[1] + "/ж*_*/вердикти.txt.gz")):
    for в in json.load(gzip.open(f, "rt"))["прогони"][0]["вердикти"]:
        if str(в["рука"]) not in "12": continue
        for c in в["етапи"]["виклики"]:
            if c["крок"] != "repair": continue
            for o in json.loads(c["запит"]["текст"])["verdict"]:
                ідей += 1; fs = o.get("findings", []); зн += len(fs)
                for fd in fs: З.update(кл(s) for s in fd.get("statements", []))
                if any(хр(i) for i in o["your_outfit"]["items"]):
                    Ф["кольорових"] += 1
                    for fd in fs:
                        for s in fd.get("statements", []):
                            if кл(s) == "focus_count_over_ceiling":
                                Ф["з K-CRA-02"] += 1; v = s[кл(s)] if isinstance(s, dict) else {}
                                Ф["  keep=%s quiet=%s" % (v.get("keep"), v.get("quiet"))] += 1
            break
print("ідей у ремонті %d · знахідок %d · на ідею %.1f" % (ідей, зн, зн / max(1, ідей)))
print("K-CRA-02 на кольорових образах:", dict(Ф))
print("найчастіші заяви:", ", ".join("%s %d" % kv for kv in З.most_common(12)))
