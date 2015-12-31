import math
import curses
import shared

class Coordinates:
    def __init__(self, beg=0, end=0, sep=0):
        self.beg = beg
        self.end = end
        self.sep = sep

class Browser:
    """A widget that allows interaction with a database table.

        Class variables:
            UP, DOWN, LEFT, RIGHT, PAGE_UP, PAGE_DOWN, HOME, END: Constants
                that specify how to scroll.
            PRIMARY_KEY: A tuple of column names that act as the table's
                primary keys.

        Instance variables:
            PRIMARY_KEY: A tuple of column names that act as the table's
                primary keys.
            _SCR_COORDS: The coordinates of the screen in which the browser is
                contained. _SCR_COORDS[0] are the coordinates of the upper left
                corner of the browser. _SCR_COORDS[1] are the coordinates of the
                lower right corner of the browser.
            _VIS_RNG: The dimensions of the visible pad area. _VIS_RNG[0] is
                the number of rows that are visible. _VIS_RNG[1] is the number
                if columns that are visible.
            _END_ROW: The last row of the pad (the number of rows that it can
                hold).
            _BEG_ROW: The first row of the pad.
            _END_COL: The last column of the pad (the number of characters that
                it can hold).
            _BEG_COL: The first column of the pad.
            _db: The connection to the database.
            _db_name: The name of the database.
            _table_name: The name of the database table that the browser
                displays.
            _row_ids: A list of tuples. The k'th element is a tuple that
                contains the primary keys of the k'th row in the pad.
            _col_names: A list of the names in the database table.
            _row_count: The number of non-empty rows in the pad (the number of
                database entries written to the pad). This is always in the
                interval [0, _END_ROW]
            _bot_row: The last row of the pad that is currently in view (the
                row that is at _SCR_COORDS[1][0]).
            _top_row: The first row of the pad that is currently in view (the
                row that is at _SCR_COORDS[0][0]).
            _left_col: The first column of the pad that is currently in view (
                the column that is at _SCR_COORDS[0][1]).
            _right_col: The last column of the pad that is currently in view (
                the column that is at _SCR_COORDS[1][1]).
            _cur_row: The currently selected row.
            _cur_col: The currently selected column.
            _col_coords: The coordinates that bound a column. This is a list of
                Coordinates. The k'th element is the coordinates of the
                k'th column.
            _pad: The pad that displays everything.
    """
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    PAGE_UP = 5
    PAGE_DOWN = 6
    HOME = 7
    END = 8
    PRIMARY_KEY = 'rowid'

    def __init__(self, upper_left_coords, bot_right_coords,
                 col_widths, db_name, table):
        try:
            self._db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            shared.DBRegistry.create(db_name)
            self._db = shared.DBRegistry.get_db(db_name)
            self._db.connect()
        self._row_ids = []
        self._col_names = self._db.get_col_names(table)
        self._db_name = db_name
        self._table = table
        self.PRIMARY_KEY = Browser.PRIMARY_KEY
        self._VIS_RNG = [bot_right_coords[0] - upper_left_coords[0],\
                bot_right_coords[1] - upper_left_coords[1]]
        self._row_count = 0
        self._SCR_COORDS = [list(upper_left_coords), list(bot_right_coords)]
        self._END_ROW = 1
        self._BEG_ROW = 0
        self._bot_row = 0
        self._top_row = self._VIS_RNG[0] # TODO: this should be bot_row

        self._END_COL = int(sum(col_widths) + 2*len(col_widths))
        self._BEG_COL = 0
        self._left_col = 0
        self._right_col = self._VIS_RNG[1]

        self._cur_row = 0
        self._cur_col = 0 # zero based
        self._col_coords = []
        self._set_col_coords(col_widths)

        self._pad = None

    # TODO: Don't hardcode the beginning of the first column. It wont
    # necessarily be zero. Also, account for zero widths.
    def _set_col_coords(self, col_widths):
        """Set the coordinates of all the columns.

        A column is confined within the bounds coords.beg and coords.end,
        inclusive. coords.sep is the coordinate that separates two columns.

        Args:
            col_widths ([ints]): The widths (in numbers of characters)
                used to display the columns in the database. The k'th
                element is the width of the k'th column.  col_width's
                length must be the same as the number of columns in the
                table. The numbers must be nonnegative integers. If a
                width is zero, then that column is not displayed.
        """
        assert(len(col_widths) == len(self._col_names))
        self._col_coords.clear()
        self._col_coords.append(Coordinates(0, col_widths[0]-1, col_widths[0]))

        # For any column, end - beg = width - 1, and beg = 1 + prev_col.sep.
        # If a column's width is 0, then set its sep to prev.sep so that there
        # is no extra gap. Also, leave its beg greater than its end so that
        # curses doesn't try to write any of it.
        for width in col_widths[1:]:
            prev_sep = self._col_coords[-1].sep
            beg = prev_sep + 1
            end = prev_sep + width
            sep = prev_sep + width + 1 if width > 0 else prev_sep
            self._col_coords.append(Coordinates(beg, end, sep))

    # TODO: save the query so that the same entries will be shown after a
    # resize.
    def create(self, rows=None):
        """Display the given rows to an empty browser.

        The browser is cleared and all data is reset to reflect the
        empty browser.  curses is initialized if it has not been
        already. Then, the rows are written to the browser. If no rows
        are given, then all rows from the database table are used.

        Args:
            rows ([tuples]): The rows to display.  Each tuple
                represents a row, and the elements in a tuple
                represent the columns in the row.
        """
        if not rows:
            rows = self._db.select_all_from(self._table)
        self._setup_curses()
        self._pad.clear()
        self._row_count = 0
        self._row_ids.clear()
        self._populate_browser(rows)

    def _setup_curses(self):
        """Initialize the browser and its settings.

        If the browser has already been initialized, then nothing
        is done.
        """
        if self._pad != None:
            return
        curses.initscr()
        self._pad = curses.newpad(self._END_ROW, self._END_COL) # height, width
        self._pad.keypad(1)
        self._pad.leaveok(0)
        self._scr_cols = curses.COLS
        self._scr_rows = curses.LINES

    def _populate_browser(self, rows):
        """Write rows to the browser.

        The rows are written to the browser starting at the first 
        empty line.  If there are not enough lines in the browser,
        then it is resized.

        Args:
            rows ([tuples]): The rows to display.  Each tuple
                represents a row, and the elements in a tuple
                represent the columns in the row.
        """
        if (self._row_count + len(rows)) > self._END_ROW:
            self._resize(2 * (self._row_count + len(rows)))
        for row in rows:
            self._row_ids.append(row[0])

            # Write each column with the correct width at the correct coord,
            # starting at the _row_count'th row.
            for coord, col_val in zip(self._col_coords, row):
                col_width = coord.end - coord.beg + 1
                self._pad.addnstr(self._row_count, coord.beg, str(col_val),\
                        col_width)
            self._row_count = self._row_count + 1

    def destroy(self):
        """Close the browser."""
        self._pad.keypad(0)

    def redraw(self):
        """Redraw the screen to show new changes."""
        self._pad.refresh(self._top_row, self._left_col,
                          *self._SCR_COORDS[0], *self._SCR_COORDS[1])

    def _resize(self, rows=None, cols=None):
        """Increase the number rows and columns of the pad.

        The pad is resized to hold the given number of rows and columns.
        If no value for a row or column is given, then the respective
        dimension is doubled. If an argument is less than or equal to
        its current value, then nothing is done. If only one dimension
        is to be resized, then make sure to give the other dimension
        a small value (such as 0).

        Args:
            rows: The new number of rows. This must be greater than the
                current number of rows.
            cols: The new number of columns. This must be greater than 
                the current number of columns.
        """
        if (rows <= self._END_ROW) and (cols <= self._END_COL):
            return
        # Get the new number of rows.
        if rows is None:
            self._END_ROW = 2 * self._END_ROW
        elif rows > self._END_ROW:
            self._END_ROW = rows
        # Get the new number of columns.
        if cols is None:
            self._END_COL = 2 * self._END_COL
        elif cols > self._END_COL:
            self._END_COL =cols
        self._pad.resize(self._END_ROW, self._END_COL)

    def on_new_query(self, rows):
        """Redraw the screen using the given rows.

        The browser's current contents are cleared, and the new rows
        are displayed.

        Args:
            rows ([tuples]): The rows to display.  Each tuple
                represents a row, and the elements in a tuple
                represent the columns in the row.
        """
        self.create(rows)
        self.redraw()

    def on_entry_inserted(self):
        """Redraw the screen with a new entry.

        This method should be called whenever a row has been inserted
        into the browser's table. The new entry is displayed.
        """
        row = [self._db.get_newest(self._table)]
        self._populate_browser(row)
        self.redraw()

    def on_entry_updated(self):
        """Redraw the current cell's value.

        This method should be called whenever a row's column has been
        changed. The current cell's value is updated to its new value.
        """
        coord = self._col_coords[self._cur_col]
        new_value = str(self.get_cur_cell())
        col_width = coord.end - coord.beg + 1

        # clear the column
        blank_col = ''.join([' ' for x in range(col_width)])
        self._pad.addstr(self._cur_row, coord.beg, blank_col)

        # update the column
        self._pad.addnstr(self._cur_row, coord.beg, new_value, col_width)
        self.redraw()

    def on_entry_deleted(self):
        """Redraw the screen without the current row.

        This method should be called whenever an entry has been deleted
        in the browser's table.
        """
        self._row_ids.pop(self._cur_row)
        self._pad.deleteln()
        self._row_count = self._row_count - 1
        self.redraw()

    def on_screen_resize(self, new_rows, new_cols):
        if new_rows != self._scr_rows:
            row_diff = new_rows - self._scr_rows
            self._SCR_COORDS[1][0] += row_diff
            self._VIS_RNG[0] += row_diff
            self._scr_rows += row_diff
        if new_cols != self._scr_cols:
            col_diff = new_cols - self._scr_cols
            self._SCR_COORDS[1][1] += col_diff
            self._VIS_RNG[1] += col_diff
        self.redraw()

    def get_cur_cell(self):
        """Return the value of the currently selected cell.

        The current cell's value is queried from the database and 
        returned as the datatype that it is stored as in the database.
        """
        cmd = 'select "{col_name}" from "{table}" where "{prim_key}"="{key}"'.\
                format(col_name=self._col_names[self._cur_col],\
                table=self._table,\
                prim_key=self.PRIMARY_KEY,\
                key=self._row_ids[self._cur_row])
        return self._db.execute(cmd)[0][0]

    def get_name(self):
        """Return the name of the browser.

        The name of the browser is db.table, where db is the path to
        the database it is connected to, and table is the table it
        displays.
        """
        return '{}.{}'.format(self._db_name, self._table)

    def get_table_name(self):
        """Return the name of the database table used by the browser."""
        return self._table

    def get_db_name(self):
        """Return the name of the database used by the browser."""
        return self._db_name

    def get_prim_key(self):
        """Return the primary key value of the current cell."""
        return self._row_ids[self._cur_row]

    def get_col_name(self):
        """Return the column name of the current cell."""
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
            #if self._cur_row > self._END_ROW - 2:
                #self._cur_row = self._bot_row = self._END_ROW - 2
                #self._top_row = self._bot_row - self._VIS_RNG[0]
            if self._cur_row > self._row_count - 1:
                self._cur_row = self._bot_row = self._row_count - 1
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
            if self._col_coords[self._cur_col].sep > self._right_col:
                self._right_col = self._col_coords[self._cur_col].sep
                self._left_col = self._right_col - self._VIS_RNG[1]
            elif self._col_coords[self._cur_col].beg < self._left_col:
                self._left_col = self._col_coords[self._cur_col].beg
                self._right_col = self._left_col + self._VIS_RNG[1]

        # highlight next line and scroll down
        cur_cell_coords = self._col_coords[self._cur_col]
        self._pad.addstr(prev_row, prev_cell_coords.beg, prev_cell_val)
        cur_cell_val = self._pad.instr(self._cur_row, cur_cell_coords.beg,\
                cur_cell_coords.sep - cur_cell_coords.beg)
        self._pad.addstr(self._cur_row, cur_cell_coords.beg, cur_cell_val,\
                curses.A_STANDOUT)
        self.redraw()
