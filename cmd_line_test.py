import curses
import re
import settings.keys
import keymap
import signals
import enums


class InputBar(signals.Observer):
    """An input bar with input history and tab completion.

    Methods:
        open: Open the bar for editing.
        destroy: Destroy the bar.

    Inherited Methods:
        receive_signal: Override signals.Observer.
    """
    def __init__(self):
        try:
            self._cmd_line_history = open('cmd_line_history', 'r')
        except FileNotFoundError:
            self._cmd_line_history = open('cmd_line_history', 'w')
            self._cmd_line_history.close()
            self._cmd_line_history = open('cmd_line_history', 'r')
        self._history = []
        for line in self._cmd_line_history:
            self._history.insert(0, line.strip())
        self._cmd_line_history.close()
        self._history_idx = -1
        self._match_gen = None
        self._match_idx = 0
        self._last_char_idx = 0
        self._is_open = False
        curses.initscr()
        curses.cbreak()
        curses.noecho()
        self._win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        self._win.keypad(1)
        self._key_map = settings.keys.CommandLineKeyMap.get()
        cmd_map = settings.keys.CommandMap.get()
        cmd_map['scroll_up'].register(self)
        cmd_map['scroll_down'].register(self)
        cmd_map['scroll_pgup'].register(self)
        cmd_map['scroll_pgdown'].register(self)
        cmd_map['scroll_left'].register(self)
        cmd_map['scroll_right'].register(self)
        cmd_map['del_char'].register(self)
        cmd_map['press_enter'].register(self)
        cmd_map['resize'].register(self)

    def receive_signal(self, signal, args=None):
        """Override signals.Subject."""
        if signal in (enums.Scroll.UP, enums.Scroll.DOWN,
                      enums.Scroll.LEFT, enums.Scroll.RIGHT,
                      enums.Scroll.PAGE_UP, enums.Scroll.PAGE_DOWN):
            self._on_scroll(signal)
        elif signal is signals.Signal.DELETE_CHAR:
            self._on_del_char()
        elif signal is signals.Signal.PRESS_ENTER:
            self._on_press_enter()
        elif signal is signals.Signal.SCREEN_RESIZED:
            self._on_screen_resize()

    def open(self, initial_str=''):
        """Open the command line.

        This opens the command line so that the user can enter a
        command.  The command is appended to the file
        'cmd_line_history'.

        Args:
            initial_str: A string to write to the command line when
                it opens.

        Returns:
            The typed string.
        """
        self._is_open = True
        history_len = len(self._history)
        key = 0
        curses.curs_set(1)
        self._win.clear()
        self._win.addstr(0, 0, initial_str)
        while self._is_open:
            key = self._win.getch()
            if key == 27: # Either alt or esc.
                self._win.nodelay(1)
                key = self._win.getch()
                self._win.nodelay(0)
                if key == -1: # esc
                    self._is_open = False
                    continue
            row, col = self._win.getyx()
            try:
                cmd = self._key_map.get_cmd(key)
            except KeyError:
                self._match_gen = None
                self._win.insch(key)
                self._win.move(row, col + 1)
                self._last_char_idx = self._last_char_idx + 1
                continue
            cmd.execute()
        curses.curs_set(0)
        return self._close(history_len)

    def destroy(self):
        """Close the command line and end curses."""
        curses.nocbreak()
        self._win.keypad(0)
        curses.echo()
        curses.endwin()

    def _close(self, history_len):
        """Append the command to the history file.

        If no command was entered, then nothing is written.

        Args:
            history_len: The length of self._history when the command
                line was opened.

        Returns:
            The contents of the command line.
        """
        if history_len == len(self._history):
            return ''
        cmd_line_history = open('cmd_line_history', 'a')
        cmd_line_history.write(self._history[0] + '\n')
        cmd_line_history.close()
        return self._history[0]

    def _on_screen_resize(self):
        self._win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)

    def _on_press_enter(self):
        """Add the command line contents to the history array.

        If nothing was entered, then the history array is unmodified.
        """
        line = self._win.instr(0, 0)
        line = line.decode('utf-8').strip()
        if line:
            self._history.insert(0, line)
            self._win.clear()
        self._history_idx = -1
        self._match_gen = None
        self._is_open = False

    def _on_del_char(self):
        """Delete the character before the cursor."""
        row, col = self._win.getyx()
        if col == 0:
            return
        self._win.delch(row, col - 1)
        self._match_gen = None
        self._last_char_idx = self._last_char_idx - 1

    def _on_scroll(self, direction):
        # Scrolling up or down moves backward or forward, respectively,
        # in the history.
        # Scrolling page up or page down moves backward or forward,
        # respectively, in the completion list.
        # Scrolling left or right moves the cursor to the left or
        # right, respectively.
        row, col = self._win.getyx()
        if direction is enums.Scroll.UP:
            if not self._history:
                return
            self._match_gen = None
            self._history_idx = self._history_idx + 1
            if self._history_idx >= len(self._history):
                self._history_idx = len(self._history) - 1
            self._win.clear()
            self._win.addstr(0, 0, self._history[self._history_idx])
            return
        elif direction is enums.Scroll.DOWN:
            if not self._history:
                return
            self._match_gen = None
            self._history_idx = self._history_idx - 1
            if self._history_idx <= -1:
                self._history_idx = 0
            self._win.clear()
            self._win.addstr(0, 0, self._history[self._history_idx])
            return
        elif direction is enums.Scroll.LEFT:
            if col == 0:
                return
            self._win.move(row, col - 1)
        elif direction is enums.Scroll.RIGHT:
            if col == self._last_char_idx:
                return
            self._win.move(row, col + 1)
        elif direction == enums.Scroll.PAGE_UP:
            if self._match_gen is None:
                cmd_map = settings.keys.CommandMap.get()
                self._match_idx = 0
                line = self._win.instr(0, 0)
                line = line.decode('utf-8').strip()
                pattern = re.compile('^{}'.format(line))
                # A generator would be preferable, but there is no reasonable
                # way to go back, which is needed for Shift+Tab.
                self._match_gen = [s for s in cmd_map.keys() if\
                             pattern.search(s) is not None]
                if not self._match_gen:
                    self._match_gen = None
                    return
            if self._match_idx >= len(self._match_gen):
                self._match_idx = 0
            match = self._match_gen[self._match_idx]
            self._win.clear()
            self._win.addstr(0, 0, match)
            self._match_idx = (self._match_idx + 1) % len(self._match_gen)
        elif direction == enums.Scroll.PAGE_DOWN:
            if self._match_gen is None:
                cmd_map = settings.keys.CommandMap.get()
                self._match_idx = 0
                line = self._win.instr(0, 0)
                line = line.decode('utf-8').strip()
                pattern = re.compile('^{}'.format(line))
                self._match_gen = [s for s in cmd_map.keys() if\
                             pattern.search(s) is not None]
                if not self._match_gen:
                    self._match_gen = None
                    return
            if self._match_idx < 0:
                self._match_idx = len(self._match_gen) - 1
            match = self._match_gen[self._match_idx]
            self._win.clear()
            self._win.addstr(0, 0, match)
            self._match_idx = (self._match_idx - 1) % len(self._match_gen)


class CommandLine:
    def __init__(self):
        self._input_bar = InputBar()
        self._cmd_args = ''
        self._cmd_name = ''

    def open(self, initial_str):
        input_str = self._input_bar.open(initial_str)
        if not input_str:
            return
        try:
            arg_idx= input_str.index(' ')
            self._cmd_name = input_str[: arg_idx]
            self._cmd_args = input_str[arg_idx + 1:]
        except ValueError:
            self._cmd_name = input_str
            self._cmd_args = ''
        # TODO: get the command associated with input_str[0]
        # TODO: get flags
        cmd_map = settings.keys.CommandMap.get()
        try:
            cmd_map[self._cmd_name].execute()
        except KeyError:
            pass
            #self.prompt("Command '{cmd_name}' does not exist.".format(
                #cmd_name=self._last_cmd_name), enums.Prompt.ERROR)
        self._cmd_name = ''
        self._cmd_args = ''

    def get_cmd_args(self):
        return self._cmd_args

    def get_cmd_name(self):
        return self._cmd_name

    def destroy(self):
        self._input_bar.destroy()


class CommandLineRegistry:
    _cmd_map = None

    @staticmethod
    def get():
        if CommandLineRegistry._cmd_map is None:
            CommandLineRegistry._cmd_map = CommandLine()
        return CommandLineRegistry._cmd_map

    @staticmethod
    def destroy():
        if CommandLineRegistry._cmd_map is not None:
            CommandLineRegistry._cmd_map.destroy()


#cmd_line = CommandLine()
#s = cmd_line.open()
#cmd_line.destroy()
#print(s)
