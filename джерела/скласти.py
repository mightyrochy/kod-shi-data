# -*- coding: utf-8 -*-
"""Складає worker.js із джерела + проби і ПЕРЕВІРЯЄ те, що воркер віддасть.

ЧОМУ ЦЕЙ ФАЙЛ ІСНУЄ (01.09.2026, спіймано живим прогоном на телефоні).
Пробу вкладено в шаблонний рядок `const ПРОБА = ` … ``. Я перевірив лише два
символи — зворотну лапку й `${` — і пропустив ЗВОРОТНИЙ СЛЕШ. Рушій JS читає
`\\n` усередині шаблонного рядка як СПРАВЖНІЙ перевід рядка, тож кожен рядковий
літерал проби, що містив `\\n`, розривався навпіл. Наслідок: сторінка
малювалась (HTML цілий), а весь блок скрипта падав із SyntaxError ще до
призначення обробника — кнопка не робила НІЧОГО, мовчки.

Це рівно той клас вади, який проєкт уже ловить деінде: щось «зібралось»,
жодної помилки ніде, і несправність видно тільки на живому прогоні.

ЛІКИ — НЕ УВАЖНІШЕ ЕКРАНУВАННЯ, А ПЕРЕВІРКА ВИХОДУ. Складач витягує сторінку
рівно так, як її віддасть воркер, вирізає з неї <script> і проганяє
`node --check`. Помилка цього класу тепер червона на складанні, а не на
телефоні.
"""
import os, re, subprocess, sys

ТУТ = os.path.dirname(os.path.abspath(__file__))


def _екранувати(текст):
    """Те, і тільки те, що має значення всередині шаблонного рядка JS.
    Порядок значущий: слеш першим, інакше він екранує вже вставлені слеші."""
    return (текст.replace("\\", "\\\\")
                 .replace("`", "\\`")
                 .replace("${", "\\${"))


def скласти(джерело="worker_джерело.js", проба="проба.html", вихід="worker.js"):
    код = open(os.path.join(ТУТ, джерело), encoding="utf-8").read()
    стор = open(os.path.join(ТУТ, проба), encoding="utf-8").read()
    мітка = "const ПРОБА = `"
    if мітка in код:
        код = код[:код.index(мітка)]
    # ПЕРЕВОДИ РЯДКІВ ПРОБИ — ЕКРАНОВАНИМИ `\n`, НЕ СИРИМИ (02.09.2026). Файл
    # вставляють у редактор Cloudflare з телефона, і вставка губила переводи
    # рядків: «Unexpected token 'export' at worker.js:195:1164» — 386 рядків
    # замість 477. Сирий перевід усередині шаблонного рядка після такої втрати
    # зникає мовчки; екранований — переживає будь-яку вставку. Той самий HTML
    # на виході GET, байт у байт.
    код = код.rstrip() + "\n\n" + мітка + _екранувати(стор).replace("\n", "\\n") + "`;\n"
    open(os.path.join(ТУТ, вихід), "w", encoding="utf-8").write(код)
    return код


def стиснути(вхід="worker.js", вихід="worker.min.js"):
    """Однорядковий файл для вставки з телефона: без коментарів `//` і без
    переводів рядків, від яких залежить розбір. `esbuild --minify-whitespace
    --minify-syntax --charset=utf8` (ідентифікатори НЕ перейменовуються, щоб
    `перевірити` бачила `worker_default`; без `--charset=utf8` кирилиця
    екранується й файл росте на 77 %, пастка 01.09).
    Повертає шлях або None, якщо esbuild недосяжний — тоді це сказано."""
    import shutil
    кандидати = [shutil.which("esbuild"),
                 os.path.join(ТУТ, "node_modules", ".bin", "esbuild"),
                 "/home/claude/jsenv/node_modules/.bin/esbuild"]
    esb = next((к for к in кандидати if к and os.path.exists(к)), None)
    if not esb:
        print("  esbuild не знайдено — worker.min.js не складено (npm install esbuild)")
        return None
    r = subprocess.run([esb, os.path.join(ТУТ, вхід), "--format=esm", "--minify-whitespace",
                        "--minify-syntax", "--charset=utf8", "--outfile=" + os.path.join(ТУТ, вихід)],
                       capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("esbuild впав:\n" + r.stderr[-600:])
    # esbuild ПОВЕРТАЄ сирі переводи рядків у шаблонний рядок ПРОБИ (так коротше),
    # тобто робить рівно те, від чого файл мав бути захищений. Тому переводи
    # всередині ПРОБИ екрануються ще раз тут, уже після нього: між `ПРОБА=\``
    # і останньою закривною лапкою перед `export`.
    # esbuild з --minify-whitespace лишає сирі переводи рядків ЛИШЕ всередині
    # шаблонних рядків (код — одним рядком), тож кожен сирий перевід можна
    # замінити на екранований `\n` — значення рядка те саме. Що це справді так,
    # доводить не міркування, а `перевірити()`: видана сторінка мусить збігтися
    # байт у байт із тією, що віддає читабельний worker.js.
    шлях = os.path.join(ТУТ, вихід)
    т = open(шлях, encoding="utf-8").read().rstrip("\n").replace("\n", "\\n") + "\n"
    open(шлях, "w", encoding="utf-8").write(т)
    return шлях


def перевірити(шлях="worker.js"):
    """Що ВІДДАСТЬ воркер на GET — через сам його код, а не розбором файлу.

    Перша версія витягувала рядок `ПРОБА` регуляркою і падала на стиснутому
    файлі, де esbuild переставляє оголошення. Тобто перевірка вміла перевіряти
    лише ту збірку, яку я й так читав очима, і мовчала на тій, яку віддають
    людині. Тепер сторінка береться ЖИВИМ викликом `fetch(GET)`.
    """
    п = os.path.join(ТУТ, шлях)
    r = subprocess.run(["node", "--check", п], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(шлях + " не парситься:\n" + r.stderr[-600:])

    добув = os.path.join(ТУТ, "_добути.mjs")
    open(добув, "w", encoding="utf-8").write(
        "import fs from 'fs';\n"
        "const сир = fs.readFileSync(%r,'utf-8')\n" % п +
        "  .replace(/export\\s*\\{\\s*worker_default as default\\s*\\}\\s*;?/, 'const М = worker_default;')\n"
        "  .replace(/^export default/m, 'const М =');\n"
        "fs.writeFileSync('/tmp/_мод.mjs', сир + '\\nexport {М};');\n"
        "const {М} = await import('/tmp/_мод.mjs');\n"
        "const в = await М.fetch(new Request('https://w.workers.dev/', {method:'GET'}), {});\n"
        "if (в.status !== 200) throw new Error('GET віддав ' + в.status);\n"
        "fs.writeFileSync('/tmp/_стор.html', await в.text());\n")
    r = subprocess.run(["node", добув], capture_output=True, text=True, cwd=ТУТ)
    os.remove(добув)
    if r.returncode:
        raise SystemExit("GET не віддав сторінку:\n" + r.stderr[-600:])

    стор = open("/tmp/_стор.html", encoding="utf-8").read()
    if "Перевірити міст" not in стор:
        raise SystemExit("у виданій сторінці нема кнопки — проба не доїхала")
    js = "\n".join(m.group(1) for m in
                   re.finditer(r"<script[^>]*>(.*?)</script>", стор, re.S))
    if not js.strip():
        raise SystemExit("у виданій сторінці нема скрипта")
    open("/tmp/_стор.js", "w", encoding="utf-8").write(js)
    r = subprocess.run(["node", "--check", "/tmp/_стор.js"], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("JS ВИДАНОЇ СТОРІНКИ НЕ ПАРСИТЬСЯ — кнопка була б мертва:\n"
                         + r.stderr[-600:])
    # обробник мусить бути ПРИЗНАЧЕНИЙ, а не просто існувати текстом
    if 'onclick' not in js:
        raise SystemExit("у скрипті нема призначення onclick — кнопка нічого не робить")
    return len(стор), len(js)


if __name__ == "__main__":
    скласти()
    с, j = перевірити()
    _сторінка_читабельного = open("/tmp/_стор.html", encoding="utf-8").read()
    print("✓ worker.js складено · видана сторінка %d Б, скрипт %d Б, парситься" % (с, j))
    if стиснути():
        с2, j2 = перевірити("worker.min.js")
        рядків = open(os.path.join(ТУТ, "worker.min.js"), encoding="utf-8").read().count("\n")
        # Те, що віддає стиснутий, мусить дорівнювати тому, що віддає читабельний.
        if (с2, j2) != (с, j) or open("/tmp/_стор.html", encoding="utf-8").read() != _сторінка_читабельного:
            raise SystemExit("worker.min.js віддає іншу сторінку: %d/%d проти %d/%d" % (с2, j2, с, j))
        print("✓ worker.min.js складено · рядків %d · та сама сторінка, парситься" % рядків)
