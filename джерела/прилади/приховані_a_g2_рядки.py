# -*- coding: utf-8 -*-
"""Прилад частини (а) розвідки «Приховані» (група G2, інтерфейс): Витягає рядкові літерали (без коментарів) з JS/HTML/PY і друкує ті, що мають слово за регексом.
Вжиток з кореня: python3 -I джерела/прилади/приховані_a_g2_рядки.py <регекс> файли..."""
import sys, re, ast, io, tokenize
pat = re.compile(sys.argv[1])
def js_strings(src):
    i, n, line = 0, len(src), 1
    out = []
    prev_sig = ''
    while i < n:
        c = src[i]
        if c == '\n': line += 1; i += 1; continue
        if src.startswith('//', i):
            j = src.find('\n', i); i = n if j < 0 else j; continue
        if src.startswith('/*', i):
            j = src.find('*/', i+2); j = n if j < 0 else j+2
            line += src.count('\n', i, j); i = j; continue
        if c in '\'"`':
            q = c; j = i+1; buf = []; start = line; depth = 0
            while j < n:
                d = src[j]
                if d == '\\': buf.append(src[j:j+2]); j += 2; continue
                if q == '`' and src.startswith('${', j):
                    # skip expression roughly
                    k = j+2; dd = 1
                    while k < n and dd:
                        if src[k] == '{': dd += 1
                        elif src[k] == '}': dd -= 1
                        k += 1
                    buf.append('${…}'); line += src.count('\n', j, k); j = k; continue
                if d == q: break
                if d == '\n': line += 1
                buf.append(d); j += 1
            out.append((start, ''.join(buf))); i = j+1; prev_sig = 'str'; continue
        if c == '/' and prev_sig in ('(', ',', '=', ':', '[', '!', '&', '|', '?', '{', '}', ';', 'return', ''):
            # regex literal
            j = i+1; cls = False
            while j < n and src[j] != '\n':
                if src[j] == '\\': j += 2; continue
                if src[j] == '[': cls = True
                elif src[j] == ']': cls = False
                elif src[j] == '/' and not cls: break
                j += 1
            i = j+1; prev_sig = 're'; continue
        if not c.isspace():
            if src.startswith('return', i) and not (src[i+6:i+7].isalnum()): prev_sig = 'return'; i += 6; continue
            prev_sig = c if c in '(,=:[!&|?{};' else 'x'
        i += 1
    return out
def html_strings(src):
    src2 = re.sub(r'<!--.*?-->', lambda m: '\n'*m.group(0).count('\n'), src, flags=re.S)
    out = []
    # script blocks -> js
    for m in re.finditer(r'<script[^>]*>(.*?)</script>', src2, flags=re.S):
        base = src2.count('\n', 0, m.start(1))
        out += [(l+base, s) for l, s in js_strings(m.group(1))]
    body = re.sub(r'<(script|style)[^>]*>.*?</\1>', lambda m: '\n'*m.group(0).count('\n'), src2, flags=re.S)
    for m in re.finditer(r'>([^<]+)<', body):
        t = m.group(1).strip()
        if t: out.append((body.count('\n', 0, m.start())+1, t))
    for m in re.finditer(r'(aria-label|placeholder|title|alt|value|content)="([^"]*)"', body):
        out.append((body.count('\n', 0, m.start())+1, m.group(2)))
    return out
def py_strings(src):
    tree = ast.parse(src)
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            b = node.body[0]
            if isinstance(b, ast.Expr) and isinstance(getattr(b, 'value', None), ast.Constant) and isinstance(b.value.value, str):
                docs.add(id(b.value))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            out.append((node.lineno, node.value))
    return out
for f in sys.argv[2:]:
    src = open(f, encoding='utf-8').read()
    if f.endswith('.py'): ss = py_strings(src)
    elif f.endswith('.html'): ss = html_strings(src)
    else: ss = js_strings(src)
    for l, s in ss:
        for m in pat.finditer(s):
            a = max(0, m.start()-50); print(f'{f}:{l}\t{s[a:m.end()+50]!r}'); break
