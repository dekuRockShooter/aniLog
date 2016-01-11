import curses
import curses.textpad
import browser
import shared
import enums
import settings.keys
import settings.positions as positions
import signals
import cmd_line_test


# TODO: no hard coding
# This class is a mess.  Methods need to be rewritten/removed/implemented
# by CommandLine.
# Give edit, get_cmd_name, and get_cmd_args to CommandLine.
# Split the bar into a StatusBar and a CommandLine.
# Rename create to _reset, update to redraw.
class StatusBar(signals.Observer):
    """Display information about the program's state.

    The status bar shows users information about anything that
    happens in the program: errors, notifications, confirmations,
    and other prompts and messages that provide useful information
    to the user.  It is used to notify users about something that
    they should know.

    Methods:
        edit: depracated.
        prompt: Write a message to the status bar.
        create: Setup the status bar.
        update: Redraw the status bar.
        destroy: Close the status bar.
        get_cmd_name: Return the name of the last command entered.
        get_cmd_args: Return the arguements of the last command entered.
    """
    # TODO: this should be __init__(self).
    def __init__(self, position, cmd_map):
        self._cmd_line = cmd_line_test.CommandLine()
        curses.initscr()
        curses.noecho()
        self._scr_right_col = curses.COLS
        self._scr_row = positions.STATUS_BAR_COORDS[0]
        self._win = curses.newwin(1, curses.COLS - 1, self._scr_row, 0)
        self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
        self._cur_str = ''
        self._last_cmd_name = ''
        self._last_cmd_args = ''
        self._cmd_map = cmd_map

        cmd_map = settings.keys.CommandMap.get()
        cmd_map['next_browser'].register(self)
        cmd_map['prev_browser'].register(self)
        cmd_map['resize'].register(self)

    def _reposition(self, scr_row, cols):
        """Redraw the status bar after resizing the screen."""
        if positions.STATUS_BAR_POSITION == positions.SCREEN_TOP:
            return
        else:
            self._scr_right_col = curses.COLS
            self._scr_row = positions.STATUS_BAR_COORDS[0]
            self._win = curses.newwin(1, curses.COLS - 1, self._scr_row, 0)
            self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
            self.update()

    # TODO: this seems useless. update is a better fit for what this
    # tries to do.  This string should be determined by the user and created
    # by something else.  Then that object should call the prompt method
    # to update the string.
    def create(self):
        """Will be removed."""
        """Update the status bar string.

        This method updates the string to be displayed in the status bar.
        """
        cur_browser = browser.BrowserRegistry.get_cur()
        if cur_browser is None:
            return
        name = cur_browser.get_name()
        idx = browser.BrowserRegistry.get_cur_idx() + 1
        browser_count = browser.BrowserRegistry.get_count()
        self._cur_str = '{}:{}/{}'.format(name, idx, browser_count)

    def update(self):
        """Will be removed."""
        """Redraw the status bar.

        This method redraws the status bar to show the updated default
        message.  For an explanation about the default message, see the
        prompt method.
        """
        self.create()
        self._clear(self._cur_str)

    def destroy(self):
        """Close the status bar."""
        curses.echo()
        self._cmd_line.destroy()

    def _clear(self, new_str=''):
        """Clear the status bar and add a new string.

        Args:
            new_str: The string to display in the status bar.
        """
        self._win.clear()
        self._win.addstr(0, 0, new_str)
        self._win.refresh()

    def edit(self, initial_str=''):
        """Will be removed."""
        """Open the status bar for editing.

        The status bar takes keyboard focus until the user is done
        editing.  The purpose of this method is to allow the user to
        enter a command, which is executed immediately.

        Args:
            initial_str: The string to initialize the status bar with.
                The user is able to edit it.
        """
        self._clear(initial_str)
        curses.curs_set(1)
        #input = self._text_pad.edit().strip()
        input = self._cmd_line.open()
        curses.curs_set(0)
        try:
            arg_idx= input.index(' ')
            self._last_cmd_name = input[: arg_idx]
            self._last_cmd_args = input[arg_idx + 1:]
        except ValueError:
            self._last_cmd_name = input
            self._last_cmd_args = ''
        # TODO: get the command associated with input[0]
        # TODO: get flags
        try:
            self._cmd_map[self._last_cmd_name].execute()
        except KeyError:
            if not self._last_cmd_name:
                self.update()
            else:
                self.prompt("Command '{cmd_name}' does not exist.".format(
                    cmd_name=self._last_cmd_name), enums.Prompt.ERROR)
        self._last_cmd_name = ''
        self._last_cmd_args = ''

    def prompt(self, prompt_str, mode):
        """Show a message.

        Show a message in the status bar.  Depending on the mode,
        different actions will be performed.

        Args:
            prompt_str: The message to display.
            mode: Specifies what actions the status bar should take.
                This can be one of the enumerations in enums.Prompt.

        Returns:
            'y'/'n': If the mode is enums.Prompt.CONFIRM.
            An empty string: If the mode is enums.Prompt.ERROR.
        """
        ret_str = ''
        if mode == enums.Prompt.CONFIRM:
            self._clear(prompt_str)
            ret_str = 0
            while not (ret_str == ord('y') or ret_str == ord('n')):
                ret_str = self._win.getch()
            self.update()
        elif mode == enums.Prompt.ERROR:
            self._clear('ERROR: {}'.format(prompt_str))
        return ret_str

    def get_cmd_name(self):
        """Will be removed."""
        """Return the name of the last command entered."""
        return self._last_cmd_name

    def get_cmd_args(self):
        """Will be removed."""
        """Return the arguments of the last command entered."""
        return self._last_cmd_args

    def scroll(self, direction, quantifier=1):
        pass

    def on_browser_switch(self):
        """Switch to the new browser and display it.

        Update the status bar string and show it.
        """
        self.update()
        self._win.refresh()

    def on_screen_resize(self):
        if positions.STATUS_BAR_POSITION == positions.SCREEN_TOP:
            return
        else:
            self._scr_right_col = curses.COLS
            self._scr_row = positions.STATUS_BAR_COORDS[0]
            self._win = curses.newwin(1, curses.COLS - 1, self._scr_row, 0)
            self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
            self.update()

    def receive_signal(self, signal, args):
        if signal is signals.Signal.SCREEN_RESIZED:
            self.on_screen_resize()
        elif signal is signals.Signal.BROWSER_SWITCHED:
            self.on_browser_switch()


class StatusBarRegistry:
    """Manage the status bar.

    This class provides static methods for creating, accessing, and
    removing the status bar.

    Methods:
        get: Return the status bar.
        create: Create the status bar.
        destroy: Destroy the status bar.
    """
    _status_bar = None

    @staticmethod
    def get():
        """Return the status bar."""
        return StatusBarRegistry._status_bar

    @staticmethod
    def create(position, cmd_map):
        """Create the status bar.

        Returns:
            The status bar.
        """
        if not StatusBarRegistry._status_bar:
            StatusBarRegistry._status_bar = StatusBar(position, cmd_map)
        return StatusBarRegistry._status_bar

    @staticmethod
    def destroy():
        """Close the status bar."""
        StatusBarRegistry._status_bar.destroy()

    @staticmethod
    def destroy_all():
        """Same as destroy."""
        StatusBarRegistry.destroy()
