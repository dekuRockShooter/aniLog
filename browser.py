import math
import curses
import bisect
import enums
import shared
import settings.positions as positions
import settings.keys
import signals


class Coordinates:
    """Define the coordinates of a table's columns.

    The coordinates specify a location on the screen and are referred
    to as screen coordinates.  They define the range occupied by one
    column of a table (table column refers to a column in a table in
    a database).

    Instance variables:
        beg: The screen column at which the table column begins.
        end: The screen column at which the table column ends.
        sep: The screen column that separates adjacent table columns.
            This is where the character used to separate columns is
            drawn.
    """
    def __init__(self, beg=0, end=0, sep=0):
        self.beg = beg
        self.end = end
        self.sep = sep


# TODO: Rename _END_ROW to _row_capacity, _END_COL to _col_capacity,
# _row_ids to _primary_keys, _db to _DB, _db_name to _DB_NAME, _table_name
# to _TABLE_NAME, _col_names to _COL_NAMES, _bot_row to _last_vis_row, _top_row
# to _first_vis_row, _left_col to _first_vis_col, _right_col to _last_vis_col,
# on_new_query to _on_new_query, on_entry_deleted to _on_entry_deleted,
# on_screen_resize to _on_screen_resize, browser_generator to table_generator,
# remove_from_name to remove_by_name, remove_from_id to remove_by_id, get to
# get_table_by_id and get_table_by_name and get_cur_table, destroy to
# destroy_cur and destroy_by_name and destroy_by_id.

# Rename get_col_name to get_cur_col_name after removing calls that use it.
# Rename scroll to _on_scroll after removing calls that use it and creating
#   a scroll signal.

# Create get_pks which returns the names of the table columns that are
#   primary keys.

# Implement destroy and destroy_all according to their documentation.
class Browser(signals.Observer):
    """A widget that allows interaction with a database table.

        Instance variables:
            PRIMARY_KEY: A tuple of column names that act as the table's
                primary keys.
    """
    """
        _SCR_COORDS: The coordinates of the screen in which the browser is
             contained.  _SCR_COORDS[0] are the coordinates of the upper left
             corner of the browser.  _SCR_COORDS[1] are the coordinates of the
             lower right corner of the browser.  These coordinates are used
             when refreshing the pad and are changed whenever the screen is
             resized.
        _VIS_RNG: The dimensions of the visible pad area.  _VIS_RNG[0] is
             the number of rows that are visible.  _VIS_RNG[1] is the number
             of columns that are visible.  The range changes whenever the
             screen is resized.
        _END_ROW: The maximum rows that the pad can hold.  This changes when
            there are more queried rows to show than there are rows in the
            pad.  This might also change when the screen is resized so that
            it has more rows than there are in the pad.
        _BEG_ROW: The first row of the pad.  This is always zero and never
            changes. 
        _END_COL: The maximum columns (chars) that the pad can hold. This
            changes whenever the screen is resized.
        _BEG_COL: The first column of the pad.  This is always zero and
            never changes.
        _db (DBConnection): The connection to the database.  It does not
            change.
        _db_name (str): The name of the database.  This is constant.
        _table_name (str): The name of the database table that the browser
             displays.  This is constant.
        _row_ids ([tuples]): The k'th element is a tuple that contains the
            primary keys of the k'th row in the pad.  This changes whenever
            the number of rows written to the pad changes (deletions,
            insertions, new queries).
        _col_names: A list of the names of the columns in the database table.
            This is constant.
        _row_count: The number of non-empty rows in the pad (the number of
             database entries written to the pad).  This is always in the
             interval [0, _END_ROW).  This changes whenever the number of rows
             written to the pad changes (deletions, insertions, new queries).
        _bot_row: The last row of the pad that is visible.  It changes whenever
            the screen is resized or when the table is scrolled vertically.
        _top_row: The first row of the pad that is visible.  It changes
            whenever the screen is resized or when the table is scrolled
            vertically.
        _left_col: The first column of the pad that is visible.  It changes
            whenever the screen is resized or when the table is scrolled
            horizontally.
        _right_col: The last column of the pad that is visible.  It changes
            whenever the screen is resized or when the table is scrolled
            horizontally.
        _cur_row: The currently selected row.  This changes whenever the table
            is scrolled vertically.
        _cur_col: The currently selected column.  This changes whenever the
            table is scrolled horizontally.
        _col_coords ([Coordinates]): The k'th element is the coordinates of the
            k'th table column.  This changes whenever the table columns are
            resized.
        _pad: The pad that displays everything.  This changes whenever new
            rows need to be displayed (scroll, queries, etc.).
    """
    def __init__(self, db_name, table):
        """Initialize a table.

        Args:
            db_name (str): The name of the database to connect to.
            table_name (str): The name of the table to display.

        Raises;
            FileNotFoundError: If the database does not exist.
            ValueError: If the given table does not exist in the
                database.
        """
        # This will raise an AssertionError if len(col_widths) != len(cols)
        col_widths = positions.COL_WIDTHS
        try:
            self._db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            self._db = shared.DBRegistry.create(db_name)
        try:
            self._db.connect()
        except FileNotFoundError:
            shared.DBRegistry.destroy(db_name)
            raise FileNotFoundError('{db} not found.'.format(db=db_name))
        if (table,) not in self._db.get_tables():
            raise ValueError('{db} has no table {table}.'.format(
                db=db_name, table=table))
        self.PRIMARY_KEY = 'rowid'
        self._col_names = self._db.get_col_names(table)
        self._row_ids = []
        self._db_name = db_name
        self._table = table
        self._VIS_RNG = [positions.BROWSER_BOTTOM_RIGHT_COORDS[0] -
                             positions.BROWSER_UPPER_LEFT_COORDS[0],
                         positions.BROWSER_BOTTOM_RIGHT_COORDS[1] -
                             positions.BROWSER_UPPER_LEFT_COORDS[1]]
        self._row_count = 0
        self._SCR_COORDS = [positions.BROWSER_UPPER_LEFT_COORDS,
                            positions.BROWSER_BOTTOM_RIGHT_COORDS]
        self._END_ROW = 1 # The last row in the pad.
        self._BEG_ROW = 0
        self._bot_row = 0 # The last row in the pad that is visible.
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
        self._select_buffer = []

        cmd_map = settings.keys.CommandMap.get()
        cmd_map['update'].register(self)
        cmd_map['edit'].register(self)
        cmd_map['new_entry'].register(self)
        cmd_map['del_entry'].register(self)
        cmd_map['sort'].register(self)
        cmd_map['filter'].register(self)
        cmd_map['resize'].register(self)
        cmd_map['select'].register(self)
        cmd_map['paste'].register(self)

    # TODO: Don't hardcode the beginning of the first column. It wont
    # necessarily be zero. Also, account for zero widths.
    def _set_col_coords(self, col_widths):
        """Set the coordinates of all the table columns.

        Args:
            col_widths ([ints]): The widths (in numbers of characters)
                used to display the columns in the database. The k'th
                element is the width of the k'th column.  col_width's
                length must be the same as the number of columns in the
                table. The numbers must be nonnegative integers. If a
                width is zero, then that column is not displayed.

        Raises:
            AssertionError: if the size of col_width is not equal to
                the number of table columns.
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
        """Display rows.

        Display the given rows.  If no rows are given, then all rows
        from the database table are displayed.

        Args:
            rows ([tuples]): The rows to display.  Each tuple
                represents a row, and the elements in a tuple
                represent the columns in the row.  The length of the
                tuples must be the same as the number of columns in
                the database table.
        """
        if not rows:
            rows = self._db.select_all_from(self._table)
        # Clear and reset everything to an empty state.
        self._setup_curses()
        self._pad.clear()
        self._row_count = 0
        self._cur_row = 0
        self._row_ids.clear()
        self._populate_browser(rows)

    def _setup_curses(self):
        """Initialize the pad and some settings."""
        # If the pad has already been initialized, then nothing is done.
        if self._pad != None:
            return
        curses.initscr()
        self._END_ROW = positions.BROWSER_BOTTOM_RIGHT_COORDS[0] * 2
        self._END_COL = positions.BROWSER_BOTTOM_RIGHT_COORDS[1] * 2
        self._pad = curses.newpad(self._END_ROW, self._END_COL)
        self._pad.keypad(1)
        self._pad.leaveok(0)

    def _populate_browser(self, rows):
        """Write rows to the browser.

        The rows are written to the browser starting at the first
        empty line.  If there are not enough lines in the browser,
        then it is resized.  Nothing is done if 'rows' is empty.

        Args:
            rows ([tuples]): The rows to display.  Each tuple
                represents a row, and the elements in a tuple
                represent the columns in the row. The size of each tuple
                must the equal to the number of columns in the database
                table.
        """
        if not rows:
            return
        if (self._row_count + len(rows)) > self._END_ROW:
            self._resize(2 * (self._row_count + len(rows)))
        for row in rows:
            self._row_ids.append(row[0])

            # Write each column with the correct width at the correct coord,
            # starting at the _row_count'th row.
            for coord, col_val in zip(self._col_coords, row):
                col_width = coord.end - coord.beg + 1
                if col_val is None:
                    col_val = ''
                self._pad.addnstr(self._row_count, coord.beg, str(col_val),
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
        """Resize the pad.

        The pad is resized to hold the given number of rows and columns.
        If no value for a row or column is given, then the respective
        dimension is doubled.  If an argument is less than or equal to
        its current value, then nothing is done.  If only one dimension
        is to be resized, then make sure to give the other dimension
        a small value (such as 0).

        Args:
            rows: The new number of rows. This must be greater than the
                current number of rows in order to resize the pad.
            cols: The new number of columns. This must be greater than
                the current number of columns in order to resize the pad.
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
        """Display the given rows.

        The table is cleared, and the new rows are displayed.

        Args:
            rows ([tuples]): The rows to display.  Each tuple
                represents a row, and the elements in a tuple
                represent the columns in the row.  The size of the
                tuple must be equal to the number of table columns.
        """
        self.create(rows)
        self.redraw()

    # TODO: This only shows the newest row.  Make it show all rows inserted
    # since the last redraw.
    def _on_entry_inserted(self):
        """Redraw the table to include newly inserted rows.

        This redraws the table with the rows that were inserted since the
        last redraw.
        """
        row = [self._db.get_newest(self._table)]
        self._populate_browser(row)
        self.scroll(enums.Scroll.END)

    def _on_entry_updated(self):
        """Redraw the current cell's value.

        This updates the current cell's value to match what it is in
        the database.
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

    # TODO: This redraws the table with one less row.  Make it able to redraw
    # the table without all the deleted rows.
    # since the last redraw.
    def on_entry_deleted(self):
        """Redraw the table to exclude newly deleted rows.

        This redraws the table without rows that were deleted since the last
        redraw.
        """
        self._row_ids.pop(self._cur_row)
        self._pad.deleteln()
        self._row_count = self._row_count - 1
        if self._cur_row >= self._row_count:
            self._cur_row = self._row_count - 1
        self.redraw()

    # TODO: Resize horizontally.
    def on_screen_resize(self):
        """Redraw the table to fit in the screen."""
        if self._END_ROW < positions.BROWSER_BOTTOM_RIGHT_COORDS[0]:
            self._resize(rows=positions.BROWSER_BOTTOM_RIGHT_COORDS[0] * 2,
                         cols=0)
        self._VIS_RNG = [positions.BROWSER_BOTTOM_RIGHT_COORDS[0] -
                             positions.BROWSER_UPPER_LEFT_COORDS[0],
                         positions.BROWSER_BOTTOM_RIGHT_COORDS[1] -
                             positions.BROWSER_UPPER_LEFT_COORDS[1]]
        self._SCR_COORDS = [positions.BROWSER_UPPER_LEFT_COORDS,
                            positions.BROWSER_BOTTOM_RIGHT_COORDS]
        self._top_row = self._VIS_RNG[0] # TODO: this should be bot_row
        self._right_col = self._VIS_RNG[1]
        self.redraw()

    # TODO: maybe move this to a method in DBConnection.
    def get_cur_cell(self):
        """Return the value of the currently selected cell.

        The value returned has the same datatype that it has in the 
        table.
        """
        cmd = 'select "{col_name}" from "{table}" where "{prim_key}"="{key}"'.\
                format(col_name=self._col_names[self._cur_col],
                       table=self._table,
                       prim_key=self.PRIMARY_KEY,
                       key=self._row_ids[self._cur_row])
        return self._db.execute(cmd)[0][0]

    def get_name(self):
        """Return the name of this Table.

        The name of the Table is db.table, where 'db' is the path to
        the database it is connected to, and 'table' is the table that
        it displays.
        """
        return '{}.{}'.format(self._db_name, self._table)

    def get_table_name(self):
        """Return the name of the database table used by this Table."""
        return self._table

    def get_db_name(self):
        """Return the name of the database used by this Table."""
        return self._db_name

    def get_cur_row_pks(self):
        """Return the primary key values of the current row.

        Returns:
            A list of the primary key values of the current row.
        """
        return self._row_ids[self._cur_row]

    def get_col_name(self):
        """Return the column name of the current cell."""
        return self._col_names[self._cur_col]

    def receive_signal(self, signal, args=None):
        """Override singals.Observer."""
        if signal is signals.Signal.SCREEN_RESIZED:
            self.on_screen_resize()
            return
        buffer = BrowserRegistry.get_buffer()
        if (buffer is None) or (buffer.get() is not self):
            return
        elif signal is signals.Signal.ENTRY_INSERTED:
            self._on_entry_inserted()
        elif signal is signals.Signal.ENTRY_DELETED:
            self.on_entry_deleted()
        elif signal is signals.Signal.ENTRY_UPDATED:
            self._on_entry_updated()
        elif signal is signals.Signal.NEW_QUERY:
            self.on_new_query(args)
        elif signal is signals.Signal.ENTRIES_SELECTED:
            self._on_select()

    def _lines_to_scroll(self, direction):
        """Return the number of rows to scroll.

        Args:
            direction: The direction in which to scroll.  This can be
                any of the enumerations in enums.Scroll that denote
                vertical scrolling.

        Returns:
            The number of rows to scroll (positive or negative), or
            zero if the direction is not vertical.
        """
        if direction == enums.Scroll.UP:
            return -1
        elif direction == enums.Scroll.DOWN:
            return 1
        elif direction == enums.Scroll.PAGE_DOWN:
            return self._VIS_RNG[0]
        elif direction == enums.Scroll.PAGE_UP:
            return -self._VIS_RNG[0]
        elif direction == enums.Scroll.HOME:
            return -self._row_count
        elif direction == enums.Scroll.END:
            return self._row_count
        else:
            return 0

    def _cols_to_scroll(self, direction):
        """Return the number of table columns to scroll.

        A table column is a database column.

        Args:
            direction: The direction in which to scroll.  This can be
                any of the enumerations in enums.Scroll that denote
                horizontal scrolling.

        Returns:
            The number of columns to scroll (positive or negative), or
            zero if the direction is not horizontal.
        """
        if direction == enums.Scroll.LEFT:
            return -1
        elif direction == enums.Scroll.RIGHT:
            return 1
        #elif direction == enums.Scroll.PAGE_RIGHT:
            #return self._VIS_RNG[0]
        #elif direction == enums.Scroll.PAGE_LEFT:
            #return -self._VIS_RNG[0]
        elif direction == enums.Scroll.H_HOME:
            return -len(self._col_names)
        elif direction == enums.Scroll.H_END:
            return len(self._col_names)

    def scroll(self, direction, quantifier=1):
        """Scroll in the given direction."""
        if self._row_count == 0:
            return
        prev_cell_coords = self._col_coords[self._cur_col]
        prev_cell_val = self._pad.instr(self._cur_row, prev_cell_coords.beg,
                prev_cell_coords.sep - prev_cell_coords.beg)
        prev_row = self._cur_row
        prev_col = self._cur_col
        if direction in (enums.Scroll.DOWN, enums.Scroll.UP,
                         enums.Scroll.PAGE_DOWN, enums.Scroll.PAGE_UP,
                         enums.Scroll.END, enums.Scroll.HOME):
            self._cur_row = self._cur_row + self._lines_to_scroll(direction)
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

        elif direction in (enums.Scroll.RIGHT, enums.Scroll.LEFT,
                         enums.Scroll.PAGE_RIGHT, enums.Scroll.PAGE_LEFT,
                         enums.Scroll.H_END, enums.Scroll.H_HOME):
            self._cur_col = self._cur_col + self._cols_to_scroll(direction)
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
        select_buffer = shared.SelectBuffer.get()
        cur_cell_coords = self._col_coords[self._cur_col]
        if str(self._row_ids[prev_row]) not in self._select_buffer:
            self._pad.addstr(prev_row, prev_cell_coords.beg, prev_cell_val)
        cur_cell_val = self._pad.instr(self._cur_row, cur_cell_coords.beg,
                cur_cell_coords.sep - cur_cell_coords.beg)
        self._pad.addstr(self._cur_row, cur_cell_coords.beg, cur_cell_val,
                curses.A_STANDOUT)
        self.redraw()

    # TODO: The first loop removes highlights.  The second loop adds
    # highlights.  Is there a way to combine this behavior?
    # TODO: add self.redraw() at the end to show highlights immediately.
    def _on_select(self):
        """Redraw the table with all selections highlighted"""
        select_buffer = shared.SelectBuffer.get()
        for id_str in self._select_buffer:
            id = int(id_str)
            row_idx = bisect.bisect_left(self._row_ids, id)
            if row_idx != len(self._row_ids) and self._row_ids[row_idx] == id:
                self._pad.chgat(row_idx, 0, -1, curses.A_NORMAL)
        for id_str in select_buffer:
            id = int(id_str)
            row_idx = bisect.bisect_left(self._row_ids, id)
            if row_idx != len(self._row_ids) and self._row_ids[row_idx] == id:
                self._pad.chgat(row_idx, 0, -1, curses.A_STANDOUT)
        self._select_buffer = select_buffer

# TODO: make this private.
class NullBrowser(Browser):
    """A Table that does nothing.

    This class is used to eliminate the need to check if a Table is
    valid, making the code cleaner.
    """
    def __init__(self, db_name, table):
        try:
            super(NullBrowser, self).__init__(db_name, table)
        except ValueError:
            pass
        except FileNotFoundError:
            pass

    def create(self, rows=None):
        pass
    def destroy(self):
        pass
    def redraw(self):
        pass
    def on_new_query(self, rows):
        pass
    def on_entry_deleted(self):
        pass
    def on_screen_resize(self):
        pass
    def get_cur_cell(self):
        return ''
    def get_name(self):
        return ''
    def get_table_name(self):
        return ''
    def get_db_name(self):
        return ''
    def get_cur_row_pks(self):
        return []
    def get_col_name(self):
        return ''
    def receive_signal(self, signal, args=None):
        pass
    def scroll(self, direction, quantifier=1):
        pass


null_browser = NullBrowser('', '')


class BrowserBuffer(signals.Observer):
    """A place to store Tables.

    This class acts like a container that holds Tables.  It can be
    used to query information about any of the opened Tables and to
    traverse them.
    """
    """
    _name_map (int -> str): a map from Table id's to Table names.  This
        changes synchronously with _browser_map when Tables are removed,
        added, or when the buffer is cleared.
    _browser_map (str -> browser): a map from Table names to Tables.
        This changes synchronsously with _name_map when Tables are
        removed, added, or when the buffer is cleared.
    _END_ROW: The maximum rows that the pad can hold.  This changes when
        there are more Tables than there are rows in the pad.
    _pad: The pad that displays the list of Tabs.  This changes whenever
        the state of the buffer changes (Tables are added, removed, switched).
    _id: A number that increments whenever a Table is added.  Its current
        value is assigned as a unique identifier for a Table and then
        incremented.
    _cur: The table that is currently visible.  This changes whenever a Table
        is switched to.
    _prev: The table that was previously visible.  This changes whenever a
        Table is switched to.
    """
    def __init__(self):
        """Initialize the buffer to an empty state."""
        self._name_map = {}
        self._browser_map = {}
        curses.initscr()
        self._END_ROW = 2
        self._pad = curses.newpad(self._END_ROW, curses.COLS)
        self._id = 0
        self._cur = null_browser
        self._prev = null_browser
        cmd_map = settings.keys.CommandMap.get()
        cmd_map['ls'].register(self)

    def name_generator(self):
        """Return a generator for Table names.

        The generator generates tuples of the form
        (Table id, Table name).  The id is an int, and the name is
        a str.
        """
        return (item for item in self._name_map.items())

    def browser_generator(self):
        """Return a generator for Tables.

        The generator generates tuples of the form (Table name, Table).
        The name is a str, and Table is a Table reference.
        """
        return (browser for browser in self._browser_map.items())

    # TODO:  Is 'name' really necessary?  It can be gotten from browser.
    # Also, this allows duplicate entries.  There needs to be a check
    # beforehand to prevent adding the same Table twice.  Also, document
    # this behavior.
    def add(self, name, browser):
        """Add a Table to the buffer.

        Args:
            name: The name of the Table as defined by Table's get_name
                method.
            Table: The Table to add.
        """
        assert(isinstance(browser, Browser))
        self._name_map[self._id] = name
        self._browser_map[name] = browser
        self._id = self._id + 1

    def remove_from_name(self, name):
        """Remove the Table with the given name.

        Args:
            name: The Table's name as defined by Table's get_name
                method.

        Raises:
            KeyError: if no Table has the given name.
            ValueError: if there is only one Table.
        """
        if not self._name_map:
            return
        id = next((k for k, v in self._name_map.items() if v == name))
        self.remove_from_id(id)

    def remove_from_id(self, id):
        """Remove the Table with the given id.

        Args:
            id (int): The id as shown by the 'ls' command.

        Raises:
            KeyError: if no Table has the given id.
            ValueError: if there is only one Table.
        """
        assert(type(id) is int)
        self._remove_startup()
        name = self._name_map.pop(id)
        removed_browser = self._browser_map.pop(name)
        self._remove_cleanup(removed_browser)

    def remove_cur(self):
        """Remove the current Table.

        Raises:
            ValueError: if there is only one Table.
        """
        name = self._cur.get_name()
        self.remove_from_name(name)

    # TODO: delete the Tables.  This means disconnecting them from their
    # respective databases.  This might be better suited to another method,
    # like wipe, to use vim parlance.  This method is then analogous to bd.
    # In that case, the id should not be reset.  Also, there might be a need
    # for more dicts, such as for hidden and visible Tables.
    def clear(self):
        """Clear the buffer and reset it to an empty state."""
        self._name_map.clear()
        self._browser_map.clear()
        self._cur = null_browser
        self._prev = null_browser
        self._id = 0
        self._END_ROW = 2

    def _remove_startup(self):
        """Ensure that the last Table is not being removed."""
        if len(self._name_map) == 1:
            raise ValueError

    def _remove_cleanup(self, removed_browser):
        """Set _cur and _prev to proper values.
        
        This method should only be called at the end of a remove method.

        There are four cases when removing, each requiring a different
        course of action.

        1) if removed_browser is _cur and _prev, then assign _cur and _prev
            to another Table.
        2) if removed_browser is only _prev, then assign _prev to _cur.
        3) if removed_browser is only _cur, then assign _cur to _prev.
        4) if removed_browser is neither _prev nor _cur, then _cur and _prev
            stay the same.
        
        Args:
            removed_browser: The Table that has been removed.
        """
        # case 1
        if (removed_browser is self._cur) and (removed_browser is self._prev):
            name = next(self.name_generator())[1]
            self._cur = self._prev = self._browser_map[name]
        # case 2
        elif removed_browser is self._prev:
            self._prev = self._cur
        # case 3
        elif removed_browser is self._cur:
            self._cur = self._prev
        # case 4 is the else clause.  Nothing special needs to be done.
        removed_browser.destroy()
        self._cur.redraw()

    # TODO: Make seperate methods for each parameter.
    def get(self, id=None, name=None):
        """Return the Table with the given id.

        Args:
            id (int): The Table's id as shown by the 'ls' command.

        Raises:
            KeyError: if no Table has the given id.
        """
        """Return the Table with the given name.

        Args:
            name (str): The Table's name as defined by Table's get_name
                method.

        Raises:
            KeyError: if no Table has the given name.
        """
        """Return the currently visible Table."""
        if id is not None:
            name = self._name_map[id]
            return self._browser_map[name]
        elif name is not None:
            return self._browser_map[name]
        else:
            return self._cur

    def set_cur_to_prev(self):
        """Set the current Table to the previous one.

        The new current Table is displayed.

        Nothing is done if the current Table is also the previous one.
        """
        if self._cur is self._prev:
            return
        self.set_cur_from_name(self._prev.get_name())

    def set_cur_from_id(self, id):
        """Set the current Table to the one with the given id.

        The new current Table is displayed.

        Args:
            id (int): The Table's id as shown by the 'ls' command.

        Raises:
            KeyError: If no Table has the given id.
        """
        name = self._name_map[id]
        self.set_cur_from_name(name)

    def set_cur_from_name(self, name):
        """Set the current Table to the one with the given name.

        The new current Table is displayed.

        Args:
            name (str): The Table's name as defined by Table's get_name
                method.

        Raises:
            KeyError: If no Table has the given name.
        """
        if self._prev is null_browser:
            self._prev = self._browser_map[name]
        else:
            self._prev = self._cur
        self._cur = self._browser_map[name]
        self._cur.redraw()

    def _update(self):
        """Write Table ids and names to the pad."""
        if len(self._name_map) > self._END_ROW:
            self._END_ROW = len(self._name_map)
            self._pad.resize(self._END_ROW * 2, curses.COLS)
        row_count = 0
        self._pad.clear()
        for id, name in self._name_map.items():
            self._pad.addstr(row_count, 0, str(id).ljust(4))
            if self._browser_map[name] is self._cur:
                self._pad.addstr(row_count, 6, '%')
            if self._browser_map[name] is self._prev:
                self._pad.addstr(row_count, 7, '#')
            self._pad.addstr(row_count, 8, name)
            self._pad.clrtoeol()
            row_count = row_count + 1

    def redraw(self):
        """Show the buffer list.

        This method draws the buffer list to the screen.  The list
        shows all of the Tables that are currently open.
        """
        """
        Variables:
            top_row: the row in the screen where the top of the pad is
                drawn.
            overflow (boolean): Whether or not the number of Tables is
                more than half the number of rows in the screen.
        """
        self._update()
        top_row = curses.LINES - len(self._name_map) - 2
        overflow = False
        if top_row < 0:
            top_row = int(curses.LINES / 2) - 1
            overflow = True
        self._pad.refresh(0, 0, top_row, 0, curses.LINES - 2, curses.COLS - 1)
        # TODO: This is an extremely poor implementation.  Make a proper
        # handler and have the buffer listen to signals.  Do something similar
        # to how UI handles keys.
        if overflow:
            pad_top_row = 0
            v_range = (curses.LINES - 1) - top_row
            key = 0
            while key != ord('q'):
                key = self._pad.getch()
                if key == ord('j'):
                    pad_top_row = pad_top_row + 1
                    if pad_top_row + v_range > len(self._name_map):
                        pad_top_row = len(self._name_map) - v_range
                elif key == ord('k'):
                    pad_top_row = pad_top_row - 1
                    if pad_top_row < 0:
                        pad_top_row = 0
                self._pad.refresh(pad_top_row, 0, top_row, 0,
                        curses.LINES - 2, curses.COLS - 1)

    def receive_signal(self, signal, args=None):
        """Override singals.Observer."""
        if signal is signals.Signal.SHOW_BUFFERS:
            self.redraw()


class BrowserRegistry:
    """Manage creation and deletion of Tables.

    This class provides static methods for creating and
    removing Tables.

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
    _browser_buffer = None

    @staticmethod
    def get_cur():
        """Will be removed."""
        return BrowserRegistry._cur_browser

    @staticmethod
    def get_buffer():
        if BrowserRegistry._browser_buffer is None:
            BrowserRegistry._browser_buffer = BrowserBuffer()
        return BrowserRegistry._browser_buffer

    @staticmethod
    def get_cur_idx():
        """Will be removed."""
        """Return the index (zero-based) of the current browser.

        Raises:
            IndexError: if _cur_idx is -1, meaning no browsers have
                been created.
        """
        return BrowserRegistry._cur_idx

    @staticmethod
    def get_count():
        """Will be removed."""
        """Return the number of browsers."""
        return len(BrowserRegistry._browser_indexes)

    @staticmethod
    def set_cur(idx):
        """Will be removed"""
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
        BrowserRegistry._cur_browser = BrowserRegistry._browser_indexes[idx]
        BrowserRegistry._cur_idx = idx

    # TODO: Remove the lines that useless things like increment the index.
    @staticmethod
    def create(db_name, table):
        """Create and display a Table.

        The Table is connected to the database 'db_name' and displays
        the table 'table'.  It is added to the table buffer, and then
        is displayed.

        Args:
            db_name (str): The name of the database to connect to.
            table_name (str): The name of the table to display.

        Returns:
            The new Table (or the matching Table if it already exists).

        Raises;
            FileNotFoundError: If the database does not exist.
            ValueError: If the given table does not exist in the
                database.
        """
        name = '{}.{}'.format(db_name, table)
        if BrowserRegistry._browser_buffer is None:
            BrowserRegistry._browser_buffer = BrowserBuffer()
        name_gen = BrowserRegistry._browser_buffer.name_generator()
        for id, browser_name in iter(name_gen):
            if browser_name == name:
                return BrowserRegistry._browser_buffer.get(name=name)
        new_browser = Browser(db_name, table)
        BrowserRegistry._browser_map[name] = new_browser
        BrowserRegistry._browser_indexes.insert(BrowserRegistry._cur_idx + 1,
                                               new_browser)
        #BrowserRegistry.set_cur(BrowserRegistry._cur_idx + 1)
        BrowserRegistry._browser_buffer.add(name, new_browser)
        BrowserRegistry._browser_buffer.get(name=name).create()
        BrowserRegistry._browser_buffer.set_cur_from_name(name)
        return new_browser

    @staticmethod
    def destroy(name=None, idx=None):
        """Close the Table with the given name.

        If the Table to close happens to be the currently visible one,
        then which Table is displayed depends on which of the
        following two cases describes the removed Table:

        1) If the removed Table is both the current and previous Table,
            then the Table displayed is the first one generated by
            BrowserBuffer's name_generator method.
        2) If the removed Table is only the current Table, then the
            previous Table is displayed.

        If the removed Table is neither of these, then the current
        Table continues to be displayed.

        Args:
            name (str): The Table's name as defined by Table's get_name
                method.

        Raises:
            KeyError: If no Table has the given name.
        """
        """Close the Table with the given id.

        See destroy_by_name for information on which Table is
        displayed next.

        Args:
            id (int): The Table's id as shown by the 'ls' command.

        Raises:
            KeyError: If no Table has the given id.
        """
        """Close the currently visible Table.

        See destroy_by_name for information on which Table is
        displayed next.
        """
        if idx:
            name = BrowserRegistry,_browser_indexes[idx].get_name()
        elif name is None:
            name = BrowserRegistry,_browser_indexes[\
                    BrowserRegistry._cur_idx].get_name()
        BrowserRegistry,_browser_map[name].destroy()
        BrowserRegistry._browser_map.pop(name)
        BrowserRegistry._browser_indexes.pop(BrowserRegistry._cur_idx)
        if BrowserRegistry._cur_idx >= len(BrowserRegistry._browser_indexes):
            BrowserRegistry._cur_idx = BrowserRegistry._cur_idx - 1
        elif BrowserRegistry._cur_idx < 0:
            BrowserRegistry._cur_idx = -1

    @staticmethod
    def destroy_all():
        """Close all open Tables."""
        for name, browser in BrowserRegistry._browser_map.items():
            browser.destroy()
        BrowserRegistry._browser_map.clear()
