/* Малює аркуш системи прикладу з window.СИСТЕМА (дані — у сторінці прикладу) і спільної карти функцій.
   Контраст рахує тут же, з тих самих кольорів, що стоять у прототипі (WCAG 2.x). */
(function () {
  var S = window.СИСТЕМА, f = S.fajl;
  function L(h) { var c = [1, 3, 5].map(function (i) { var v = parseInt(h.substr(i, 2), 16) / 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); }); return .2126 * c[0] + .7152 * c[1] + .0722 * c[2]; }
  function K(a, b) { var x = L(a), y = L(b); return ((Math.max(x, y) + .05) / (Math.min(x, y) + .05)).toFixed(1); }
  function sc(n, t) { return '<a href="' + f + '#' + n + '">' + (t || 'сцена ' + n) + '</a>'; }
  function tabl(h, r) { return '<table><thead><tr>' + h.map(function (x) { return '<th>' + x + '</th>'; }).join('') + '</tr></thead><tbody>' + r.map(function (x) { return '<tr>' + x.map(function (y) { return '<td>' + y + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table>'; }
  function ul(a) { return '<ul>' + a.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ul>'; }
  var h = '<header class="sh"><span>Люстерко · ' + (S.shapka || 'приклад ' + S.n + ' з трьох') + ' · аркуш системи</span><span><a href="' + f + '">прототип</a> · <a href="../інтерфейси_дизайнера.html">' + (S.ohljad || 'огляд трьох') + '</a></span></header>' +
    '<h1>' + S.nazva + '</h1><p class="ideja">' + S.ideja + '</p><p class="poz">' + S.pozycija + '</p>' +
    '<h2>Правила, що випливають з ідеї</h2><ol class="prav">' + S.pravyla.map(function (x) { return '<li>' + x + '</li>'; }).join('') + '</ol>' +
    '<h2>Головні екрани</h2><p class="poz">Живі сцени прототипу в розмірі телефона 390 × 844, зменшені на чверть; фото речей вантажаться з крамниць за адресою.</p><div class="ekr">' + S.ekrany.map(function (e) { return '<figure><div class="ram"><iframe title="' + e[1] + '" src="' + f + '?чисто#' + e[0] + '"></iframe></div><figcaption>' + sc(e[0], e[1]) + '</figcaption></figure>'; }).join('') + '</div>' +
    '<h2>Сценарій і стани</h2>' + tabl(['Крок чи стан', 'Що на екрані', 'Де'], S.stany.map(function (x) { return [x[0], x[1], sc(x[2])]; })) +
    '<h2>Аркуш системи</h2><h3>Сітка й пропорції</h3>' + ul(S.sitka) +
    '<h3>Шрифти</h3><div class="shr">' + S.shryfty.map(function (x) { return '<div><div class="zr" style="' + x.styl + '">' + x.zrazok + '</div><small><b>' + x.nazva + '</b> — ' + x.pro + '<br>Ліцензія: ' + x.lic + '</small></div>'; }).join('') + '</div>' +
    '<h3>Кольори: роль і контраст</h3><div class="kol">' + S.kolory.map(function (c) { return '<div><i style="background:' + c[1] + ';color:' + c[3] + '">' + c[0] + '</i><span><code>' + c[1] + '</code> — ' + c[2] + '<br>з <code>' + c[3] + '</code>: контраст ' + K(c[1], c[3]) + ' : 1' + (c[4] ? ' — ' + c[4] : '') + '</span></div>'; }).join('') + '</div>' +
    '<div class="dv"><div><h3>Складники</h3>' + ul(S.skladnyky) + '</div><div><h3>Фото одягу</h3>' + ul(S.foto) + '<h3>Рух</h3>' + ul(S.rukh) + '<h3>Знаки</h3>' + ul(S.znaky) + '</div></div>' +
    '<h2>Карта функцій</h2><p class="poz">Рядки — таблиця дій із роботи менеджера 15.11 (розділ 2) і те, що буде. «Намальовано» — є сцена; «місце» — показано, де стане, без окремої сцени.</p>' +
    tabl(['Функція', 'Де живе в цьому прикладі', 'Стан у прототипі'], window.КАРТА.map(function (r) { var v = r[S.kljuch]; return [r.f + '<br><small>' + r.stan + '</small>', v[0], v[1] ? sc(v[1], 'намальовано · сцена ' + v[1]) : 'місце, сцени нема']; })) +
    '<h2>Родовід</h2>' + tabl(['Рішення', 'Взірець або сучасна робота', 'Прийом перенесення', 'Що вийшло'], S.rodovid) +
    '<h3>Чого свідомо не взято</h3>' + ul(S.nevzjato) +
    '<h2>' + (S.kil_kil || 'Три кола') + ': знімок → критика → правка</h2>' + tabl(['Коло', 'Що побачила на знімках', 'Що змінила'], S.kola) +
    '<h2>Власна критика</h2>' + ul(S.krytyka);
  document.querySelector('main').innerHTML = h;
})();
