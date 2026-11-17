/* Теми «Мальованого люстерка»: каркас один, рук і барв — кілька (слово власника 17.11.2026).
   Каркас — шапка з медальйоном, два боки (зворот — розмова, лице — образ), три місця внизу, одна дія кроку —
   живе в мальоване.js і мальоване.css і про теми не знає. Тема про сцени не знає теж; вона дає лише це:
     nazva, pro           — ім’я теми й один рядок про руку (для вибору «Твоє люстерко»);
     zminni               — барви й шрифт інтерфейсу: значення змінних --tlo, --bila, --bura, --tin, --zel, --zhov, --lin, --f;
     css                  — стилі теми: стан малюнка під час чекання, стиль тексту; усе під html[data-tema="…"];
     BARVY                — ті самі барви для малюнків: bura — лінія й текст, zhov — барва вибраного, zel — друга, tlo — тло;
     malyunok(o)          — головний малюнок: перший екран і чекання (каркас додає кореню класи k1…k5 і vypal),
                            помилка (o.klas 'pom'), сама постать (o.je без p), саме люстерко з фото (o.je лише v, o.portret);
     znak(o)              — знак образу з барв речей (o.barvy), люстерко-голос (o.sklo), медальйон із фото (o.portret);
     pelustka(px, barva)  — знак однієї барви;   plama(w, h, barva, zerno) — позначка вибраного під складником;
     spilni()             — спільні визначення svg, раз на сторінку;
     napys(s, h, kl)      — великий напис у рамці кривих Misto (нема — самі криві Misto з написи.js);
     slova                — слова про ремесло: pidpys, poklychu, hotovo, nedo, shche, pusto, pustoT, pich (нема — слова кахлі).
   Вибір: ?тема=<id> в адресі, далі пам’ять браузера (сцена, вбудована рамкою в іншу сторінку, пам’яті не слухає);
   ТЕМА.obraty(id) перемальовує сцену без перезавантаження.
   Тут дві теми: «Кахля» (кахля.js) і службова «Каркас» — сама будова без руки й барви, щоб було видно, що не міняється. */
(function (root) {
  var T = {}, POR = [], potochna = null, sluhachi = [];
  var ZM0 = { '--tlo': '#FAF6EA', '--bila': '#fff', '--bura': '#4B2A1B', '--tin': '#775D4F', '--zel': '#1F9A6C', '--zhov': '#E8B32A', '--lin': 'rgba(75,42,27,.3)',
    '--f': "Geologica,system-ui,-apple-system,'Segoe UI',sans-serif" };
  function dodaty(id, t) { t.id = id; T[id] = t; if (POR.indexOf(id) < 0) POR.push(id); return t; }
  function pamjat(v) { try { if (v === undefined) return root.localStorage.getItem('люстерко-тема'); root.localStorage.setItem('люстерко-тема', v); } catch (e) { return null; } }
  function zastosuvaty(id) {
    var t = T[id] || T[POR[0]], el = document.documentElement, k, st, sp, m;
    potochna = t; el.setAttribute('data-tema', t.id);
    for (k in ZM0) el.style.setProperty(k, (t.zminni && t.zminni[k]) || ZM0[k]);
    m = document.querySelector('meta[name="theme-color"]'); if (m) m.setAttribute('content', (t.zminni && t.zminni['--tlo']) || ZM0['--tlo']);
    st = document.getElementById('tema-css'); if (!st) { st = document.createElement('style'); st.id = 'tema-css'; document.head.appendChild(st); }
    st.textContent = t.css || '';
    sp = document.getElementById('tema-spilni');
    if (!sp) { sp = document.createElement('div'); sp.id = 'tema-spilni'; sp.setAttribute('aria-hidden', 'true'); sp.style.cssText = 'position:absolute;width:0;height:0;overflow:hidden'; document.body.insertBefore(sp, document.body.firstChild); }
    sp.innerHTML = t.spilni ? t.spilni() : '';
    sluhachi.forEach(function (f) { f(t); });
  }
  function vydymi() { return POR.filter(function (id) { return !T[id].sluzhbova; }); }
  /* вибір теми: 'kr' — три люстерка в кутку першого екрана; 'kartky' — рядки з іменем і рукою у «Знайомстві» */
  function vybir(vyd) {
    var a = vydymi(); if (a.length < 2) return '';
    return '<div class="temy ' + vyd + '" role="radiogroup" aria-label="Обери своє люстерко">' + a.map(function (id) {
      var t = T[id];
      return '<button type="button" role="radio" aria-checked="' + (t === potochna) + '" data-tema-do="' + id + '" aria-label="Люстерко «' + t.nazva + '»: ' + t.pro + '">' +
        t.znak({ px: vyd === 'kr' ? 30 : 40, sklo: 1, vinets: t.BARVY.zhov, rysky: false, id: 't' + id }) +
        (vyd === 'kr' ? '' : '<span><b>' + t.nazva + '</b><small>' + t.pro + '</small></span>') + '</button>';
    }).join('') + '</div>';
  }
  function obraty(id) { if (!T[id]) return; pamjat(id); zastosuvaty(id); root.dispatchEvent(new Event('hashchange')); pult(); }
  var pb;
  function pult() { /* у смузі прототипу — кнопка, що перебирає всі теми, і службову теж */
    var p = document.querySelector('.pult'); if (!p) return;
    if (!pb) { pb = document.createElement('button'); pb.className = 'pt'; pb.onclick = function () { obraty(POR[(POR.indexOf(potochna.id) + 1) % POR.length]); }; p.appendChild(pb); }
    pb.textContent = 'тема: ' + potochna.nazva;
  }

  /* ───── «Кахля»: теперішня рука прототипу ───── */
  var K = root.КАХЛЯ;
  K.nazva = 'Кахля'; K.pro = 'мальована лінія й полива, Косів';
  dodaty('kahlja', K);

  /* ───── «Каркас»: сама будова. На місці малюнка — рамка з назвою гнізда, знак — коло з барв речей ───── */
  var S = '#2A2A2A', SV = '#D9D9D4';
  function ramka(o, w, h, pidpys, kroky) {
    var s = '<rect x="2" y="2" width="' + (w - 4) + '" height="' + (h - 4) + '" fill="none" stroke="' + S + '" stroke-width="1.5" stroke-dasharray="7 6"/>' +
      '<path d="M2 2L' + (w - 2) + ' ' + (h - 2) + 'M' + (w - 2) + ' 2L2 ' + (h - 2) + '" stroke="' + S + '" stroke-width="1" opacity=".22"/>' +
      '<rect x="' + (w / 2 - 92) + '" y="' + (h / 2 - 19) + '" width="184" height="38" fill="#F3F3F1"/>' +
      '<text x="' + w / 2 + '" y="' + (h / 2 + 5) + '" text-anchor="middle" font-family="system-ui,sans-serif" font-size="14" fill="' + S + '">' + pidpys + '</text>';
    if (kroky) for (var i = 1; i <= 5; i++) s += '<rect class="kk kk' + i + '" x="' + (w / 2 - 62 + (i - 1) * 26) + '" y="' + (h / 2 + 30) + '" width="20" height="8" fill="none" stroke="' + S + '" stroke-width="1.5"/>';
    return '<svg class="kah kark' + (o.klas ? ' ' + o.klas : '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="Місце малюнка теми: ' + pidpys + '">' + s + '</svg>';
  }
  function kolo(o) {
    o = o || {}; var px = o.px || 64, n = o.barvy ? o.barvy.length : 0, vys = o.patoky || o.misce ? 252 : 216, s = '', i, a, b, id = o.id || 'z';
    function pt(r, k) { return (r * Math.cos(k)).toFixed(1) + ' ' + (r * Math.sin(k)).toFixed(1); }
    if (o.vinets) s += '<circle r="98" fill="' + SV + '" stroke="none"/>';
    if (o.portret) s += '<clipPath id="ck' + id + '"><circle r="60"/></clipPath><image href="' + o.portret + '" x="-61" y="-61" width="122" height="122" preserveAspectRatio="xMidYMid slice" clip-path="url(#ck' + id + ')"/>';
    if (!o.sklo) for (i = 0; i < n; i++) { /* барви речей — вміст, а не шкірка: лишаються і в каркасі */
      a = i / n * Math.PI * 2 - Math.PI / 2; b = (i + 1) / n * Math.PI * 2 - Math.PI / 2;
      s += '<path d="M0 0L' + pt(60, a) + 'A60 60 0 0 1 ' + pt(60, b) + 'Z" fill="' + (o.barvy[i] || 'none') + '" stroke="#F3F3F1" stroke-width="3"/>';
    }
    s += '<circle r="98" fill="none" stroke-dasharray="' + (o.sklo ? '0' : '9 8') + '"/>' + (o.sklo && !o.portret ? '<circle r="60" fill="none"/>' : '');
    return '<svg class="znak' + (o.klas ? ' ' + o.klas : '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="-108 -108 216 ' + vys + '" width="' + px + '" height="' + Math.round(px * vys / 216) + '"' +
      (o.pidpys ? ' role="img" aria-label="' + o.pidpys + '"' : ' aria-hidden="true"') + ' stroke="' + S + '" stroke-width="' + Math.max(4, 1.4 * 216 / px).toFixed(1) + '">' + s + '</svg>';
  }
  dodaty('karkas', {
    nazva: 'Каркас', pro: 'сама будова, без руки й барви', sluzhbova: true,
    zminni: { '--tlo': '#F3F3F1', '--bura': S, '--tin': '#6E6E6E', '--zel': '#8C8C8C', '--zhov': SV, '--lin': 'rgba(42,42,42,.3)', '--f': "system-ui,-apple-system,'Segoe UI',sans-serif" },
    BARVY: { bura: S, zel: '#8C8C8C', zhov: SV, tlo: '#F3F3F1' },
    css: 'html[data-tema="karkas"] .chek.k1 .kk1,html[data-tema="karkas"] .chek.k2 .kk2,html[data-tema="karkas"] .chek.k3 .kk3,html[data-tema="karkas"] .chek.k4 .kk4,html[data-tema="karkas"] .chek.k5 .kk5{fill:' + S + '}' +
      'html[data-tema="karkas"] .mal-zl .kah{max-height:220px}html[data-tema="karkas"] .napys-t{font-family:system-ui,sans-serif}',
    malyunok: function (o) {
      o = o || {}; var je = o.je || { l: 1, p: 1, v: 1 };
      if (je.v && !je.l && !je.p) return kolo({ px: 216, sklo: 1, portret: o.portret, vinets: 1, id: o.id, pidpys: o.pidpys, klas: 'kah' });
      if (!je.p) return ramka(o, 300, 280, 'постать теми', false);
      return ramka(o, 360, 396, o.klas === 'pom' ? 'малюнок: урвалось' : 'головний малюнок теми', o.klas === 'chek');
    },
    znak: kolo,
    pelustka: function (px, barva) { return '<svg class="pel1" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" width="' + px + '" height="' + px + '" viewBox="-12 -12 24 24"><circle r="7.5" fill="' + (barva || 'none') + '" stroke="' + S + '" stroke-width="1.5"/></svg>'; },
    plama: function (w, h, barva) { return '<svg class="plama" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" width="' + (w + 40) + '" height="' + (h + 50) + '" viewBox="-20 -20 ' + (w + 40) + ' ' + (h + 50) + '"><rect width="' + w + '" height="' + h + '" fill="' + SV + '"/></svg>'; },
    napys: function (s, h, kl) { return tekst(s, h, kl, 'system-ui,sans-serif', 600, 900, ''); },
    slova: { pidpys: 'Каркас: на цьому місці тема ставить свій малюнок, знак і барви', poklychu: 'покличу, коли зберу', hotovo: 'Зібрала. Образ — на лиці.', nedo: 'Не зібрала', shche: 'Зібрати ще раз',
      pusto: 'Тут поки порожньо', pustoT: 'Кожен образ, який ти збережеш, ляже сюди плиткою — зі знаком із барв його речей і датою.',
      pich: 'Плитка за кожен образ: знак — із барв його речей. Вдягла — торкнись «ще не вдягала», і знак це покаже.' }
  });

  /* напис звичайним шрифтом у тій самій рамці, що й криві Misto: розкладка сцен від шрифту теми не залежить */
  function tekst(s, h, kl, rodyna, vaha, kegl, osi) {
    var n = root.НАПИСИ && root.НАПИСИ[s], w = n ? n[0] : s.length * 700, k = h / 700;
    return '<svg class="napys napys-t ' + (kl || '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="-10 -712 ' + (w + 20) + ' 728" width="' + Math.round((w + 20) * k) + '" height="' + Math.round(728 * k) + '" overflow="visible" role="img" aria-label="' + s + '">' +
      '<text x="0" y="0" font-family="' + rodyna + '" font-weight="' + vaha + '" font-size="' + kegl + '" textLength="' + w + '" lengthAdjust="spacing" fill="currentColor"' + (osi ? ' style="font-variation-settings:' + osi + '"' : '') + '>' + s + '</text></svg>';
  }

  root.ТЕМИ = T;
  root.ТЕМА = { dodaty: dodaty, obraty: obraty, vybir: vybir, tekst: tekst, spysok: function () { return POR.slice(); }, potochna: function () { return potochna; },
    koly: function (f) { sluhachi.push(f); if (potochna) f(potochna); },
    pochaty: function () { var m = /тема=([a-z]+)/.exec(decodeURIComponent(location.search)), sama = true;
      try { sama = root.top === root; } catch (e) { sama = false; }  /* сцена в рамці огляду чи аркуша системи пам’яті не слухає */
      zastosuvaty((m && T[m[1]] && m[1]) || (sama && T[pamjat()] && pamjat()) || root.ТЕМА_ПОЧАТКОВА || POR[0]); } };
  document.addEventListener('click', function (e) { var b = e.target.closest && e.target.closest('[data-tema-do]'); if (b) { e.preventDefault(); obraty(b.getAttribute('data-tema-do')); } });
  document.addEventListener('DOMContentLoaded', function () { setTimeout(pult, 0); });
})(typeof window !== 'undefined' ? window : globalThis);
