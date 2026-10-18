import re
def make_refs(rows):
    def refs(n,field):
        t=rows[n][field]
        t=re.sub(r'`[^`]*`','',t)
        out=set()
        for m in re.finditer(r'ряд\w*\s+((?:\d{2,4}(?:\s*[,–]\s*|\s+і\s+)?)+)',t):
            for k in re.findall(r'\d{2,4}',m.group(1)): out.add(int(k))
        for m in re.finditer(r'(?<![#\d.,:/_])(\d{4})(?![\d%_.,:/-])',t):
            k=int(m.group(1)); pre=t[max(0,m.start()-8):m.start()]
            if k>=4000 and not re.search(r'(#|PR|сід|seed|ж-|файл |запис |сцен\w* )\s*$',pre): out.add(k)
        return {k for k in out if k in rows and k<n}
    return refs
