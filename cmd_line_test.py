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
        cmd_map['scroll_pgup'].register(self)
        cmd_map['scroll_pgdown'].register(self)
        cmd_map['scroll_left'].register(self)
        cmd_map['scroll_right'].register(self)
        cmd_map['del_char'].register(self)
        cmd_map['press_enter'].register(self)

    def receive_signal(self, signal, args=None):
        if signal in (enums.Scroll.UP, enums.Scroll.DOWN,
                      enums.Scroll.LEFT, enums.Scroll.RIGHT,
                      enums.Scroll.PAGE_UP, enums.Scroll.PAGE_DOWN):
            self._on_scroll(signal)
        elif signal is signals.Signal.DELETE_CHAR:
            self._on_del_char()
        elif signal is signals.Signal.PRESS_ENTER:
            self._on_press_enter()

    def open(self, str=''):
        key = 0
        while key != -1:
            key = self._win.getch()
            if key == 27: # Either alt or esc.
                self._win.nodelay(1)
                key = self._win.getch()
                self._win.nodelay(0)
                if key == -1: # esc
                    continue
            row, col = self._win.getyx()
            try:
                cmd = km.get_cmd(key)
            except KeyError:
                self._match_gen = None
                self._win.insch(key)
                self._win.move(row, col + 1)
                continue
            cmd.execute()

    def _on_press_enter(self):
        line = self._win.instr(0, 0)
        line = line.decode('utf-8').strip()
        self._history.insert(0, line)
        self._win.clear()
        self._history_idx = -1
        self._match_gen = None

    def _on_del_char(self):
        row, col = self._win.getyx()
        self._win.delch(row, col - 1)
        self._match_gen = None

    def _on_scroll(self, direction):
        row, col = self._win.getyx()
        if direction is enums.Scroll.UP:
            self._match_gen = None
            self._history_idx = self._history_idx + 1
            if self._history_idx >= len(self._history):
                self._history_idx = len(self._history)
            self._win.clear()
            self._win.addstr(0, 0, self._history[self._history_idx])
            return
        elif direction is enums.Scroll.DOWN:
            self._match_gen = None
            self._history_idx = self._history_idx - 1
            if self._history_idx <= -1:
                self._history_idx = -1
            self._win.clear()
            self._win.addstr(0, 0, self._history[self._history_idx])
            return
        elif direction is enums.Scroll.LEFT:
            self._win.move(row, col - 1)
        elif direction is enums.Scroll.RIGHT:
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
