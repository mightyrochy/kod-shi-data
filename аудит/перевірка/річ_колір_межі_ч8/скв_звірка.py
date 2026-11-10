"""Звірка ч8: `кут_розсіяння` (тепер `колір_тон.кругова_скв`) проти старої формули на 200 000 випадкових наборів тонів і ваг.

Запуск із `джерела/`: python3 ../аудит/перевірка/річ_колір_межі_ч8/скв_звірка.py"""
import math, random, sys
sys.path.insert(0, '.')
from колір_простір_риси import кут_розсіяння
def старе(hs, ваги=None):
    if not hs: return None
    ваги = ваги or [1.0]*len(hs); S = sum(ваги) or 1.0
    Cc = sum(w*math.cos(math.radians(h)) for h, w in zip(hs, ваги)) / S
    Ss = sum(w*math.sin(math.radians(h)) for h, w in zip(hs, ваги)) / S
    R = (Cc*Cc + Ss*Ss) ** 0.5
    return round(math.degrees((-2*math.log(max(R, 1e-9))) ** 0.5), 1)
random.seed(8); n = рівні = падінь_старого = нові_на_падінні = 0; різні = []
for _ in range(200000):
    k = random.randint(0, 5)
    hs = [random.choice([random.uniform(0, 360), round(random.uniform(0, 360)), 37.3]) for _ in range(k)]
    if random.random() < 0.3 and hs: hs = [hs[0]] * k
    ваги = None if random.random() < 0.5 else [random.choice([random.uniform(0, 3), 0.25, 1.0]) for _ in hs]
    n += 1
    try: a = старе(hs, ваги)
    except TypeError:
        падінь_старого += 1; b = кут_розсіяння(hs, ваги); нові_на_падінні += (b == 0.0); continue
    b = кут_розсіяння(hs, ваги)
    if a == b: рівні += 1
    else: різні.append((hs, ваги, a, b))
print("наборів", n, "рівні", рівні, "старе падало TypeError", падінь_старого, "з них нове 0.0", нові_на_падінні, "різні", len(різні), різні[:3])
