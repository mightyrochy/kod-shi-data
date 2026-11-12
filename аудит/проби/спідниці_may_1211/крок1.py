import sys, json, base64
sys.path.insert(0, '/home/user/kod-shi-data/джерела')
import warnings; warnings.filterwarnings('ignore')
import міст_вхід as МВ, міст_річ as МР
from PIL import Image
У = '/root/.claude/uploads/1ddfeba9-3459-57a6-83c6-de9694b909c9/'
# ── 1. ЇЇ КОЛЬОРИ З ПОРТРЕТА: відповідь моделі ─────────────────────
A = '{"photo": "portrait_face_small", "skin": [], "hair": [], "eyes": null, "limbal_ring": null, "light_cast": "none", "light_correction": "none"}'
print('ПОРТРЕТ A (чесна відповідь моделі):', json.dumps(МВ.прийняти_колір(A), ensure_ascii=False))
B = json.dumps({"photo": "usable", "skin": ["#aa7b67", "#c7937e", "#aa7865"], "hair": ["#c2a377", "#9f8459"],
                "eyes": None, "limbal_ring": None, "light_cast": "none", "light_correction": "none"})
print('ПОРТРЕТ B (якби придатний, очей не видно):', json.dumps(МВ.прийняти_колір(B), ensure_ascii=False))
# ── 2. РЕЧІ З ФОТО: промпт і відповідь моделі ───────────────────────
ФОТО = [dict(ід='ф%d' % i, ширина=909, висота=2000) for i in range(1, 6)]
ФАЙЛИ = dict(ф1='d2684e76', ф2='8a6d9294', ф3='f73c50c7', ф4='1269cb00', ф5='99fb7682')
п = json.loads(МР.річ_з_фото(dict(опис_фото='промпт', фото=ФОТО)))
print('ПРОМПТ речей: %d символів; підписи %s' % (len(п['промпт']), п['підписи']))
def р(ф, name, color, cut, form, fr, fabric=None):
    return dict(photo=ф, name=name, slot='bottom', kind='skirt', color=color, fabric=fabric, cut=cut, length='midi',
                pattern='floral', formality=form, owner='want_to_buy' if False else 'unknown',
                frame=dict(zip(('left', 'top', 'right', 'bottom'), fr)))
ВІДП = dict(items=[
  р('ф1', 'FLORA FALL purple sequin floral tulle midi skirt set', 'purple', 'pencil', 'smart', (297, 335, 710, 838)),
  р('ф2', 'MALVA powder pink 3D flower organza midi skirt', 'powder_pink', 'pencil', 'smart', (248, 330, 757, 830)),
  р('ф3', 'MALVA black 3D flower organza midi skirt', 'black', 'pencil', 'smart', (154, 248, 809, 883)),
  р('ф4', 'FLORA FALL green sequin floral tulle midi skirt set', 'pine_green', 'pencil', 'smart', (198, 248, 748, 883)),
  р('ф5', 'FLORA beige sequin floral tulle midi skirt', 'beige', 'pencil', 'smart', (171, 178, 794, 868)),
])
рр = json.loads(МР.річ_з_фото(dict(опис_фото='відповідь', фото=ФОТО, відповідь_моделі=json.dumps(ВІДП))))
print('РОЗБІР: причина=%s незнайомі=%s нотатки=%s' % (рр.get('причина'), рр.get('незнайомі'), рр.get('нотатки')))
for x in рр['речі_з_фото']:
    print('  ', {k: x.get(k) for k in ('ід', 'фото', 'слот', 'колір', 'крій', 'довжина', 'принт', 'ошатність', 'чия', 'закріплена')})
json.dump(dict(речі=рр['речі_з_фото'], файли=ФАЙЛИ), open('/tmp/прогін/речі.json', 'w'), ensure_ascii=False, default=str)
