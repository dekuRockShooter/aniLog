"""Manage objects that are shared among various classes.

This module contains classes that manage shared resources.  Use these
classes to create and get objects, as doing so will ensure that
everything is accounted for and that no wasteful copies are lingering
about.

Classes:
    UIRegistry: manage the user interface.
    DBRegistry: manage database connections.
    BrowserFactory: manage the browsers.
    StatusBarRegistry: manage the status bar.
    CopyBuffer: manage the copy buffer.
"""
#cls class method
import db
import browser
import status_bar
import ui

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
        """Create the user interface if it doesn't exist already."""
        if UIRegistry._ui is None:
            UIRegistry._ui = ui.UI(keymap)

    @staticmethod
    def destroy():
        """Destroy the user interface.

        This method calls the user interface's destroy method.
        """
        UIRegistry._ui.destroy()

class BrowserFactory:
    """Manage all browsers.

    This class provides static methods for creating, accessing, and
    removing browsers.

    Methods:
        get: return the current browser.
        get_idx: return the index of the current browser.
        get_count: return the number of browsers.
        set: switch to another browser.
        create: create a new browser.
        destroy: destroy the current browser.
    """
    _browser_map = {}
    _id = 0
    _browser_indexes = []
    _cur_browser = None
    _cur_idx = -1

    @staticmethod
    def get_cur():
        """Return the current browser."""
        return BrowserFactory._cur_browser

    @staticmethod
    def get_cur_idx():
        """Return the index (zero-based) of the current browser.

        Raises:
            IndexError: if _cur_idx is -1, meaning no browsers have
                been created.
        """
        return BrowserFactory._cur_idx

    @staticmethod
    def get_count():
        """Return the number of browsers."""
        return len(BrowserFactory._browser_indexes)

    @staticmethod
    def set_cur(idx):
        """Switch to another browser.

        The browser to switch to can be identified via its index or its
        name.

        If both idx and name are given, then the method first tries to 
        switch using the index.  If that is unsuccessful, then it tries
        using the name.

        Args:
            idx: The index of the browser to open.
            name: The name of the browser to open.

        Raises:
            IndexError: if idx or name are out of bounds.
        """
        BrowserFactory._cur_browser = BrowserFactory._browser_indexes[idx]
        BrowserFactory._cur_idx = idx

    @staticmethod
    def create(upper_left_coords, bot_right_coords,
               col_widths, db_name, table):
        """Create a new browser.

        Args:
            upper_left_coords (tuple): The screen coordinates at which
                the upper left corner of the browser is drawn. The
                format is (row, column).
            bot_right_coords (tuple): The screen coordinates at which
                the bottom right corner of the browser is drawn. The
                format is (row, column).
            col_widths (list): The widths (in numbers of characters)
                 that each column in the table are displayed with.
            db_name: The name of the database to use.
            table_name: The name of the table to use.
        """
        name = '{}.{}'.format(db_name, table)
        if name in BrowserFactory._browser_map:
            return BrowserFactory._browser_map[name]
        new_browser = browser.Browser(upper_left_coords, bot_right_coords,
                                      col_widths, db_name, table)
        BrowserFactory._browser_map[name] = new_browser
        BrowserFactory._cur_idx = BrowserFactory._cur_idx + 1
        BrowserFactory._browser_indexes.insert(BrowserFactory._cur_idx,\
                new_browser)
        return new_browser

    @staticmethod
    def destroy(name='', idx=None):
        """Raises a KeyError"""
        if idx:
            name = BrowserFactory,_browser_indexes[idx].get_name()
        elif not name:
            name = BrowserFactory,_browser_indexes[\
                    BrowserFactory._cur_idx].get_name()
        BrowserFactory,_browser_map[name].destroy()
        BrowserFactory._browser_map.pop(name)
        BrowserFactory._browser_indexes.pop(BrowserFactory._cur_idx)
        if BrowserFactory._cur_idx >= len(BrowserFactory._browser_indexes):
            BrowserFactory._cur_idx = BrowserFactory._cur_idx - 1
        elif BrowserFactory._cur_idx < 0:
            BrowserFactory._cur_idx = -1

    @staticmethod
    def destroy_all():
        for name, browser in BrowserFactory._browser_map.items():
            browser.destroy()
        BrowserFactory._browser_map.clear()

class StatusBarRegistry:
    _status_bar = None

    @staticmethod
    def get():
        return StatusBarRegistry._status_bar

    @staticmethod
    def create(scr_top_row, scr_right_col):
        if not StatusBarRegistry._status_bar:
            StatusBarRegistry._status_bar =\
                status_bar.StatusBar(scr_top_row, scr_right_col)
        return StatusBarRegistry._status_bar

    @staticmethod
    def destroy():
        StatusBarRegistry._status_bar.destroy()

    @staticmethod
    def destroy_all():
        StatusBarRegistry.destroy()

class DBRegistry:
    _db_map = {}

    @staticmethod
    def create(name):
        if name in DBRegistry._db_map:
            return
        DBRegistry._db_map[name] = db.DBConnection(name)

    @staticmethod
    def get_db(name):
        """Raises a KeyError"""
        return DBRegistry._db_map[name]

    @staticmethod
    def destroy(name):
        """Raises a KeyError"""
        DBRegistry._db_map[name].close()
        del DBRegistry._db_map[name]

    @staticmethod
    def destroy_all():
        for db in DBRegistry._db_map.values():
            db.close()
        DBRegistry._db_map.clear()

class CopyBuffer:
    DEFAULT_KEY = '0'
    _copy_buffer = {}

    @staticmethod
    def set(key, val):
        CopyBuffer._copy_buffer[key] = val

    @staticmethod
    def get(key):
        """Raises a KeyError"""
        return CopyBuffer._copy_buffer[key]
