import commands
import keymap

cmd_map = {
    'filter': commands.Filter('filter',
                              'Show entries that match the search term.'),
    'edit': commands.EditCell('edit', 'Edit a cell.'),
    'new_entry': commands.NewEntry('new_entry', 'Insert a new entry.'),
    'del_entry': commands.DeleteEntry('del_entry', 'Delete an entry.'),
    'sort': commands.Sort('del_entry', 'Delete an entry.'),
    'next_browser': commands.NextBrowser('del_entry', 'Delete an entry.'),
    'prev_browser': commands.PreviousBrowser('del_entry', 'Delete an entry.'),
    'resize': commands.Resize('resize', 'Delete an entry.'),
    }
key_map = keymap.KeyMap(keymap.AniLogKeyParser())
# Command settings
# Keymap settings
key_map.add_key('k',commands.ScrollUp('scroll_up', 'Scroll one line up.'))
key_map.add_key('j',commands.ScrollDown('scroll_down',
    'Scroll one line down.'))
key_map.add_key('h',commands.ScrollLeft('scroll_left',
    'Scroll one column left.'))
key_map.add_key('l',commands.ScrollRight('scroll_right',
    'Scroll one column right,'))
key_map.add_key('i', cmd_map['new_entry'])
key_map.add_key('y',commands.CopyEntry('copy_entry', 'Copy an entry'))
key_map.add_key('p',commands.PasteEntry('paste_entry', 'Paste an entry'))
key_map.add_key('gt', cmd_map['next_browser'])
key_map.add_key('gT', cmd_map['prev_browser'])
key_map.add_key(':',commands.Write('', 'open_console',
    'Open console for editing.'))
key_map.add_key('c',commands.Write('edit %p %v', 'edit_cell',
    "Edit the current cell's value."))
key_map.add_key('d',commands.Write('del_entry %p', 'del_entry',
    'Delete an entry'))
key_map.add_key('/',commands.Write('filter ', 'del_entry',
    'Delete an entry'))
key_map.add_key('<Rsz>', cmd_map['resize'])
