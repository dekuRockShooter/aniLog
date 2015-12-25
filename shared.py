import db
import browser
import status_bar
import ui

class UIRegistry:
    _ui = None

    @staticmethod
    def get():
        return UIRegistry._ui

    @staticmethod
    def create(keymap):
        if not UIRegistry._ui:
            UIRegistry._ui = ui.UI(keymap)

    @staticmethod
    def destroy():
        UIRegistry._ui.destroy()

    @staticmethod
    def destroy_all():
        pass

class BrowserFactory:
    _browser_map = {}
    _id = 0
    _browser_indexes = []
    _cur_browser = None
    _cur_idx = -1

    @staticmethod
    def get_cur():
        return BrowserFactory._cur_browser

    @staticmethod
    def get_cur_idx():
        return BrowserFactory._cur_idx

    @staticmethod
    def set_cur(idx):
        """Raises an IndexError"""
        #BrowserFactory._cur_browser = BrowserFactory._browser_map[idx]
        BrowserFactory._cur_browser = BrowserFactory._browser_indexes[idx]
        BrowserFactory._cur_idx = idx

    @staticmethod
    def create(scr_top_row, scr_left_col, scr_bot_row, scr_right_col,\
            col_widths, db_name, table):
        name = '{}.{}'.format(db_name, table)
        if name in BrowserFactory._browser_map:
            return
        new_browser = browser.Browser(scr_top_row, scr_left_col, scr_bot_row,\
                scr_right_col, col_widths,  db_name, table)
        BrowserFactory._browser_map[name] = new_browser
        BrowserFactory._cur_idx = BrowserFactory._cur_idx + 1
        BrowserFactory._browser_indexes.insert(BrowserFactory._cur_idx,\
                new_browser)

    @staticmethod
    def destroy(name):
        """Raises a KeyError"""
        BrowserFactory,_browser_map[name].destroy()
        BrowserFactory._browser_map.pop(name)
        BrowserFactory._browser_indexes.pop(BrowserFactory._cur_idx)

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
        if StatusBarRegistry._status_bar:
            return
        StatusBarRegistry._status_bar =\
                status_bar.StatusBar(scr_top_row, scr_right_col)

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
