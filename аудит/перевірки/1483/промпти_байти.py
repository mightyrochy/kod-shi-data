import hashlib, json, os, sys, io, contextlib
дер = sys.argv[1]; os.chdir(дер); sys.path.insert(0, os.path.abspath("джерела")); sys.path.insert(0, os.path.abspath("джерела/прилади"))
import warnings; warnings.simplefilter("ignore")
import промпти_перелік as ПП, збирач_промптів as ЗП
вих = {}
for кл, о, збир in ПП.оголошення():
    дані = {}
    for п in о.вхід:
        к = п.шлях.split(".")[0].split("[")[0]
        дані.setdefault(к, [] if "[]" in п.шлях else "x")
    for мова in (None, "uk", "en"):
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                т = ЗП.зібрати(о, дані, мова) if мова else ЗП.зібрати(о, дані)
            ск = json.dumps(ЗП.скелет(о), ensure_ascii=False, sort_keys=True, default=str) if о.відповідь_як == "json" else ""
            вих["%s|%s" % (кл, мова)] = hashlib.sha256((str(т) + "\0" + ск).encode()).hexdigest()[:16]
        except Exception as e:
            вих["%s|%s" % (кл, мова)] = "ВИНЯТОК " + type(e).__name__ + ":" + str(e)[:60]
for к in sorted(вих): print(к, вих[к])
