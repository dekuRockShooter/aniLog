import commands
import keymap

class CommandMap:
    cmd_map = {}

    @staticmethod
    def get():
        if CommandMap.cmd_map:
            return CommandMap.cmd_map
        CommandMap.cmd_map = {
            'filter': commands.Filter('', ''),
            'edit': commands.EditCell('', ''),
            'new_entry': commands.NewEntry('', ''),
            'del_entry': commands.DeleteEntry('', ''),
            'sort': commands.Sort('', ''),
            'next_browser': commands.NextBrowser('', ''),
            'prev_browser': commands.PreviousBrowser('', ''),
            'resize': commands.Resize('', ''),
            'new_browser': commands.NewBrowser('', ''),
            'select': commands.Select('', ''),
            }
        return CommandMap.cmd_map


class KeyMap:
    key_map = None

    @staticmethod
    def get():
        if KeyMap.key_map:
            return KeyMap.key_map
        cmd_map = CommandMap.get()
        KeyMap.key_map = keymap.KeyMap(keymap.AniLogKeyParser())
        KeyMap.key_map.add_key('k',commands.ScrollUp('', ''))
        KeyMap.key_map.add_key('j',commands.ScrollDown('', ''))
        KeyMap.key_map.add_key('h',commands.ScrollLeft('', ''))
        KeyMap.key_map.add_key('l',commands.ScrollRight('', ''))
        KeyMap.key_map.add_key('i', cmd_map['new_entry'])
        KeyMap.key_map.add_key('y',commands.CopyEntry('', ''))
        KeyMap.key_map.add_key('p',commands.PasteEntry('', ''))
        KeyMap.key_map.add_key('gt', cmd_map['next_browser'])
        KeyMap.key_map.add_key('gT', cmd_map['prev_browser'])
        KeyMap.key_map.add_key(':',commands.Write('', '', ''))
        KeyMap.key_map.add_key('c',commands.Write('edit %p %v', '', ""))
        KeyMap.key_map.add_key('d',commands.Write('del_entry %p', '', ''))
        KeyMap.key_map.add_key('/',commands.Write('filter ', '', ''))
        KeyMap.key_map.add_key('<Rsz>', cmd_map['resize'])
        return KeyMap.key_map
