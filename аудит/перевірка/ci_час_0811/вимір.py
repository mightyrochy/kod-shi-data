# -*- coding: utf-8 -*-
"""Час CI від пушу до зеленого: черга й виконання по джобах на всіх запусках (наряд CI-час-злиття, 08.11).

Джерело — публічний API GitHub (`actions/runs`, `runs/<id>/jobs`, `pulls`, `pulls/<n>/files`), без токена.
Кожна відповідь лягає в кеш (`--кеш`, типово /tmp/ci_час_кеш): повтор не витрачає ліміту запитів; відповіді
про ще не завершені запуски не кешуються.

ЗАПУСК (з кореня репозиторію):
    python3 -I аудит/перевірка/ci_час_0811/вимір.py --від 2026-11-01 --до 2026-11-08 --md аудит/перевірка/ci_час_0811/ДО.md
    python3 -I аудит/перевірка/ci_час_0811/вимір.py --pr 3401,3402,3403 --md …   # мірило: лише названі PR

Числа:
  черга джоба     = started_at − created_at джоба (GitHub створює джоб, коли його needs виконано);
  черга запуску   = run_started_at − created_at запуску;
  виконання       = completed_at − started_at джоба;
  CI від пушу PR  = від created_at першого запуску (подія pull_request) останньої голови PR до completed_at
                    останнього з них; частка черги — сума черг джобів критичного шляху (найдовший ланцюг) / весь час.
  документний PR  = усі змінені файли — `аудит/**` чи `*.md` (як у наряді); «продуктний» прапор збірки —
                    окремо, тим самим правилом, що джоб `zminy` у zbirka.yml.
  паралельність   = скільки джобів одночасно на раннері (started..completed) і скільки чекає в черзі
                    (created..started), щохвилини.
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import defaultdict

REPO = "mightyrochy/kod-shi-data"
API = "https://api.github.com/repos/" + REPO


def _kesh_shliakh(kesh, url):
    return os.path.join(kesh, hashlib.sha1(url.encode()).hexdigest() + ".json")


def otrymaty(url, kesh, kešuvaty=True):
    shl = _kesh_shliakh(kesh, url)
    if os.path.exists(shl):
        with open(shl, encoding="utf-8") as f:
            return json.load(f)
    for sproba in range(5):
        try:
            zap = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json",
                                                       "User-Agent": "ci-chas-vymir"})
            with urllib.request.urlopen(zap, timeout=60) as v:
                dani = json.load(v)
            break
        except urllib.error.HTTPError as e:
            print(f"HTTP {e.code} {url} (спроба {sproba + 1})", file=sys.stderr, flush=True)
            if e.code in (403, 429) or e.code >= 500:
                time.sleep(2 ** sproba * 5)
                continue
            raise
        except (urllib.error.URLError, OSError):
            time.sleep(2 ** sproba)
    else:
        raise RuntimeError("не отримано: " + url)
    if kešuvaty:
        os.makedirs(kesh, exist_ok=True)
        with open(shl, "w", encoding="utf-8") as f:
            json.dump(dani, f)
    return dani


def chas(s):
    return dt.datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None


def khv(a, b):
    return (b - a).total_seconds() / 60 if a and b else None


def zapusky_za_den(den, kesh, sohodni):
    """Усі запуски, створені за день UTC (пошук API віддає до 1000 на запит — день їх не перевищує)."""
    vsi, storinka = [], 1
    while True:
        url = f"{API}/actions/runs?per_page=100&page={storinka}&created={den}"
        d = otrymaty(url, kesh, kešuvaty=den < sohodni)
        vsi += d["workflow_runs"]
        if len(d["workflow_runs"]) < 100:
            return vsi
        storinka += 1


def dzhoby(run, kesh):
    zaversheno = run["status"] == "completed"
    vsi, storinka = [], 1
    while True:
        url = f"{API}/actions/runs/{run['id']}/attempts/{run['run_attempt']}/jobs?per_page=100&page={storinka}"
        d = otrymaty(url, kesh, kešuvaty=zaversheno)
        vsi += d["jobs"]
        if len(d["jobs"]) < 100:
            return vsi
        storinka += 1


def faily_pr(n, kesh):
    vsi, storinka = [], 1
    while True:
        d = otrymaty(f"{API}/pulls/{n}/files?per_page=100&page={storinka}", kesh)
        vsi += [f["filename"] for f in d]
        if len(d) < 100 or storinka >= 30:
            return vsi
        storinka += 1


def spysok_pr(vid, kesh):
    """PR, створені від дати `vid` (і старші відкриті на той час не потрібні — їх ловить діапазон закриття)."""
    vsi, storinka = [], 1
    while True:
        url = f"{API}/pulls?state=all&sort=created&direction=desc&per_page=100&page={storinka}"
        d = otrymaty(url, kesh, kešuvaty=False)
        vsi += d
        if len(d) < 100 or d[-1]["created_at"][:10] < vid:
            return vsi
        storinka += 1


def pr(n, kesh):
    url = f"{API}/pulls/{n}"
    d = otrymaty(url, kesh)
    if d.get("state") == "open":          # відкритий PR ще зміниться — кеш не тримаємо
        os.remove(_kesh_shliakh(kesh, url))
    return d


def dokumentnyi(faily):
    return bool(faily) and all(f.startswith("аудит/") or f.endswith(".md") for f in faily)


def produkt_zbirky(faily):
    """Те саме правило, що крок «які шляхи змінено» джоба zminy у zbirka.yml (подія pull_request)."""
    for f in faily:
        if f.startswith("аудит/проби/автоживий-"):
            continue
        if (f.startswith("джерела/") or f.startswith("аудит/проби/")
                or f in ("каталог_повний.xml.gz", "index.html", "build.txt", ".github/workflows/zbirka.yml")):
            return True
    return False


def nazva_dzhoba(n):
    return "записаний живий шлях у Pyodide (×10)" if n.startswith("записаний живий шлях") else n


def kvantyl(xs, q):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    i = min(len(xs) - 1, max(0, int(round(q * (len(xs) - 1)))))
    return xs[i]


def f1(x):
    return "—" if x is None else f"{x:.1f}"


def med_p90(xs):
    xs = [x for x in xs if x is not None]
    return f"{f1(statistics.median(xs)) if xs else '—'} / {f1(kvantyl(xs, 0.9))}"


def krytychnyi_shliakh(jobs):
    """Черга й виконання на найдовшому ланцюгу джобів запуску: останній завершений джоб, далі — назад
    той, що завершився найпізніше не пізніше старту поточного (його needs)."""
    js = [j for j in jobs if j.get("started_at") and j.get("completed_at") and j["conclusion"] != "skipped"]
    if not js:
        return 0.0, 0.0
    j = max(js, key=lambda j: chas(j["completed_at"]))
    cherga = vykon = 0.0
    while j:
        cherga += max(0.0, khv(chas(j["created_at"]), chas(j["started_at"])))
        vykon += khv(chas(j["started_at"]), chas(j["completed_at"]))
        start = chas(j["created_at"])
        poperedni = [k for k in js if chas(k["completed_at"]) <= start + dt.timedelta(seconds=5)
                     and chas(k["started_at"]) < chas(j["started_at"])]
        j = max(poperedni, key=lambda k: chas(k["completed_at"])) if poperedni else None
    return cherga, vykon


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--від", default="2026-11-01")
    ap.add_argument("--до", default="2026-11-08")
    ap.add_argument("--pr", default="", help="лише ці PR (через кому) — мірило")
    ap.add_argument("--кеш", default="/tmp/ci_час_кеш")
    ap.add_argument("--md", default="")
    ap.add_argument("--csv", default="")
    a = ap.parse_args()
    sohodni = dt.datetime.now(dt.timezone.utc).date().isoformat()

    runs = []
    if a.pr:
        nomery = [int(x) for x in a.pr.split(",") if x.strip()]
        for n in nomery:
            p = pr(n, a.кеш)
            url = f"{API}/actions/runs?per_page=100&head_sha={p['head']['sha']}"
            runs += otrymaty(url, a.кеш, kešuvaty=False)["workflow_runs"]
    else:
        den = dt.date.fromisoformat(a.від)
        kinets = dt.date.fromisoformat(a.до)
        while den <= kinets:
            runs += zapusky_za_den(den.isoformat(), a.кеш, sohodni)
            den += dt.timedelta(days=1)
    runs = list({r["id"]: r for r in runs}.values())

    # PR кожного запуску pull_request: поле pull_requests, інакше — за гілкою голови.
    pr_za_hilkoiu = {}
    ryadky = []          # по джобу
    kroky = defaultdict(list)   # (workflow, джоб, крок) → хвилини
    from concurrent.futures import ThreadPoolExecutor
    zaversheni = [r for r in runs if r["status"] == "completed"]
    with ThreadPoolExecutor(8) as pul:
        po_zapusku = dict(zip([r["id"] for r in zaversheni], pul.map(lambda r: dzhoby(r, a.кеш), zaversheni)))
    for r in zaversheni:
        js = po_zapusku[r["id"]]
        for j in js:
            for k in j.get("steps") or []:
                if k.get("started_at") and k.get("completed_at"):
                    kroky[(r["name"], nazva_dzhoba(j["name"]), k["name"])].append(
                        khv(chas(k["started_at"]), chas(k["completed_at"])))
            ryadky.append(dict(
                den=r["created_at"][:10], workflow=r["name"], podiia=r["event"], run=r["id"],
                sproba=r["run_attempt"], hilka=r["head_branch"], sha=r["head_sha"],
                vysnovok_run=r["conclusion"], dzhob=j["name"], vysnovok=j["conclusion"],
                ranner=(j.get("labels") or ["?"])[0],
                cherga_run=khv(chas(r["created_at"]), chas(r.get("run_started_at"))),
                cherga=khv(chas(j["created_at"]), chas(j.get("started_at"))) if j["conclusion"] != "skipped" else None,
                vykon=khv(chas(j.get("started_at")), chas(j.get("completed_at"))) if j["conclusion"] != "skipped" else None,
                created=j["created_at"], started=j.get("started_at"), completed=j.get("completed_at"),
            ))

    # PR: номер → запуски pull_request за головами
    # Поле pull_requests запуску здебільшого порожнє (у вимірі 01–08.11 — 143 з 4264): PR шукаємо за гілкою
    # голови й часом (PR відкрито до запуску й закрито не раніше).
    pr_runs = defaultdict(list)
    vid_pr = (min(r["created_at"] for r in runs)[:10] if runs else a.від)
    dt_vid = (dt.date.fromisoformat(vid_pr) - dt.timedelta(days=14)).isoformat()
    for p in spysok_pr(dt_vid, a.кеш):
        pr_za_hilkoiu.setdefault(p["head"]["ref"], []).append(p)
    for r in runs:
        if r["event"] != "pull_request" or r["status"] != "completed":
            continue
        nn = [p["number"] for p in r.get("pull_requests") or []]
        if not nn:
            for p in pr_za_hilkoiu.get(r["head_branch"], []):
                if p["created_at"] <= r["created_at"] and (not p["closed_at"] or r["created_at"] <= p["closed_at"]):
                    nn = [p["number"]]
        for n in nn:
            pr_runs[n].append(r)

    pr_ryadky = []
    with ThreadPoolExecutor(8) as pul:
        list(pul.map(lambda n: (pr(n, a.кеш), faily_pr(n, a.кеш)), sorted(pr_runs)))
    for n, rs in sorted(pr_runs.items()):
        try:
            p = pr(n, a.кеш)
        except urllib.error.HTTPError:
            continue
        faily = faily_pr(n, a.кеш)
        golova = p["head"]["sha"]
        ostanni = [r for r in rs if r["head_sha"] == golova]
        if not ostanni:   # голова PR без запуску в межах вибірки — беремо останню виміряну голову
            sha = max(rs, key=lambda r: r["created_at"])["head_sha"]
            ostanni = [r for r in rs if r["head_sha"] == sha]
        # Тіло PR, змінене після пушу (подія edited), знову ганяє «рядок ЖИВИЙ ПІСЛЯ» на тій самій голові — це не
        # час CI від пушу: з кожного workflow голови береться перший не скасований запуск (скасовані всі — перший).
        po_wf = defaultdict(list)
        for r in sorted(ostanni, key=lambda r: r["created_at"]):
            po_wf[r["name"]].append(r)
        ostanni = [next((r for r in rr if r["conclusion"] != "cancelled"), rr[0]) for rr in po_wf.values()]
        start = min(chas(r["created_at"]) for r in ostanni)
        kin = max(chas(r["updated_at"]) for r in ostanni)
        js_vsi = [j for r in ostanni for j in po_zapusku.get(r["id"], [])]
        jk = [chas(j["completed_at"]) for j in js_vsi if j.get("completed_at")]
        if jk:
            kin = max(jk)
        z_js = [(chas(j["completed_at"]), f"{r['name']}: {nazva_dzhoba(j['name'])}") for r in ostanni
                for j in po_zapusku.get(r["id"], []) if j.get("completed_at") and j["conclusion"] != "skipped"]
        ostannii = max(z_js)[1] if z_js else "—"
        zb = [r for r in ostanni if r["name"] == "збірка показу"]
        cherga_kr, vykon_kr = krytychnyi_shliakh(po_zapusku.get(max(zb, key=lambda r: r["id"])["id"], []) if zb else js_vsi)
        pr_ryadky.append(dict(
            pr=n, den=start.date().isoformat(), vid="документ" if dokumentnyi(faily) else "код", produkt=produkt_zbirky(faily),
            zlyto=p.get("merged_at"), stvoreno=p["created_at"], golova=golova[:8],
            ci=khv(start, kin), cherga_kr=cherga_kr, vykon_kr=vykon_kr,
            pr_do_zlyttia=khv(chas(p["created_at"]), chas(p.get("merged_at"))),
            zelenyi_do_zlyttia=khv(kin, chas(p.get("merged_at"))),
            ostannii=ostannii,
            dzhoby=sorted({f"{r['name']}: {nazva_dzhoba(j['name'])}" for r in ostanni for j in po_zapusku.get(r['id'], [])
                           if j["conclusion"] not in ("skipped", None)}),
            vysnovky=sorted({r["conclusion"] for r in ostanni}),
        ))

    vyvid = zvit(ryadky, pr_ryadky, runs, a, kroky)
    print(vyvid)
    if a.md:
        with open(a.md, "w", encoding="utf-8") as f:
            f.write(vyvid + "\n")
    if a.csv:
        import csv
        with open(a.csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(ryadky[0].keys()))
            w.writeheader()
            for rr in ryadky:
                w.writerow({k: (f"{v:.2f}" if isinstance(v, float) else v) for k, v in rr.items()})


def paralelnist_tochna(ryadky):
    """Точна (до секунди) паралельність: макс одночасно на раннерах; скільки на раннерах у мить, коли
    джоб стає в чергу довше ніж на 2 хв (видно ліміт раннерів)."""
    rez = {}
    for os_ in ("linux", "windows"):
        rr = [r for r in ryadky if r["started"] and r["completed"] and r["cherga"] is not None
              and (("windows" in r["ranner"]) == (os_ == "windows"))]
        podii = sorted([(chas(r["started"]), 1) for r in rr] + [(chas(r["completed"]), -1) for r in rr],
                       key=lambda x: (x[0], x[1]))
        tut, maks, chasy, znach = 0, 0, [], []
        for t, d in podii:
            tut += d
            maks = max(maks, tut)
            chasy.append(t)
            znach.append(tut)
        import bisect
        pry_cherzi = []
        for r in rr:
            if r["cherga"] > 2:
                t = chas(r["created"]) + dt.timedelta(minutes=1)
                i = bisect.bisect_right(chasy, t) - 1
                pry_cherzi.append(znach[i] if i >= 0 else 0)
        rez[os_] = (maks, pry_cherzi, len(rr))
    return rez


def paralelnist(ryadky):
    """Щохвилинно: джобів на раннерах і в черзі, окремо Linux і Windows."""
    podii = defaultdict(lambda: defaultdict(int))
    for r in ryadky:
        if not r["started"] or not r["completed"] or r["cherga"] is None:
            continue
        os_ = "windows" if "windows" in r["ranner"] else "linux"
        c, s, k = chas(r["created"]), chas(r["started"]), chas(r["completed"])
        t = c.replace(second=0)
        while t < k:
            if t >= s:
                podii[t][os_ + "_іде"] += 1
            else:
                podii[t][os_ + "_чекає"] += 1
            t += dt.timedelta(minutes=1)
    return podii


def zvit(ryadky, pr_ryadky, runs, a, kroky):
    L = []
    L.append(f"# Час CI: вибірка {'PR ' + a.pr if a.pr else a.від + '…' + a.до} (UTC)")
    L.append("")
    L.append(f"Запусків {len(runs)} (завершених {sum(r['status'] == 'completed' for r in runs)}), джобів "
             f"{len(ryadky)} (пропущених {sum(r['vysnovok'] == 'skipped' for r in ryadky)}), PR з запусками {len(pr_ryadky)}.")
    L.append("")
    L.append("## По джобу (хв): черга мед / p90 · виконання мед / p90 · запусків · висновки")
    L.append("")
    L.append("| workflow: джоб | n | черга | виконання | висновки |")
    L.append("|---|---|---|---|---|")
    grupy = defaultdict(list)
    for r in ryadky:
        if r["vysnovok"] == "skipped":
            continue
        nazva = nazva_dzhoba(r["dzhob"])
        grupy[f"{r['workflow']}: {nazva}"].append(r)
    for k, rs in sorted(grupy.items(), key=lambda kv: -sum(x["vykon"] or 0 for x in kv[1])):
        vys = defaultdict(int)
        for x in rs:
            vys[x["vysnovok"]] += 1
        L.append(f"| {k} | {len(rs)} | {med_p90([x['cherga'] for x in rs])} | {med_p90([x['vykon'] for x in rs])} | "
                 + ", ".join(f"{v} {n}" for v, n in sorted(vys.items(), key=lambda kv: -kv[1])) + " |")
    L.append("")
    L.append("## По дню: черга й виконання джобів (хв, мед / p90), хвилини раннерів")
    L.append("")
    L.append("| день | джобів | черга | виконання | хв раннера |")
    L.append("|---|---|---|---|---|")
    po_dniu = defaultdict(list)
    for r in ryadky:
        if r["vysnovok"] != "skipped" and r["vykon"] is not None:
            po_dniu[r["den"]].append(r)
    for d, rs in sorted(po_dniu.items()):
        L.append(f"| {d} | {len(rs)} | {med_p90([x['cherga'] for x in rs])} | {med_p90([x['vykon'] for x in rs])} | "
                 f"{sum(x['vykon'] for x in rs):.0f} |")
    L.append("")
    L.append("## PR: CI від останнього пушу (хв, мед / p90) і частка черги на критичному шляху збірки")
    L.append("")
    L.append("| вид PR | n | CI від пушу | черга на шляху | виконання на шляху | частка черги | зелений → злиття |")
    L.append("|---|---|---|---|---|---|---|")
    for vid in ("документ", "код"):
        rs = [p for p in pr_ryadky if p["vid"] == vid and p["ci"] is not None]
        if not rs:
            continue
        sum_ci = sum(p["cherga_kr"] + p["vykon_kr"] for p in rs) or 1
        L.append(f"| {vid} | {len(rs)} | {med_p90([p['ci'] for p in rs])} | {med_p90([p['cherga_kr'] for p in rs])} | "
                 f"{med_p90([p['vykon_kr'] for p in rs])} | {100 * sum(p['cherga_kr'] for p in rs) / sum_ci:.0f} % | "
                 f"{med_p90([p['zelenyi_do_zlyttia'] for p in rs if p['zlyto']])} |")
    L.append("")
    L.append("CI від пушу по дню старту останньої голови (мед / p90, n):")
    L.append("")
    L.append("| день | документ | код |")
    L.append("|---|---|---|")
    for d in sorted({p["den"] for p in pr_ryadky}):
        kom = []
        for vid in ("документ", "код"):
            xs = [p["ci"] for p in pr_ryadky if p["den"] == d and p["vid"] == vid and p["ci"] is not None]
            kom.append(f"{med_p90(xs)} ({len(xs)})")
        L.append(f"| {d} | {kom[0]} | {kom[1]} |")
    L.append("")
    L.append("Найдовший джоб останньої голови PR (той, що закінчився останнім), за видом PR:")
    L.append("")
    ostanni = defaultdict(lambda: defaultdict(int))
    for p in pr_ryadky:
        ostanni[p["vid"]][p["ostannii"]] += 1
    for vid, lich in ostanni.items():
        L.append(f"- {vid}: " + "; ".join(f"{k} — {v}" for k, v in sorted(lich.items(), key=lambda kv: -kv[1])[:5]))
    L.append("")
    L.append("## Документні PR: які джоби йдуть (з усіх документних PR)")
    L.append("")
    lich = defaultdict(int)
    hv = defaultdict(float)
    doc = [p for p in pr_ryadky if p["vid"] == "документ"]
    for p in doc:
        for d in p["dzhoby"]:
            lich[d] += 1
    for r in ryadky:
        pass
    L.append(f"Документних PR: {len(doc)}; з них продуктний прапор збірки (аудит/проби/…): "
             f"{sum(p['produkt'] for p in doc)}.")
    L.append("")
    L.append("| джоб | на скількох документних PR |")
    L.append("|---|---|")
    for k, v in sorted(lich.items(), key=lambda kv: -kv[1]):
        L.append(f"| {k} | {v} |")
    L.append("")
    pod = paralelnist(ryadky)
    if pod:
        for os_ in ("linux", "windows"):
            ide = [v[os_ + "_іде"] for v in pod.values()]
            chek = [v[os_ + "_чекає"] for v in pod.values()]
            khv_cherga = sum(1 for v in pod.values() if v[os_ + "_чекає"] > 0)
            L.append(f"- Паралельність {os_}: одночасно на раннерах макс {max(ide)}, p90 {kvantyl(ide, 0.9)}; "
                     f"чекають у черзі макс {max(chek)}; хвилин, коли хтось чекає, — {khv_cherga} з {len(pod)}; "
                     f"у ці хвилини на раннерах мед {statistics.median([v[os_ + '_іде'] for v in pod.values() if v[os_ + '_чекає'] > 0] or [0])}.")
    for os_, (maks, pry, n) in paralelnist_tochna(ryadky).items():
        if n:
            L.append(f"- {os_}: точний макс одночасно на раннерах {maks}; джобів, що чекали > 2 хв, — {len(pry)} з {n}; "
                     f"у ту мить на раннерах мед {statistics.median(pry) if pry else '—'}, p10 {kvantyl(pry, 0.1)}.")
    L.append("")
    vsogo = sum(r["vykon"] or 0 for r in ryadky)
    L.append(f"## Кроки, що забирають найбільше хвилин раннерів (усього джобами {vsogo:.0f} хв)")
    L.append("")
    L.append("| workflow: джоб: крок | n | мед | хв усього | частка |")
    L.append("|---|---|---|---|---|")
    for (wf, dz, kr), xs in sorted(kroky.items(), key=lambda kv: -sum(kv[1]))[:12]:
        L.append(f"| {wf}: {dz}: {kr} | {len(xs)} | {f1(statistics.median(xs))} | {sum(xs):.0f} | "
                 f"{100 * sum(xs) / (vsogo or 1):.0f} % |")
    L.append("")
    L.append("## Хвилини раннерів за подією й workflow")
    L.append("")
    L.append("| подія | workflow | хв раннера | запусків |")
    L.append("|---|---|---|---|")
    hvr = defaultdict(float)
    zap = defaultdict(set)
    for r in ryadky:
        if r["vykon"] is not None:
            hvr[(r["podiia"], r["workflow"])] += r["vykon"]
            zap[(r["podiia"], r["workflow"])].add(r["run"])
    for (pod, wf), v in sorted(hvr.items(), key=lambda kv: -kv[1]):
        L.append(f"| {pod} | {wf} | {v:.0f} | {len(zap[(pod, wf)])} |")
    L.append("")
    if a.pr:
        L.append("## PR вибірки")
        L.append("")
        for p in pr_ryadky:
            L.append(f"- #{p['pr']} {p['vid']} (продукт збірки: {p['produkt']}), голова {p['golova']}: CI {f1(p['ci'])} хв, "
                     f"висновки {', '.join(str(v) for v in p['vysnovky'])}; джоби: {'; '.join(p['dzhoby'])}")
    return "\n".join(L)


if __name__ == "__main__":
    main()
