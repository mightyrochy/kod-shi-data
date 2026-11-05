import os, pathlib, subprocess, sys

root = pathlib.Path(sys.argv[1]).resolve()
source = root / 'джерела'
original = (source / 'тест_показу.js').read_text(encoding='utf-8')
prefix = original.split('(async () => {\n  батареяПочалась = true;', 1)[0]
tail = r'''
(async () => {
  const {w, d, дом, помилки} = сторінка({url: 'https://mightyrochy.github.io/kod-shi-data/показ.html'});
  const $ = id => d.getElementById(id);
  await чекатиСтарт(w);
  w.eval("МІСТ_П.адреса = 'https://local.invalid'; МІСТ_П.токен = 'стенд';");
  await w.eval("писатиКв(ключФото('портрет'), new Blob(['портрет'], {type:'image/jpeg'}))");
  w.блобВБазу = async () => ({тип:'image/jpeg', дані:'AAAA', ширина:1568, висота:1176, якість:0.85});
  let викликів = 0;
  w.модельП = async () => { викликів++; return '{"photo":"usable","skin":["#f2d6c4"],"hair":["#4a4644"],"eyes":"#6b8cae"}'; };
  async function збій() {
    w.eval("містП = async () => { throw new Error('контрольний збій моста'); }");
    await w.зчитатиКольориЗПортрета();
  }
  await збій();
  if (викликів !== 1 || $('кол-повтор').hidden) throw new Error('Контрольний збій не пройшов модель і не відкрив повтор');
  const збійА = {повторВидимий:!$('кол-повтор').hidden, ручнеПоле:$('кол-відповідь').value};
  мостКольорів(w);
  await w.повторитиЧитанняКольорівП();
  const успіх = {шкіра:w.eval('КОЛІР.шкіра'), повторПрихований:$('кол-повтор').hidden, викликів};
  await збій();
  const профільА = w.eval('АКТИВНИЙ');
  await w.створитиПрофіль();
  const профільБ = w.eval('АКТИВНИЙ');
  const до = {шкіра:w.eval('КОЛІР.шкіра'), повторВидимий:!$('кол-повтор').hidden,
    портрет:!!(await w.eval("читатиКв(ключФото('портрет'))")), профіліРізні:профільА !== профільБ};
  мостКольорів(w);
  $('кол-повтор').click();
  await чекатиНа(() => $('кол-повтор').hidden && !$('кол-повтор').disabled, 'повтор у профілі Б');
  const записБ = await w.читатиКв('профіль:' + профільБ);
  const після = {шкіра:w.eval('КОЛІР.шкіра'), записанаШкіра:записБ.колір.шкіра, викликів,
    ручнеПоле:$('кол-відповідь').value, помилки};
  console.log(JSON.stringify({збійА, успіх, до, після}, null, 2));
  дом.window.close();
})().catch(e => { console.error(e); process.exitCode = 1; });
'''
script = source / '_перевірка2814.cjs'
script.write_text(prefix + tail, encoding='utf-8')
try:
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    result = subprocess.run(['node', str(script)], cwd=source, env=env)
    sys.exit(result.returncode)
finally:
    script.unlink()
