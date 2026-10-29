"""Нова сліпа вибірка 10×4 змінених вимірів сім'ї очей, сід 1213958.
Запуск із джерела/: python проби/сімя_очей_вибірка_958.py /tmp/очі.json.
ДО — дуга #935; попередні 200 пар виключено; це склад, не оцінка очима."""
import sys, json, glob, random, re, subprocess, hashlib
sys.path.insert(0, '.')
import feed as Ф, colorspace as cs, колір_річ as КР, palettes as ПЛ
def записати_вибірку():
    """Пише склад сліпої вибірки, не оцінюючи правильності кольору."""
    старі = [('9baf2cf1b404749c20e16b9e1f89a1b04180e6e5', 'сімя_очей_2.md'),
             ('29903122d646d8069958b142f701e3cf2715721b', 'сімя_очей.md'),
             ('62bebbad5e2c46aadd6756537d9b0b1e699b288b', 'сімя_очей_2.md'), ('ffb681ade9578fb24d40c379fa8d5129594fa723', 'сімя_очей_2.md'),
             ('990d547e3fba1bb8ee88679ae2e3beb11f3fab0e', 'сімя_очей_2.md')]
    виключені = set()
    for sha, назва in старі:
        текст = subprocess.check_output(['git', 'show', sha + ':аудит/перевірка/935/' + назва]).decode()
        виключені.update(re.findall(r'\|\s*\d+\s*\|\s*`(#[0-9a-f]{6})`\s*\|\s*`(#[0-9a-f]{6})`', текст))
    очі = [json.load(open('стенд_вх.json'))['очі']]
    очі += [json.load(open(f))['eyes'] for f in sorted(glob.glob('../аудит/проби/жінки/ж*.json'))]
    очі = list(dict.fromkeys(очі + ['#6b6740', '#8aa9ad']))
    кат = Ф._прочитати_каталог(Ф.каталог_на_диску(), ліміт_фото=0)['каталог']
    кат = [x for x in кат if КР.не_вимір(x) is None and КР.нейтраль_меж(x) == 'ні']
    rnd, вибірка, кількість = random.Random(1213958), [], {}
    for о in очі:
        lab = cs.hx(о); запис = КР.запис_кольору(dict(lab=lab)); кандидати = []
        for x in sorted(кат, key=lambda x: x['id']):
            hex = cs.hex_з_lab(x['lab']).lower()
            до = КР.у_дугах_кола(x, [ПЛ.дуга_очей(cs.lch(lab)[2])], до_кінця_згасання=True)
            після = КР.у_сім_ї_очей(x, запис)
            if до == після or (о, hex) in виключені: continue
            кандидати.append(dict(очі=о, hex=hex, lab=x['lab'], id=x['id'], до=до, після=після,
                                 фото=x.get('фото_опису') or (x.get('фото') or [None])[0],
                                 url=x.get('url'), назва=x.get('назва')))
        кількість[о] = len(кандидати); вибірка += rnd.sample(кандидати, 4)
    вихід = dict(seed=1213958, baseline='3dec14c5c9b5920e427293f4c10541532082de20',
                 кандидати=кількість, виключених_пар=len(виключені), пари=вибірка,
                 код_sha256=hashlib.sha256(open('колір_відношення.py','rb').read()).hexdigest())
    json.dump(вихід, open(sys.argv[1], 'w'), ensure_ascii=False, indent=2)
    print('10×4:', len(вибірка), 'кандидатів', sum(кількість.values()), 'виключено', len(виключені))
if __name__ == "__main__":
    записати_вибірку()
