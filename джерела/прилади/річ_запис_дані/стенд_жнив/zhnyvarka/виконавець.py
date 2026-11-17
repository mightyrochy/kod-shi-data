"""Штучний браузерний офер з читанням body й штатною відмовою числового SKU."""
import json
import re

from bs4 import BeautifulSoup

ЗЛІПОК_DOM = """() => {
  let основа = document.body, найбільший = 0;
  document.querySelectorAll('.product').forEach(вузол => {
    const довжина = (вузол.textContent || '').length;
    if (довжина > найбільший) { найбільший = довжина; основа = вузол; }
  });
  if (найбільший < 500) основа = document.body;
  return {text: основа.textContent || '', title: document.title};
}"""


def картка_з_dom(_url, тіло, dom):
    """Переносить body в опис офера; числовий SKU відмовляє, адреса в цьому випадку не потрібна."""
    суп = BeautifulSoup(тіло, 'html.parser')
    вузол = суп.select_one('script[type="application/ld+json"]')
    дані = json.loads(вузол.get_text()) if вузол else {}
    артикул = (дані.get('sku') or '')[:60]
    опис = re.search(r'Опис (.*?) Характеристики', dom['text'], re.S)
    return dict(артикул=артикул, опис=опис.group(1) if опис else '')
