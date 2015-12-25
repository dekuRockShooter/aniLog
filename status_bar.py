import curses
import curses.textpad
import shared

# TODO: no hard coding
class StatusBar:
    def __init__(self, scr_top_row, scr_right_col):
        curses.initscr()
        curses.noecho()
        self._win = curses.newwin(1, 80, scr_top_row, scr_right_col)
        self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
        self._cur_str = ''
        self._scr_top_row = scr_top_row
        self._scr_right_col = scr_right_col

    def set_str(self, new_str):
        self._cur_str = new_str

    def create(self):
        cur_browser = shared.BrowserFactory.get_cur()
        name = cur_browser.get_name()
        idx = shared.BrowserFactory.get_cur_idx() + 1
        browser_count = shared.BrowserFactory.get_count()
        self._cur_str = '{}:{}/{}'.format(name, idx, browser_count)

    def update(self):
        """Redisplays itself using updated information."""
        self._win.addstr(0,0, ''.join([' ' for i in range(79)]))#\
        self.create()
        self._win.addstr(0, 0, self._cur_str)
        self._win.refresh()

    def destroy(self):
        curses.echo()

    def redraw(self):
        self._win.addstr(0,0, ''.join([' ' for i in range(79)]))#\
        self._win.addstr(0, 0, self._cur_str)
        self._win.refresh()
        txt = self._text_pad.edit()
        parsed_str = []
        token = []
        in_single_quotes = False
        in_double_quotes = False
        for letter in txt:
            if in_single_quotes:
                if letter == '\'':
                    parsed_str.append(''.join(token))
                    token.clear()
                    in_single_quotes = False
                else:
                    token.append(letter)
            elif in_double_quotes:
                if letter == '"':
                    parsed_str.append(''.join(token))
                    token.clear()
                    in_double_quotes = False
                else:
                    token.append(letter)
            else:
                if letter == ' ' and len(token) > 0:
                    parsed_str.append(''.join(token))
                    token.clear()
                elif letter == '\'':
                    in_single_quotes = True
                elif letter == '"':
                    in_double_quotes = True
                else:
                    token.append(letter.strip())
        if in_single_quotes or in_double_quotes:
            pass
        else:
            # cmd_map[parsed_str[0]](parsed_str[1:]*)
            pass
        self._win.addstr(0,0, ''.join([' ' for i in range(79)]))#\
        self.update()
        return parsed_str

    def scroll(self, direction, quantifier=1):
        pass

    def on_browser_switch(self):
        """ Switch to the new browser and display it.

        Assumes that the current browser has already had its create method
        called.
        """
        cur_browser = shared.BrowserFactory.get_cur()
        name = cur_browser.get_name()
        idx = shared.BrowserFactory.get_cur_idx() + 1
        browser_count = shared.BrowserFactory.get_count()
        self._cur_str = '{}:{}/{}'.format(name, idx, browser_count)
        self.update()
