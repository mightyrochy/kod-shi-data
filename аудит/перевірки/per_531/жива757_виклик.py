import sys, os, json, tempfile, base64, subprocess, urllib.request, time, re
sys.path.insert(0, "/home/user/kod-shi-data/джерела"); os.chdir("/home/user/kod-shi-data/джерела")
import bridge as B, feed as F
SYS = ('You are the model behind a mobile styling app. The user message is the application prompt, verbatim. Do exactly what it asks and output only the answer it asks for: raw JSON with no code fence when it asks for JSON, plain prose when it asks for prose. No preamble, no commentary, no tools, no questions back.')
вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), каталог=F.каталог_на_диску("каталог_повний.xml"), сід=3)
вх["кеш_кольорів"] = os.path.join(tempfile.gettempdir(), "кеш_живого_шляху.json")
міст = lambda ім, d: json.loads(B.виклик(ім, json.dumps(d, ensure_ascii=False)))
IDS = json.loads(os.environ.get("IDS") or '["ж-03375@sunwin-store.com","ж-06971@cooshwear.com","ж-08702@attico.ua","ж-08209@attico.ua","ж-07742@honchstudio.com"]')
КЕШ = "/tmp/фото757"; os.makedirs(КЕШ, exist_ok=True)
def кадр(u):
    f = os.path.join(КЕШ, re.sub(r"\W", "_", u)[-120:])
    if not os.path.exists(f):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=40)
            open(f, "wb").write(r.read()); open(f + ".t", "w").write(r.headers.get("content-type", "image/jpeg").split(";")[0])
        except Exception as e: return None
    return (open(f + ".t").read(), base64.b64encode(open(f, "rb").read()).decode())
def жива(prompt, urls):
    bl, lost = [], 0
    for i, u in enumerate(urls):
        k = кадр(u)
        bl.append({"type": "text", "text": "Photo %d%s" % (i + 1, ":" if k else ": not available")})
        if k: bl.append({"type": "image", "source": {"type": "base64", "media_type": k[0], "data": k[1]}})
        else: lost += 1
    bl.append({"type": "text", "text": prompt})
    t0 = time.time()
    p = subprocess.run(["claude", "-p", "--model", "sonnet", "--tools", "", "--strict-mcp-config", "--no-session-persistence", "--input-format", "stream-json", "--output-format", "stream-json", "--verbose", "--system-prompt", SYS],
        input=json.dumps({"type": "user", "message": {"role": "user", "content": bl}}) + "\n", capture_output=True, text=True, timeout=600, cwd="/tmp")
    res = None
    for l in p.stdout.splitlines():
        try: o = json.loads(l)
        except Exception: continue
        if o.get("type") == "result": res = o
    return (res or {}).get("result", ""), round(time.time() - t0, 1), lost
def розібрати(t):
    t = t.strip(); t = re.sub(r"^```(?:json)?|```$", "", t, flags=re.M).strip()
    return json.loads(t)
if __name__ == "__main__":
    оп = dict(вх, ітерація=2, відповідь="ОПИС_ВІДПОВІДЬ_V1", ід=IDS, інші_образи=[])
    for n in range(int(sys.argv[1])):
        о = міст("опис", dict(вх, речі=IDS))
        т, с, lost = жива(о["промпт"], о["фото"])
        print("== спроба %d: %.1f с, кадрів %d, не дійшло %d" % (n + 1, с, len(о["фото"]), lost))
        try: a = розібрати(т)
        except Exception as e: print("   не JSON:", т[:200]); continue
        print("   swap:", a.get("swap"), "| wrong_photos:", a.get("wrong_photos"))
        print("   text:", (a.get("text") or "")[:400].replace("\n", " / "))
        if a.get("swap"):
            з = міст("від_моделі", dict(оп, текст_моделі=т))["заміна"]
            print("   код:", json.dumps({k: з.get(k) for k in ("стан", "відмова", "слот", "річ", "чому")}, ensure_ascii=False), "запасні", [x["id"] for x in з.get("запасні", [])], "відкинуто", [(x["id"], x["чому"]) for x in з.get("відкинуто", [])])
            if з.get("запасні"):
                зап = dict(річ=з["річ"], чому=з["чому"], запасні=[x["id"] for x in з["запасні"]])
                о2 = міст("опис", dict(вх, речі=IDS, номери=з["номери"], заміна=зап))
                т2, с2, l2 = жива(о2["промпт"], о2["фото"])
                print("   другий виклик: %.1f с, кадрів %d, не дійшло %d" % (с2, len(о2["фото"]), l2))
                a2 = розібрати(т2); print("   swap2:", a2.get("swap"))
                р = міст("від_моделі", dict(оп, заміна_запасні=зап, текст_моделі=т2))["заміна"]
                print("   рішення коду:", json.dumps({k: р.get(k) for k in ("стан", "відмова", "на", "річ")}, ensure_ascii=False))
                print("   text2:", (a2.get("text") or "")[:500].replace("\n", " / "))
