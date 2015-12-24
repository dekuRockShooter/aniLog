import curses
import curses
import shared
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
    PRIMARY_KEY = 'rowid'
    _browser_id = 0

    def __init__(self, scr_top_row, scr_left_col, scr_bot_row, scr_right_col,\
            col_widths, db_name, table):
        try:
            self._db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            shared.DBRegistry.create(db_name)
            self._db = shared.DBRegistry.get_db(db_name)
        finally:
            self._db.connect()
        self._row_ids = []
        self._col_names = []
        for row in self._db.execute('pragma table_info({})'.format(table)):
            self._col_names.append(row[1])
        self._db_name = db_name
        self._table = table
        self._cur_line = 0
        self.PRIMARY_KEY = Browser.PRIMARY_KEY
        self._VIS_RNG = (scr_bot_row - scr_top_row,\
                scr_right_col - scr_left_col)

        self._row_count = 0
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
        self._cur_col = 0 # zero based
        self._cursor_col = 0
        self._col_coords = []
        self._reset_col_coords(col_widths)

        curses.initscr()
        self._pad = curses.newpad(self._END_ROW, self._END_COL) # height, width
        self._pad.keypad(1)
        self._pad.leaveok(0)
        Browser._browser_id = Browser._browser_id + 1
        self._id = Browser._browser_id

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
        self._row_count = 0
        for row in self._db.select_all_from(self._table):
            self._row_ids.append(row[0]) # the row id
            for coord, col_val in zip(self._col_coords, row):
                try:
                    col_str = str(col_val)[: coord.end - coord.beg + 1].ljust(0)
                except IndexError:
                    col_str = str(col_val).ljust()
                self._pad.addstr(self._row_count, coord.beg, col_str)
            self._row_count = self._row_count + 1
        self.redraw()

    def get_name(self):
        return '{}.{}'.format(self._db_name, self._table)

    def destroy(self):
        self._pad.keypad(0)

    def redraw(self):
        self._pad.refresh(self._top_row, self._left_col,\
                self._scr_top_row, self._scr_left_col,\
                self._scr_bot_row, self._scr_right_col)

    def update_new_entry(self):
        row = self._db.get_newest(self._table)
        # this is the same as the inner loop of create()
        self._row_ids.append(row[0]) # the row id
        for coord, col_val in zip(self._col_coords, row):
            try:
                col_str = str(col_val)[: coord.end - coord.beg + 1].ljust(0)
            except IndexError:
                col_str = str(col_val).ljust()
            self._pad.addstr(self._row_count, coord.beg, col_str)
        self._row_count = self._row_count + 1
        self.redraw()

    def update_cur_cell(self):
        coord = self._col_coords[self._cur_col]
        cell_value = str(self.get_cur_cell())
        try:
            col_str = cell_value[: coord.end - coord.beg + 1].ljust(0)
        except IndexError:
            col_str = cell_value.ljust(0)
        self._pad.addstr(self._cur_row, coord.beg, col_str)
        self.redraw()

    def update_del_entry(self):
        row_idx = self._row_count - 1
        self._row_ids.pop(self._cur_row)
        for row_idx in range(self._cur_row + 1, self._row_count):
            row = self._pad.instr(row_idx, 0)
            self._pad.addstr(row_idx - 1, 0, row)
        self._pad.addstr(row_idx, 0,\
                ''.join([' ' for i in range(self._END_COL)]))
        self._row_count = self._row_count - 1
        self.redraw()

    def get_cur_cell(self):
        cmd = 'select "{}" from "{}" where "{}"="{}"'.\
                format(self._col_names[self._cur_col],\
                self._table, self.PRIMARY_KEY,\
                self._row_ids[self._cur_row])
        return self._db.execute(cmd)[0][0]

    def get_cur_rowid(self):
        return self._row_ids[self._cur_row]

    def get_col_name(self):
        return self._col_names[self._cur_col]

    def scroll(self, direction, quantifier=1):
        prev_cell_coords = self._col_coords[self._cur_col]
        prev_cell_val = self._pad.instr(self._cur_row, prev_cell_coords.beg,\
                prev_cell_coords.sep - prev_cell_coords.beg)
        prev_row = self._cur_row
        prev_col = self._cur_col
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

        elif direction == Browser.LEFT or direction == Browser.RIGHT:
            if direction == Browser.LEFT:
                self._cur_col = self._cur_col - quantifier
            else:
                self._cur_col = self._cur_col + quantifier
            if self._cur_col < 0:
                self._cur_col = 0
            elif self._cur_col >= len(self._col_names):
                self._cur_col = len(self._col_names) - 1

        # highlight next line and scroll down
        cur_cell_coords = self._col_coords[self._cur_col]
        self._pad.addstr(prev_row, prev_cell_coords.beg, prev_cell_val)
        cur_cell_val = self._pad.instr(self._cur_row, cur_cell_coords.beg,\
                cur_cell_coords.sep - cur_cell_coords.beg)
        self._pad.addstr(self._cur_row, cur_cell_coords.beg, cur_cell_val,\
                curses.A_STANDOUT)
        self.redraw()
