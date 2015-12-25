import curses
from browser import Browser
from shared import BrowserFactory, StatusBarRegistry, DBRegistry, CopyBuffer,\
        UIRegistry

class Command:
    def __init__(self, name, desc, quantifier=1, **kwargs):
        self._name = name
        self._desc = desc
        self._quantifier = quantifier
        self._args = kwargs

    def execute(self):
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
        cur_status_bar.set_str(str(cur_browser.get_cur_cell()))
        cmd = cur_status_bar.redraw()
        if len(cmd) != 3 or (cmd[1] == cmd[2]):
            return
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'update "{table}" set "{col_name}"="{value}"\
                where "{primary_key}"="{id}"'.format(\
                table=table_name,\
                col_name=cur_browser.get_col_name(),\
                value=cmd[2],\
                primary_key=cur_browser.PRIMARY_KEY,\
                id=cur_browser.get_cur_rowid())
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.update_cur_cell()

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
        cur_browser.update_new_entry()

class DeleteEntry(Command):
    def execute(self):
        cur_browser = BrowserFactory.get_cur()
        browser_name = cur_browser.get_name()
        db_name = browser_name[: browser_name.rfind('.')]
        table_name = browser_name[browser_name.rfind('.') + 1:]
        cur_db = DBRegistry.get_db(db_name)
        s = 'delete from "{table}" where "{prim_key}"="{val}"'.format(\
                table=table_name,
                prim_key=cur_browser.PRIMARY_KEY,
                val=cur_browser.get_cur_rowid())
        cur_db.execute(s)
        cur_db.commit()
        cur_browser.update_del_entry()

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
                val=cur_browser.get_cur_rowid())
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
        cur_browser.update_new_entry()

class NextBrowser(Command):
    def execute(self):
        cur_idx = BrowserFactory.get_cur_idx()
        BrowserFactory.set_cur(cur_idx + 1)
        UIRegistry.get().on_browser_switch()
        StatusBarRegistry.get().on_browser_switch()

class PreviousBrowser(Command):
    def execute(self):
        cur_idx = BrowserFactory.get_cur_idx()
        BrowserFactory.set_cur(cur_idx - 1)
        UIRegistry.get().on_browser_switch()
        StatusBarRegistry.get().on_browser_switch()
