import curses
import shared

class Coordinates:
    def __init__(self, beg=0, end=0, sep=0):
        self.beg = beg
        self.end = end
        self.sep = sep

class Browser:
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    PAGE_UP = 5
    PAGE_DOWN = 6
    HOME = 7
    END = 8

    def __init__(self, scr_top_row, scr_left_col, scr_bot_row, scr_right_col,\
            col_widths, db_name, table):
        try:
            self._db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            shared.DBRegistry.create(db_name)
            self._db = shared.DBRegistry.get_db(db_name)
        finally:
            self._db.connect()
        self._table = table
        self._cur_line = 0
        self._VIS_RNG = (scr_bot_row - scr_top_row,\
                scr_right_col - scr_left_col)

        self._scr_top_row = scr_top_row
        self._scr_bot_row = scr_bot_row
        self._scr_left_col = scr_left_col
        self._scr_right_col = scr_right_col
        self._END_ROW = 100
        self._BEG_ROW = 0
        self._bot_row = 0
        self._top_row = self._VIS_RNG[0]

        self._END_COL = 100
        self._BEG_COL = 0
        self._left_col = 0
        self._right_col = self._VIS_RNG[1]

        self._cur_row = 0
        self._cur_col = 0
        self._cursor_col = 0
        self._col_coords = []
        self._reset_col_coords(col_widths)

        curses.initscr()
        self._pad = curses.newpad(self._END_ROW, self._END_COL) # height, width
        self._pad.keypad(1)
        self._pad.leaveok(0)

    def _reset_col_coords(self, col_widths):
        assert(len(col_widths) > 0)
        self._col_coords.clear()
        self._col_coords.append(Coordinates(0, col_widths[0]-1, col_widths[0]))
        for width in col_widths[1:]:
            prev_sep = self._col_coords[-1].sep
            if width == 0:
                self._col_coords.append(None)
                continue
            beg = prev_sep + 1
            end = prev_sep + width
            sep = prev_sep + width + 1
            self._col_coords.append(Coordinates(beg, end, sep))

    def create(self):
        _cur_row = 0
        for row in self._db.select_all_from(self._table):
            for coord, col_val in zip(self._col_coords, row):
                try:
                    col_str = str(col_val)[: coord.end - coord.beg + 1].ljust(0)
                except IndexError:
                    col_str = str(col_val).ljust()
                self._pad.addstr(_cur_row, coord.beg, col_str)
            _cur_row = _cur_row + 1
        self.redraw()

    def destroy(self):
        self._pad.keypad(0)

    def redraw(self):
        self._pad.refresh(self._top_row, self._left_col,\
                self._scr_top_row, self._scr_left_col,\
                self._scr_bot_row, self._scr_right_col)

    def get_cur_str(self):
        cur_coord = self._col_coords[self._cur_col]
        width = cur_coord.end - cur_coord.beg + 1
        return self._pad.instr(self._cur_row, self._cur_col, width)

    def scroll(self, direction, quantifier=1):
        prev_line = self._pad.instr(self._cur_row, 0)
        prev_row = self._cur_row
        if direction == Browser.DOWN or direction == Browser.UP:
            if direction == Browser.UP:
                self._cur_row = self._cur_row - quantifier
            else:
                self._cur_row = self._cur_row + quantifier
            if self._cur_row > self._END_ROW - 2:
                self._cur_row = self._bot_row = self._END_ROW - 2
                self._top_row = self._bot_row - self._VIS_RNG[0]
            elif self._cur_row > self._bot_row:
                self._bot_row = self._cur_row
                self._top_row = self._bot_row - self._VIS_RNG[0]
            elif self._cur_row < self._BEG_ROW:
                self._cur_row = self._top_row = self._BEG_ROW
                self._bot_row = self._top_row + self._VIS_RNG[0]
            elif self._cur_row < self._top_row:
                self._top_row = self._cur_row
                self._bot_row = self._top_row + self._VIS_RNG[0]

        # highlight next line and scroll down
        self._pad.addstr(prev_row, 0, prev_line)
        cur_line = self._pad.instr(self._cur_row, 0)
        self._pad.addstr(self._cur_row, 0, cur_line, curses.A_STANDOUT)
        self.redraw()
