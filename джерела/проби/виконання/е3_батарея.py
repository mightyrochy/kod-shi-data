"""Оркестратор батареї й запису кожної ваги погоди; аргументи: префікс, коміт ДО."""
def main():
    """Виконати батарею й зберегти ваги погодних знахідок на базі або голові."""
    import gzip,json,os,pathlib,runpy,subprocess,sys,time,traceback,functools,inspect
    корінь=pathlib.Path.cwd(); джерела=корінь/'джерела'; sys.path[:0]=[str(джерела),str(джерела/'проби')]
    префікс=sys.argv[1]; база=sys.argv[2] if len(sys.argv)>2 else None
    if база:
        from виконання.е3_база import встановити
        встановити(база)
    import суд_погода as П
    from реєстр_сила import обмежити_вагу
    записи=[]; мітка=''
    def обгорнути(функція):
        """Обгорнути погодну функцію записом її результату."""
        @functools.wraps(функція)
        def виклик(*аргументи,**параметри):
            """Записати сиру й обмежену вагу кожної поверненої знахідки."""
            результат=функція(*аргументи,**параметри)
            for з in результат if isinstance(результат,list) else []:
                if isinstance(з,dict) and 'правило' in з:
                    записи.append([мітка,функція.__name__,з.get('правило'),з.get('суть'),з.get('речі'),з.get('сила'),з.get('сила_нп'),обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return результат
        return виклик
    for ім,функція in list(vars(П).items()):
        if inspect.isfunction(функція) and функція.__module__==П.__name__:
            обгортка=обгорнути(функція)
            ід_оригіналу=id(функція)
            for модуль in list(sys.modules.values()):
                if модуль and hasattr(модуль,'__dict__'):
                    for ключ,значення in list(vars(модуль).items()):
                        if id(значення)==ід_оригіналу: setattr(модуль,ключ,обгортка)
    мітка='самоперевірка записника'
    П.придушення_знахідка(dict(частка=1,смуга_погоди='frost'),[])
    assert записи, 'записник не бачить погодних знахідок'
    if os.environ.get('E3_RECORDER_CHECK'):
        print('самоперевірка записника:', len(записи), 'знахідок'); return
    перевірки=[(джерела/'стенд_знімок.py',['--дим']),(джерела/'тест_живого_шляху.py',[]),
           (джерела/'тест_протоколу.py',[]),(джерела/'прилади/розділи_гейтів.py',[]),(джерела/'audit_contracts.py',[])]
    каталог=pathlib.Path(os.environ['TMP'])/'е3_каталог.json'
    for шлях in sorted((джерела/'проби').glob('wea_*.py')):
        аргументи=[str(джерела),str(каталог)] if шлях.name in ('wea_вхід.py','wea_канон.py','wea_спека.py') else []
        перевірки.append((шлях,аргументи))
    if not база: перевірки.append((джерела/'проби/сила_частка.py',[]))
    if база or os.environ.get('E3_WEIGHTS_ONLY'): перевірки = перевірки[3:4] + перевірки[5:]
    провали=[]
    with open(префікс+'.log','w',encoding='utf-8',buffering=1) as журнал:
        for шлях,аргументи in перевірки:
            if шлях.name in ('wea_канон.py','wea_спека.py') and not каталог.exists():
                with gzip.open(pathlib.Path(os.environ['TMP'])/'е3_каталог.json.gz','rt',encoding='utf-8') as файл:
                    каталог.write_text(файл.read(),encoding='utf-8')
            мітка=шлях.name; результат=sys.stdout; потік_помилок=sys.stderr; sys.argv=[str(шлях),*аргументи]; os.chdir(джерела)
            print('СТАРТ',мітка,flush=True); початок=time.monotonic()
            sys.stdout=sys.stderr=журнал; код=0
            try: runpy.run_path(str(шлях),run_name='__main__')
            except SystemExit as збій: код=збій.code or 0
            except BaseException as збій: код=1; traceback.print_exc()
            finally: sys.stdout=результат;sys.stderr=потік_помилок;журнал.flush()
            if код: провали.append([мітка,код])
            print('КІНЕЦЬ',мітка,'код',код,'секунд',round(time.monotonic()-початок),flush=True)
        мітка='тест_показу.js'; print('СТАРТ',мітка,flush=True)
        процес=subprocess.run(['node','тест_показу.js'],cwd=джерела,stdout=журнал,stderr=журнал)
        if процес.returncode: провали.append([мітка,процес.returncode])
    with gzip.open(префікс+'.json.gz','wt',encoding='utf-8') as файл: json.dump(dict(записи=записи,провали=провали),файл,ensure_ascii=False)
    print('ГОТОВО',len(записи),'знахідок; провали',провали,flush=True)
    if провали:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
