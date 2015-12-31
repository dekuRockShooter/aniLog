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
        """Create the user interface if it doesn't exist already.

        The user interface is returned.

        Args:
            keymap (KeyMap): The keymap to use.
        """
        if UIRegistry._ui is None:
            UIRegistry._ui = ui.UI(keymap)
        return UIRegistry._ui

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
            IndexError: if idx is out of bounds.
            KeyError: if name is not a name of a browser.
        """
        BrowserFactory._cur_browser = BrowserFactory._browser_indexes[idx]
        BrowserFactory._cur_idx = idx

    @staticmethod
    def create(upper_left_coords, bot_right_coords,
               col_widths, db_name, table):
        """Create and return a new browser.

        Create a browser within the given screen coordinates. The
        browser will be named db_name.table_name. The browser is then
        returned. If a browser with the same name already exists, then
        that one is returned. If a new browser was created, then that
        browser is opened.

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
        BrowserFactory._browser_indexes.insert(BrowserFactory._cur_idx + 1,
                                               new_browser)
        BrowserFactory.set_cur(BrowserFactory._cur_idx + 1)
        return new_browser

    @staticmethod
    def destroy(name=None, idx=None):
        """Destroy (close) a browser.

        The browser to destroy be identified via its index or its name.

        If both idx and name are given, then the method first tries to 
        destroy using the index.  If that is unsuccessful, then it tries
        using the name.

        If neither idx nor name is given, then the current browser is
        destroyed.

        The new browser is the one after the destroyed one.  If the
        destroyed browser was the last one, then the new browser is
        the one that was before it.

        Args:
            idx: The index of the browser to destroy.
            name: The name of the browser to destroy.

        Raises:
            IndexError: if idx is out of bounds.
            KeyError: if name is not a name of a browser.
        """
        if idx:
            name = BrowserFactory,_browser_indexes[idx].get_name()
        elif name is None:
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
    """Manage the status bar.

    This class provides static methods for creating, accessing, and
    removing the status bar.

    Methods:
        get: Return the status bar.
        create: Create the status bar.
        destroy: Destroy the status bar.
    """
    _status_bar = None

    @staticmethod
    def get():
        """Return the status bar."""
        return StatusBarRegistry._status_bar

    @staticmethod
    def create(position, cmd_map):
        """Create the status bar.

        The status bar is created if it has not been already.  The
        status bar is returned.
        """
        if not StatusBarRegistry._status_bar:
            StatusBarRegistry._status_bar =\
                status_bar.StatusBar(position, cmd_map)
        return StatusBarRegistry._status_bar

    @staticmethod
    def destroy():
        """Destroy (close) the status bar."""
        StatusBarRegistry._status_bar.destroy()

    @staticmethod
    def destroy_all():
        StatusBarRegistry.destroy()


class DBRegistry:
    """Manage connections to databases.

    This class provides static methods for creating, accessing, and
    removing connections to databases.

    One connection per database is allowed, which can be shared by
    any class.

    Methods:
        get: Return a database connection.
        create: Create a database connection.
        destroy: Close a database connection.
    """
    _db_map = {}

    @staticmethod
    def create(name):
        """Open a database connection.

        A connection to the database is created and returned.  If the
        connection already exists, then it is just returned.

        Args:
            name (path): The name of the database to connect to.
        """
        if name not in DBRegistry._db_map:
            DBRegistry._db_map[name] = db.DBConnection(name)
        return DBRegistry._db_map[name]

    @staticmethod
    def get_db(name):
        """Return a database connection.

        Args:
            name (path): The name of the database.

        Raises:
            KeyError: if no database with the given name has been
                connected to.
        """
        return DBRegistry._db_map[name]

    @staticmethod
    def destroy(name):
        """Close a database connection.

        Args:
            name (path): The name of the database.

        Raises:
            KeyError: if no database with the given name has been
                connected to.
        """
        DBRegistry._db_map[name].close()
        DBRegistry._db_map.pop(name)

    @staticmethod
    def destroy_all():
        for db in DBRegistry._db_map.values():
            db.close()
        DBRegistry._db_map.clear()


class CopyBuffer:
    """Manage the copy buffers.

    This class provides static methods to access and modify the copy
    buffers. The copy buffer is simply a map from a single character
    (English alphabet, upper or lower case) to a tuple. The name of
    a buffer is thus the character used as the key, and the contents
    of a buffer is the tuple.  The tuple is intended to represent a row
    in a database table. Thus, its elements should be the values of
    each column.  Use this class to copy a row from one table into 
    another table (provided both have the same schema).

    Attributes:
        DEFAULT_BUFFER: The buffer that is used if no buffer is given.

    Methods:
        get: Return the contents of a copy buffer.
        set: Change the contents of a copy buffer.
    """
    DEFAULT_KEY = '0'
    _copy_buffer = {}

    @staticmethod
    def set(key, val):
        """Change the contents of a buffer.

        Args:
            key (char): The name of the buffer.
            val (tuple): The new content of the buffer. Each element is
                the value of a column in some database table.
        """
        CopyBuffer._copy_buffer[key] = val

    @staticmethod
    def get(key):
        """Return the contents of a buffer.

        Args:
            key: The name of the buffer.

        Raises:
            KeyError: if no buffer with the given name exists.
        """
        return CopyBuffer._copy_buffer[key]
