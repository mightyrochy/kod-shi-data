/* ── ЕКРАН: ОБРАЗ НА ВЕСЬ ЕКРАН ────────────────────────────────────────────
   Дотик до приміряного образу на полотні відкриває його на весь екран. Перегляд тримає фокус на єдиній кнопці й
   повертає його на відкривач; як і аркуш, дослівно відновлює попередній inert фону, а не вмикає його весь.
   Стан — ключ `перегляд` {відкрито}; вузли (відкривач, фон) — поза станом, у `ПЕРЕГЛЯД`. */
const ПЕРЕГЛЯД = {відкривач: null, фон: [], прокрутка: ''};
Екран.дія('перегляд-відкрити', (п, відкривач) => { ПЕРЕГЛЯД.відкривач = відкривач; Екран.змінити({перегляд: {відкрито: true}}); });
Екран.дія('перегляд-закрити', () => Екран.змінити({перегляд: {відкрито: false}}));
/* відкривачі — на картках, яких при старті ще нема: один слухач документа */
document.addEventListener('click', е => {
  const т = е.target.closest && е.target.closest('.полотно .перегляд-відкрити');
  if (т){ Екран.відЖінки('перегляд-відкрити', е, т); return; }
  const п = $('перегляд');
  if (!п.hidden && (е.target === п || е.target === п.querySelector('img') || е.target.closest('#перегляд button')))
    Екран.відЖінки('перегляд-закрити');
});
document.addEventListener('keydown', е => {
  if ($('перегляд').hidden) return;
  if (е.key === 'Escape'){ е.preventDefault(); Екран.відЖінки('перегляд-закрити'); }
  else if (е.key === 'Tab'){ е.preventDefault(); $('перегляд').querySelector('button').focus(); }
});
Екран.малювач('перегляд', ['перегляд'], с => {
  const п = $('перегляд'), і = п.querySelector('img'), відкривач = ПЕРЕГЛЯД.відкривач;
  if (с.перегляд.відкрито){
    і.src = відкривач.querySelector('img').src; п.hidden = false;
    ПЕРЕГЛЯД.прокрутка = document.body.style.overflow; document.body.style.overflow = 'hidden';
    for (const в of document.body.children){
      if (в === п || /^(SCRIPT|STYLE)$/.test(в.tagName)) continue;
      ПЕРЕГЛЯД.фон.push([в, в.getAttribute('inert')]); в.setAttribute('inert', '');
    }
    п.querySelector('button').focus();
    return;
  }
  п.hidden = true; і.removeAttribute('src'); document.body.style.overflow = ПЕРЕГЛЯД.прокрутка;
  for (const [в, було] of ПЕРЕГЛЯД.фон){
    if (було === null) в.removeAttribute('inert'); else в.setAttribute('inert', було);
  }
  ПЕРЕГЛЯД.фон = [];
  if (відкривач && відкривач.isConnected && !відкривач.closest('[inert]') && відкривач.getClientRects().length)
    відкривач.focus({preventScroll: true});
  ПЕРЕГЛЯД.відкривач = null;
});
