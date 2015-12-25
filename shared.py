import db
import browser
import status_bar

class BrowserFactory:
    _browser_map = {}
    _cur_browser = None

    @staticmethod
    def get_cur():
        return BrowserFactory._cur_browser

    @staticmethod
    def set_cur(idx):
        """Raises a KeyError"""
        BrowserFactory._cur_browser = BrowserFactory._browser_map[idx]

    @staticmethod
    def create(scr_top_row, scr_left_col, scr_bot_row, scr_right_col,\
            col_widths, db_name, table):
        name = '{}.{}'.format(db_name, table)
        if name in BrowserFactory._browser_map:
            return
        BrowserFactory._browser_map[name] =\
                browser.Browser(scr_top_row, scr_left_col, scr_bot_row,\
                scr_right_col, col_widths,  db_name, table)

    @staticmethod
    def destroy(name):
        """Raises a KeyError"""
        BrowserFactory,_browser_map[name].destroy()
        BrowserFactory._browser_map.pop(name)

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
