# -*- coding: utf-8 -*-
"""П.4: «радимо» = мовчазний дефолт = верх рангу (bridge.py:565-577). Чи це
завжди нейтраль (тоді «радимо» нічого не радить) і чи поділ рекомендовані/
інші має опору в корпусі."""
import sys, os, json, subprocess
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as cs, bridge as B

вх = json.load(open("стенд_вх.json", encoding="utf-8"))
ПРОФІЛІ = [
    ("1 середня нейтральна", вх["шкіра"], вх["волосся"][0], вх["очі"]),
    ("2 світла холодна", "#eec2b0", "#e8d5b0", "#8a9bb0"),
    ("3 смаглява тепла", "#96632f", "#3a2a1a", "#4a3222"),
]

усі_нейтраль = True
for назва, шк, вл, оч in ПРОФІЛІ:
    F = cs.features(cs.hx(шк), cs.hx(вл), cs.hx(оч))
    _топ = (B._основи(F, intent="conventional")["рекомендовані"] or [None])[0]
    рід = "нейтраль" if _топ["осі"]["Cstar"] < 8 else "колір"   # той самий поріг, що bridge.py:576
    усі_нейтраль = усі_нейтраль and (рід == "нейтраль")
    print("профіль %-24s радимо: %s %-10s Cstar=%.1f бал=%.3f — %s"
          % (назва, _топ["hex"], _топ["назва"], _топ["осі"]["Cstar"], _топ["бал"], рід))

print("\nу всіх трьох профілів «радимо» = нейтраль: %s" % усі_нейтраль)

п = subprocess.run(["grep", "-n", "-i", "рекомендован\\|радимо", "аудит/ПРАВИЛА.md"],
                    capture_output=True, text=True)
print("grep -n -i 'рекомендован|радимо' аудит/ПРАВИЛА.md → %d рядків (%s)"
      % (len([l for l in п.stdout.splitlines() if l]), "порожньо" if not п.stdout.strip() else "є збіги"))
print('bases.py:43: «...ранг лишається T3-конвенцією, а не виміром. Тому в UI '
      'він і зветься «рекомендовані», а не «ваші кольори», і сусідній ряд '
      '«інші» ніколи не ховається.»')
