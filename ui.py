import curses
import os
import keymap
from browser import Browser
from shared import BrowserFactory

class UI:
    def __init__(self):
        self._cur_browser = BrowserFactory.get_cur()
        self._win = None

    def create(self):
        os.environ['ESCDELAY'] = '25'
        self._win = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self._cur_browser.create()

    def destroy(self):
        self._cur_browser.destroy()
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

    def get_key(self):
        key = 0
        while key != ord('q'):
            key = self._win.getch()
            self._cur_browser.scroll(Browser.DOWN)
