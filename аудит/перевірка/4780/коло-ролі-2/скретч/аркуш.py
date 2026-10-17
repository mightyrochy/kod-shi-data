import sys, os, json, pickle, random
SP = os.path.dirname(os.path.abspath(__file__)) + "/"; sys.path.insert(0, SP)
import в as V, foto
def зробити(в, мітка, зерно=1, n=40, ф=None):
    З = V.зміни(в)
    if ф: З = [з for з in З if eval(ф, {}, з)]
    print(мітка, "змін", len(З)); print(V.зведення(З)[:10])
    вибір = random.Random(зерно).sample(З, min(n, len(З))); рр = []
    for з in вибір:
        рр.append(dict(ід=з["ід"], фото=з["фото"], lab=з["lab"], центр_h=з["ц"], до=з["до"], пс=з["пс"],
                       підпис="%s/%s %s h%.0f→ц%.0f±%.0f L%.0f C%.0f" % (з["сх"][:6], з["роль"][:4], "сл" if з["слово"] else "вим", з["h"], з["ц"], з["пів"], з["L"], з["C"])))
    foto.аркуш(рр, SP + мітка + "_%d.png")
    json.dump([dict(з, lab=list(з["lab"]) if з["lab"] else None) for з in вибір], open(SP + мітка + ".json", "w"), ensure_ascii=False, indent=0)
    return З, вибір
if __name__ == "__main__":
    зробити(json.loads(sys.argv[1]), sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5] if len(sys.argv) > 5 else None)
