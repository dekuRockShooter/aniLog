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
import signals
from status_bar import StatusBar
from browser import Browser
from shared import BrowserFactory, StatusBarRegistry, DBRegistry, CopyBuffer,\
        UIRegistry


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
        cur_browser = BrowserFactory.get_cur()
        cur_browser.scroll(Browser.DOWN, self._quantifier)


class ScrollUp(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        cur_browser.scroll(Browser.UP, self._quantifier)


class ScrollLeft(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        cur_browser.scroll(Browser.LEFT, self._quantifier)


class ScrollRight(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        cur_browser.scroll(Browser.RIGHT, self._quantifier)


class EditCell(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        new_val = ''
        if not args:
            stat_bar.prompt('Usage: edit primary_key_val new_cell_value',
                              StatusBar.ERROR)
            return
        try:
            sep_idx = args.index(' ')
            new_val = args[sep_idx + 1:]
        except ValueError:
            sep_idx = len(args)
        prim_key = args[: sep_idx]
        cur_browser = BrowserFactory.get_cur()
        db_name = cur_browser.get_db_name()
        cur_db = DBRegistry.get_db(db_name)
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
        cur_browser = BrowserFactory.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = DBRegistry.get_db(db_name)
        s = 'insert into "{table}" default values'.format(table=table_name)
        cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_INSERTED)


class DeleteEntry(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        if not args:
            stat_bar.prompt('Usage: del_entry primary_key_val',
                            StatusBar.ERROR)
            return
        reply = stat_bar.prompt('Confirm deletion (y/n): ',
                                      StatusBar.CONFIRM)
        if reply == ord('n'):
            return
        cur_browser = BrowserFactory.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = DBRegistry.get_db(db_name)
        s = 'delete from "{table}" where "{prim_key}"="{val}"'.format(
                table=table_name,
                prim_key=cur_browser.PRIMARY_KEY,
                val=args)
        cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_DELETED)


class CopyEntry(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = DBRegistry.get_db(db_name)
        s = 'select * from "{table}" where "{prim_key}"="{val}"'.format(
                table=table_name,
                prim_key=cur_browser.PRIMARY_KEY,
                val=cur_browser.get_prim_key())
        row =  list(cur_db.execute(s)[0])
        row[0] = 'null' # for autoincrementing the rowid
        for idx, val in enumerate(row[1:], 1):
            val = str(val)
            # Make entries that have spaces work properly when pasting.
            if val.startswith('"') and val.endswith('"'):
                continue
            row[idx] = '{}{}{}'.format('"', val, '"')
        CopyBuffer.set(CopyBuffer.DEFAULT_KEY, tuple(row))


class PasteEntry(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = DBRegistry.get_db(db_name)
        row = ','.join(CopyBuffer.get(CopyBuffer.DEFAULT_KEY))
        s = 'insert into "{table}" values ({val})'.format(
                table=table_name,
                val=str(row))
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.on_entry_inserted()


class NextBrowser(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        cur_idx = BrowserFactory.get_cur_idx()
        try:
            BrowserFactory.set_cur(cur_idx + 1)
        except IndexError:
            BrowserFactory.set_cur(0)
        self.emit(signals.Signal.BROWSER_SWITCHED)


class PreviousBrowser(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        cur_idx = BrowserFactory.get_cur_idx()
        try:
            if cur_idx == 0:
                raise IndexError
            BrowserFactory.set_cur(cur_idx - 1)
        except IndexError:
            BrowserFactory.set_cur(BrowserFactory.get_count() - 1)
        self.emit(signals.Signal.BROWSER_SWITCHED)


class Filter(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = StatusBarRegistry.get()
        arg = stat_bar.get_cmd_args()
        cur_browser = BrowserFactory.get_cur()
        col_name = cur_browser.get_col_name()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = DBRegistry.get_db(db_name)
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
        cur_browser = BrowserFactory.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        cur_db = DBRegistry.get_db(db_name)
        col_name = ''
        direction = self._direction
        if self._direction is None:
            stat_bar = StatusBarRegistry.get()
            args = stat_bar.get_cmd_args()
            try:
                sep_idx = args.index(' ')
            except ValueError:
                sep_idx = len(args)
            direction = args[: sep_idx]
            if direction not in (Sort.ASC, Sort.DES):
                stat_bar.prompt('Usage: sort asc|desc [column_name]',
                                StatusBar.ERROR)
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
        stat_bar = StatusBarRegistry.get()
        try:
            cmd_str = self._expand(self._cmd_str)
        except ValueError as err:
            stat_bar.prompt(str(err), StatusBar.ERROR)
            return
        stat_bar.edit(cmd_str)

    def _expand(self, cmd_str):
        """Expand all the macros.

        Raises:
            ValueError: if cmd_str contains invalid macros.
        """
        browser = BrowserFactory.get_cur()
        possible_macro = False
        expanded_str = []
        for letter in cmd_str:
            if possible_macro:
                if letter == 'p':
                    letter = str(browser.get_prim_key())
                elif letter == 'c':
                    letter = browser.get_col_name()
                elif letter == 'v':
                    letter = str(browser.get_cur_cell())
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
