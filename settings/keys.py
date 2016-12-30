import commands
import keymap
import enums
import signals


class CommandMap:
    cmd_map = {}

    @staticmethod
    def get():
        if CommandMap.cmd_map:
            return CommandMap.cmd_map
        clone_cmd = commands.Clone('', '')
        CommandMap.cmd_map = {
            'filter': commands.Filter('', ''),
            'update': commands.Update('', ''),
            'increment': commands.Increment('', ''),
            'new_entry': commands.Insert('', ''),
            'del_entry': commands.Delete('', ''),
            'sort': commands.Sort('', ''),
            'next_browser': commands.NextBrowser('', ''),
            'prev_browser': commands.PreviousBrowser('', ''),
            'resize': commands.Resize('', ''),
            'edit': commands.Edit('', ''),
            'select': commands.Select('', ''),
            'ls': commands.ShowBuffers('', ''),
            'clone': clone_cmd,
            'clone!': clone_cmd,
            'bd': commands.RemoveTable('', ''),
            'b': commands.SwitchTable('', ''),
            'b#': commands.SwitchTable('', ''),
            'mksession': commands.SaveSession('', ''),
            'ldsession': commands.LoadSession('', ''),
            'paste': commands.Paste('', ''),
            'del_char': commands.SendSignal(signals.Signal.DELETE_CHAR,'',''),
            'press_enter': commands.SendSignal(signals.Signal.PRESS_ENTER,
                                               '', ''),
            }
        return CommandMap.cmd_map


class CommandLineKeyMap:
    key_map = None

    @staticmethod
    def get():
        if CommandLineKeyMap.key_map:
            return CommandLineKeyMap.key_map
        cmd_map = CommandMap.get()
        CommandLineKeyMap.key_map = keymap.KeyMap(keymap.AniLogKeyParser())
        CommandLineKeyMap.key_map.add_key('<Ctrl-p>',
                commands.CmdLineScroll(enums.Scroll.UP, '', ''))
        CommandLineKeyMap.key_map.add_key('<Ctrl-n>',
                commands.CmdLineScroll(enums.Scroll.DOWN, '', ''))
        CommandLineKeyMap.key_map.add_key('<Left>',
                commands.CmdLineScroll(enums.Scroll.LEFT, '', ''))
        CommandLineKeyMap.key_map.add_key('<Right>',
                commands.CmdLineScroll(enums.Scroll.RIGHT, '', ''))
        CommandLineKeyMap.key_map.add_key('<S-Tab>',
                commands.CmdLineScroll(enums.Scroll.PAGE_UP, '', ''))
        CommandLineKeyMap.key_map.add_key('<Tab>',
                commands.CmdLineScroll(enums.Scroll.PAGE_DOWN, '', ''))
        CommandLineKeyMap.key_map.add_key('<BS>',cmd_map['del_char'])
        # Whenever there is an <Enter>, there must be a <C-m> and <C-j>.
        # This is a law of curses.
        CommandLineKeyMap.key_map.add_key('<Enter>',cmd_map['press_enter'])
        CommandLineKeyMap.key_map.add_key('<Ctrl-m>',cmd_map['press_enter'])
        CommandLineKeyMap.key_map.add_key('<Ctrl-j>',cmd_map['press_enter'])
        return CommandLineKeyMap.key_map


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
        KeyMap.key_map.add_key('yy', commands.Copy('', ''))
        KeyMap.key_map.add_key('p',cmd_map['paste'])
        KeyMap.key_map.add_key('gt', cmd_map['next_browser'])
        KeyMap.key_map.add_key('gT', cmd_map['prev_browser'])
        KeyMap.key_map.add_key(':',commands.Write('', '', ''))
        KeyMap.key_map.add_key('cc',commands.Write('update %p %v', '', ""))
        KeyMap.key_map.add_key('C',commands.Write('update %p ', '', ""))
        KeyMap.key_map.add_key('dd',commands.Write('del_entry %p', '', ''))
        KeyMap.key_map.add_key('/',commands.Write('filter ', '', ''))
        KeyMap.key_map.add_key('<Rsz>', cmd_map['resize'])
        KeyMap.key_map.add_key('v', cmd_map['select'])
        KeyMap.key_map.add_key('++', cmd_map['increment'])
        return KeyMap.key_map
