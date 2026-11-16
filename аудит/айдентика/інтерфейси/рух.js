/* Спільний рушій прототипів: сцени за адресою (#3), перемикач сцен, поводження з фото.
   Прототип задає window.СЦЕНИ = [{ nazva, html: function () { return '…'; }, pislja: function (корінь) {} }].
   ?чисто в адресі ховає перемикач (для знімків). */
(function () {
  var V = window.ВМІСТ, korin, n = 0, pult;
  function nomer() { var m = /#(\d+)/.exec(location.hash); return m ? Math.max(0, Math.min(window.СЦЕНИ.length - 1, +m[1] - 1)) : 0; }
  function pokaz() {
    n = nomer();
    var s = window.СЦЕНИ[n];
    korin.innerHTML = s.html();
    korin.setAttribute('data-scena', s.id || n + 1);
    document.documentElement.setAttribute('data-scena', s.id || n + 1);
    foto(korin);
    if (s.pislja) s.pislja(korin);
    window.scrollTo(0, 0); korin.scrollTop = 0;
    if (pult) pult.querySelector('b').textContent = (n + 1) + ' / ' + window.СЦЕНИ.length + ' · ' + s.nazva;
  }
  /* Фото з крамниці: не більшим, ніж дала крамниця; не завантажилось — чесна плашка зі словами, а не порожня рамка. */
  function foto(el) {
    [].forEach.call(el.querySelectorAll('img[data-rich]'), function (im) {
      var r = V.rechi[im.getAttribute('data-rich')];
      function nema() { var p = im.closest('.foto') || im.parentNode; p.classList.add('nema-foto'); p.setAttribute('data-nema', r.kram + ' · фото нема'); }
      im.addEventListener('error', nema);
      if (im.complete && !im.naturalWidth) nema();
    });
  }
  window.ФОТО = function (k, dod) {
    var r = V.rechi[k], male = r.w < 300;
    return '<span class="foto' + (r.pohane ? ' pohane' : '') + (male ? ' male' : '') + ' tlo-' + (r.tlo === 'біле' || r.tlo === 'сіре' ? 'rivne' : 'zhyve') + '" ' + (dod || '') + '>' +
      '<img data-rich="' + k + '" src="' + r.foto + '" alt="' + r.nazva + ', ' + r.kram + '" loading="lazy"' + (male ? ' style="max-width:' + r.w + 'px;max-height:' + r.h + 'px"' : '') + '></span>';
  };
  window.ДАЛІ = function (d) { location.hash = '#' + (Math.max(1, Math.min(window.СЦЕНИ.length, n + 1 + (d || 1)))); };
  window.СЦЕНА = function (id) { for (var i = 0; i < window.СЦЕНИ.length; i++) if (window.СЦЕНИ[i].id === id) { location.hash = '#' + (i + 1); return; } };
  document.addEventListener('DOMContentLoaded', function () {
    korin = document.getElementById('korin');
    if (!/чисто/.test(decodeURIComponent(location.search))) {
      pult = document.createElement('nav'); pult.className = 'pult';
      pult.innerHTML = '<button aria-label="попередня сцена">‹</button><b></b><button aria-label="наступна сцена">›</button><a href="../інтерфейси_дизайнера.html">огляд</a>';
      pult.children[0].onclick = function () { window.ДАЛІ(-1); };
      pult.children[2].onclick = function () { window.ДАЛІ(1); };
      document.body.appendChild(pult);
    }
    document.body.addEventListener('click', function (e) {
      var a = e.target.closest('[data-dali],[data-scena-do]');
      if (!a) return;
      e.preventDefault();
      if (a.hasAttribute('data-scena-do')) window.СЦЕНА(a.getAttribute('data-scena-do')); else window.ДАЛІ(+a.getAttribute('data-dali') || 1);
    });
    window.addEventListener('hashchange', pokaz);
    pokaz();
  });
})();
