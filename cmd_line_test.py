import curses
import re
import settings.keys
import keymap
import signals
import enums


#send_signal = SendSignal('lol', '', '')
cmd_map = settings.keys.CommandMap.get()
km = settings.keys.CommandLineKeyMap.get()


class CommandLine(signals.Observer):
    def __init__(self):
        self._cmd_line_history = open('cmd_line_history', 'r')
        self._history = []
        for line in self._cmd_line_history:
            self._history.append(line.strip())
        self._cmd_line_history.close()
        self._history_idx = -1
        self._match_gen = None
        self._match_idx = 0
        curses.initscr()
        curses.cbreak()
        curses.noecho()
        self._win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        self._win.keypad(1)
        cmd_map['scroll_up'].register(self)
        cmd_map['scroll_down'].register(self)

    def receive_signal(self, signal, args=None):
        if signal in (enums.Scroll.UP, enums.Scroll.DOWN):
            self._on_scroll(signal)

    def open(self, str=''):
        key = 0
        while key != ord('q'):
            key = self._win.getch()
            row, col = self._win.getyx()
            try:
                cmd = km.get_cmd(key)
                cmd.execute()
                continue
            except KeyError:
                pass
            if key in (curses.KEY_BACKSPACE, curses.KEY_DC):
                self._win.delch(row, col - 1)
                self._match_gen = None
            elif key in (curses.KEY_ENTER, 10, 13):
                line = self._win.instr(0, 0)
                line = line.decode('utf-8').strip()
                self._history.insert(0, line)
                self._win.clear()
                self._history_idx = -1
                self._match_gen = None
            else:
                self._match_gen = None
                self._win.insch(key)
                self._win.move(row, col + 1)

    def _on_scroll(self, direction):
        self._match_gen = None
        if direction is enums.Scroll.UP:
            self._history_idx = self._history_idx + 1
            if self._history_idx >= len(self._history):
                self._history_idx = len(self._history)
            self._win.clear()
            self._win.addstr(0, 0, self._history[self._history_idx])
            self._win.refresh()
            return
        elif direction is enums.Scroll.DOWN:
            self._history_idx = self._history_idx - 1
            if self._history_idx <= -1:
                self._history_idx = -1
            self._win.clear()
            self._win.addstr(0, 0, self._history[self._history_idx])
            return
        elif direction == enums.Scroll.LEFT:
            self._win.move(row, col - 1)
        elif direction == enums.Scroll.RIGHT:
            self._win.move(row, col + 1)
        elif direction == enums.Scroll.PAGE_UP:
            if self._match_gen is None:
                self._match_idx = 0
                line = self._win.instr(0, 0)
                line = line.decode('utf-8').strip()
                pattern = re.compile('^{}'.format(line))
                # A generator would be preferable, but there is no reasonable
                # way to go back, which is needed for Shift+Tab.
                self._match_gen = [s for s in cmd_map.keys() if\
                             pattern.search(s) is not None]
            if self._match_idx >= len(self._match_gen):
                self._match_idx = 0
            match = self._match_gen[self._match_idx]
            self._win.clear()
            self._win.addstr(0, 0, match)
            self._match_idx = (self._match_idx + 1) % len(self._match_gen)
        elif direction == enums.Scroll.PAGE_DOWN:
            if self._match_gen is None:
                self._match_idx = 0
                line = self._win.instr(0, 0)
                line = line.decode('utf-8').strip()
                pattern = re.compile('^{}'.format(line))
                self._match_gen = [s for s in cmd_map.keys() if\
                             pattern.search(s) is not None]
            if self._match_idx < 0:
                self._match_idx = len(self._match_gen) - 1
            match = self._match_gen[self._match_idx]
            self._win.clear()
            self._win.addstr(0, 0, match)
            self._match_idx = (self._match_idx - 1) % len(self._match_gen)

    def destroy(self):
        curses.nocbreak()
        self._win.keypad(0)
        curses.echo()
        curses.endwin()
        cmd_line_history = open('cmd_line_history', 'w')
        for line in self._history:
            cmd_line_history.write(line)
            cmd_line_history.write('\n')
        cmd_line_history.close()


cmd_line = CommandLine()
cmd_line.open()
cmd_line.destroy()
