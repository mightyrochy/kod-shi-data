/* «Мальоване люстерко»: сцени прототипу. Вміст — вміст.js (та сама Оксана, ті самі речі каталогу),
   малюнок — кахля.js, написи — написи.js, рушій сцен — рух.js. На людях нічого не перевірено. */
(function () {
  var V = window.ВМІСТ, K = window.КАХЛЯ, R = V.rechi, N = window.НАПИС, B = K.BARVY, taj = [];
  var ad = decodeURIComponent(location.search), krokZ = (/крок=(\d)/.exec(ad) || [])[1];
  var TYHO = !!(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  var POVNYJ = { l: 0, p: 1, v: 1, kv: { v: { pol: 1, sklo: 1 }, l: { pol: 0 }, p: { pol: 1 } } };
  function mal(o) { var r = {}, k; for (k in POVNYJ) r[k] = POVNYJ[k]; for (k in o) r[k] = o[k]; return K.malyunok(r); }
  function barvy(a) { return a.map(function (k) { return R[k].barva; }); }
  function znakO(a, px, o) { o = o || {}; o.px = px; o.barvy = barvy(a); return K.znak(o); }
  function foto(k, dod) { var r = R[k]; return window.ФОТО(k, 'data-or="' + (r.w / r.h <= 0.8 ? 'st' : 'le') + '"' + (r.pohane ? ' data-prym="' + r.pohane + '"' : '') + (dod || '')); }
  function hrn(n) { return V.hrn(n); }
  function suma(a) { return a.reduce(function (s, k) { return s + R[k].cina; }, 0); }
  function rechej(n) { return n + (n === 1 ? ' річ' : n < 5 ? ' речі' : ' речей'); }
  /* ім’я великим написом: у ширину sh px, велика літера не вища за h; довге — у два рядки */
  function imja(nazva, sh, h) {
    var s = nazva.toUpperCase(), n = window.НАПИСИ, ch = s.split(' '), a = [s];
    if (n[s] && (n[s][0] + 20) * h / 700 > sh && ch.length > 1) { a = ch.length === 3 ? (n[ch[0] + ' ' + ch[1]] ? [ch[0] + ' ' + ch[1], ch[2]] : [ch[0], ch[1] + ' ' + ch[2]]) : ch; }
    var sz = a.reduce(function (m, x) { return n[x] ? Math.min(m, Math.floor(sh * 700 / (n[x][0] + 20))) : m; }, h);
    return '<span class="imja" role="heading" aria-level="2" aria-label="' + nazva + '" style="row-gap:' + Math.round(sz * 0.38) + 'px">' + a.map(function (x) { return N(x, sz, 'im'); }).join('') + '</span>';
  }

  /* ───── каркас: шапка, два боки, перемикач ───── */
  function verh() {
    return '<header class="verh"><a class="lz" data-scena-do="pochatok" aria-label="Люстерко: на початок">' + N('ЛЮСТЕРКО', 15) + '</a>' +
      '<a class="ja" data-scena-do="znajomstvo" aria-label="Оксана: фото й обхвати">' + K.znak({ px: 44, sklo: 1, vinets: B.zhov, portret: V.vona.portret, rysky: false, id: 'v' }) + '</a></header>';
  }
  function hid(tut, nove) {
    return '<nav class="hid" aria-label="Розділи">' + [['rozmova', 'Розмова'], ['obraz', 'Образ'], ['moji', 'Мої образи']].map(function (x) {
      return '<a data-scena-do="' + x[0] + '"' + (x[0] === tut ? ' aria-current="page"' : '') + (nove && x[0] === 'moji' ? ' class="nove"' : '') + '>' + x[1] + '</a>';
    }).join('') + '</nav>';
  }
  function arkush(bik, zv, ly, tut, nove) {
    taj.forEach(clearTimeout); taj = [];
    var obert = window._bik && window._bik !== bik; window._bik = bik;
    return '<div class="ark' + (obert ? ' obert' : '') + '" data-bik="' + bik + '">' + verh() +
      '<main class="dva"><section class="bik zvorot" aria-label="Зворот: розмова й пам’ять">' + zv + '</section><section class="bik lyce" aria-label="Лице: ти й одяг">' + ly + '</section></main>' + hid(tut, nove) + '</div>';
  }
  function polyty(korin) { /* полива під вибраним: пляма в розмірі складника */
    [].forEach.call(korin.querySelectorAll('[data-pol]'), function (el, i) {
      var w = el.offsetWidth, h = el.offsetHeight; if (w) el.insertAdjacentHTML('afterbegin', K.plama(w, h, el.getAttribute('data-pol'), i + 2));
    });
  }
  if (!document.getElementById('fpS')) document.body.insertAdjacentHTML('afterbegin', K.spilni());
  function dija(h, kl) { return '<div class="dija' + (kl ? ' ' + kl : '') + '">' + h + '</div>'; }

  /* ───── голоси ───── */
  function vona(t, dod) { return '<p class="hv">' + t + (dod ? '<span class="dr">' + dod + '</span>' : '') + '</p>'; }
  function lust(t, dod) { return '<div class="hl">' + K.znak({ px: 30, sklo: 1, vinets: B.zhov, rysky: false }) + '<p>' + t + '</p>' + (dod || '') + '</div>'; }

  /* ───── зворот: що я зрозуміла, барви ───── */
  function rjadky(kor) {
    return '<ul class="zr' + (kor ? ' kor' : '') + '">' + V.zrozumila.map(function (z) {
      var dii = z.k === 'Гроші' ? '<button type="button">назвати межу</button>' : '<button type="button" data-pry>прибрати</button><button type="button">змінити</button>';
      return '<li class="' + (z.ska ? 'ska' : 'pry') + (z.holovne ? ' hol' : '') + '">' + (kor ? '' : '<span class="k">' + z.k + '</span>') + '<span class="v">' + z.v + '</span>' +
        (kor ? '' : z.ska ? '<span class="dz">ти сказала: <i>«' + z.ska + '»</i></span>' : '<span class="dz">' + z.chomu + '</span><span class="dii">' + dii + '</span>') + '</li>';
    }).join('') + '</ul>';
  }
  var P = V.barvy.plamy, SYN = '#1F2A44';
  function kvitkaBarv(px) {
    return K.znak({ px: px, barvy: [P[0][1], P[1][1], P[0][1], P[2][1], P[0][1], P[1][1]], vinets: P[3][1], sered: P[4][1], id: 'b' + px,
      pidpys: 'Квітка барв: три пелюстки бордо, дві кемел, одна шоколад, вінець айворі, серединка — хвоя' });
  }
  function lehenda() {
    var sl = ['три пелюстки', 'дві', 'одна', 'вінець', 'серединка'];
    function zn(c, i) { /* пелюстка, вінець чи серединка — тим самим знаком, що у квітці */
      return i < 3 ? K.pelustka(20, c) : '<svg class="pel1" aria-hidden="true" width="20" height="20" viewBox="-10 -10 20 20" stroke="' + B.bura + '" stroke-width="1.5"><circle r="' + (i === 3 ? 8 : 4.2) + '" fill="' + c + '"/>' + (i === 3 ? '<circle r="3.6" fill="' + B.tlo + '"/>' : '') + '</svg>';
    }
    return '<ul>' + P.map(function (p, i) { return '<li>' + zn(p[1], i) + '<b>' + p[0] + '</b><span>' + p[3] + ' · ' + sl[i] + '</span></li>'; }).join('') + '</ul>';
  }
  /* зворот поруч із лицем на широкому екрані: що сказано й барви лишаються на очах */
  function zvPidsumok() {
    return '<div class="lsh"><h2>Що я зрозуміла</h2>' + rjadky(1) + '<h3>Барви</h3><div class="barv ryad">' + kvitkaBarv(112) + lehenda() + '</div><a class="tyh" data-scena-do="rozmova">до розмови</a></div>';
  }
  /* лице поруч зі зворотом на широкому екрані: шість місць під речі */
  function lyceMisce(zFoto) {
    return '<div class="lsh"><p class="dr" style="margin:0 0 14px">Лице. Тут буде образ — шість місць під речі.</p><div class="sitka">' + V.obraz.rechi.map(function (k) {
      return '<div class="rich pusta" data-k="' + k + '">' + (zFoto ? foto(k) : '<span class="foto"></span>') + '<span class="slot">' + R[k].slot + '</span></div>';
    }).join('') + '</div></div>';
  }

  /* ───── лице: образ ───── */
  function richPl(k, o) {
    o = o || {}; var r = R[k], sv = o.svoje === k, nov = o.nove === k;
    return '<a class="rich' + (nov ? ' nova' : '') + '"' + (o.kudy ? ' data-scena-do="' + o.kudy(k) + '"' : '') + '>' +
      (sv ? '<span class="foto svoja">' + K.pelustka(52, r.barva) + 'твоє, з шафи</span>' : foto(k)) +
      '<span class="slot">' + K.pelustka(16, r.barva) + r.slot + (nov ? ' · нове' : '') + '</span><b>' + (sv ? 'Твоє пальто, кемел' : o.povni && r.povna ? r.povna : r.nazva) + '</b>' +
      '<span class="kc">' + (sv ? 'не купуємо' : '<i>' + hrn(r.cina) + '</i> · ' + r.kram) + '</span></a>';
  }
  function derevo(n) {
    var a = [[V.obraz.rechi, 'тихо', 'obraz'], [V.druhyj.rechi, 'сміливіше', 'druhyj']];
    return '<nav class="derevo" aria-label="Образи до цієї нагоди"><span class="slot">образи до цієї нагоди</span><div>' + a.map(function (x, i) {
      return '<a data-scena-do="' + x[2] + '"' + (i + 1 === n ? ' aria-current="true"' : '') + '>' + znakO(x[0], 28, { rysky: false }) + x[1] + '</a>';
    }).join('') + '<a class="shche">' + K.znak({ px: 28, barvy: [null, null, null, null, null, null], rysky: false, sered: 'none' }) + 'ще один</a></div></nav>';
  }
  function obraz(o) {
    var kup = o.rechi.filter(function (k) { return k !== o.svoje; }), kram = {}; kup.forEach(function (k) { kram[R[k].kram] = 1; });
    return '<header class="obv">' + znakO(o.rechi, 68, { pidpys: 'Знак образу: пелюстки барвами його речей', id: 'o' }) + '<div>' + imja(o.nazva, 246, 30) + '<p class="pro">' + o.pro + '</p></div></header>' +
      (o.zber || '') +
      '<p class="slova' + (o.dovhi ? ' dovhi' : '') + '">' + (o.dovhi || o.slova) + '</p>' + (o.dovhi ? '<button type="button" class="tyh" data-vse>читати далі</button>' : '') +
      '<div class="sitka">' + o.rechi.map(function (k) { return richPl(k, o); }).join('') + '</div>' +
      '<p class="razom"><span>Разом · ' + rechej(kup.length) + ' з ' + Object.keys(kram).length + ' крамниць</span><b>' + (o.bulo ? '<s>' + hrn(o.bulo) + '</s>' : '') + hrn(suma(kup)) + '</b></p>' + derevo(o.n) + (o.nyz || '');
  }
  var NAH = V.nahoda.povna + '<br>' + V.nahoda.koly, PERSHI = suma(V.obraz.rechi), PISLJA = ['sukn', 'palt', 'lofe', 'sumk', 'pala', 'sere'];
  function kudy(k) { return k === 'cher' ? 'zamina' : 'rich'; }

  /* ───── піч ───── */
  function znakK(m, i, pol, lyje) { return znakO(m.rechi, 92, { vinets: pol ? B.zhov : null, patoky: !!pol, misce: 1, zerno: 3 + i, id: 'k' + i, klas: lyje ? 'lyje' : '' }); }
  function kahlja(m, i) {
    return '<div class="kl" data-i="' + i + '"><a data-scena-do="' + (i ? 'druhyj' : 'pislja') + '" aria-label="' + m.nazva + ': відкрити образ">' + znakK(m, i, m.vdjahla) +
      imja(m.nazva, 142, 15) + '<span class="pd">' + m.pro + ' · ' + m.data + '</span></a>' +
      '<button type="button" class="st" aria-pressed="' + !!m.vdjahla + '">' + (m.vdjahla ? 'вдягла' : 'ще не вдягала') + '</button></div>';
  }

  window.СЦЕНИ = [
    { id: 'pochatok', nazva: 'Початок: зворот люстерка', html: function () {
      taj.forEach(clearTimeout); taj = []; window._bik = 'zvorot';
      return '<div class="poch"><div class="mal">' + mal({ id: 'p', anim: 1, klas: 'chek' }) + '</div>' +
        '<div class="sl">' + N('ЛЮСТЕРКО', 37) + '<p class="zakl">Скажи, куди збираєшся. Зберу образ із речей українських крамниць — і скажу чесно, чи до лиця.</p>' +
        '<div class="nyz"><button type="button" class="kn" data-dali>Почнімо</button><a class="tyh" data-scena-do="porozhnio">Вже була тут — мої образи</a>' +
        '<p class="pid">Малюнок — за кахлею Петра Кошака. Пістинь, 1911</p></div></div></div>';
    }, pislja: function (k) { /* люстерко відповідає: праворуч з’являється відбиття — лінією, потім поливою */
      var svg = k.querySelector('.chek');
      if (krokZ || TYHO) { svg.setAttribute('class', svg.getAttribute('class') + ' bezruhu k1 k2 k3 k4 k5 vypal'); return; }
      [[450, ['k1']], [2000, ['k2', 'k3', 'k4', 'k5']], [3100, ['vypal']]].forEach(function (x) {
        taj.push(setTimeout(function () { x[1].forEach(function (c) { svg.classList.add(c); }); }, x[0]));
      });
    } },

    { id: 'znajomstvo', nazva: 'Знайомство: її лице в люстерку', html: function () {
      var v = V.vona;
      return arkush('lyce',
        '<div class="lsh"><div class="mal-zl">' + K.malyunok({ je: { l: 1 }, l: 0, kv: { l: null }, bez: { vnutr: 1 }, vb: [40, 450, 450, 590], id: 'zl', pidpys: 'Олень, обведений лінією' }) + '</div>' +
        '<h2>Спершу — ти, як є</h2><p class="slova">Портрет і фото на повен зріст — раз і назавжди. З них я бачу барви шкіри, очей і волосся та силует; далі питатиму лише про нагоду.</p></div>',
        '<div class="lust-m">' + K.malyunok({ je: { v: 1 }, v: 1, kv: { v: { pol: 1, sklo: 1 } }, portret: v.portret, vb: [340, 66, 300, 322], id: 'zn', pidpys: 'Портрет Оксани в склі люстерка' }) + '</div>' +
        '<h2>' + v.imja + ', бачу тебе</h2>' +
        '<ul class="oz">' + v.barvy.map(function (b) { return '<li>' + K.pelustka(20, b[1]) + b[0] + '</li>'; }).join('') + '</ul>' +
        '<p class="opys">' + v.opys + ' — тобі до лиця тепла гама.</p>' +
        '<div class="dvafoto"><figure><img src="' + v.portret + '" alt="Портрет Оксани"><figcaption>портрет <button type="button">змінити</button></figcaption></figure>' +
        '<figure><img src="' + v.zrist + '" alt="Оксана на повен зріст"><figcaption>на повен зріст <button type="button">змінити</button></figcaption></figure></div>' +
        '<p class="obkh"><span class="dr">обхвати, зріст</span>' + v.obkhvaty.replace(', зріст', ' ·') + '<button type="button">виправити</button></p>' +
        dija('<button type="button" class="kn" data-dali>Так, це я</button>'));
    } },

    { id: 'rozmova', nazva: 'Розмова про нагоду', html: function () {
      var r = V.rozmova;
      return arkush('zvorot',
        lust(r[0].t) +
        '<div class="plyt">' + V.plytky.map(function (p) { return '<button type="button" aria-pressed="' + (p === 'свято') + '"' + (p === 'свято' ? ' data-pol="zhov"' : '') + '>' + p + '</button>'; }).join('') + '</div>' +
        vona(r[1].t, 'з голосу · торкнись, щоб виправити') + lust(r[2].t) + vona(r[3].t, 'з голосу · торкнись, щоб виправити') +
        lust(r[4].t, '<button type="button" class="kn" data-dali>Глянути, що я зрозуміла</button>') +
        '<div class="dija pole"><button type="button" class="kn lin"><i></i>Сказати</button><button type="button" class="kn lin">Написати</button></div>',
        lyceMisce(), 'rozmova');
    }, pislja: function (k) {
      polyty(k);
      [].forEach.call(k.querySelectorAll('.plyt button'), function (b) {
        b.onclick = function () {
          var bulo = b.getAttribute('aria-pressed') === 'true', pl = b.querySelector('.plama');
          b.setAttribute('aria-pressed', !bulo); if (pl) pl.remove();
          if (bulo) b.removeAttribute('data-pol'); else { b.setAttribute('data-pol', 'zhov'); b.insertAdjacentHTML('afterbegin', K.plama(b.offsetWidth, b.offsetHeight, 'zhov', 5)); }
        };
      });
    } },

    { id: 'zrozumila', nazva: 'Що я зрозуміла', html: function () {
      return arkush('zvorot',
        '<header class="zr-v"><span class="slot">що я зрозуміла</span>' + imja(V.nahoda.nazva, 300, 30) + '<p class="pro">' + NAH + '</p></header>' +
        '<p class="leg"><span><i class="m"></i>ти сказала</span><span><i class="m pry"></i>я припустила</span></p>' + rjadky() +
        dija('<button type="button" class="kn" data-dali>Усе так — до барв</button>'), lyceMisce(), 'rozmova');
    }, pislja: function (k) {
      [].forEach.call(k.querySelectorAll('[data-pry]'), function (b) {
        b.onclick = function () { var li = b.closest('li'), n = li.classList.toggle('nema'); b.textContent = n ? 'повернути' : 'прибрати'; };
      });
    } },

    { id: 'barvy', nazva: 'Барви: квітка', html: function () {
      var bv = V.barvy, kol = { 'бордо': P[0][1], 'хвоя': P[4][1], 'темно-синій': SYN, 'шоколад': P[2][1], 'графіт': '#3A3A3C' };
      var kv = [[P[0][1], P[1][1], P[0][1], P[2][1], P[0][1], P[1][1]], [P[0][1], P[4][1], P[0][1], P[4][1], P[0][1], P[4][1]], [P[0][1], P[4][1], SYN, P[0][1], P[4][1], SYN], [null, null, null, null, null, null]];
      return arkush('zvorot',
        '<h2>Барви</h2><div class="barv">' + kvitkaBarv(196) + lehenda() + '</div>' + lust(bv.chomu) +
        '<h3>Основа</h3><div class="osn">' + bv.osnovy.map(function (o, i) { return '<button type="button" aria-pressed="' + (i === 0) + '">' + K.pelustka(20, kol[o]) + o + '</button>'; }).join('') + '</div>' +
        '<h3>Як їх поєднати</h3><div class="skh">' + bv.skhemy.map(function (s, i) {
          return '<button type="button" aria-pressed="' + (i === 0) + '">' + K.znak({ px: 44, barvy: kv[i], rysky: false, sered: i === 3 ? 'none' : B.bura }) + '<span>' + (i === 3 ? 'хай обере люстерко' : s[0]) + (s[1] ? '<small>' + s[1] + '</small>' : '') + '</span></button>';
        }).join('') + '</div>' + dija('<button type="button" class="kn" data-dali>Збирай</button>'), lyceMisce(), 'rozmova');
    }, pislja: function (k) {
      ['.osn', '.skh'].forEach(function (g) {
        [].forEach.call(k.querySelectorAll(g + ' button'), function (b) { b.onclick = function () { [].forEach.call(k.querySelectorAll(g + ' button'), function (x) { x.setAttribute('aria-pressed', x === b); }); }; });
      });
    } },

    { id: 'chekannja', nazva: 'Чекання: люстерко малює', html: function () {
      return arkush('zvorot',
        '<div class="chek-m">' + mal({ anim: 1, id: 'c', klas: 'chek', pidpys: 'Люстерко малює: правий олень з’являється лінією, потім поливою' }) + '</div>' +
        '<p class="krok-n dr" aria-hidden="true"></p><p class="krok-t" aria-live="polite"></p><p class="krok-f dr"></p>' +
        '<div class="znajd">' + V.obraz.rechi.map(function (k) { return '<span class="m6" data-k="' + k + '">' + foto(k) + '</span>'; }).join('') + '</div>' +
        '<button type="button" class="kn hotovo" data-dali hidden>Обернути на лице</button>' +
        '<div class="chekaty"><p class="dr">Збирання триває дві–п’ять хвилин (тут пришвидшено). Можна згорнути — покличу, коли домалюю.</p>' +
        '<button type="button" class="kn lin mala" aria-pressed="true" data-pol="zhov">Покликати мене</button></div>',
        lyceMisce(1), 'rozmova');
    }, pislja: function (k) {
      var c = V.chekannja, svg = k.querySelector('.chek'), i = 0, hto = [['sukn', 'palt'], ['cher', 'sumk'], ['pala', 'sere']];
      polyty(k);
      function stan(n) { /* 1–5 — кроки збирання, 6 — випал */
        var j, kr = c.kroky[Math.max(1, Math.min(n, 5)) - 1], h = '';
        for (j = 1; j <= Math.min(n, 5); j++) svg.classList.add('k' + j);
        if (n >= 6) svg.classList.add('vypal');
        for (j = 1; j <= 5; j++) h += '<i' + (j <= n ? ' class="je"' : '') + '></i>';
        k.querySelector('.krok-n').innerHTML = h + '<span>' + (n >= 6 ? 'готово' : 'крок ' + Math.max(1, n) + ' з 5') + '</span>';
        k.querySelector('.krok-t').textContent = n >= 6 ? 'Домалювала й випалила. Образ — на лиці.' : kr[0];
        k.querySelector('.krok-f').textContent = n >= 6 ? 'шість речей із шести крамниць' : kr[1];
        hto.slice(0, Math.max(0, Math.min(n, 4) - 1)).forEach(function (a) { a.forEach(function (x) { [].forEach.call(k.querySelectorAll('[data-k="' + x + '"]'), function (e) { e.classList.add('je'); }); }); });
        k.querySelector('.hotovo').hidden = n < 6; k.querySelector('.chekaty').hidden = n >= 6;
      }
      if (krokZ) { svg.classList.add('bezruhu'); stan(+krokZ); return; }
      (function dali() { i++; stan(i); if (i < 6) taj.push(setTimeout(dali, i === 1 ? 2700 : 2500)); })();
    } },

    { id: 'obraz', nazva: 'Образ: лице', html: function () {
      return arkush('lyce', zvPidsumok(), obraz({ n: 1, nazva: V.nahoda.nazva, pro: NAH, rechi: V.obraz.rechi, slova: V.obraz.slova, kudy: kudy,
        nyz: dija('<button type="button" class="kn" data-scena-do="pislja">Вдягну</button><button type="button" class="kn lin" data-scena-do="zamina">Щось не те</button>', 'dvi') }), 'obraz');
    } },

    { id: 'rich', nazva: 'Річ зблизька', html: function () {
      var r = R.sukn;
      return arkush('lyce', zvPidsumok(),
        '<a class="nazad" data-scena-do="obraz">← до образу</a><div class="zbl">' + foto('sukn') + '</div><span class="slot">' + r.slot + '</span><h2>' + r.nazva + '</h2><p class="kc cina"><i>' + hrn(r.cina) + '</i> · ' + r.kram + '</p>' +
        lust(r.chomu) + '<div class="dii st"><a class="kn" href="' + r.url + '" target="_blank" rel="noopener">У крамницю ' + r.kram + ' →</a>' +
        '<button type="button" class="kn lin" data-scena-do="zamina">Не ця — покажи інші</button><button type="button" class="kn lin">Збери інший образ під цю сукню</button></div>', 'obraz');
    } },

    { id: 'zamina', nazva: 'Сумнів і заміна речі', html: function () {
      var s = V.sumniv, st = R[s.rich];
      return arkush('lyce', zvPidsumok(),
        '<a class="nazad" data-scena-do="obraz">← до образу</a>' + vona(s.slova) + lust('Зрозуміла: дешевше й легше. Ось три пари замість черевиків — і що кожна зробить з образом.') +
        '<ul class="zam">' + s.zaminy.map(function (k, i) {
          var r = R[k], d = r.cina - st.cina;
          return '<li>' + foto(k) + '<div>' + (i === 0 ? '<span class="radzhu">раджу ці</span>' : '') + '<b>' + r.nazva + '</b><span class="rz">' + hrn(r.cina) + ' · ' + r.kram + ' · ' + (d < 0 ? 'на ' + hrn(-d) + ' дешевше' : 'на ' + hrn(d) + ' дорожче') + '</span>' + r.chomu +
            (i === 0 ? '<button type="button" class="kn mala" data-scena-do="pislja">Узяти ці</button>' : '<button type="button" class="kn lin mala" data-scena-do="pislja">Узяти ці</button>') + '</div></li>';
        }).join('') + '</ul>' + vona(s.svoje.slova) + lust(s.svoje.vidpovid), 'obraz');
    } },

    { id: 'pislja', nazva: 'Після заміни: збережено', html: function () {
      return arkush('lyce', zvPidsumok(), obraz({ n: 1, nazva: V.nahoda.nazva, pro: NAH, rechi: PISLJA, slova: V.sumniv.vidpovid, svoje: 'palt', nove: 'lofe', bulo: PERSHI, kudy: kudy,
        zber: '<p class="zber"><i class="m"></i><span>Збережено в «Мої образи». Увечері суботи спитаю, чи вдягла.</span></p>',
        nyz: dija('<button type="button" class="kn" data-scena-do="moji">До моїх образів</button>') }), 'obraz', 1);
    } },

    { id: 'kupyty', nazva: 'Купити чи ні', html: function () {
      var q = V.kupyty, r = R[q.rich], m = V.moji;
      return arkush('lyce', zvPidsumok(),
        vona(q.slova, 'фото з крамниці') +
        '<div class="kup">' + foto(q.rich) + '<div><span class="slot">' + r.kram + ' · ' + hrn(r.cina) + '</span>' + N('НЕ ЗАРАЗ', 26, 'vyrok') + '<p class="dr">Сумка гарна. Не до цієї нагоди.</p></div></div>' +
        '<ul class="prych"><li>' + q.chomu[0] + '</li><li>' + q.chomu[1] + '<span class="zn2">' + znakO(m[0].rechi, 34, { rysky: false }) + znakO(m[1].rechi, 34, { rysky: false }) + '</span></li><li class="ale">' + q.chomu[2] + '</li></ul>' +
        '<h3>Поруч із тією, що вже в образі</h3><div class="para">' + richPl(q.rich) + richPl(q.porivn) + '</div>' +
        '<h3>Схожі, дешевші</h3><div class="troje">' + q.skhozhi.map(function (k) { return richPl(k); }).join('') + '</div>' +
        '<div class="dii st"><button type="button" class="kn">Не беру</button><button type="button" class="kn lin">Усе ж беру — додай до моїх речей</button></div>', 'obraz');
    } },

    { id: 'svij', nazva: 'Оціни мій образ', html: function () {
      var s = V.svij;
      return arkush('lyce', zvPidsumok(),
        vona(s.slova_v, 'фото з дзеркала') +
        '<div class="svij"><img src="' + V.vona.svij + '" alt="Оксана у своєму одязі"><div>' + N('ДОБРЕ', 26, 'vyrok') + '<p class="iodna">і одна порада</p>' +
        '<p class="dr"><i class="m"></i>бачу: ' + s.rozpiznala.join(', ') + '</p><p class="dr"><i class="m pry"></i>не бачу ' + s.nema + ' — про них мовчу</p></div></div>' +
        lust(s.dobre) + lust(s.porada) + '<div class="dii st"><button type="button" class="kn">' + s.dija.charAt(0).toUpperCase() + s.dija.slice(1) + '</button></div>', 'obraz');
    } },

    { id: 'moji', nazva: 'Мої образи: піч', html: function () {
      var m = V.moji, vd = m.filter(function (x) { return x.vdjahla; }).length;
      return arkush('zvorot',
        '<div class="pich-v">' + N('МОЇ ОБРАЗИ', 20) + '<span class="dr lich">' + m.length + ' образи · ' + vd + ' вдягала</span></div>' +
        '<div class="pich">' + m.map(kahlja).join('') + '<a class="kl pusta" data-scena-do="rozmova"><i>+</i>новий образ</a></div>' +
        '<p class="dr">Кахля за кожен образ: пелюстки — барви його речей. Вдягла — торкнись «ще не вдягала», і вінець поллється.</p>',
        '<div class="lsh">' + obraz({ n: 1, nazva: V.nahoda.nazva, pro: NAH, rechi: PISLJA, slova: V.sumniv.vidpovid, svoje: 'palt', kudy: kudy }) + '</div>', 'moji');
    }, pislja: function (k) { /* вдягла — вінець поливається жовтим; не вдягала — лишається лінією */
      var m = V.moji, lich = k.querySelector('.lich');
      [].forEach.call(k.querySelectorAll('.kl[data-i]'), function (kl) {
        var i = +kl.getAttribute('data-i'), b = kl.querySelector('.st');
        b.onclick = function () {
          var tak = b.getAttribute('aria-pressed') !== 'true';
          b.setAttribute('aria-pressed', tak); b.textContent = tak ? 'вдягла' : 'ще не вдягала';
          kl.querySelector('.znak').outerHTML = znakK(m[i], i, tak, tak);
          lich.textContent = m.length + ' образи · ' + k.querySelectorAll('.st[aria-pressed=true]').length + ' вдягала';
        };
      });
    } },

    { id: 'druhyj', nazva: 'Кілька образів: другий', html: function () {
      var d = V.druhyj;
      return arkush('lyce', zvPidsumok(), obraz({ n: 2, nazva: d.nazva, pro: NAH, rechi: d.rechi, slova: d.slova,
        nyz: dija('<button type="button" class="kn">Вдягну цей</button><button type="button" class="kn lin" data-scena-do="obraz">До тихого</button>', 'dvi') }), 'obraz');
    } },

    { id: 'dovhyj', nazva: 'Довгий текст і довгі назви', html: function () {
      return arkush('lyce', zvPidsumok(), obraz({ n: 1, nazva: V.nahoda.nazva, pro: NAH, rechi: V.obraz.rechi, dovhi: V.obraz.dovhi, povni: 1, kudy: kudy }), 'obraz');
    }, pislja: function (k) { var b = k.querySelector('[data-vse]'); b.onclick = function () { var v = k.querySelector('.slova').classList.toggle('vse'); b.textContent = v ? 'згорнути' : 'читати далі'; }; } },

    { id: 'pomylka', nazva: 'Помилка збирання', html: function () {
      var c = V.chekannja.kroky;
      return arkush('zvorot',
        '<div class="chek-m">' + K.malyunok({ l: 0, p: 0, v: 0, anim: 1, id: 'e', klas: 'pom', kv: { v: { pol: 0, sklo: 1 }, l: { pol: 0 }, p: { pol: 0 } }, pidpys: 'Правий олень лишився перерваною лінією' }) + '</div>' +
        '<h2>Не домалювала</h2><p class="slova">' + V.pomylka + '</p>' +
        '<ul class="kroky"><li class="je">' + c[0][0] + '</li><li class="je">' + c[1][0] + '</li><li class="tut">Тут урвалось: дві крамниці не відповіли за хвилину</li></ul>' +
        '<div class="dii st"><button type="button" class="kn" data-scena-do="chekannja">Домалювати ще раз</button><button type="button" class="kn lin" data-scena-do="zrozumila">Змінити щось у розмові</button></div>',
        lyceMisce(), 'rozmova');
    } },

    { id: 'porozhnio', nazva: 'Порожня піч', html: function () {
      return arkush('zvorot',
        '<div class="pich-v">' + N('МОЇ ОБРАЗИ', 20) + '<span class="dr">поки жодного</span></div>' +
        '<div class="pich"><div class="kl mal-k">' + K.malyunok({ je: { l: 1 }, l: 0, kv: { l: null }, bez: { vnutr: 1, lystok: 1 }, vb: [50, 455, 440, 580], id: 'pp', tov: 7, tovst: 14, filtry: false, pidpys: 'Олень лінією' }) + '</div>' +
        '<a class="kl pusta" data-scena-do="znajomstvo"><i>+</i>перший образ</a><div class="kl pusta"></div><div class="kl pusta"></div></div>' +
        '<h2>Піч ще холодна</h2><p class="slova">Кожен образ, який ти збережеш, ляже сюди кахлею — зі знаком із барв його речей і датою.</p>' +
        '<button type="button" class="kn" data-scena-do="znajomstvo">Зібрати перший</button>', lyceMisce(), 'moji');
    } }
  ];
})();
