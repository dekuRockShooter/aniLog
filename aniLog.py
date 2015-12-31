from ui import UI
import commands
import keymap
import shared
from status_bar import StatusBar

key_map = keymap.KeyMap(keymap.AniLogKeyParser())
# Load settings
# Sizes and position settings
STATUS_BAR_POSITION = StatusBar.BOTTOM
COL_WIDTHS = [3,20,4,4,10,10,3,10,20]
# Database settings
DEFAULT_DB_NAME = 'Sybil.db'
# Command settings
cmd_map = {
    'filter': commands.Filter('filter',
                              'Show entries that match the search term.'),
    'edit': commands.EditCell('edit', 'Edit a cell.'),
    'new_entry': commands.NewEntry('new_entry', 'Insert a new entry.'),
    'del_entry': commands.DeleteEntry('del_entry', 'Delete an entry.'),
    'sort': commands.Sort('del_entry', 'Delete an entry.'),
    }
# Keymap settings
key_map.add_key('k',commands.ScrollUp('scroll_up', 'Scroll one line up.'))
key_map.add_key('j',commands.ScrollDown('scroll_down',
    'Scroll one line down.'))
key_map.add_key('h',commands.ScrollLeft('scroll_left',
    'Scroll one column left.'))
key_map.add_key('l',commands.ScrollRight('scroll_right',
    'Scroll one column right,'))
key_map.add_key('i',commands.NewEntry('new_entry', 'Create a new entry'))
key_map.add_key('y',commands.CopyEntry('copy_entry', 'Copy an entry'))
key_map.add_key('p',commands.PasteEntry('paste_entry', 'Paste an entry'))
key_map.add_key('gt',commands.NextBrowser('next_browser',
    'Go to the next browser'))
key_map.add_key('gT',commands.PreviousBrowser('previous_browser',
    'Go to the previous browser'))
key_map.add_key('sa',commands.Sort('sort_asc', 
    'Sort in ascending order based on the current column.',
    direction=commands.Sort.ASC))
key_map.add_key('sd',commands.Sort('sort_dec',
    'Sort in descending order based on the current column.',
    direction=commands.Sort.DES))
key_map.add_key(':',commands.Write('', 'open_console',
    'Open console for editing.'))
key_map.add_key('c',commands.Write('edit %p %v', 'edit_cell',
    "Edit the current cell's value."))
key_map.add_key('d',commands.Write('del_entry %p', 'del_entry',
    'Delete an entry'))
key_map.add_key('/',commands.Write('filter ', 'del_entry',
    'Delete an entry'))

# Set coordinates
if STATUS_BAR_POSITION == StatusBar.TOP:
    BROWSER_UPPER_LEFT_COORDS = (1, 0)
    BROWSER_BOTTOM_RIGHT_COORDS = (13, 80)
else:
    BROWSER_UPPER_LEFT_COORDS = (0, 0)
    BROWSER_BOTTOM_RIGHT_COORDS = (12, 80)

# Create widgets.
b1 = shared.BrowserFactory.create(BROWSER_UPPER_LEFT_COORDS,
                                  BROWSER_BOTTOM_RIGHT_COORDS,
                                  COL_WIDTHS,
                                  DEFAULT_DB_NAME,
                                  'watching')
b2 = shared.BrowserFactory.create(BROWSER_UPPER_LEFT_COORDS,
                                  BROWSER_BOTTOM_RIGHT_COORDS,
                                  COL_WIDTHS,
                                  DEFAULT_DB_NAME,
                                  'backlog')
b3 = shared.BrowserFactory.create(BROWSER_UPPER_LEFT_COORDS,
                                  BROWSER_BOTTOM_RIGHT_COORDS,
                                  COL_WIDTHS,
                                  DEFAULT_DB_NAME,
                                  'completed')
b1.create()
b2.create()
b3.create()
b1.redraw()
shared.BrowserFactory.set_cur(0)
shared.StatusBarRegistry.create(STATUS_BAR_POSITION, cmd_map).update()
shared.UIRegistry.create(key_map)
ui = shared.UIRegistry.get()
ui.create()
ui.get_key()
shared.UIRegistry.destroy()
