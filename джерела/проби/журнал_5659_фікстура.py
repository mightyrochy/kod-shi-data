"""Offline-контекст: справжній збережений HTML, контрольний HTTP 200; решта адрес — явний збій."""
import asyncio
from collections import defaultdict
from types import SimpleNamespace
from виконавець import Виконавець


class Сторінка:
    """Відтворює один збережений файл; мережі й фото не відкриває."""
    def __init__(self, url, тіло, виклики):
        self.канон, self.тіло, self.виклики, self.cutoff = url, тіло, виклики, False
    async def route(self, *_): pass
    async def goto(self, url, **_):
        self.url = url; self.виклики.append(url)
        if url != self.канон: raise RuntimeError("CONTROL_NO_SAVED_RESPONSE")
        return self
    status = 200  # Контроль, а не виміряний мережевий статус збереженого файла.
    async def body(self): return self.тіло
    async def all_headers(self): return {"content-type": "text/html"}
    async def content(self): return self.тіло.decode("utf-8")
    async def evaluate(self, *_): return {}  # DOM не вимірюємо; парсер читає LD/og самого HTML.
    async def wait_for_load_state(self, *_ , **__): pass
    async def wait_for_timeout(self, *_):
        if self.cutoff: await asyncio.sleep(1)
    async def new_page(self): return self


def прогін(корінь, рецепт, адреси, сторінка, стеля):
    """Викликає штатний шлях _жнива → _картка → _пиши, підміняє тільки пошук і браузер."""
    в = Виконавець(SimpleNamespace(журнал=корінь, стеля=стеля, пауза=0, оновити_перелік=False))
    async def перелік(*_):
        if адреси is None: raise AssertionError("DISCOVERY_RESTARTED")
        return адреси
    в._horoshop_адреси = перелік
    л = defaultdict(int, адрес=0, бали=[], нотатка="")
    try: asyncio.run(asyncio.wait_for(в._жнива(сторінка, рецепт, л), timeout=0.01 if сторінка.cutoff else 1))
    except TimeoutError: assert сторінка.cutoff
    п = в.проходи[рецепт["домен"]]; звіт = п.звіт(); п.закрити()
    return звіт
