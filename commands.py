"""Define commands.

    This module holds various commands to use in aniLog.

    Classes:
        Command: The interface for all commands.
        ScrollDown: scroll down in the browser.
        ScrollUp: scroll up in the browser.
        ScrollLeft: scroll left in the browser.
        ScrollRight: scroll right in the browser.
        EditCell: edit the current cell's value.
        NewEntry: Add a new entry to the browser.
        DeleteEntry: Delete the current entry.
        CopyEntry: copy the current entry.
        PasteEntry: paste a copied entry into the current browser.
        NextBrowser: switch to the next browser.
        PreviousBrowser: switch to the previous browser.
        Filter: Show entries that match a search term.
        Sort: Sort the entries.
        Write: Write a string to the command line.
"""
import curses
import signals
import enums
import browser
import status_bar
import settings.positions as positions
import shared


class Command:
    """Command interface.

    Abstract methods:
        execute: Execute the command.
    """
    def __init__(self, name, desc, quantifier=1, **kwargs):
        self._name = name
        self._desc = desc
        self._quantifier = quantifier
        self._args = kwargs

    def execute(self):
        """Execute the command.

        This method is meant to be overriden.
        """
        raise NotImplementedError('This method must be overriden.')
        pass


class ScrollDown(Command):
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        cur_browser.scroll(enums.Scroll.DOWN, self._quantifier)


class ScrollUp(Command):
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        cur_browser.scroll(enums.Scroll.UP, self._quantifier)


class ScrollLeft(Command):
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        cur_browser.scroll(enums.Scroll.LEFT, self._quantifier)


class ScrollRight(Command):
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        cur_browser.scroll(enums.Scroll.RIGHT, self._quantifier)


class EditCell(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        new_val = ''
        if not args:
            stat_bar.prompt('Usage: edit primary_key_val new_cell_value',
                              enums.Prompt.ERROR)
            return
        try:
            sep_idx = args.index(' ')
            new_val = args[sep_idx + 1:]
        except ValueError:
            sep_idx = len(args)
        prim_key = args[: sep_idx]
        cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        s = 'update "{table}" set "{col_name}"="{value}"\
                where "{primary_key}"="{id}"'.format(
                table=cur_browser.get_table_name(),
                col_name=cur_browser.get_col_name(),
                value=new_val,
                primary_key=cur_browser.PRIMARY_KEY,
                id=prim_key)
        cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_UPDATED)
        cur_browser.on_entry_updated()


class NewEntry(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        s = 'insert into "{table}" default values'.format(table=table_name)
        cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_INSERTED)


class DeleteEntry(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        if not args:
            stat_bar.prompt('Usage: del_entry primary_key_val',
                            enums.Prompt.ERROR)
            return
        reply = stat_bar.prompt('Confirm deletion (y/n): ',
                                      enums.Prompt.CONFIRM)
        if reply == ord('n'):
            return
        cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        rowids = shared.SelectBuffer.get()
        if not rowids:
            rowids = [args]
        for id in rowids:
            s = 'delete from "{table}" where "{prim_key}"="{val}"'.format(
                    table=table_name,
                    prim_key=cur_browser.PRIMARY_KEY,
                    val=id)
            cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_DELETED)
        shared.SelectBuffer.set([])


class CopyEntry(Command):
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        rowids = shared.SelectBuffer.get()
        entries = []
        if not rowids:
            rowids = [str(cur_browser.get_prim_key())]
        for id in rowids:
            s = 'select * from "{table}" where "{prim_key}"="{val}"'.format(
                    table=table_name,
                    prim_key=cur_browser.PRIMARY_KEY,
                    val=id)
            row = list(cur_db.execute(s)[0])
            row[0] = 'null' # for autoincrementing the rowid
            for idx, val in enumerate(row[1:], 1):
                val = str(val)
                # Make entries that have spaces work properly when pasting.
                if val.startswith('"') and val.endswith('"'):
                    continue
                row[idx] = '{}{}{}'.format('"', val, '"')
            entries.append(tuple(row))
        shared.CopyBuffer.set(shared.CopyBuffer.DEFAULT_KEY, entries)


class PasteEntry(Command):
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        rows = shared.CopyBuffer.get(shared.CopyBuffer.DEFAULT_KEY)
        for row in rows:
            values = ','.join(row)
            s = 'insert into "{table}" values ({val})'.format(
                    table=table_name,
                    val=values)
            cur_db.execute(s)
        cur_db.commit()
        cur_browser.on_entry_inserted()


class NextBrowser(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        cur_idx = browser.BrowserRegistry.get_cur_idx()
        try:
            browser.BrowserRegistry.set_cur(cur_idx + 1)
        except IndexError:
            browser.BrowserRegistry.set_cur(0)
        self.emit(signals.Signal.BROWSER_SWITCHED)


class PreviousBrowser(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        cur_idx = browser.BrowserRegistry.get_cur_idx()
        try:
            if cur_idx == 0:
                raise IndexError
            browser.BrowserRegistry.set_cur(cur_idx - 1)
        except IndexError:
            browser.BrowserRegistry.set_cur(browser.BrowserRegistry.get_count() - 1)
        self.emit(signals.Signal.BROWSER_SWITCHED)


class NewBrowser(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        try:
            db_name, table_name = self._parse(args)
        except ValueError as err:
            stat_bar.prompt(str(err), enums.Prompt.ERROR)
            return
        try:
            brw = browser.BrowserRegistry.create(db_name, table_name)
        except FileNotFoundError as err:
            stat_bar.prompt(str(err), enums.Prompt.ERROR)
            return
        except ValueError as err:
            stat_bar.prompt(str(err), enums.Prompt.ERROR)
            return
        brw.create()

    def _parse(self, args):
        stat_bar = status_bar.StatusBarRegistry.get()
        arg_list = args.split()
        if len(arg_list) < 2:
            raise ValueError('Usage: db_name table_name')
        # db name and table name contain no spaces.
        if len(arg_list) == 2:
            return arg_list
        # at least one arg is enclosed in quotes.
        sep_idx = args.find('"', 1)
        if sep_idx  == -1:
            raise ValueError('Names with spaces go in quotes.')
        if args[sep_idx + 1] == ' ':
            sep_idx = sep_idx + 1
        elif args[sep_idx - 1] != ' ':
            raise ValueError('Usage: db_name table_name')
        return [args[: sep_idx], args[sep_idx:].strip()]


class Filter(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        arg = stat_bar.get_cmd_args()
        cur_browser = browser.BrowserRegistry.get_cur()
        col_name = cur_browser.get_col_name()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        s = 'select * from "{table}" where "{col_name}" like \'%{val}%\''.\
                format(table=table_name,
                       col_name=col_name,
                       val=arg)
        rows = cur_db.execute(s)
        self.emit(signals.Signal.NEW_QUERY, rows)


class Sort(Command, signals.Subject):
    ASC='asc'
    DES='desc'

    def __init__(self, name, desc, quantifier=1, direction=None, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)
        self._direction = direction

    # TODO: This is a little more complicated than it should be.  A possibly
    # better implementation would be to remove the static variables ASC and
    # DES and just have then be command line arguments.  The code would be
    # much easier to follow.
    def execute(self):
        cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = shared.DBRegistry.get_db(db_name)
        col_name = ''
        direction = self._direction
        if self._direction is None:
            stat_bar = status_bar.StatusBarRegistry.get()
            args = stat_bar.get_cmd_args()
            try:
                sep_idx = args.index(' ')
            except ValueError:
                sep_idx = len(args)
            direction = args[: sep_idx]
            if direction not in (Sort.ASC, Sort.DES):
                stat_bar.prompt('Usage: sort asc|desc [column_name]',
                                enums.Prompt.ERROR)
                return
            col_name = args[sep_idx + 1:]
        if not col_name:
            col_name = cur_browser.get_col_name()
        s = 'select * from "{table}" order by "{col_name}" {dir}'.format(
                table=table_name,
                col_name=col_name,
                dir=direction)
        rows = cur_db.execute(s)
        self.emit(signals.Signal.NEW_QUERY, rows)


class Write(Command):
    """Write a string to the command line.

    This is a command to write a string to the command line so that
    it can be edited and run.  The string can consist of macros that
    allow easy access to helpful information that can be used as
    arguments to commands.
    """
    def __init__(self, cmd_str, name, desc, quantifier=1, **kwargs):
        """Constructor.

        Args:
            cmd_str: The string to write to the command line.  It
                contains characters and macros.

        Macros:
            %p: the primary key value of the current entry.
            %c: the name of the current column.
            %v: the value of the current cell.
            %%: a literal '%'.
        """
        super(Write, self).__init__(name, desc, quantifier, **kwargs)
        self._cmd_str = cmd_str

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        try:
            cmd_str = self._expand(self._cmd_str)
        except ValueError as err:
            stat_bar.prompt(str(err), enums.Prompt.ERROR)
            return
        stat_bar.edit(cmd_str)

    def _expand(self, cmd_str):
        """Expand all the macros.

        Raises:
            ValueError: if cmd_str contains invalid macros.
        """
        cur_browser = browser.BrowserRegistry.get_cur()
        possible_macro = False
        expanded_str = []
        for letter in cmd_str:
            if possible_macro:
                if letter == 'p':
                    letter = str(cur_browser.get_prim_key())
                elif letter == 'c':
                    letter = cur_browser.get_col_name()
                elif letter == 'v':
                    letter = str(cur_browser.get_cur_cell())
                elif letter == '%':
                    pass
                else:
                    raise ValueError('Unknown macro: %{}'.format(letter))
                expanded_str.append(letter)
                possible_macro = False
            elif letter == '%':
                possible_macro = True
            else:
                expanded_str.append(letter)
        return ''.join(expanded_str)


class Resize(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        self._set_coords()
        self.emit(signals.Signal.SCREEN_RESIZED)

    def _set_coords(self):
        curses.update_lines_cols()
        if positions.STATUS_BAR_POSITION == positions.SCREEN_TOP:
            positions.STATUS_BAR_COORDS = (0, 0)
            positions.BROWSER_UPPER_LEFT_COORDS = (1, 0)
            positions.BROWSER_BOTTOM_RIGHT_COORDS = (curses.LINES - 1,
                                                    curses.COLS - 1)
        else:
            positions.STATUS_BAR_COORDS = (curses.LINES - 1, 0)
            positions.BROWSER_UPPER_LEFT_COORDS = (0, 0)
            positions.BROWSER_BOTTOM_RIGHT_COORDS = (curses.LINES - 2,
                                                    curses.COLS - 1)


class Select(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        rowids = self._parse_args(args)
        shared.SelectBuffer.set(rowids)
        self.emit(signals.Signal.ENTRIES_SELECTED)

    def _parse_args(self, arg_str):
        if not arg_str:
            return []
        rowids = []
        beg_idx = 0
        arg_str_iter = iter(enumerate(arg_str))
        for end_idx, letter in arg_str_iter:
            if letter.isdigit():
                continue
            elif letter == ',':
                rowid = arg_str[beg_idx : end_idx]
                if rowid.isdigit():
                    rowids.append(rowid)
                    beg_idx = end_idx + 1
                else:
                    raise ValueError('Not an integer: {}'.format(rowid))
            elif letter == '-':
                max_rowid_end = arg_str.find(',', end_idx)
                if max_rowid_end == -1:
                    max_rowid_end = len(arg_str)
                min_rowid = arg_str[beg_idx : end_idx]
                max_rowid = arg_str[end_idx + 1 : max_rowid_end]
                if min_rowid.isdigit() and max_rowid.isdigit():
                    id_interval =\
                        [str(x) for x in
                         range(int(min_rowid), int(max_rowid) + 1)]
                    rowids.extend(id_interval)
                    # There are no more numbers to get.
                    if max_rowid_end == len(arg_str):
                        return rowids
                    # Move to the first comma.
                    while end_idx != max_rowid_end:
                        end_idx, letter = next(arg_str_iter)
                    beg_idx = end_idx + 1
                else:
                    raise ValueError('Not an integer: {}'.format(rowid))
            else:
                raise ValueError('Invalid syntax.')
        # Don't forget to get the last number.
        rowid = arg_str[beg_idx :]
        rowids.append(rowid)
        return rowids
