import commands
import keymap
import enums

class CommandMap:
    cmd_map = {}

    @staticmethod
    def get():
        if CommandMap.cmd_map:
            return CommandMap.cmd_map
        clone_cmd = commands.CloneTable('', '')
        CommandMap.cmd_map = {
            'filter': commands.Filter('', ''),
            'update': commands.EditCell('', ''),
            'new_entry': commands.NewEntry('', ''),
            'del_entry': commands.DeleteEntry('', ''),
            'sort': commands.Sort('', ''),
            'next_browser': commands.NextBrowser('', ''),
            'prev_browser': commands.PreviousBrowser('', ''),
            'resize': commands.Resize('', ''),
            'edit': commands.NewBrowser('', ''),
            'select': commands.Select('', ''),
            'ls': commands.ShowBuffers('', ''),
            'clone': clone_cmd,
            'clone!': clone_cmd
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
        KeyMap.key_map.add_key('k', commands.Scroll(
            enums.Scroll.UP, '', ''))
        KeyMap.key_map.add_key('j', commands.Scroll(
            enums.Scroll.DOWN, '', ''))
        KeyMap.key_map.add_key('h', commands.Scroll(
            enums.Scroll.LEFT, '', ''))
        KeyMap.key_map.add_key('l', commands.Scroll(
            enums.Scroll.RIGHT, '', ''))
        KeyMap.key_map.add_key('gg', commands.Scroll(
            enums.Scroll.HOME, '', ''))
        KeyMap.key_map.add_key('G', commands.Scroll(
            enums.Scroll.END, '', ''))
        KeyMap.key_map.add_key('<Ctrl-b>', commands.Scroll(
            enums.Scroll.PAGE_UP, '', ''))
        KeyMap.key_map.add_key('<Ctrl-f>', commands.Scroll(
            enums.Scroll.PAGE_DOWN, '', ''))
        KeyMap.key_map.add_key('^', commands.Scroll(
            enums.Scroll.H_HOME, '', ''))
        KeyMap.key_map.add_key('$', commands.Scroll(
            enums.Scroll.H_END, '', ''))
        KeyMap.key_map.add_key('i', cmd_map['new_entry'])
        KeyMap.key_map.add_key('yy',commands.CopyEntry('', ''))
        KeyMap.key_map.add_key('p',commands.PasteEntry('', ''))
        KeyMap.key_map.add_key('gt', cmd_map['next_browser'])
        KeyMap.key_map.add_key('gT', cmd_map['prev_browser'])
        KeyMap.key_map.add_key(':',commands.Write('', '', ''))
        KeyMap.key_map.add_key('c',commands.Write('update %p %v', '', ""))
        KeyMap.key_map.add_key('dd',commands.Write('del_entry %p', '', ''))
        KeyMap.key_map.add_key('/',commands.Write('filter ', '', ''))
        KeyMap.key_map.add_key('<Rsz>', cmd_map['resize'])
        return KeyMap.key_map
