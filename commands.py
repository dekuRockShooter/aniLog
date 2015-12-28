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
"""
import curses
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


class EditCell(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        cur_status_bar = StatusBarRegistry.get()
        cur_value = str(cur_browser.get_cur_cell())
        cmd = cur_status_bar.edit(cur_value)
        new_value = ' '.join(cmd)
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'update "{table}" set "{col_name}"="{value}"\
                where "{primary_key}"="{id}"'.format(\
                table=table_name,\
                col_name=cur_browser.get_col_name(),\
                value=new_value,\
                primary_key=cur_browser.PRIMARY_KEY,\
                id=cur_browser.get_prim_key())
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.on_entry_updated()



class NewEntry(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'insert into "{table}" default values'.format(table=table_name)
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.on_entry_inserted()

class DeleteEntry(Command):
    def execute(self):
        cur_status_bar = StatusBarRegistry.get()
        cur_status_bar.set_str('Confirm deletion (y//n): ')
        reply = cur_status_bar.redraw()[-1]
        if reply not in ('y', 'Y'):
            return
        cur_browser = BrowserFactory.get_cur()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'delete from "{table}" where "{prim_key}"="{val}"'.format(\
                table=table_name,
                prim_key=cur_browser.PRIMARY_KEY,
                val=cur_browser.get_prim_key())
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.on_entry_deleted()


class CopyEntry(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'select * from "{table}" where "{prim_key}"="{val}"'.format(\
                table=table_name,
                prim_key=cur_browser.PRIMARY_KEY,
                val=cur_browser.get_prim_key())
        row =  list(cur_db.execute(s)[0])
        row[0] = 'null' # for autoincrementing the rowid
        for idx, val in enumerate(row[1:], 1):
            val = str(val)
            if val.startswith('"') and val.endswith('"'):
                continue
            row[idx] = '{}{}{}'.format('"', val, '"')
        CopyBuffer.set(CopyBuffer.DEFAULT_KEY, tuple(row))


class PasteEntry(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        row = ','.join(CopyBuffer.get(CopyBuffer.DEFAULT_KEY))
        s = 'insert into "{table}" values ({val})'.format(\
                table=table_name,
                val=str(row))
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.on_entry_inserted()


class NextBrowser(Command):
    def execute(self):
        cur_idx = BrowserFactory.get_cur_idx()
        try:
            BrowserFactory.set_cur(cur_idx + 1)
        except IndexError:
            BrowserFactory.set_cur(0)
        UIRegistry.get().on_browser_switch()
        StatusBarRegistry.get().on_browser_switch()


class PreviousBrowser(Command):
    def execute(self):
        cur_idx = BrowserFactory.get_cur_idx()
        try:
            if cur_idx == 0:
                raise IndexError
            BrowserFactory.set_cur(cur_idx - 1)
        except IndexError:
            BrowserFactory.set_cur(BrowserFactory.get_count() - 1)
        UIRegistry.get().on_browser_switch()
        StatusBarRegistry.get().on_browser_switch()


class Filter(Command):
    def execute(self):
        cur_status_bar = StatusBarRegistry.get()
        cur_status_bar.set_str(':filter ')
        search_term = ' '.join(cur_status_bar.redraw()[1:])
        cur_browser = BrowserFactory.get_cur()
        col_name = cur_browser.get_col_name()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'select * from "{table}" where "{col_name}" like \'%{val}%\''.format(\
                table=table_name,
                col_name=col_name,
                val=search_term)
        cur_browser.on_new_query(cur_db.execute(s))


class Sort(Command):
    ASC='asc'
    DES='desc'

    def __init__(self, name, desc, quantifier=1, direction=None, **kwargs):
        super(Sort, self).__init__(name, desc, quantifier, **kwargs)
        self._direction = direction or Sort.ASC

    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        col_name = cur_browser.get_col_name()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'select * from "{table}" order by "{col_name}" {dir}'.format(\
                table=table_name,
                col_name=col_name,
                dir=self._direction)
        cur_browser.on_new_query(cur_db.execute(s))
