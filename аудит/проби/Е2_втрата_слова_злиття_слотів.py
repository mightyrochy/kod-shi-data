"""Межа з коментаря (15511): записи ОДНОГО слова про різні слоти зберігаються об'єднанням, порядок записів не важить.
Запуск (модель і платні API не викликаються):
    python3 аудит/проби/Е2_втрата_слова_злиття_слотів.py <корінь дерева> <каталог.pickle.gz>
Каталог — pickle `feed._прочитати_каталог(feed.каталог_на_диску(), ліміт_фото=0)['каталог']` (27 525 речей).
Друкує: слоти меж на обох порядках (міді; large_print) через `паспорт_з_коментаря`; на каталозі — речі слота названого
в записах, яких слово торкається, а межа з паспорта їх НЕ зняла («пропущено»); глобальну межу (запис без слота)."""
import gzip, itertools, os, pickle, sys, warnings
from pathlib import Path
дерево = Path(sys.argv[1]).resolve()
os.chdir(дерево / "джерела"); sys.path.insert(0, str(Path.cwd())); warnings.simplefilter("ignore")
import мовний_шар as М, пакет_моделі as ПМ
каталог = pickle.load(gzip.open(sys.argv[2], "rb"))
ЗАПИСИ = {"midi": [dict(slot="outerwear", length="midi"), dict(slot="dress", length="midi")],
          "large_print": [dict(slot="outerwear", feature="large_print"), dict(slot="dress", feature="large_print")]}
def вето(записи):
    п = M_(dict(vetoes=записи))
    return (п["паспорт"] or {}).get("вето_тверде") or {}
M_ = lambda в: М.паспорт_з_коментаря(в, паспорт_досі={"вето": {}, "бажання": []})
for ім, зап in ЗАПИСИ.items():
    слово = М._ВМ.ключ("length" if ім == "midi" else "feature", ім)
    цілі = {"сукня", "верхній_шар"}; пропущено = {}
    добре = 0
    for порядок in itertools.permutations(зап):
        в = вето(list(порядок)); сл = (в.get("слоти") or {}).get(слово) or []
        добре += set(сл) == цілі
        пропущено[порядок[0]["slot"]] = {с: sum(1 for r in каталог if r.get("слот") == с
            and (ПМ.жорстке_відсічення(r, вето={"типи": [слово]}) or "").startswith("person_veto")
            and not (ПМ.жорстке_відсічення(r, вето=в) or "").startswith("person_veto")) for с in sorted(цілі)}
        print("  порядок першим %s: слоти %s" % (порядок[0]["slot"], сл))
    print("%s: обидва слоти в %d з 2 порядків; пропущено на каталозі %d речей (%s)" % (
        ім, добре, len(каталог), пропущено))
# глобальна межа: запис без слота + запис зі слотом тієї самої межі — лишається глобальною
for порядок in itertools.permutations([dict(length="midi"), dict(slot="dress", length="midi")]):
    в = вето(list(порядок)); print("глобальна:", "слоти.міді" if "міді" in (в.get("слоти") or {}) else "міді без слота (глобально)",
                                  "типи", в.get("типи"))
