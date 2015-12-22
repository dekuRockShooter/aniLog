from browser import Browser

class BrowserFactory:
    _browser_list = {}
    _cur_browser = None

    @staticmethod
    def get_cur():
        return BrowserFactory._cur_browser

    @staticmethod
    def set_cur(idx):
        try:
            BrowserFactory._cur_browser = BrowserFactory._browser_list[idx]
        except KeyError:
            pass

    @staticmethod
    def create_browser(name, scr_top_row, scr_left_col,\
            scr_bot_row, scr_right_col):
        if name in BrowserFactory._browser_list:
            return
        BrowserFactory._browser_list[name] =\
                Browser(scr_top_row, scr_left_col, scr_bot_row, scr_right_col)

    @staticmethod
    def delete_browser(name):
        try:
            del BrowserFactory,_browser_list[name]
        except KeyError:
            pass
