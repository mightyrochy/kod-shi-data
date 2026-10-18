"""Елементи розмітки без читачів: id з HTML `показ.html`, яких не згадує ні JS (рядком чи шаблоном), ні CSS;
класи з HTML, яких не згадує ні CSS, ні JS. Запуск з кореня: python3 аудит/огляд_коду/скрипти/показ/розмітка.py"""
import re
Т = open("джерела/показ.html", encoding="utf-8").read()
скрипти = " ".join(re.findall(r"<script[^>]*>(.*?)</script>", Т, re.S))
стилі = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", Т, re.S))
стилі = re.sub(r"/\*.*?\*/", "", стилі, flags=re.S)
html = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", Т, flags=re.S)
ід = re.findall(r"\sid=\"([^\"]+)\"", html)
кл = {к for в in re.findall(r"\sclass=\"([^\"]+)\"", html) for к in в.split()}
def у_js(с):
    return re.search(r"['\"`#\s(]" + re.escape(с) + r"['\"`\s,)\]:.\[]", скрипти) is not None
def у_css(с, знак):
    return re.search(re.escape(знак + с) + r"(?![\wЀ-ӿ-])", стилі) is not None
символи = set(re.findall(r"<symbol id=\"([^\"]+)\"", html))
def складене(і):
    """піктограма, яку JS бере складеним id: '#і-' + ім"""
    if і not in символи:
        return False
    п = і.split("-")[0] + "-"
    return re.search(r"['\"`]#?" + re.escape(п) + r"['\"`]\s*\+", скрипти) is not None
без_ід = [і for і in ід if not у_js(і) and not у_css(і, "#") and not складене(і)
          and not re.search(r"\s[\w\u0400-\u04FF-]+=\"#?" + re.escape(і) + "\"", html)]
без_кл = sorted(к for к in кл if not у_css(к, ".") and not у_js(к))
print("id у розмітці %d (різних %d); без читача в JS (піктограми — і складеним id), CSS, атрибутах розмітки: %d" % (len(ід), len(set(ід)), len(без_ід)))
print("  ", " ".join(без_ід[:40]))
print("класів у розмітці %d; без читача в CSS і JS: %d" % (len(кл), len(без_кл)))
print("  ", " ".join(без_кл[:40]))
повтори = sorted({і for і in ід if ід.count(і) > 1})
print("id, що повторюються в розмітці: %d %s" % (len(повтори), " ".join(повтори[:10])))
