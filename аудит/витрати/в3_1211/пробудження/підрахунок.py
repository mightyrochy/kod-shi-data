"""Пробудження координаторів: подій result у вікні за origin.kind (пр_*.tsv цього тижня, пр0_*.tsv минулого; рядок: час, origin, total_cost_usd, num_turns, токени)."""
import csv,collections,glob,os
В=os.path.dirname(os.path.abspath(__file__))
ТИЖ={'0512':('2026-11-05T00:00:00','2026-11-12T00:00:00',
  {'менеджер':['a6nzmnfV','ZpRFDaVD','YXzFVPfN'],'диспетчер':['XXt31teF','Xoe5Djj6','acf6reBG','XYU1bjhB','b2wM67V4','YP2kgihe']},'пр_'),
 '0511':('2026-10-29T00:00:00','2026-11-05T00:00:00',
  {'менеджер':['az2yECem','YEiCWmgR','ZSwAz7j9','Zyd9M1gn'],'диспетчер':['ashigctm','astP8DST','Z1MYxadS','Y6a3ufUC']},'пр0_')}
# цього тижня додатково: менеджер 03.11 (Zyd9M1gn, пр0_) і диспетчер-15 (Y6a3ufUC, пр0_) — їхні події після 05.11 00:00
ДОДАТИ={'менеджер':['пр0_Zyd9M1gn'],'диспетчер':['пр0_Y6a3ufUC']}
for т,(a,b,г,пр) in ТИЖ.items():
    for роль,ід in г.items():
        c=collections.Counter(); п=[пр+i for i in ід]+(ДОДАТИ[роль] if т=='0512' else [])
        for f in п:
            for r in csv.reader(open(f'{В}/{f}.tsv'),delimiter='\t'):
                if a<=r[0]<b: c[r[1]]+=1
        print(т,роль,sum(c.values()),dict(c))
