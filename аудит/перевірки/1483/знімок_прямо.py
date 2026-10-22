import asyncio, gzip, os, sys, hashlib
дер = sys.argv[1]; вих = sys.argv[2]
дж = os.path.join(дер, "джерела")
вхід = os.path.join(дер, "аудит/проби/знімок_входи_сід3.jsonl.gz")
sys.path.insert(0, os.path.join(дж, "прилади"))
import warnings; warnings.simplefilter("ignore")
import знімок_мосту as З
З.підготувати(дж)
текст = gzip.open(вхід, "rt", encoding="utf-8").read()
знімок, час = asyncio.run(З.прогнати(текст))
open(вих, "w", encoding="utf-8").write(знімок)
print("викликів", знімок.count("\n") - 1, "· мс_разом", час["мс_разом"], "· помилок", знімок.count('"помилка"'))
