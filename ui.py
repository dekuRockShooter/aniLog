import curses
import os
import settings.keys
import settings.positions as positions
import signals
import browser
import status_bar
from shared import DBRegistry

# TODO: merge in aniLog.py
class UI(signals.Observer):
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
        signals.Subject.__init__(self)
        signals.Observer.__init__(self)
        self._win = None
        self._key_map = key_map
        settings.keys.cmd_map['next_browser'].register(self)
        settings.keys.cmd_map['prev_browser'].register(self)

    def create(self):
        """Start curses and create the user interface."""
        os.environ['ESCDELAY'] = '25'
        self._win = curses.initscr()
        curses.cbreak()
        curses.noecho()
        curses.curs_set(0)
        self._set_coords()
        self._create_widgets()

    def _create_widgets(self):
        #status_bar.StatusBarRegistry.create(1, settings.keys.cmd_map).update()
        tables = [('Watching'), ('backlog'), ('completed')]
        for table in tables:
            try:
                b = browser.BrowserRegistry.create(
                       positions.DEFAULT_DB_NAME,
                       table)
            except FileNotFoundError as err:
                #stat_bar.prompt(str(err), enums.Prompt.ERROR)
                continue
            except ValueError as err:
                #stat_bar.prompt(str(err), enums.Prompt.ERROR)
                continue
            b.create()
        status_bar.StatusBarRegistry.create(1, settings.keys.cmd_map).update()

    def _set_coords(self):
        curses.update_lines_cols()
        if positions.STATUS_BAR_POSITION == positions.SCREEN_TOP:
            positions.STATUS_BAR_COORDS = (0, 0)
            positions.BROWSER_UPPER_LEFT_COORDS = (1, 0)
            positions.BROWSER_BOTTOM_RIGHT_COORDS = (curses.LINES - 1,
                                                    curses.COLS - 1)
        else:
            positions.STATUS_BAR_COORDS = (curses.LINES - 1, 0)
            positions.BROWSER_UPPER_LEFT_COORDS = (0, 0)
            positions.BROWSER_BOTTOM_RIGHT_COORDS = (curses.LINES - 2,
                                                    curses.COLS - 1)

    def destroy(self):
        """Destroy all object and end curses."""
        DBRegistry.destroy_all()
        browser.BrowserRegistry.destroy_all()
        curses.nocbreak()
        curses.echo()
        curses.curs_set(1)
        curses.endwin()

    # TODO: no hardcoding.  Also, Alt-q quits the program because key is q.
    # This would be a problem, but the current while loop conditional is
    # temporary,.  Fixing this bug right now might actually be a bad thing.
    def get_key(self):
        """Get keys from the user and run a command.

        Keys are sent to KeyMap's get_cmd method, which returns
        the Command object that corresponds to the current key or
        keysequence.  If the command is valid, then it is executed.
        """
        key = 0
        cmd = None
        while key != ord('q'):
            key = self._win.getch()
            if key == 27: # alt or esc
                # Get a char while pressing Alt.  Otherwise, the char is
                # gotten after releasing Alt.
                self._win.nodelay(True)
                key = self._win.getch()
                self._win.nodelay(False)
                if key == -1: # esc
                    continue
                try:
                    self._key_map.get_cmd(27)
                    cmd = self._key_map.get_cmd(key)
                except KeyError:
                    cmd = None
            else:
                try:
                    cmd = self._key_map.get_cmd(key)
                except KeyError:
                    cmd = None
            if cmd is not None:
                cmd.execute()

    def on_browser_switch(self):
        """Display a new browser.

        This method should be called whenever the current browser has
        changed. It simply redraws the current browser (as indicated by
        BrowserRegistry.get()).
        """
        browser.BrowserRegistry.get_cur().redraw()

    def receive_signal(self, signal, args):
        if signal == signals.Signal.BROWSER_SWITCHED:
            self.on_browser_switch()


class UIRegistry:
    """Manage the user interface.

    This class provides static methods to create and access the user
    interface. It makes sure that there is only one user interface.

    Methods:
        get: return the reference to the user interface.
        create: create the user interface.
        destroy: deallocate the user interface.
    """
    _ui = None

    @staticmethod
    def get():
        """Return the reference to the user interface."""
        return UIRegistry._ui

    @staticmethod
    def create(keymap):
        """Create the user interface if it doesn't exist already.

        The user interface is returned.

        Args:
            keymap (KeyMap): The keymap to use.
        """
        if UIRegistry._ui is None:
            UIRegistry._ui = UI(keymap)
        return UIRegistry._ui

    @staticmethod
    def destroy():
        """Destroy the user interface.

        This method calls the user interface's destroy method.
        """
        UIRegistry._ui.destroy()
