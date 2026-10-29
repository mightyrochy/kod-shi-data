import sys, json, hashlib, os
sys.path.insert(0, "."); sys.path.insert(0, "../аудит/колір_р3")
import cv2, numpy as np
import виміряти as В
from жнива_маски import маска_речі
from жнива_промпти import тип_речі
import feed as F
ід_список = sys.argv[2:]; вих = sys.argv[1]
offers = {o["id"]: o for o in F.читати_yml(F.каталог_на_диску())[0]}
ж = В.зроблені()
плитки = []
for ід in ід_список:
    j = ж[[k for k in ж if k.startswith(ід)][0]]
    o = offers[j["id"]]
    ф = В.скачати(j["url"], j["id"])
    слот = тип_речі(o)[1]
    м, dom, чому, дж = маска_речі(ф["шлях"], слот)
    img = cv2.imread(ф["шлях"]); h, w = img.shape[:2]; s = 300 / h
    img = cv2.resize(img, (int(w * s), 300))
    ов = img.copy()
    if м is not None:
        мм = cv2.resize(м, (img.shape[1], 300)) > 127
        ов[мм] = (0.5 * ов[мм] + 0.5 * np.array([0, 255, 0])).astype("uint8")
    cv2.putText(ов, "%s %s->%s" % (ід[-5:], j["слово_було"], j["основний"]["слово"]), (5, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    cv2.putText(ов, "%s m=%.2f" % (j["маска"], j["частка_маски"]), (5, 45), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    сх = np.zeros((300, 360, 3), "uint8"); 
    for k, c in enumerate(j["кластери"][:4]):
        hx = c[2].lstrip("#"); bgr = tuple(int(hx[i:i+2], 16) for i in (4, 2, 0))
        cv2.rectangle(сх, (0, k*90), (360, k*90+85), bgr, -1); cv2.putText(сх, "%s %.2f" % (c[0], c[1]), (5, k*90+50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255) , 2)
    плитки.append(np.hstack([img, ов, сх]))
W=max(t.shape[1] for t in плитки)
плитки=[np.pad(t,((0,0),(0,W-t.shape[1]),(0,0))) for t in плитки]
cv2.imwrite(вих, np.vstack(плитки), [cv2.IMWRITE_JPEG_QUALITY, 70])
