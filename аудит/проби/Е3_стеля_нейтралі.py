"""Генератор вікна проти перевіряльника нейтралі на всьому каталозі — ДО і ПІСЛЯ одного визначення стелі
(корінь Е3-одна-величина, спроба 13; дошка 13465, 13466).

Запуск (модель і платні API не викликаються):
    python3 аудит/проби/Е3_стеля_нейтралі.py <корінь дерева> <каталог.pickle.gz>
Каталог — той самий pickle, що в `Е3_жорстке_ні_слова.py`. Друкує лічбу й відбитки:
  · розбіжність «генератор каже нейтраль» (`палітра_гамут.поріг_кольору(h, L)`: C* нижче порогу) проти
    `колір_річ.нейтраль(lab)` — на `lab` кожної речі й на сітці Lab (L* 0–100, a*, b* −60…60, крок 2), за
    ділянками тону;
  · `фід_добір.відстань_до_вікна` кожної речі до нейтрального вікна (L* 0–100, без температури): відбиток dC
    і скільки речей мають інше dC.
"""
import gzip, hashlib, json, os, pickle, sys, warnings
from pathlib import Path


def ділянка(h):
    """Ділянка тону для лічби: холодна, тепла, буре, решта."""
    if 230 <= h <= 300: return "холодна"
    if 45 <= h <= 115: return "тепла"
    if 28 <= h < 45: return "буре"
    return "решта"


def головна():
    """Розбіжності генератора й перевіряльника та відстань до нейтрального вікна."""
    дерево, каталог_шлях = Path(sys.argv[1]).resolve(), sys.argv[2]
    os.chdir(дерево / "джерела")
    sys.path.insert(0, str(Path.cwd()))
    warnings.simplefilter("ignore")
    import колір_річ as КР, палітра_гамут as ПГ, фід_добір as ФД
    from colorspace import lch
    with gzip.open(каталог_шлях, "rb") as ф:
        каталог = pickle.load(ф)
    def розбіжність(lab):
        L, C, h = lch(lab)
        генератор = C < ПГ.поріг_кольору(h, L)
        перевіряльник = КР.нейтраль(lab) is not None
        return None if генератор == перевіряльник else (ділянка(h), "генератор" if генератор else "перевіряльник")
    def лічба(точки):
        р = {}
        for lab in точки:
            в = розбіжність(lab)
            if в: р["%s: нейтраль каже лише %s" % в] = р.get("%s: нейтраль каже лише %s" % в, 0) + 1
        return dict(sorted(р.items()))
    речі = [r for r in каталог if r.get("lab")]
    сітка = [(L, a, b) for L in range(0, 101, 2) for a in range(-60, 61, 2) for b in range(-60, 61, 2)]
    вікно = dict(L_min=0.0, L_max=100.0, нейтраль=True)
    dC = {str(r.get("id")): ФД.відстань_до_вікна(r["lab"], вікно)["dC"] for r in речі}
    def відбиток(о):
        return hashlib.sha256(json.dumps(о, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:16]
    print(json.dumps(dict(
        речей_з_lab=len(речі), розбіжність_каталог=лічба(r["lab"] for r in речі),
        точок_сітки=len(сітка), розбіжність_сітка=лічба(сітка),
        dC_ненульових=sum(1 for v in dC.values() if v), відбиток_dC=відбиток(dC)), ensure_ascii=False))
    if len(sys.argv) > 3:
        with gzip.open(sys.argv[3], "wt", encoding="utf-8") as ф:
            json.dump(dC, ф)
    return 0


if __name__ == "__main__":
    sys.exit(головна())
