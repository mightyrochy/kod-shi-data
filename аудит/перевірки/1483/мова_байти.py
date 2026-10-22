import json, os, sys, hashlib
дер = sys.argv[1]; os.chdir(дер); sys.path.insert(0, os.path.abspath("джерела"))
import вердикт_моделі as ВМ
м = dict(можна_видавати=False, порушення=[dict(правило="X", суть="тест", збіги=["a"])])
for н in ("ОБРАЗИ_V1", "ДОПОВНЕННЯ_V1"):
    o = ВМ.мова_повтор(м, спроба=1, відповідь=н)
    print(н, hashlib.sha256(json.dumps(o, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12], o["формат"])
