# -*- coding: utf-8 -*-
"""Штучні шляхи пікселів: джерело, перенесення, суд, видимий і прихований показ."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from корінь_річ_примірка_та_сама_людина import лічба


class Прилад(unittest.TestCase):
    """Мініатюрні дерева без залежності від назв та рядків продукту."""

    def перевірити(self, файли, кількість):
        """Створює окреме дерево, запускає справжній обхід і звіряє число."""
        with tempfile.TemporaryDirectory() as т:
            дж = Path(т) / 'джерела'
            дж.mkdir()
            for ім, текст in файли.items():
                ф = дж / ім
                ф.parent.mkdir(parents=True, exist_ok=True)
                ф.write_text(текст, encoding='utf-8')
            звіт = лічба(т)
            self.assertEqual(звіт['місць'], кількість, json.dumps(звіт['входи'], ensure_ascii=False, indent=2))
            return звіт

    def test_прямий_показ(self):
        """Джерело має довільне локальне ім'я."""
        self.перевірити({'а.js': "const x=generate_image();\nconst i=document.createElement('img');\ni.src=x;\ndocument.body.appendChild(i);"}, 1)

    def test_суд(self):
        """Генерований кадр у вимірі шкіри — умова а."""
        self.перевірити({'а.js': "const x=generate_image();\nmeasure_skin(x);"}, 1)

    def test_оригінал(self):
        """Завантажений файл не стає генерацією через назву поля."""
        self.перевірити({'а.js': "const картинка=input.files[0];\nconst i=document.createElement('img');\ni.src=картинка;document.body.appendChild(i);\njudge(картинка);"}, 0)

    def test_відокремлені_поля(self):
        """Картинка та портрет одного запису мають різне походження."""
        self.перевірити({'а.js': "const k={картинка:generate_image(),портрет:input.files[0]};\njudge(k.портрет);\nconst i=document.createElement('img');i.src=k.картинка;document.body.appendChild(i);"}, 1)

    def test_аліас_функція(self):
        """Аргумент, повернення, аліас функції й поле не розривають шлях."""
        self.перевірити({'а.js': "function f(a){return {value:a};}\nconst g=f;const q=g(generate_image());\njudge(q.value);"}, 1)

    def test_масив_callback(self):
        """Кадр проходить через масив та callback map/find."""
        self.перевірити({'а.js': "const a=[generate_image()].map(x=>({v:x}));\nconst b=a.find(x=>x);\njudge(b.v);"}, 1)

    def test_між_файлами(self):
        """Спільні глобальні JS з'єднуються незалежно від порядку файлів."""
        self.перевірити({'вкладена/а.js': 'judge(z.picture);', 'я.js': 'const z={picture:generate_image()};'}, 1)

    def test_html(self):
        """Вбудований JS має рядки вихідного HTML, текст промпту не виконується."""
        звіт = self.перевірити({'а.html': '<html>\n<script>\nconst x=generate_image();\nconst h=\'<img src="\'+x+\'">\';\nрозміткаЖінціП(document.body,h);\n</script></html>'}, 1)
        self.assertEqual(next(р['рядок'] for р in звіт['входи'] if р['місце']), 5)

    def test_приховане_декодування(self):
        """Image, який нікуди не додано, не є показом жінці."""
        self.перевірити({'а.js': 'const i=new Image();\ni.src=generate_image();'}, 0)

    def test_промпт(self):
        """Слова про шкіру і img у промпті — дані."""
        self.перевірити({'а.py': 'PROMPT = "judge skin, keep face; <img src=generated>"\n'}, 0)

    def test_не_продукт(self):
        """Вкладені тести та прилади не збільшують число."""
        self.перевірити({'проби/а.js': 'judge(generate_image());', 'прилади/а.py': 'judge(generate_image())',
                         'ще/тест_а.js': 'judge(generate_image());'}, 0)

    def test_python(self):
        """Python також простежується від джерела до входу суду."""
        self.перевірити({'а.py': 'def wrap(x):\n    return {"face": x}\np = wrap(generate_image())\njudge(p["face"])\n'}, 1)

    def test_імпорт_python(self):
        """Повернення через імпортований модуль зберігає джерело."""
        self.перевірити({'а.py': 'from б import picture\njudge(picture())\n',
                         'б.py': 'def picture():\n    return generate_image()\n'}, 1)

    def test_два_поля_дві_умови(self):
        """Одне файл:рядок рахується один раз при двох умовах."""
        self.перевірити({'а.js': "const i=document.createElement('img'); i.src=generate_image(); document.body.appendChild(i); judge(i.src);"}, 1)

    def test_назва_маски_не_доказ(self):
        """Обгортка з обіцянкою повернення не очищає згенеровані пікселі."""
        self.перевірити({'а.js': "function повернутиЗаМаскою(x,photo,mask){return x;}\njudge(повернутиЗаМаскою(generate_image(),input.files[0],mask));"}, 1)

    def test_повернуто_оригінал(self):
        """Результат, який справді є оригіналом, не є кадром генератора."""
        self.перевірити({'а.js': "function restore(x,photo,mask){return photo;}\njudge(restore(generate_image(),input.files[0],mask));"}, 0)

    def test_помилковий_js(self):
        """Нерозбірний JS не дає зеленого нуля."""
        with self.assertRaises(ValueError):
            self.перевірити({'а.js': 'const = ;'}, 0)

    def test_незалежні_виклики_перетворення(self):
        """Транспорт фото не змішує походження двох викликів."""
        self.перевірити({'а.js': 'const a=блобВБазу(generate_image());\nconst b=блобВБазу(input.files[0]);\njudge(b);\njudge(a);'}, 1)

    def test_src_через_setAttribute(self):
        """Атрибут src є таким самим входом показу, як властивість."""
        self.перевірити({'а.js': "const i=document.createElement('img');\ni.setAttribute('src',generate_image());\ndocument.body.appendChild(i);"}, 1)

    def test_порожній_обсяг_помилка(self):
        """Відсутнє дерево не маскується нульовим числом."""
        with tempfile.TemporaryDirectory() as т:
            with self.assertRaises(ValueError):
                лічба(т)

    def test_текст_відповіді_не_пікселі(self):
        """Текстовий блок генератора не є пікселями примірки."""
        self.перевірити({'а.js': "const a=модельП_блоки([]);\nconst b=a.find(x=>x.type==='text');\njudge(b.text);"}, 0)

    def test_блок_зображення(self):
        """Справжні байти графічного блока доходять до суду."""
        self.перевірити({'а.js': "const a=модельП_блоки([]);\nconst b=a.find(x=>x.type==='image');\njudge(b.source.data);"}, 1)

    def test_збереження_json(self):
        """JSON-копія не очищає походження згенерованого кадру."""
        self.перевірити({'а.js': 'const a={picture:generate_image()};\nconst b=JSON.parse(JSON.stringify(a));\njudge(b.picture);'}, 1)

    def test_повтор_генерації(self):
        """Обидві альтернативи кадру доходять до одного місця показу."""
        звіт = self.перевірити({'а.js': "let a=generate_image();\nif(retry)a=generate_image();\nconst i=document.createElement('img');\ni.src=a;\ndocument.body.appendChild(i);"}, 1)
        self.assertIn('джерела/а.js:1', next(р['чому'] for р in звіт['входи'] if р['місце']))
        self.assertIn('джерела/а.js:2', next(р['чому'] for р in звіт['входи'] if р['місце']))

    def test_невидимий_журнал(self):
        """Запис генерації в журналі не є судом і показом."""
        self.перевірити({'а.js': 'const log={picture:generate_image()};\nconsole.log(log);'}, 0)

    def test_деструктуризація(self):
        """Деструктуризація об'єкта зберігає поле кадру."""
        self.перевірити({'а.js': 'const {picture:q}={picture:generate_image()};\njudge(q);'}, 1)

    def test_два_окремих_покази(self):
        """Два місця src рахуються окремо."""
        self.перевірити({'а.js': "const a=generate_image();\nconst i=document.createElement('img'), j=document.createElement('img');\ni.src=a;\nj.src=a;\ndocument.body.appendChild(i);document.body.appendChild(j);"}, 2)

    def test_байти_та_розміри(self):
        """Геометрія кадру не стає виміром шкіри."""
        self.перевірити({'а.js': 'const a=generate_image();\nconst width=a.width;\nmeasure_skin(width);'}, 0)

    def test_помилка_python_cli(self):
        """Помилка Python у дочірньому процесі завершується кодом 1."""
        with tempfile.TemporaryDirectory() as т:
            дж = Path(т) / 'джерела'
            дж.mkdir()
            (дж / 'а.py').write_text('def (', encoding='utf-8')
            процес = subprocess.run([sys.executable, str(Path(__file__).with_name('корінь_річ_примірка_та_сама_людина.py')),
                                    '--корінь', т], capture_output=True, encoding='utf-8')
            self.assertNotEqual(процес.returncode, 0)

    def test_сталий_індекс_масиву(self):
        """Сталий та змінний індекси читають елементи масиву."""
        self.перевірити({'а.js': 'const a=[generate_image()];\njudge(a[0]);'}, 1)

    def test_сховище(self):
        """Кадр проходить put/getAll зі збереженням назви сховища."""
        self.перевірити({'а.js': "const z={P:{cards:[{picture:generate_image()}]}};\ntx(db,'runs','readwrite',s=>s.put(z,'key'));\nconst r=db.transaction('runs').objectStore('runs').getAll();\njudge(r.result[0].P.cards[0].picture);"}, 1)

    def test_повноекранний_показ(self):
        """Повноекранний src простежується до вже показаного img."""
        self.перевірити({'а.js': "const i=document.createElement('img');\ni.src=generate_image();\ndocument.body.appendChild(i);\nconst big=document.querySelector('img');\nbig.src=document.body.querySelector('img').src;"}, 2)

    def test_не_зображення(self):
        """src видимого script не стає показом зображення."""
        self.перевірити({'а.js': "const s=document.createElement('script');\ns.src=generate_image();document.body.appendChild(s);"}, 0)

    def test_транспорт_став_генератором(self):
        """Зміна тіла транспортної функції не лишає старої гарантії."""
        self.перевірити({'а.js': 'function блобВБазу(x){return generate_image();}\njudge(блобВБазу(input.files[0]));'}, 1)

    def test_бібліотека_через_групи(self):
        """Map бібліотеки переносить збережені картки в мініатюру."""
        self.перевірити({'а.js': "const a=[{картинка:generate_image()}];\nconst groups=new Map();\na.forEach(x=>{groups.set('key',[]);groups.get('key').push(x)});\nfor(const [key,list] of groups){list.forEach(k=>розміткаЖінціП(document.body,'<img src=\"'+k.картинка+'\">'));}"}, 1)

    def test_метадані_не_байти_blob(self):
        """Запис бібліотеки не перетворюється на пікселі портрета."""
        self.перевірити({'а.js': 'const record={картинка:generate_image()};\njudge(блобВБазу(record));'}, 0)

    def test_урл_лише_з_даних_фото(self):
        """URL фото читає дані, а не службову сусідню картинку."""
        self.перевірити({'а.js': "const photo={дані:'original',картинка:generate_image()};\njudge(урлФотоП(photo));"}, 0)

    def test_string_запису_не_пікселі(self):
        """String(object) не серіалізує його графічні поля."""
        self.перевірити({'а.js': 'const record={картинка:generate_image()};\njudge(String(record));'}, 0)

    def test_аліас_джерела(self):
        """Перейменування операції генерації не приховує її походження."""
        self.перевірити({'а.js': 'const draw=generate_image;\njudge(draw());'}, 1)


if __name__ == '__main__':
    unittest.main()
