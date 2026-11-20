import json,sys,collections
r=[json.loads(l) for l in open(sys.argv[1])]
П=lambda k:sum(x['після'][k] for x in r); Д=lambda k:sum(x['до'][k] for x in r)
print('викликів сторінки',len(r),'статуси після',dict(collections.Counter(x['після']['статус'] for x in r)),'до(тінь)',dict(collections.Counter(x['до']['статус'] for x in r)))
print('міст надіслав двічі: ДО',sum(1 for x in r if x['до']['провайдеру']>1),'ПІСЛЯ',sum(1 for x in r if x['після']['провайдеру']>1))
print('запитів провайдеру: ДО',Д('провайдеру'),'ПІСЛЯ',П('провайдеру'))
print('фото за адресою до провайдера: ДО',Д('url_фото'),'ПІСЛЯ',П('url_фото'),'| 400 на фото: ДО',sum(1 for x in r if x['до']['фото_400']),'ПІСЛЯ',sum(1 for x in r if x['після']['фото_400']))
print('фото, яких міст ПІСЛЯ не дотягнув (x-images-dropped):',sum(int(x['після'].get('x-images-dropped') or 0) for x in r),'у викликах',sum(1 for x in r if int(x['після'].get('x-images-dropped') or 0)))
