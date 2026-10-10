# -*- coding: utf-8 -*-
"""Рядок 2894 у справжньому Chromium на ЗІБРАНІЙ сторінці: картка з питаннями кольору `на_розгортання` —
кнопка згорнута, підпис лічить усі; шар під час збирання їх не пише; дотик розгортає, шар пише лише їх,
речення з'являються. Шар — заглушка контракту `мова` (як `тест_показу.js`).
Запуск із `джерела`: python3 проби/питання_кольору_розгортання.py <зібраний index.html>"""
import sys, pathlib
from playwright.sync_api import sync_playwright
url = pathlib.Path(sys.argv[1]).resolve().as_uri() + "#міст=http://localhost:8787&т=tok-a1"
JS = """async () => { const в = [];
  містП = async (ім, д) => { if (д.повідомлення){ в.push(Object.keys(д.повідомлення));
      return {промпт: 'П', розмітка: Object.keys(д.повідомлення).map((к, і) => ({н: і + 1, ключ: к}))}; }
    if (д.розмітка_повідомлень) return {тексти: Object.fromEntries(д.розмітка_повідомлень.map(р => [р.ключ,
      р.ключ === 'кнопка' ? 'Чого я ще не звірила' : 'Речення ' + р.ключ.split('.')[1]])), без_відповіді: []};
    return {промпт: '', розмітка: []}; };
  модельМовиП = async () => '{}';
  const п = (код, р) => ({правило: 'K-COL-06', повідомлення: {kind: 'card_code_unknown', statements: [{code: код}]}, ...р});
  const к = {рука: '1', речі: [], опис: '', як_носити: [], неповний: '', текст: '', питання: [
    п('items_register_unknown', {}), п('cannot_tell_two_different_whites', {на_розгортання: 1}),
    п('cannot_tell_lightness_structure', {на_розгортання: 1}), п('areas_not_measured', {для_всіх: 1})]};
  await мовоюКарткуП(к, 'hand_1'); const збирання = в.map(х => х.join());
  П = {картки: [к]}; ПИТАННЯ_РОЗГОРНУТО = false;
  const вузол = рендерКартку(0); document.body.appendChild(вузол);
  const б = вузол.querySelector('.питання-коду'), рядки = () => б.querySelectorAll('.задум div').length;
  const до = {відкрито: б.open, підпис: б.querySelector('summary').textContent, рядків: рядки()};
  б.querySelector('summary').click(); await new Promise(р => setTimeout(р, 300));
  return {збирання, до, після: {відкрито: б.open, підпис: б.querySelector('summary').textContent, рядків: рядки(),
          текст: б.querySelector('.задум').textContent}, дотик: в.slice(збирання.length).map(х => х.join())}; }"""
with sync_playwright() as pw:
    б = pw.chromium.launch(); с = б.new_page(viewport={"width": 390, "height": 844})
    помилки = []; с.on("pageerror", lambda е: помилки.append(str(е)))
    с.goto(url); с.wait_for_function("typeof рендерКартку === 'function'", timeout=60000)
    р = с.evaluate(JS); б.close()
print("збирання — виклики шару:", р["збирання"])
print("ДО дотику:", р["до"]); print("ПІСЛЯ дотику:", р["після"]); print("дотик — виклики шару:", р["дотик"])
print("помилок сторінки:", len(помилки), помилки[:2])
