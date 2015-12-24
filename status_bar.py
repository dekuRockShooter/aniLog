import curses
import curses.textpad

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
        pass

    def destroy(self):
        curses.echo()

    def redraw(self):
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
                #['x' for i in range(self._scr_right_col - 1)]))
        self._win.refresh()
        return parsed_str

    def scroll(self, direction, quantifier=1):
        pass
