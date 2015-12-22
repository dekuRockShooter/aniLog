import curses
from browser import Browser
from shared import BrowserFactory

class Command:
    def __init__(self, name, desc, quantifier=1, **kwargs):
        self._name = name
        self._desc = desc
        self._quantifier = quantifier
        self._args = kwargs

    def execute(self):
        pass

class ScrollDown(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        cur_browser.scroll(Browser.DOWN, self._quantifier)

class ScrollUp(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        cur_browser.scroll(Browser.UP, self._quantifier)
