"""Е2 п.1–2: порівняння зі стартом кроку на всіх відповідних записах каталогу."""
import pathlib, sys, subprocess, collections
src = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(src))
import feed, фід_верхнє as upper, profile, пакет_моделі as model
import фід_каталог as fk
БАЗА = "92ebb6e6c70cab3718ac5ffb301069962f3878d0"

def до(name):
    ns = dict(__name__="до_" + name, __file__=str(src / (name + ".py")))
    code = subprocess.check_output(["git", "show", БАЗА + ":джерела/" + name + ".py"]).decode("utf8")
    exec(compile(code, ns["__file__"], "exec"), ns)
    return ns

u, p, m = до("фід_верхнє"), до("profile"), до("пакет_моделі")
offers, _ = feed.читати_yml(feed.каталог_на_диску("каталог_повний.xml"))
checked, delta = collections.Counter(), collections.Counter()
for offer in offers:
    a, b = u["верхні_атрибути"](offer), upper.верхні_атрибути(offer)
    checked["верхні"] += bool(a or b)
    delta["верхні"] += a != b
    record = fk.побудувати_запис_речі(offer)
    r = dict(offer, **record, сезон_тканини=record["ознаки_зі_слів"]["тканина"].get("сезон"))
    if r.get("слот") == "взуття":
        r.update(feed.взуттєві_атрибути(offer))
        checked["сенсорна"] += 1
        delta["сенсорна"] += p["сенсорний_збіг"]("підбори", r) != profile.сенсорний_збіг("підбори", r)
    if r.get("сезон_тканини") is not None and r.get("ціна"):
        for t in (-5, 15, 30):
            checked["тканина"] += 1
            delta["тканина"] += m["жорстке_відсічення"](r, темп_c=t) != model.жорстке_відсічення(r, темп_c=t)
print("Оферів: %d; перевірено: %s; змінено рішень: %s" % (len(offers), dict(checked), dict(delta)))
assert all(checked[k] for k in ("верхні", "сенсорна", "тканина")), checked
assert not any(delta.values()), delta
