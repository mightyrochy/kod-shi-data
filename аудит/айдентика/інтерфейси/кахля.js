/* Малюнок за кахлею Петра Кошака «Олень» (Пістинь, 1911; Національний музей народного мистецтва
   Гуцульщини та Покуття; знімок — суспільне надбання, Вікісховище, File:Koshak_Tile_Deer_1911.jpg).
   Координати — простір знімка 960 × 1087. Лівий олень, листок і ліва квітка обведені зі знімка;
   правий бік — дзеркальне відбиття лівого довкола осі A. Барви — три поливи кахлі й бура лінія. */
(function (root) {
  'use strict';
  var A = 490;
  var BARVY = { bura: '#4B2A1B', zel: '#1F9A6C', zhov: '#E8B32A', tlo: '#FAF6EA' };

  function r1(n) { return Math.round(n * 10) / 10; }
  function t(p) { return r1(p[0]) + ' ' + r1(p[1]); }
  /* гладка крива через точки (Catmull–Rom → кубічні Безьє) */
  function kr(p, pochatok) {
    var d = pochatok === false ? '' : 'M' + t(p[0]);
    for (var i = 0; i < p.length - 1; i++) {
      var p0 = p[i - 1] || p[i], p1 = p[i], p2 = p[i + 1], p3 = p[i + 2] || p2;
      d += 'C' + t([p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6]) + ' ' +
        t([p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]) + ' ' + t(p2);
    }
    return d;
  }
  function zamk(p) {
    var n = p.length, d = 'M' + t(p[0]);
    for (var i = 0; i < n; i++) {
      var p0 = p[(i - 1 + n) % n], p1 = p[i], p2 = p[(i + 1) % n], p3 = p[(i + 2) % n];
      d += 'C' + t([p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6]) + ' ' +
        t([p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6]) + ' ' + t(p2);
    }
    return d + 'Z';
  }
  /* листок: дві криві, що сходяться гострими кінцями */
  function lyst(verh, nyz) { return kr(verh) + kr([verh[verh.length - 1]].concat(nyz, [verh[0]]), false) + 'Z'; }
  /* симетрична форма з лівого півпрофілю (згори донизу) довкола осі */
  function sym(pp, os) {
    os = os == null ? A : os;
    var prav = pp.slice().reverse().map(function (q) { return [2 * os - q[0], q[1]]; });
    return kr(pp) + 'L' + t(prav[0]) + kr(prav, false) + 'Z';
  }
  function zsuv(p, dx, dy) { return p.map(function (q) { return [q[0] + dx, q[1] + dy]; }); }
  function rnd(seed) { var s = seed >>> 0; return function () { s += 0x6D2B79F5; var z = s; z = Math.imul(z ^ (z >>> 15), z | 1); z ^= z + Math.imul(z ^ (z >>> 7), z | 61); return ((z ^ (z >>> 14)) >>> 0) / 4294967296; }; }
  function vseredyni(q, poly) {
    var c = false;
    for (var i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      var a = poly[i], b = poly[j];
      if ((a[1] > q[1]) !== (b[1] > q[1]) && q[0] < (b[0] - a[0]) * (q[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c;
    }
    return c;
  }
  function krapla(x, y, sh, dov) { /* патьок поливи донизу */
    var h = sh / 2;
    return 'M' + t([x - h, y]) + 'L' + t([x - h * 0.9, y + dov - h]) + 'C' + t([x - h * 0.9, y + dov + h * 0.5]) + ' ' + t([x + h * 0.9, y + dov + h * 0.5]) + ' ' + t([x + h * 0.9, y + dov - h]) + 'L' + t([x + h, y]) + 'Z';
  }

  /* ───── олень (лівий) ───── */
  var spyna = [[86, 664], [92, 680], [106, 692], [140, 698], [200, 697], [240, 691], [268, 676], [290, 652], [306, 626], [322, 606], [342, 596], [372, 597], [400, 604], [428, 620], [448, 648], [459, 676], [458, 690]];
  var olen = { linii: [], tovsti: [], plamy: [], zel: [], zhov: [] };
  olen.linii.push(
    kr(spyna),
    kr([[458, 690], [446, 698], [430, 690], [414, 670], [398, 652], [392, 672], [390, 705], [396, 740], [402, 775], [396, 795], [380, 803]]),
    kr([[100, 694], [101, 730], [102, 790], [103, 830]]),
    kr([[303, 808], [250, 822], [200, 831], [160, 833]]),
    kr([[103, 830], [95, 860], [84, 890], [81, 930], [82, 990]]), kr([[128, 838], [118, 870], [102, 900], [100, 940], [104, 990]]),
    kr([[136, 838], [134, 900], [139, 960], [142, 990]]), kr([[198, 836], [190, 880], [166, 912], [160, 960], [162, 988]]),
    kr([[303, 808], [303, 880], [301, 972]]), kr([[328, 806], [323, 900], [320, 975]]),
    kr([[344, 806], [345, 900], [343, 978]]), kr([[372, 803], [368, 900], [371, 985]]),
    zamk([[343, 618], [354, 607], [366, 605], [378, 608], [388, 618], [377, 628], [365, 631], [353, 628]]),
    kr([[452, 695], [441, 691], [431, 683]]),
    lyst([[340, 597], [326, 584], [311, 580]], [[320, 592], [333, 601]])
  );
  /* грива: риски під лінією спини й уздовж шиї */
  (function () {
    var g = rnd(7), x;
    for (x = 124; x < 262; x += 10.6) olen.linii.push(kr([[x + g() * 2, 704], [x - 1 + g() * 2, 716], [x - 3 + g() * 2, 727 + g() * 3]]));
    var shyia = [[272, 682], [282, 670], [292, 657], [301, 643], [309, 629], [318, 616], [328, 606]];
    shyia.forEach(function (q, i) { var d = 26 + i * 1.5; olen.linii.push(kr([[q[0] + 3, q[1] + 5], [q[0] + 6, q[1] + 5 + d / 2], [q[0] + 7 + g() * 2, q[1] + 5 + d]])); });
  })();
  /* роги — товстий бурий штрих */
  olen.tovsti.push(
    kr([[358, 592], [353, 562], [347, 528], [336, 494], [327, 472]]), kr([[349, 536], [334, 530], [322, 514]]),
    kr([[354, 566], [371, 540], [378, 508], [373, 482]]), kr([[336, 494], [347, 484], [350, 470]]),
    kr([[382, 594], [397, 568], [409, 538], [407, 508], [398, 484]]), kr([[407, 542], [425, 531], [436, 512]]),
    kr([[397, 568], [418, 563], [434, 550]]), kr([[407, 508], [418, 496], [420, 480]])
  );
  /* бурі плями: зіниця, ніс, копита, крапки */
  function kolo(x, y, r) { return 'M' + t([x - r, y]) + 'A' + r1(r) + ' ' + r1(r) + ' 0 1 0 ' + t([x + r, y]) + 'A' + r1(r) + ' ' + r1(r) + ' 0 1 0 ' + t([x - r, y]) + 'Z'; }
  function kopyto(x, y) { return zamk([[x - 22, y + 2], [x - 20, y - 12], [x - 6, y - 15], [x, y - 5], [x + 7, y - 15], [x + 21, y - 11], [x + 22, y + 4], [x + 12, y + 15], [x, y + 9], [x - 12, y + 16]]); }
  olen.plamy.push(zamk([[355, 620], [366, 614], [378, 620], [373, 629], [365, 631], [357, 629]]), kolo(449, 684, 7.5),
    kopyto(93, 1008), kopyto(152, 1008), kopyto(311, 996), kopyto(358, 1006));
  (function () {
    var g = rnd(11), poly = [[110, 736], [262, 732], [294, 702], [318, 664], [338, 640], [388, 670], [394, 790], [300, 805], [200, 827], [110, 827]], ry = 0;
    for (var y = 655; y < 826; y += 21.5, ry++) for (var x = 118 + (ry % 2) * 12.5; x < 394; x += 25) {
      var q = [x + (g() - 0.5) * 6, y + (g() - 0.5) * 6];
      if (vseredyni(q, poly) && vseredyni([q[0] - 8, q[1]], poly) && vseredyni([q[0] + 8, q[1]], poly) && vseredyni([q[0], q[1] + 8], poly)) olen.plamy.push(kolo(q[0], q[1], 6.2 + g() * 1.9));
    }
  })();
  /* полива оленя: жовта — спина й шия, зелена — груди, черево й голова */
  olen.zhov.push(zamk([[112, 706], [180, 703], [262, 696], [298, 664], [326, 622], [350, 640], [318, 700], [280, 744], [210, 768], [150, 762], [112, 752]]),
    zamk([[138, 842], [196, 840], [188, 884], [164, 916], [160, 990], [142, 990], [136, 910]]),
    zamk([[346, 808], [371, 806], [368, 900], [370, 984], [345, 978], [346, 900]]));
  olen.zel.push(zamk([[112, 758], [150, 770], [212, 774], [282, 750], [322, 706], [354, 646], [392, 662], [398, 742], [398, 794], [330, 808], [250, 824], [160, 836], [108, 830]]),
    zamk([[380, 603], [404, 608], [430, 622], [450, 650], [460, 680], [452, 698], [432, 692], [412, 668], [398, 650], [384, 628]]),
    zamk([[104, 834], [127, 840], [117, 872], [102, 902], [101, 944], [104, 990], [84, 990], [82, 930], [85, 890], [96, 860]]),
    zamk([[304, 810], [327, 808], [322, 900], [320, 974], [302, 972], [304, 890]]),
    krapla(436, 696, 8, 34), krapla(449, 698, 6, 17));

  /* ───── листок над спиною ───── */
  var lystok = { linii: [], tovsti: [], plamy: [], zel: [], zhov: [] };
  var lv = [[60, 621], [100, 600], [150, 571], [200, 555], [240, 562], [257, 585]], ln = [[258, 612], [240, 640], [200, 651], [150, 646], [100, 633]];
  lystok.linii.push(lyst(lv, ln), kolo(275, 592, 11), kr([[287, 590], [312, 589], [338, 593]]));
  [[100, 616], [122, 612], [146, 608], [167, 606], [187, 604], [205, 603], [222, 602], [238, 601]].forEach(function (q, i) {
    var h = 9 + Math.min(i, 5) * 1.6; lystok.linii.push(kr([[q[0] + 3, q[1] - h], [q[0] - 2, q[1]], [q[0] + 2, q[1] + h]]));
  });
  lystok.plamy.push(kolo(275, 592, 4));
  lystok.zel.push(lyst(zsuv(lv, 2, 6), zsuv(ln, 2, 7)), krapla(128, 640, 9, 20), krapla(176, 650, 11, 34), krapla(214, 652, 8, 16));

  /* ───── внутрішні листки при осі (лівий бік) ───── */
  var vnutr = { linii: [], tovsti: [], plamy: [], zel: [], zhov: [] };
  var zl_n = [[480, 468], [452, 446], [430, 424], [404, 412], [396, 392], [368, 378], [362, 356], [340, 340], [334, 322]], zl_v = [[356, 318], [372, 330], [388, 350], [408, 372], [432, 398], [458, 430]];
  vnutr.linii.push(kr(zl_n) + kr([[334, 322]].concat(zl_v, [[480, 468]]), false) + 'Z');
  vnutr.zel.push(kr(zsuv(zl_n, 0, 5)) + kr(zsuv([[334, 322]].concat(zl_v, [[480, 468]]), 0, 5), false) + 'Z', krapla(398, 414, 8, 18));
  vnutr.plamy.push(kr([[484, 452], [462, 424], [448, 396], [428, 372], [420, 346], [402, 318]]) + kr([[402, 318], [424, 330], [440, 352], [452, 376], [470, 404], [486, 434]], false) + 'Z');

  /* ───── вісь: держак, листок між носами, насінина, вазон ───── */
  var vis = { linii: [], tovsti: [], plamy: [], zel: [], zhov: [] };
  var lanc = [[A, 590], [A - 9, 612], [A - 13, 642], [A - 9, 674], [A, 704]];
  var bud = [[A, 764], [A - 7, 776], [A - 20, 792], [A - 36, 812], [A - 42, 838], [A - 36, 870], [A - 26, 910], [A - 18, 960], [A - 12, 1010], [A - 8, 1040]];
  var sertse = [[A, 836], [A - 12, 852], [A - 19, 880], [A - 17, 920], [A - 11, 970], [A - 4, 1036]];
  var vl_z = [[386, 822], [393, 862], [412, 896], [400, 930], [430, 958], [424, 992], [452, 1040]], vl_v = [[470, 1040], [460, 958], [444, 898], [418, 848]];
  vis.linii.push(kr([[A, 318], [A - 1, 400], [A, 480], [A, 588]]), sym(lanc), sym(bud));
  vnutr.linii.push(kr(vl_z) + 'L' + t(vl_v[0]) + kr(vl_v.concat([[386, 822]]), false) + 'Z');
  vis.plamy.push(sym([[A, 721], [A - 11, 728], [A - 16, 742], [A - 11, 757], [A, 763]]), sym(sertse));
  vis.zel.push(sym(zsuv(lanc, 0, 5)), krapla(A - 5, 700, 6, 26), krapla(A + 6, 702, 5, 14));
  vnutr.zel.push(kr(zsuv(vl_z, 2, 5)) + 'L' + t([472, 1045]) + kr(zsuv(vl_v.concat([[386, 822]]), 2, 5), false) + 'Z');
  vis.zhov.push(sym(zsuv(bud, 0, 4)));

  /* ───── квітка: серединка, шість пелюсток через одну, вінець із рисок, зубчастий край ───── */
  function kvitka(cx, cy, R, o) {
    o = o || {}; var g = rnd(o.zerno || 3), k = { linii: [], tovsti: [], plamy: [], zel: [], zhov: [], pelustky: [], vinets: '', sered: '' };
    function pt(r, a) { return [cx + R * r * Math.cos(a), cy + R * r * Math.sin(a)]; }
    var n = 22, kr_ = [], i, a;
    for (i = 0; i < n; i++) { a = (i / n) * Math.PI * 2 + 0.1; kr_.push(pt(0.985 + (g() - 0.5) * 0.03, a)); kr_.push(pt(0.915 + (g() - 0.5) * 0.02, a + Math.PI / n)); }
    k.linii.push(zamk(kr_));
    var vn = []; for (i = 0; i < 30; i++) { a = (i / 30) * Math.PI * 2; vn.push(pt(0.6 + (g() - 0.5) * 0.02, a)); }
    k.linii.push(zamk(vn));
    for (i = 0; i < 38; i++) { a = (i / 38) * Math.PI * 2 + (g() - 0.5) * 0.04; k.linii.push(kr([pt(0.68 + g() * 0.02, a), pt(0.76, a + 0.012), pt(0.845 + g() * 0.02, a)])); }
    var np = o.n || 6;
    for (i = 0; i < np; i++) {
      a = (i / np) * Math.PI * 2 - Math.PI / 2 + (np === 6 ? 0.26 : 0) + (g() - 0.5) * 0.06;
      var w = 2.4 / np, d = zamk([pt(0.13, a), pt(0.34, a - w), pt(0.52, a - w * 0.68), pt(0.565, a), pt(0.52, a + w * 0.68), pt(0.34, a + w)]);
      k.pelustky.push(d);
    }
    var sr = []; for (i = 0; i < 10; i++) { a = (i / 10) * Math.PI * 2; sr.push(pt(0.085 + (g() - 0.5) * 0.012, a)); }
    k.sered = zamk(sr);
    /* вінець для поливи: кільце між внутрішнім колом і краєм, зсунуте донизу */
    var zov = [], vnu = [];
    for (i = 0; i < 26; i++) { a = (i / 26) * Math.PI * 2; zov.push(pt(0.99 + (g() - 0.5) * 0.05, a)); vnu.push(pt(0.6, -a)); }
    k.vinets = zamk(zsuv(zov, 0, R * 0.045)) + zamk(zsuv(vnu, 0, R * 0.02));
    k.patoky = [krapla(cx - R * 0.42, cy + R * 0.86, R * 0.13, R * 0.3), krapla(cx + R * 0.1, cy + R * 0.97, R * 0.1, R * 0.17), krapla(cx + R * 0.5, cy + R * 0.82, R * 0.11, R * 0.36)];
    return k;
  }


  /* ───── складання малюнка ─────
     o.vb — вікно [x, y, w, h]; o.l, o.p, o.v — чи полито лівий бік, правий бік і вісь;
     o.je — які боки малювати {l, p, v}; o.bez — без яких частин боку {olen, lystok, vnutr};
     o.kv — квітки {v, l, p}: null — нема; {pol: 0|1, sklo: 1 — порожнє скло люстерка, barvy: [...] — знак образу};
     o.portret — адреса фото в склі верхньої квітки; o.anim — номери штрихам (--i) для руху «малює»;
     o.filtry === false — без тремтіння лінії й плям поливи (дрібні розміри) */
  var LIV = [207, 407, 115], VERH = [A, 200, 117];
  function filtry(id) {
    return '<filter id="fp' + id + '" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.016" numOctaves="2" seed="8" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="13" xChannelSelector="R" yChannelSelector="G" result="d"/><feTurbulence type="fractalNoise" baseFrequency="0.028" numOctaves="3" seed="21" result="t"/><feColorMatrix in="t" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1.5 0 0 0 -0.52" result="w"/><feComposite in="d" in2="w" operator="out"/></filter>' +
      '<filter id="fl' + id + '" x="-2%" y="-2%" width="104%" height="104%"><feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="2.6" xChannelSelector="R" yChannelSelector="G"/></filter>';
  }
  function malyunok(o) {
    o = o || {}; var vb = o.vb || [40, 70, 900, 990], id = o.id || 'k', B = BARVY, n = 0, F = o.filtry !== false;
    var je = o.je || { l: 1, p: 1, v: 1 }, bez = o.bez || {};
    var kv = o.kv === undefined ? { v: { pol: o.v }, l: { pol: o.l }, p: { pol: o.p } } : o.kv;
    function sh(d) { return '<path class="sh" d="' + d + '"' + (o.anim ? ' pathLength="1" style="--i:' + (n++) + '"' : '') + '/>'; }
    function shary(ch, pol, imja) { /* частина → шари */
      return { imja: imja, zhov: pol ? ch.zhov.join('') : '', zel: pol ? ch.zel.join('') : '', plamy: ch.plamy.join(''), linii: ch.linii.map(function (d) { return sh(d); }).join(''), tovsti: ch.tovsti.map(function (d) { return sh(d); }).join('') };
    }
    function kvit(c, st) {
      if (!st) return null;
      var k = kvitka(c[0], c[1], c[2], { zerno: st.zerno || 3, n: st.barvy ? st.barvy.length : 6 }), r = { imja: 'kvitka', zhov: '', zel: '', plamy: '', linii: k.linii.map(function (d) { return sh(d); }).join(''), tovsti: '', svoi: '' };
      if (st.barvy) { /* знак образу: пелюстки — кольори речей */
        r.svoi = '<path d="' + k.vinets + '" fill="' + (st.vinets || '#EFE6CF') + '" fill-rule="evenodd"/>' + k.pelustky.map(function (d, i) { return '<path d="' + d + '" fill="' + st.barvy[i % st.barvy.length] + '"/>'; }).join('') + '<path d="' + k.sered + '" fill="' + (st.sered || B.bura) + '"/>';
      } else if (st.pol) {
        r.zhov = k.vinets + k.patoky.join('') + (st.sklo ? '' : k.sered); r.zel = st.sklo ? '' : k.pelustky.filter(function (d, i) { return i % 2 === 1; }).join('');
        r.plamy = st.sklo ? '' : k.pelustky.filter(function (d, i) { return i % 2 === 0; }).join('');
      }
      if (!st.sklo) r.linii += k.pelustky.map(function (d) { return sh(d); }).join('') + sh(k.sered);
      return r;
    }
    function bik(pol, stKv) {
      n = 0; var a = [], q = kvit(LIV, stKv);
      if (!bez.olen) a.push(shary(olen, pol, 'olen'));
      if (!bez.lystok) a.push(shary(lystok, pol, 'lystok'));
      if (!bez.vnutr) a.push(shary(vnutr, pol, 'vnutr'));
      if (q) { a.push(q); a.push({ imja: 'kvitka', linii: sh(kr([[283, 497], [310, 540], [340, 584]])) }); }
      return a;
    }
    var L = je.l ? bik(o.l, kv.l) : [], P = je.p ? bik(o.p, kv.p) : [], V = [], qv;
    if (je.v) { n = 0; V.push(shary(vis, o.v, 'vis')); qv = kvit(VERH, kv.v); if (qv) V.push(qv); }
    var dz = ' transform="translate(' + (2 * A) + ' 0) scale(-1 1)"';
    function shar(pole, atr, yak) {
      function f(a) { return a.map(function (x) { return yak ? yak(x[pole] || '', x.imja) : (x[pole] || ''); }).join(''); }
      return '<g ' + atr + '>' + (je.l ? '<g class="bik-l">' + f(L) + '</g>' : '') + (je.p ? '<g class="bik-p"' + dz + '>' + f(P) + '</g>' : '') + (je.v ? '<g class="bik-v">' + f(V) + '</g>' : '') + '</g>';
    }
    function pth(c) { return function (d, imja) { return d ? '<path class="pol ch-' + imja + '" d="' + d + '" fill="' + c + '" fill-rule="evenodd"/>' : ''; }; }
    var foto = o.portret ? '<clipPath id="cs' + id + '"><circle cx="' + A + '" cy="200" r="70"/></clipPath><image class="portret" href="' + o.portret + '" x="' + (A - 71) + '" y="129" width="142" height="142" preserveAspectRatio="xMidYMid slice" clip-path="url(#cs' + id + ')"/>' : '';
    return '<svg class="kah' + (o.klas ? ' ' + o.klas : '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="' + vb.join(' ') + '" role="img" aria-label="' + (o.pidpys || 'Два олені обабіч квітки — малюнок за кахлею Петра Кошака, 1911') + '">' +
      '<defs>' + (F ? filtry(id) : '') + '</defs>' + foto +
      shar('zhov', 'class="shar zhov" style="mix-blend-mode:multiply"' + (F ? ' filter="url(#fp' + id + ')"' : ''), pth(B.zhov)) +
      shar('zel', 'class="shar zel" style="mix-blend-mode:multiply"' + (F ? ' filter="url(#fp' + id + ')"' : ''), pth(B.zel)) +
      shar('svoi', 'class="shar svoi"') +
      '<g' + (F ? ' filter="url(#fl' + id + ')"' : '') + '>' +
      shar('plamy', 'class="shar plamy" fill="' + B.bura + '"', function (d, imja) { return d ? '<path class="pl ch-' + imja + '" d="' + d + '"/>' : ''; }) +
      shar('linii', 'class="shar linii" fill="none" stroke="' + B.bura + '" stroke-width="' + (o.tov || 4.4) + '" stroke-linecap="round" stroke-linejoin="round"') +
      shar('tovsti', 'class="shar tovsti" fill="none" stroke="' + B.bura + '" stroke-width="' + (o.tovst || 11) + '" stroke-linecap="round" stroke-linejoin="round"') +
      '</g></svg>';
  }

  /* ───── знак: квітка окремо ─────
     o.px — розмір на екрані (лінія не тонша за 1,4 px); o.barvy — кольори пелюсток (речі образу; null — пелюстка лише лінією);
     o.vinets — колір вінця (полива чи нема); o.sklo — люстерко: порожнє скло; o.portret — фото в склі;
     o.rysky === false — без рисок вінця (дрібний знак); o.patoky — патьоки поливи під вінцем */
  function znak(o) {
    o = o || {}; var px = o.px || 64, R = 100, B = BARVY, np = o.sklo ? 6 : (o.barvy ? o.barvy.length : 6);
    var k = kvitka(0, 0, R, { zerno: o.zerno || 3, n: np }), tov = Math.max(4.4, 1.4 * 216 / px), s = '', id = o.id || 'z';
    var rysky = o.rysky === undefined ? px >= 56 : o.rysky, vys = o.patoky ? 252 : 216;
    if (o.vinets) s += '<path class="vin" d="' + k.vinets + (o.patoky ? k.patoky.join('') : '') + '" fill="' + o.vinets + '" fill-rule="evenodd"/>';
    if (o.portret) s += '<clipPath id="cz' + id + '"><circle r="60"/></clipPath><image href="' + o.portret + '" x="-61" y="-61" width="122" height="122" preserveAspectRatio="xMidYMid slice" clip-path="url(#cz' + id + ')"/>';
    if (!o.sklo) {
      s += k.pelustky.map(function (d, i) { var c = o.barvy && o.barvy[i]; return '<path class="pel" d="' + d + '" fill="' + (c || 'none') + '"' + (c ? '' : ' stroke-dasharray="' + r1(tov * 0.2) + ' ' + r1(tov * 2) + '"') + '/>'; }).join('');
      s += '<path d="' + k.sered + '" fill="' + (o.sered || B.bura) + '" stroke="none"/>';
    }
    s += '<path d="' + k.linii[0] + '" fill="none"/><path d="' + k.linii[1] + '" fill="none"/>';
    if (rysky) s += '<path fill="none" d="' + k.linii.slice(2).join('') + '"/>';
    return '<svg class="znak' + (o.klas ? ' ' + o.klas : '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="-108 -108 216 ' + vys + '" width="' + px + '" height="' + Math.round(px * vys / 216) + '"' + (o.pidpys ? ' role="img" aria-label="' + o.pidpys + '"' : ' aria-hidden="true"') + ' stroke="' + B.bura + '" stroke-width="' + r1(tov) + '" stroke-linecap="round" stroke-linejoin="round">' + s + '</svg>';
  }

  /* ───── полива під складником інтерфейсу ─────
     пляма w × h px: виходить за контур і стікає патьоком; фільтр #fpS — один на сторінку (spilni) */
  function plama(w, h, barva, zerno) {
    var g = rnd(zerno || 1), p = [], i, n, vy = 4, bo = 6;
    n = Math.max(3, Math.round(w / 46)); for (i = 0; i <= n; i++) p.push([-bo + (w + 2 * bo) * i / n + (g() - .5) * 5, -vy + (g() - .5) * 5]);
    n = Math.max(2, Math.round(h / 40)); for (i = 1; i <= n; i++) p.push([w + bo + (g() - .5) * 5, -vy + (h + 2 * vy) * i / n + (g() - .5) * 4]);
    n = Math.max(3, Math.round(w / 46)); for (i = 1; i <= n; i++) p.push([w + bo - (w + 2 * bo) * i / n + (g() - .5) * 5, h + vy + (g() - .5) * 6]);
    n = Math.max(2, Math.round(h / 40)); for (i = 1; i < n; i++) p.push([-bo + (g() - .5) * 5, h + vy - (h + 2 * vy) * i / n + (g() - .5) * 4]);
    var kx = w * (0.16 + g() * 0.5), d = zamk(p) + krapla(kx, h + vy - 3, 7 + g() * 3, 12 + g() * 12) + (w > 150 ? krapla(kx + 20 + g() * 30, h + vy - 3, 5 + g() * 2, 7 + g() * 7) : '');
    return '<svg class="plama" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" width="' + (w + 40) + '" height="' + (h + 60) + '" viewBox="-20 -20 ' + (w + 40) + ' ' + (h + 60) + '"><path d="' + d + '" fill="' + (BARVY[barva] || barva) + '" filter="url(#fpS)"/></svg>';
  }
  function spilni() {
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><filter id="fpS" x="-10%" y="-10%" width="120%" height="130%"><feTurbulence type="fractalNoise" baseFrequency="0.045" numOctaves="2" seed="8" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="5" xChannelSelector="R" yChannelSelector="G" result="d"/><feTurbulence type="fractalNoise" baseFrequency="0.07" numOctaves="3" seed="21" result="t"/><feColorMatrix in="t" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1.5 0 0 0 -0.5" result="w"/><feComposite in="d" in2="w" operator="out"/></filter></defs></svg>';
  }

  root.КАХЛЯ = { A: A, W: 960, H: 1087, BARVY: BARVY, olen: olen, lystok: lystok, vnutr: vnutr, vis: vis, kvitka: kvitka, malyunok: malyunok, znak: znak, plama: plama, spilni: spilni, kr: kr, zamk: zamk, krapla: krapla, rnd: rnd };
})(typeof window !== 'undefined' ? window : globalThis);
