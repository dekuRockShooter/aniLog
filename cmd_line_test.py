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
        def f():
            return (x for x in range(0))
        self._cmd_arg_iter = _CommandArgIter('.', '.', f)
        curses.initscr()
        curses.cbreak()
        curses.noecho()
        self._win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
        self._win.keypad(1)
        self._key_map = settings.keys.CommandLineKeyMap.get()
        cmd_map = settings.keys.CommandMap.get()
        #cmd_map['scroll_up'].register(self)
        #cmd_map['scroll_down'].register(self)
        #cmd_map['scroll_pgup'].register(self)
        #cmd_map['scroll_pgdown'].register(self)
        #cmd_map['scroll_left'].register(self)
        #cmd_map['scroll_right'].register(self)
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
        self._win.move(0, 0)
        self._win.clrtoeol()
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
        self._win.move(0, 0)
        self._win.clrtoeol()
        self._win.refresh()
        self._last_char_idx = 0
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
        self._win.keypad(1)

    def _on_press_enter(self):
        """Add the command line contents to the history array.

        If the line is empty or is the same as the most recently
        entered line, then the history array is unmodified.
        """
        line = self._win.instr(0, 0)
        line = line.decode('utf-8').strip()
        if line and ((not self._history) or (line != self._history[0])):
            self._history.insert(0, line)
            self._win.move(0, 0)
            self._win.clrtoeol()
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
            def f():
                if self._history_idx >= len(self._history):
                    self._history_idx = len(self._history) - 1
            self._on_up_down(direction, f)
            return
        elif direction is enums.Scroll.DOWN:
            def f():
                if self._history_idx <= -1:
                    self._history_idx = 0
            self._on_up_down(direction, f)
            return
        elif direction is enums.Scroll.LEFT:
            if col == 0:
                return
            self._win.move(row, col - 1)
        elif direction is enums.Scroll.RIGHT:
            if col >= self._last_char_idx:
                self._win.move(row, self._last_char_idx)
                return
            self._win.move(row, col + 1)
        elif direction is enums.Scroll.PAGE_UP:
            def f():
                if self._match_idx >= len(self._match_gen):
                    self._match_idx = 0
            self._on_pgup_pgdwn(direction, f)
        elif direction is enums.Scroll.PAGE_DOWN:
            def f():
                if self._match_idx < 0:
                    self._match_idx = len(self._match_gen) - 1
            self._on_pgup_pgdwn(direction, f)

    def _on_up_down(self, direction, check_bounds):
        """Run code common to UP and DOWN."""
        if not self._history:
            return
        if direction is enums.Scroll.UP:
            self._history_idx = self._history_idx + 1
        elif direction is enums.Scroll.DOWN:
            self._history_idx = self._history_idx - 1
        else:
            return
        self._match_gen = None
        check_bounds()
        hist_str = self._history[self._history_idx]
        self._win.move(0, 0)
        self._win.clrtoeol()
        self._win.addstr(0, 0, hist_str)
        self._last_char_idx = len(hist_str)

    def _on_pgup_pgdwn(self, direction, check_bounds):
        """Run code common to PAGE_UP and PAGE_DOWN."""
        if direction is enums.Scroll.PAGE_UP:
            step = 1
        elif direction is enums.Scroll.PAGE_DOWN:
            step = -1
        else:
            return
        # Tab through the Command's arguments.
        cmd_line_contents = self._win.instr(0, 0, self._last_char_idx)
        cmd_line_contents = cmd_line_contents.decode('utf-8')
        arg_idx = cmd_line_contents.find(' ')
        if arg_idx > 0:
            cmd_map = settings.keys.CommandMap.get()
            cmd_name = cmd_line_contents[: arg_idx]
            cmd_args = cmd_line_contents[arg_idx + 1:].lstrip()
            if cmd_name == self._cmd_arg_iter.cmd_name and\
                cmd_args.find(self._cmd_arg_iter.base_arg) != -1:
                    pass
            else:
                try:
                    completion_list = cmd_map[cmd_name].tab(cmd_args)
                    self._cmd_arg_iter = _CommandArgIter(cmd_name, cmd_args,
                                                        completion_list)
                except KeyError:
                    return
            try:
                match = str(next(self._cmd_arg_iter))
            except StopIteration:
                match = cmd_args
            self._win.move(0, 0)
            self._win.clrtoeol()
            self._win.addstr(0, 0, cmd_name + ' ' + match)
            self._last_char_idx = len(cmd_name) + len(match)
            self._match_gen = None
            return
        # Tab through Commands.
        if self._match_gen is None:
            cmd_map = settings.keys.CommandMap.get()
            self._match_idx = 0
            line = self._win.instr(0, 0)
            line = line.decode('utf-8').strip()
            pattern = re.compile('^{}'.format(line))
            # A generator is preferable, but those can't be traversed
            # backward, so unfortunately, we need a list.
            self._match_gen = [s for s in cmd_map.keys() if\
                         pattern.search(s) is not None]
            if not self._match_gen:
                self._match_gen = None
                return
        check_bounds()
        match = self._match_gen[self._match_idx]
        self._win.move(0, 0)
        self._win.clrtoeol()
        self._win.addstr(0, 0, match)
        self._match_idx = (self._match_idx + step) % len(self._match_gen)
        self._last_char_idx = len(match)


class _CommandArgIter:
    """Iterate through a Command's tab completion list.

    Attributes:
        cmd_name: The name of the Command.
        base_arg: The string that was in the command line when tab
            completion was requested.  This string is given to a
            Command object so that it can decide what the tab
            completion list consists of.
    """
    """
    Private Attributes:
        completion_gen: A generator that generates the items in the
            completion list.
        iter: The iterator over the completion list.
    """
    def __init__(self, cmd_name, base_arg, completion_gen):
        self.cmd_name = cmd_name
        self.base_arg = base_arg
        self._completion_gen = completion_gen
        self._iter = iter(self._completion_gen())

    def __next__(self):
        try:
            return next(self._iter)
        except StopIteration:
            self._iter = iter(self._completion_gen())
        except RuntimeError:
            self._iter = iter(self._completion_gen())
        return next(self._iter)


class CommandLine:
    """Run commands entered in the InputBar.

    Methods:
        open: Open the command line for editing.
        get_cmd_args: Return the arguments for the command.
        get_cmd_name: Return the name of the command.
        destroy: See InputBar's destroy method.
        receive_signal: See InputBar's receive_signal method.
    """
    def __init__(self):
        self._input_bar = InputBar()
        self._cmd_args = ''
        self._cmd_name = ''

    def open(self, initial_str):
        """Open the command line and execute a command.

        Args:
            initial_str: The string to initialize the command line with.
        """
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
        self._cmd_name = ''
        self._cmd_args = ''

    def get_cmd_args(self):
        """Return the arguments of the command.

        Returns:
            A string of the contents after the command's name.
        """
        return self._cmd_args

    def get_cmd_name(self):
        """Return the name of the command."""
        return self._cmd_name

    def destroy(self):
        """Functionally equivalent to InputBar.destroy."""
        self._input_bar.destroy()

    def receive_signal(self, signal):
        """Functionally equivalent to InputBar.receive_signal."""
        self._input_bar.receive_signal(signal)


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
