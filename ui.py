import curses
import os
import keymap
import commands
from browser import Browser
from shared import BrowserFactory
from keymap import KeyMap

class UI:
    def __init__(self, key_map):
        self._cur_browser = BrowserFactory.get_cur()
        self._win = None
        self._key_map = key_map

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
            cmd = self._key_map.get_cmd(key)
            if cmd:
                cmd.execute()
