# -*- coding: utf-8 -*-
"""Знімок Shopify 06.11 з ноутбука: `zhnyvarka/shopify_знімок.py` із прямим `requests` (власний UA бібліотеки) замість
Chrome-подібного транспорту жниварки — wearme.ua віддає йому «Browser verification» (403), а прямому запиту — JSON.
Запуск: REQUESTS_CA_BUNDLE=<сховище ОС> python знімок_shopify.py <тека> [домен …]"""
import os, sys, time, requests
ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ТУТ, "..", "..", "..", "zhnyvarka"))
import жниварка as ж                                               # noqa: E402
import shopify_знімок as зн                                        # noqa: E402


class Прямий:
    def __init__(self, пауза=1.0, **_):
        self.пауза = пауза

    def get(self, url, **_):
        time.sleep(self.пауза)
        for спроба in range(4):
            r = requests.get(url, timeout=40)
            if r.status_code not in (429, 503):
                break
            time.sleep(30 * 2 ** спроба)
        return dict(код=r.status_code, тіло=r.text, url=url)


ж.Транспорт = Прямий
if __name__ == "__main__":
    sys.exit(зн.main())
