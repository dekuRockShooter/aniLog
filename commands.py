"""Define commands.

    This module holds various commands to use in aniLog.

    Classes:
        Command: The interface for all commands.
        Scroll: Scroll the browser.
        Update: edit the current cell's value.
        Insert: Add a new entry to the browser.
        Delete: Delete the current entry.
        Copy: copy the current entry.
        Paste: paste a copied entry into the current browser.
        NextTable: switch to the next browser.
        PreviousTable: switch to the previous browser.
        Clone: Copy a table's schema.
        RemoveTable: Remove a Table from the buffer.
        SwitchTable: Switch Tables.
        Edit: Edit a Table.
        Filter: Show entries that match a search term.
        Sort: Sort the entries.
        Write: Write a string to the command line.
        Resize: Send a signal to resize the screen.
        Select: Select (highlight) rows.
        ShowBuffers: Show a list of open Tables.
        SaveSession: Save the current session.
        LoadSession: Load a session.
"""
import json
import curses
import re
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


# TODO: emit a signal and remove the Browser reference.
class Scroll(Command, signals.Subject):
    def __init__(self, direction, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)
        self._direction = direction

    def execute(self):
        #cur_browser = browser.BrowserRegistry.get_cur()
        buffer = browser.BrowserRegistry.get_buffer()
        #self.emit(signals.Signal.Scroll, self._direction)
        if buffer is None:
            return
        cur_browser = buffer.get()
        cur_browser.scroll(self._direction, self._quantifier)


class Update(Command, signals.Subject):
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
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        db_name = cur_browser.get_db_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
        s = 'update "{table}" set "{col_name}"="{value}"\
                where "{primary_key}"="{id}"'.format(
                table=cur_browser.get_table_name(),
                col_name=cur_browser.get_cur_col_name(),
                value=new_val,
                primary_key=cur_browser.PRIMARY_KEY,
                id=prim_key)
        cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_UPDATED)


# TODO: The table created requires a restart to display.
class Clone(Command, signals.Subject):
    """Clone a table.

    clone tbl makes an empty table name tbl with the same schema as the
        current table.
    clone! tbl copies all or selected rows from the current table to
        the new table named tbl.
    """
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        rowids = shared.SelectBuffer.get()
        stat_bar = status_bar.StatusBarRegistry.get()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
        clone_table_name = stat_bar.get_cmd_args()
        if not clone_table_name:
            return
        # New blank table with the same schema as the original table.
        s = 'select sql from sqlite_master where\
                type="table" and name="{original_table}"'.format(
                        original_table=table_name)
        schema = cur_db.execute(s)[0][0]
        s = schema.replace(table_name, clone_table_name, 1)
        cur_db.execute(s)
        if stat_bar.get_cmd_name().endswith('!'):
            s = 'insert into "{clone}" select * from "{original}"'.format(
                    clone=clone_table_name,
                    original=table_name)
            if rowids:
                where_clause = ' where rowid in ({selected_ids})'.format(
                        selected_ids=','.join(rowids))
                s += where_clause
            cur_db.execute(s)
        cur_db.commit()
        #self.emit(signals.Signal.ENTRY_INSERTED)


class Insert(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        #cur_browser = browser.BrowserRegistry.get_cur()
        stat_bar = status_bar.StatusBarRegistry.get()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
        s = 'insert into "{table}" default values'.format(table=table_name)
        cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_INSERTED)
        #cur_browser.redraw()


class Delete(Command, signals.Subject):
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
        #cur_browser = browser.BrowserRegistry.get_cur()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
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


class Copy(Command):
    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        #cur_browser = browser.BrowserRegistry.get_cur()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
        rowids = shared.SelectBuffer.get()
        entries = []
        if not rowids:
            rowids = [str(cur_browser.get_cur_row_pks())]
        s = 'select * from "{table}" where rowid in ({selected_ids})'.format(
                table=table_name,
                selected_ids=','.join(rowids))
        rows = cur_db.execute(s)
        for row_tuple in rows:
            # Convert to a list to be able to format entries.
            row = list(row_tuple)
            row[0] = 'null' # for autoincrementing the rowid
            for idx, val in enumerate(row[1:], 1):
                if val is None:
                    val = ''
                else:
                    val = str(val)
                # Make entries that have spaces work properly when pasting.
                if val.startswith('"') and val.endswith('"'):
                    continue
                row[idx] = '"{}"'.format(val)
            entries.append(tuple(row))
        shared.CopyBuffer.set(shared.CopyBuffer.DEFAULT_KEY, entries)


class Paste(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
        rows = shared.CopyBuffer.get(shared.CopyBuffer.DEFAULT_KEY)
        for row in rows:
            values = ','.join(row)
            s = 'insert into "{table}" values ({val})'.format(
                    table=table_name,
                    val=values)
            cur_db.execute(s)
        cur_db.commit()
        self.emit(signals.Signal.ENTRY_INSERTED)


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


class RemoveTable(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        buffer = browser.BrowserRegistry.get_buffer()
        args = stat_bar.get_cmd_args()
        try:
            if not args:
                buffer.remove_cur()
                return
            elif args.isdigit():
                buffer.remove_by_id(int(args))
                return
        except KeyError:
            pass
        except ValueError:
            stat_bar.prompt('Cannot remove last table.', enums.Prompt.ERROR)
            return
        # TODO: put this in its own function to prevent code duplication.
        # Also, for some reason, buffer.remove_from_name(name) does not
        # work.  Instead, it raises a KeyError.
        try:
            pattern = re.compile(args)
            name_gen = buffer.name_generator()
            for id, name in iter(name_gen):
                if pattern.search(name) is not None:
                    buffer.remove_by_id(id)
                    return
        except KeyError:
            stat_bar.prompt('No matching table found.', enums.Prompt.ERROR)
        # TODO: Use/make a more appropriate error.
        except ValueError:
            stat_bar.prompt('Cannot remove last table.', enums.Prompt.ERROR)


class SwitchTable(Command, signals.Subject):
    """Switch to another table in the buffer.

    Usage:
        b id
        b regex
        There is ambiguity if the regex is a number.  First, it is
        treated as an id.  If no matching id is found, then it is
        treated as a regex.
    """
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        buffer = browser.BrowserRegistry.get_buffer()
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        if self._switch_to_prev(stat_bar, args):
            buffer.set_cur_to_prev()
            return
        if not args:
            stat_bar.prompt('usage: b id/regex', enums.Prompt.ERROR)
            return
        try:
            buffer.set_cur_from_id(int(args))
        except KeyError:
            pass
        except ValueError:
            pass
        try:
            pattern = re.compile(args)
            name_gen = buffer.name_generator()
            for id, name in iter(name_gen):
                if pattern.search(name) is not None:
                    buffer.set_cur_from_name(name)
                    return
        except KeyError:
            stat_bar.prompt('No matching table found.', enums.Prompt.ERROR)

    def _switch_to_prev(self, stat_bar, args):
        if not args and stat_bar.get_cmd_name().endswith('#'):
            return True
        elif (len(args) == 1) and (args[0] == '#'):
            return True
        else:
            return False


# TODO: usage: edit db table.  At the moment, this opens a new table
# as well as switches to an existing table.  A better implementation would
# be to split these behaviors into two seperate commands.  Also, edit db *
# breaks the command; no more tables can be added (switching works fine).
class Edit(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        buffer = browser.BrowserRegistry.get_buffer()
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        name = ''
        names = []
        db_name = ''
        table_names = []
        table_name = ''
        try:
            names = self._parse(args)
            if names[0] is None:
                raise ValueError('usage: edit db table')
        except ValueError as err:
            stat_bar.prompt(str(err), enums.Prompt.ERROR)
            return
        # Open a new buffer with the given database and table.
        if names[1] != '*':
            db_name = names[0]
            table_names.append((names[1],))
        elif names[1] == '*':
            db_name = names[0]
            new_db = shared.DBRegistry.create(db_name)
            new_db.connect()
            table_names = new_db.get_tables()
        for name in table_names:
            try:
                table_name = name[0]
                brw = browser.BrowserRegistry.create(db_name, table_name)
            except FileNotFoundError as err:
                stat_bar.prompt(str(err), enums.Prompt.ERROR)
                return
            except ValueError as err:
                stat_bar.prompt(str(err), enums.Prompt.ERROR)
                return
        buffer = browser.BrowserRegistry.get_buffer()
        buffer.set_cur_from_name(table_name)

    def _parse(self, args):
            """Return a combination of db name, table name, and id.

            Returns:
                A list with three elements.  The first and second
                elements are the database and table name, respectively.
                The third element is None.

            Raises:
                ValueError: if the arguments have invalid syntax.
            """
            names = []
            self._parse_helper(names, args, 0)
            if len(names) != 3:
                raise ValueError('usage: edit db table')
            return names

    def _parse_helper(self, names, args, beg_idx):
        """Split the string into two arguments.

        The arguments are separated by a space.  An argument needs to
        be enclosed in either double or single quotes if it contains
        any spaces, otherwise, the quotes are not necessary.
        """
        if args == '':
            names.append(None)
            return
        name_end = -1
        name = ''
        if args[0] in ('"', "'"):
            if args[beg_idx] == '"':
                name_end = args.find('"', beg_idx + 1)
            else:
                name_end = args.find("'", beg_idx + 1)
            if name_end == -1:
                raise ValueError('Missing closing quotes.')
            beg_idx = beg_idx + 1
        else:
            name_end = args.find(' ', 1)
            if name_end == -1:
                name_end = len(args)
        name = args[beg_idx : name_end]
        names.append(name)
        self._parse_helper(names, args[name_end + 1:].strip(), 0)
        if len(names) > 3:
            raise ValueError('Syntax error.')


class Filter(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        stat_bar = status_bar.StatusBarRegistry.get()
        arg = stat_bar.get_cmd_args()
        #cur_browser = browser.BrowserRegistry.get_cur()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        col_name = cur_browser.get_cur_col_name()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
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
        #cur_browser = browser.BrowserRegistry.get_cur()
        stat_bar = status_bar.StatusBarRegistry.get()
        cur_browser = browser.BrowserRegistry.get_buffer().get()
        db_name = cur_browser.get_db_name()
        table_name = cur_browser.get_table_name()
        try:
            cur_db = shared.DBRegistry.get_db(db_name)
        except KeyError:
            stat_bar.prompt('No connection to the database.',
                              enums.Prompt.ERROR)
            return
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
            col_name = cur_browser.get_cur_col_name()
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
        #cur_browser = browser.BrowserRegistry.get_cur()
        buffer = browser.BrowserRegistry.get_buffer()
        if not buffer:
            return ''
        cur_browser = buffer.get()
        possible_macro = False
        expanded_str = []
        for letter in cmd_str:
            if possible_macro:
                if letter == 'p':
                    letter = str(cur_browser.get_cur_row_pks())
                elif letter == 'c':
                    letter = cur_browser.get_cur_col_name()
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
        # TODO: This doesn't do anything.  For the intended effect, check
        # if the current table's database is connected to.
        if not rowids:
            stat_bar.prompt('Nothing to select.', enums.Prompt.ERROR)
            return
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


class ShowBuffers(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        self.emit(signals.Signal.SHOW_BUFFERS)


class SaveSession(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        buffer = browser.BrowserRegistry.get_buffer()
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        table_name = ''
        db_name = ''
        if not args:
            stat_bar.prompt('usage: mksession session_name',
                    enums.Prompt.ERROR)
            return
        if buffer is None:
            stat_bar.prompt('Cannot save an empty session.',
                    enums.Prompt.ERROR)
            return
        session = open(args, 'w')
        for name, table in iter(buffer.table_generator()):
            table_name = table.get_table_name()
            db_name = table.get_db_name()
            json.dump((db_name, table_name), session)
            session.write('\n')
        session.close()
        #self.emit(signals.Signal.SHOW_BUFFERS)


class LoadSession(Command, signals.Subject):
    def __init__(self, name, desc, quantifier=1, **kwargs):
        Command.__init__(self, name, desc, quantifier, **kwargs)
        signals.Subject.__init__(self)

    def execute(self):
        all_tables_loaded = True
        buffer = browser.BrowserRegistry.get_buffer()
        stat_bar = status_bar.StatusBarRegistry.get()
        args = stat_bar.get_cmd_args()
        table_name = ''
        db_name = ''
        if not args:
            stat_bar.prompt('usage: ldsession session_name',
                    enums.Prompt.ERROR)
            return
        try:
            session = open(args, 'r')
        except FileNotFoundError as err:
            stat_bar.prompt(str(err), enums.Prompt.ERROR)
            return
        browser.BrowserRegistry.destroy_all()
        if buffer is not None:
            buffer.clear()
        for line in session:
            try:
                browser.BrowserRegistry.create(*(json.loads(line)))
            except ValueError:
                all_tables_loaded = False
            except FileNotFoundError as err:
                stat_bar.prompt(str(err), enums.Prompt.ERROR)
                break
        if not all_tables_loaded:
            stat_bar.prompt('Some tables could not be loaded.',
                            enums.Prompt.ERROR)
        session.close()
