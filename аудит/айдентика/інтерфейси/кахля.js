/* Малюнок «Жінка перед люстерком»: придуманий, рукою косівської мальованої кахлі.
   Жінка й усе її вбрання намальовані тут, без взірця; квітка-люстерко, листки й вазон обведені з кахлі
   Петра Кошака «Олень» (Пістинь, 1911; Національний музей народного мистецтва Гуцульщини та Покуття;
   знімок — суспільне надбання, Вікісховище, File:Koshak_Tile_Deer_1911.jpg). Координати — простір того
   знімка, 960 × 1087. Правий бік — дзеркальне відбиття лівого довкола осі A: ліворуч вона, праворуч її
   відбиття. Барви — зелена й жовта поливи, бура лінія й бура пляма. */
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

  /* ───── жінка перед люстерком (ліва; обернена до осі) ─────
     Постать придумана, не обведена: сучасна жінка рукою косівської кахлі — голова й ступні в профіль,
     тулуб прямо. Кожна річ образу — окрема частина зі своєю поливою: сукня — зелена, пальто — жовта,
     черевики, сумка й смуги палантина — бура, сережка — жовта. */
  function kolo(x, y, r) { return 'M' + t([x - r, y]) + 'A' + r1(r) + ' ' + r1(r) + ' 0 1 0 ' + t([x + r, y]) + 'A' + r1(r) + ' ' + r1(r) + ' 0 1 0 ' + t([x - r, y]) + 'Z'; }
  function lam(p) { return 'M' + p.map(function (q) { return t(q); }).join('L') + 'Z'; }
  function obert(p, c, kut) { var a = kut * Math.PI / 180, co = Math.cos(a), si = Math.sin(a); return p.map(function (q) { var dx = q[0] - c[0], dy = q[1] - c[1]; return [c[0] + dx * co - dy * si, c[1] + dx * si + dy * co]; }); }
  function vzd(pl, u) { var x = u * (pl.length - 1), i = Math.min(pl.length - 2, Math.floor(x)), f = x - i; return [pl[i][0] + (pl[i + 1][0] - pl[i][0]) * f, pl[i][1] + (pl[i + 1][1] - pl[i][1]) * f]; }
  function chastyna() { return { linii: [], tovsti: [], plamy: [], zel: [], zhov: [], bura: [] }; }
  var SHYJA = [262, 378], NAHYL = -7;
  function hol(p) { return obert(p, SHYJA, NAHYL); } /* голова трохи закинута: дивиться в люстерко */
  var zhinka = chastyna(), suknia = chastyna(), palto = chastyna(), shkira = chastyna(), palantyn = chastyna(), serezhky = chastyna();

  /* голова: профіль, око, брова, волосся з гулькою, шия */
  zhinka.linii.push(
    kr(hol([[286, 280], [294, 292], [297, 306], [295, 314], [303, 326], [309, 335], [304, 341], [300, 346], [303.5, 351], [299.5, 355], [302.5, 359.5], [298.5, 365], [300, 373], [294, 381], [280, 380], [266, 372], [256, 360]])),
    lyst(hol([[272, 322], [281, 315], [291, 319]]), hol([[282, 325]])),
    kr(hol([[270, 310], [281, 304], [292, 307]])), kr(hol([[299.5, 355], [295, 355.5], [291, 353]])),
    kr([hol([[244, 356]])[0], [242, 372], [240, 386]]), kr([hol([[282, 381]])[0], [283, 388]])
  );
  (function () {
    var z = hol([[283, 320]])[0], gu = hol([[226, 262]])[0];
    zhinka.plamy.push(kolo(z[0], z[1], 3.4), kolo(gu[0], gu[1], 22),
      zamk(hol([[286, 280], [276, 270], [258, 264], [240, 268], [226, 282], [220, 302], [222, 324], [230, 342], [242, 354], [250, 352], [254, 340], [258, 326], [264, 310], [274, 294]])));
  })();
  /* руки: ближча тримає держак люстерка, дальня — сумку; ноги */
  zhinka.linii.push(
    kr([[457, 460], [470, 452], [483, 455], [487, 468], [484, 481], [471, 485]]), kr([[468, 464], [478, 463]]),
    kr([[149, 630], [146, 648], [152, 662], [163, 665], [170, 653], [171, 634]]),
    kr([[225, 902], [226, 962]]), kr([[248, 903], [248, 962]]), kr([[283, 903], [284, 962]]), kr([[306, 902], [306, 962]])
  );

  /* сукня міді: смуга в розпаху пальта, пасок, крапки */
  var smuha = [[245, 424], [279, 424], [286, 480], [292, 560], [302, 720], [313, 892], [262, 900], [211, 892], [222, 720], [232, 560], [238, 480]];
  suknia.linii.push(kr([[210, 895], [262, 903], [314, 895]]));
  suknia.tovsti.push(kr([[236, 563], [262, 566], [288, 563]]));
  (function () {
    var g = rnd(11), ry = 0, y, x, q;
    for (y = 442; y < 888; y += 24, ry++) for (x = 216 + (ry % 2) * 11; x < 314; x += 22) {
      q = [x + (g() - 0.5) * 4, y + (g() - 0.5) * 4];
      if (q[1] > 544 && q[1] < 584) continue;
      if (vseredyni(q, smuha) && vseredyni([q[0] - 9, q[1]], smuha) && vseredyni([q[0] + 9, q[1]], smuha)) suknia.plamy.push(kolo(q[0], q[1], 4 + g() * 1.3));
    }
  })();
  suknia.zel.push(lam(zsuv(smuha, 1, 5)), krapla(248, 904, 8, 24), krapla(290, 900, 6, 13));

  /* пальто, довше за сукню: рукави, боки, краї розпаху, поділ із рисками ворсу, ґудзики, кишеня */
  palto.linii.push(
    kr([[297, 404], [318, 404], [336, 409], [346, 418], [366, 458], [384, 494], [391, 504]]), kr([[391, 504], [420, 486], [455, 462]]),
    kr([[313, 440], [342, 492], [366, 536], [380, 548], [396, 541], [432, 512], [469, 482]]), kr([[455, 462], [469, 482]]),
    kr([[188, 404], [181, 421], [170, 475], [161, 529], [154, 580], [148, 628]]), kr([[212, 452], [200, 492], [191, 535], [181, 584], [172, 632]]), kr([[148, 628], [172, 632]]),
    kr([[212, 452], [203, 560], [192, 700], [177, 830], [165, 925]]), kr([[313, 440], [318, 480], [323, 560], [334, 700], [348, 830], [359, 925]]),
    kr([[243, 419], [238, 480], [232, 560], [222, 720], [210, 895], [207, 925]]), kr([[281, 419], [286, 480], [292, 560], [302, 720], [314, 895], [317, 925]]),
    kr([[165, 925], [186, 930], [207, 925]]), kr([[317, 925], [338, 930], [359, 925]]),
    kr([[309, 686], [320, 690], [331, 687]])
  );
  (function () { var x; for (x = 173; x < 204; x += 7.5) palto.linii.push(kr([[x, 905], [x - 1, 918]])); for (x = 322; x < 354; x += 7.5) palto.linii.push(kr([[x, 905], [x + 1, 918]])); })();
  palto.plamy.push(kolo(297, 470, 4.6), kolo(302, 530, 4.6), kolo(306, 592, 4.6));
  palto.zhov.push(
    lam(zsuv([[238, 417], [238, 480], [232, 560], [222, 720], [208, 925], [186, 930], [165, 925], [177, 830], [192, 700], [203, 560], [212, 452], [200, 492], [191, 535], [181, 584], [172, 632], [148, 628], [154, 580], [161, 529], [170, 475], [181, 421], [188, 404], [210, 409], [231, 414]], 2, 5)),
    lam(zsuv([[281, 419], [297, 406], [318, 404], [336, 409], [346, 418], [366, 458], [384, 494], [391, 504], [420, 486], [455, 462], [469, 482], [432, 512], [396, 541], [380, 548], [366, 536], [342, 492], [313, 440], [318, 480], [323, 560], [334, 700], [348, 830], [359, 925], [338, 930], [317, 925], [314, 895], [302, 720], [292, 560], [286, 480]], 2, 5)),
    krapla(182, 934, 9, 26), krapla(344, 934, 8, 18), krapla(388, 552, 7, 20));

  /* черевики й сумка коричнева шкіряна */
  function chobit(dx) { return zsuv([[226, 962], [225, 1000], [222, 1024], [223, 1040], [237, 1040], [239, 1031], [247, 1034], [248, 1040], [270, 1040], [276, 1034], [273, 1022], [262, 1010], [251, 996], [248, 962]], dx, 0); }
  var sumka = [[102, 702], [134, 700], [165, 700], [170, 738], [172, 776], [134, 780], [96, 781], [98, 742]];
  shkira.linii.push(lam(chobit(0)), lam(chobit(58)), zamk(sumka), kr([[157, 662], [132, 676], [116, 701]]), kr([[162, 665], [160, 682], [152, 700]]), kr([[99, 727], [134, 724], [169, 724]]));
  shkira.bura.push(lam(chobit(0)), lam(chobit(58)), zamk(sumka) + kolo(134, 725, 6.5));

  /* палантин: петля довкола шиї й кінець, що летить за плечем; смуги й торочки */
  var pv = [[233, 383], [200, 368], [165, 367], [133, 354], [105, 345], [82, 348]], pn = [[231, 414], [197, 405], [163, 403], [131, 391], [104, 382], [86, 386]];
  palantyn.linii.push(zamk([[236, 384], [260, 390], [284, 386], [296, 394], [297, 408], [281, 418], [256, 419], [236, 411], [229, 398]]), kr(pv), kr(pn), kr([pv[5], [82, 367], pn[5]]));
  [[0.14, 0.19], [0.24, 0.29], [0.38, 0.52], [0.60, 0.65], [0.70, 0.75], [0.84, 0.95]].forEach(function (b) {
    var a1 = vzd(pv, b[0]), a2 = vzd(pv, b[1]), b2 = vzd(pn, b[1]), b1 = vzd(pn, b[0]);
    palantyn.bura.push('M' + t(a1) + 'L' + t(a2) + 'L' + t(b2) + 'L' + t(b1) + 'Z');
    if (b[1] - b[0] > 0.1) palantyn.linii.push('M' + t(a1) + 'L' + t(b1), 'M' + t(a2) + 'L' + t(b2)); /* вузькі смуги — лише поливою */
  });
  palantyn.bura.push(lam([[246, 387], [254, 389], [252, 418], [243, 415]]), lam([[270, 389], [279, 387], [279, 418], [269, 419]]));
  (function () { for (var i = 0; i < 6; i++) { var f0 = [82 + i * 0.7, 351 + i * 6.6]; palantyn.linii.push(kr([f0, [f0[0] - 10, f0[1] + 1 + (i % 2)], [f0[0] - 19, f0[1] + 4 + (i % 3)]])); } })();

  /* сережка */
  (function () {
    var s = hol([[256, 349]])[0], kr_ = [[s[0], s[1] + 7], [s[0] + 7, s[1] + 17], [s[0], s[1] + 26], [s[0] - 7, s[1] + 17]];
    serezhky.linii.push(kr([s, [s[0], s[1] + 7]]), zamk(kr_));
    serezhky.zhov.push(zamk(zsuv(kr_, 1, 2)));
  })();

  /* ───── внутрішні листки при осі (лівий бік) ───── */
  var vnutr = chastyna();
  function nyzhche(p) { return p.map(function (q) { return [484 + (q[0] - 484) * 0.62, 468 + (q[1] - 468) * 0.62 + 236]; }); } /* листки кахлі — менші й під руками */
  var zl_n = nyzhche([[480, 468], [452, 446], [430, 424], [404, 412], [396, 392], [368, 378], [362, 356], [340, 340], [334, 322]]), zl_v = nyzhche([[356, 318], [372, 330], [388, 350], [408, 372], [432, 398], [458, 430]]);
  vnutr.linii.push(kr(zl_n) + kr([zl_n[8]].concat(zl_v, [zl_n[0]]), false) + 'Z');
  vnutr.zel.push(kr(zsuv(zl_n, 0, 4)) + kr(zsuv([zl_n[8]].concat(zl_v, [zl_n[0]]), 0, 4), false) + 'Z', krapla(432, 672, 6, 13));
  vnutr.plamy.push(kr(nyzhche([[484, 452], [462, 424], [448, 396], [428, 372], [420, 346], [402, 318]])) + kr(nyzhche([[402, 318], [424, 330], [440, 352], [452, 376], [470, 404], [486, 434]]), false) + 'Z');

  /* ───── вісь: держак, листок між носами, насінина, вазон ───── */
  var vis = chastyna();
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
     o.je — які боки малювати {l, p, v}; o.bez — без яких частин боку {zhinka, vnutr};
     o.kv — квітки {v, l, p}: null — нема; {pol: 0|1, sklo: 1 — порожнє скло люстерка, barvy: [...] — знак образу};
     o.portret — адреса фото в склі верхньої квітки; o.anim — номери штрихам (--i) для руху «малює»;
     o.filtry === false — без тремтіння лінії й плям поливи (дрібні розміри) */
  var LIV = [138, 168, 78], VERH = [A, 200, 117];
  var VBRANNJA = [[zhinka, 'zhinka'], [suknia, 'suknia'], [palto, 'palto'], [shkira, 'shkira'], [palantyn, 'palantyn'], [serezhky, 'serezhky']];
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
      return { imja: imja, zhov: pol ? ch.zhov.join('') : '', zel: pol ? ch.zel.join('') : '', bura: pol ? ch.bura.join('') : '', plamy: ch.plamy.join(''), linii: ch.linii.map(function (d) { return sh(d); }).join(''), tovsti: ch.tovsti.map(function (d) { return sh(d); }).join('') };
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
      if (!bez.zhinka) VBRANNJA.forEach(function (c) { a.push(shary(c[0], pol, c[1])); });
      if (!bez.vnutr) a.push(shary(vnutr, pol, 'vnutr'));
      if (q) a.push(q);
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
    return '<svg class="kah' + (o.klas ? ' ' + o.klas : '') + '" xmlns="http://www.w3.org/2000/svg" viewBox="' + vb.join(' ') + '" role="img" aria-label="' + (o.pidpys || 'Жінка перед люстерком і її відбиття — малюнок рукою косівської кахлі') + '">' +
      '<defs>' + (F ? filtry(id) : '') + '</defs>' + foto +
      shar('zhov', 'class="shar zhov" style="mix-blend-mode:multiply"' + (F ? ' filter="url(#fp' + id + ')"' : ''), pth(B.zhov)) +
      shar('zel', 'class="shar zel" style="mix-blend-mode:multiply"' + (F ? ' filter="url(#fp' + id + ')"' : ''), pth(B.zel)) +
      shar('svoi', 'class="shar svoi"') +
      '<g' + (F ? ' filter="url(#fl' + id + ')"' : '') + '>' +
      shar('plamy', 'class="shar plamy" fill="' + B.bura + '"', function (d, imja) { return d ? '<path class="pl ch-' + imja + '" d="' + d + '"/>' : ''; }) +
      shar('bura', 'class="shar bura" fill="' + B.bura + '"', function (d, imja) { return d ? '<path class="pol ch-' + imja + '" d="' + d + '" fill-rule="evenodd"/>' : ''; }) +
      shar('linii', 'class="shar linii" fill="none" stroke="' + B.bura + '" stroke-width="' + (o.tov || 4.4) + '" stroke-linecap="round" stroke-linejoin="round"') +
      shar('tovsti', 'class="shar tovsti" fill="none" stroke="' + B.bura + '" stroke-width="' + (o.tovst || 11) + '" stroke-linecap="round" stroke-linejoin="round"') +
      '</g></svg>';
  }

  /* ───── знак: квітка окремо ─────
     o.px — розмір на екрані (лінія не тонша за 1,4 px); o.barvy — кольори пелюсток (речі образу; null — пелюстка лише лінією);
     o.vinets — колір вінця (полива чи нема); o.sklo — люстерко: порожнє скло; o.portret — фото в склі;
     o.rysky === false — без рисок вінця (дрібний знак); o.patoky — патьоки поливи під вінцем;
     o.misce — лишити місце під патьоки й без них (знаки в одному ряду — однієї висоти) */
  function znak(o) {
    o = o || {}; var px = o.px || 64, R = 100, B = BARVY, np = o.sklo ? 6 : (o.barvy ? o.barvy.length : 6);
    var k = kvitka(0, 0, R, { zerno: o.zerno || 3, n: np }), tov = Math.max(4.4, 1.4 * 216 / px), s = '', id = o.id || 'z';
    var rysky = o.rysky === undefined ? px >= 56 : o.rysky, vys = o.patoky || o.misce ? 252 : 216;
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

  /* ───── пелюстка окремо: знак однієї барви чи однієї речі — та сама форма, що в квітці ─────
     px — розмір на екрані; barva — колір (нема — лише лінія); kut — куди дивиться широкий кінець */
  function pelustka(px, barva, kut) {
    var a = kut == null ? -1.12 : kut, w = 0.4, s = 50;
    function pt(r, b) { return [100 * r * Math.cos(b), 100 * r * Math.sin(b)]; }
    var d = zamk([pt(0.13, a), pt(0.34, a - w), pt(0.52, a - w * 0.68), pt(0.565, a), pt(0.52, a + w * 0.68), pt(0.34, a + w)]), c = pt(0.35, a);
    return '<svg class="pel1" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" width="' + px + '" height="' + px + '" viewBox="' + r1(c[0] - s / 2) + ' ' + r1(c[1] - s / 2) + ' ' + s + ' ' + s + '"><path d="' + d + '" fill="' + (barva || 'none') + '" stroke="' + BARVY.bura + '" stroke-width="' + r1(1.5 * s / px) + '" stroke-linejoin="round"/></svg>';
  }

  /* ───── полива під складником інтерфейсу ─────
     пляма w × h px: виходить за контур і стікає патьоком; фільтр #fpS — один на сторінку (spilni) */
  function plama(w, h, barva, zerno) {
    var g = rnd(zerno || 1), p = [], i, n, vy = 3, bo = 4;
    n = Math.max(3, Math.round(w / 46)); for (i = 0; i <= n; i++) p.push([-bo + (w + 2 * bo) * i / n + (g() - .5) * 4, -vy + (g() - .5) * 4]);
    n = Math.max(2, Math.round(h / 40)); for (i = 1; i <= n; i++) p.push([w + bo + (g() - .5) * 4, -vy + (h + 2 * vy) * i / n + (g() - .5) * 3]);
    n = Math.max(3, Math.round(w / 46)); for (i = 1; i <= n; i++) p.push([w + bo - (w + 2 * bo) * i / n + (g() - .5) * 4, h + vy + (g() - .5) * 4]);
    n = Math.max(2, Math.round(h / 40)); for (i = 1; i < n; i++) p.push([-bo + (g() - .5) * 4, h + vy - (h + 2 * vy) * i / n + (g() - .5) * 3]);
    var kx = w * (0.16 + g() * 0.5), d = zamk(p) + krapla(kx, h + vy - 3, 6 + g() * 2.5, 8 + g() * 5) + (w > 150 ? krapla(kx + 20 + g() * 30, h + vy - 3, 4.5 + g() * 2, 5 + g() * 4) : '');
    return '<svg class="plama" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" width="' + (w + 40) + '" height="' + (h + 50) + '" viewBox="-20 -20 ' + (w + 40) + ' ' + (h + 50) + '"><path d="' + d + '" fill="' + (BARVY[barva] || barva) + '" filter="url(#fpS)"/></svg>';
  }
  function spilni() {
    return '<svg width="0" height="0" style="position:absolute" aria-hidden="true"><defs><filter id="fpS" x="-10%" y="-10%" width="120%" height="130%"><feTurbulence type="fractalNoise" baseFrequency="0.04" numOctaves="2" seed="8" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="4" xChannelSelector="R" yChannelSelector="G" result="d"/><feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="2" seed="21" result="t"/><feColorMatrix in="t" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  1.1 0 0 0 -0.46" result="w"/><feComposite in="d" in2="w" operator="out"/></filter></defs></svg>';
  }

  root.КАХЛЯ = { A: A, W: 960, H: 1087, BARVY: BARVY, zhinka: zhinka, suknia: suknia, palto: palto, shkira: shkira, palantyn: palantyn, serezhky: serezhky, vnutr: vnutr, vis: vis, kvitka: kvitka, malyunok: malyunok, znak: znak, pelustka: pelustka, plama: plama, spilni: spilni, kr: kr, zamk: zamk, krapla: krapla, rnd: rnd };
})(typeof window !== 'undefined' ? window : globalThis);
