import curses
import os
import keymap
import commands
from browser import Browser
from shared import BrowserFactory, DBRegistry
from keymap import KeyMap

class UI:
    """Display all widgets and get keyboard input.

    This class starts curses and displays all of the widgets. It
    also gives the user control over the keyboard.

    Methods:
        create: start curses and initialize all widgets.
        destroy: end curses and close all widgets.
        get_key: get input from the keyboard.

    """
    def __init__(self, key_map):
        """Constructor.

        Args:
            key_map (KeyMap): The keymap to use for the interface.
        """
        self._cur_browser = BrowserFactory.get_cur()
        self._win = None
        self._key_map = key_map

    def create(self):
        """Start curses and create the user interface."""
        os.environ['ESCDELAY'] = '25'
        self._win = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self._cur_browser.create()

    def destroy(self):
        """Destroy all object and end curses."""
        DBRegistry.destroy_all()
        BrowserFactory.destroy_all()
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

    def get_key(self):
        """Get keys from the user and run a command.

        Keys are sent to KeyMap's get_cmd method, which returns
        the Command object that corresponds to the current key or
        keysequence. If the command is valid, then it is executed.
        """
        key = 0
        while key != ord('q'):
            key = self._win.getch()
            cmd = self._key_map.get_cmd(key)
            if cmd is not None:
                cmd.execute()

    def on_browser_switch(self):
        """Display a new browser.

        This method should be called whenever the current browser has
        changed. It simply redraws the current browser (as indicated by
        BrowserRegistry.get()).
        """
        self._cur_browser = BrowserFactory.get_cur()
        self._cur_browser.redraw()
