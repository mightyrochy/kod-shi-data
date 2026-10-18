# Скретч 2.1-Б: різниця вердиктів ДО (main) → ПІСЛЯ (гілка) зі збирача; аркуш 40 речей (одна зміна на річ, сід), без ролі очей K-PAL-17 (5010).
import sys, os, json, random, collections as K
SP = os.path.dirname(os.path.abspath(__file__)) + "/"; sys.path.insert(0, SP); import foto, colour_hex
до, пс = (json.load(open(f, encoding="utf-8")) for f in sys.argv[1:3]); сід = int(sys.argv[3]); вих = sys.argv[4]
кут = lambda a, b: min(abs(a - b) % 360, 360 - abs(a - b) % 360)
Л, з = K.Counter(), []
for к, в0 in до["тон"].items():
    в1 = пс["тон"][к]
    if в0 == в1: continue
    ід, ім, д = к.split("|"); д = json.loads(д); р = до["речі"][ід]; дж = "суд" if р["вим"] else "суд-сл"; Л[(дж, ім.split("/")[0], в0 + "→" + в1)] += 1
    пів = ((д[1] - д[0]) % 360) / 2; ц = (д[0] + пів) % 360; кр = д[0] if кут(р["h"], д[0]) < кут(р["h"], д[1]) else д[1]
    з.append(dict(р, ід=ід, дж=дж, ім=ім, д=д, ц=ц, пів=пів, до=в0, пс=в1, край_h=кр, центр_h=ц))
for к, (с0, р0, о) in до["17"].items():
    с1, р1, _ = пс["17"][к]; ід = к.split("|")[0]; р = до["речі"][ід]
    if р0 != р1: Л[("17-очі", р0 + "→" + р1)] += 1
    if с0 != с1:
        Л[("17-стан", с0 + "→" + с1)] += 1; з.append(dict(р, ід=ід, дж="17-стан", ім="очі " + о, д=None, ц=р["h"], пів=0, до=с0[:7], пс=с1[:7], край_h=None, центр_h=None))
for к, v in sorted(Л.items()): print("  %-50s %6d" % (" · ".join(к), v))
по = {}
for p in random.Random(сід).sample(з, len(з)): по.setdefault(p["ід"], p)
вибір = list(по.values())[:40]
for p in вибір: p["фото"] = (p["фото"] or [None])[0] if isinstance(p["фото"], list) else p["фото"]
print("змін", len(з), "речей", len(по), K.Counter(p["дж"] for p in вибір))
for p in вибір:
    за = max(0.0, кут(p["h"], p["ц"]) - p["пів"]) if p["д"] else 0.0
    p["підпис"] = "%s %s h%.0f %s +%.1f° L%.0f C%.0f" % (p["дж"], p["ім"][:14], p["h"], ("ц%.0f±%.0f" % (p["ц"], p["пів"])) if p["д"] else "", за, p["L"], p["C"])
foto.аркуш(вибір, SP + вих + "_%d.png")
json.dump(вибір, open(SP + вих + ".json", "w"), ensure_ascii=False, indent=0)
