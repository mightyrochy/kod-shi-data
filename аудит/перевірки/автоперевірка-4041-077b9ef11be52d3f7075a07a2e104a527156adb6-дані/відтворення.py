import json,pathlib,sys

source=pathlib.Path(sys.argv[1]).resolve()/'джерела'
sys.path.insert(0,str(source))
import формальність as F, outfit as O
from реєстр_константи import REGISTRY
from реєстр_тіри import тір_правила

item=dict(id='сукня-біла',назва='Біла сукня',слот='сукня',тип='сукня',
          colors=[dict(hex='#ffffff',coverage=1.0)],площа=0.6,блиск=3,
          місце_стилістки={'біля_обличчя':'так'})
kwargs=dict(нагода='весілля_гість',зарезервований_колір='near_white',пора='вечір',речі=[item])
def findings():
    return [dict(правило=z['правило'],сила=z['сила'],вага=z.get('сила_нп'),блокує=z.get('блокує'),
                 регістр=z.get('регістр'),суть=z.get('суть'))
            for z in F.нагода_палітра(O.елементи([item],стан='надворі'),**kwargs)]
print('КОНСТАНТА',json.dumps(REGISTRY['біле_хрома_підлога'],ensure_ascii=False))
print('ГОЛОВА',json.dumps(dict(тір=тір_правила('K-KOH-08'),знахідки=findings()),ensure_ascii=False))
# Лише в пам'яті проби: те саме число й T3, додано належність правилу з паспорта.
REGISTRY['біле_хрома_підлога']['прав']=['K-KOH-08']
print('З_ПРАВ',json.dumps(dict(тір=тір_правила('K-KOH-08'),знахідки=findings()),ensure_ascii=False))
