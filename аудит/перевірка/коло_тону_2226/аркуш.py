import json, random, sys
from PIL import Image, ImageDraw, ImageFont
п = json.load(open("/tmp/пр/мої.json", encoding="utf-8"))
р = random.Random(2910)
зм = [x for x in п if "незм" not in x]; ні = [x for x in п if "незм" in x and x["до"]=="ні" and 10 <= x["дк"] <= 40]
вибір = р.sample(зм, 30) + р.sample(ні, 20)
ш = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
оп=[]
for л in range(0, 50, 10):
    ар = Image.new("RGB", (1000, 10*120), "white"); д = ImageDraw.Draw(ар)
    for i, x in enumerate(вибір[л:л+10]):
        y=i*120; н=л+i+1
        for j, c in enumerate((x["a"], x["b"])):
            X=10+j*330; д.rectangle((X, y+5, X+300, y+85), fill=c[2]); д.text((X, y+90), "%s %s"%(c[2], (c[1] or "")[:34]), fill="black", font=ш)
        д.text((680, y+35), "#%d Δколо %.1f\n%s → %s"%(н, x["дк"], x["до"], x["піс"]), fill="black", font=ш)
        д.line((0,y+118,1000,y+118), fill="#999"); оп.append(dict(x,н=н))
    ар.save("/tmp/мій/аркуш_%d.png"%(л//10+1))
json.dump(оп, open("/tmp/мій/аркуш.json","w",encoding="utf-8"), ensure_ascii=False)
