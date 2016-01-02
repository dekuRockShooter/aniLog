import curses
import curses.textpad
import browser
import ui
import shared
import enums
import settings.keys
import settings.positions as positions
import signals

# TODO: no hard coding
class StatusBar(signals.Observer):
    """Display information or enter commands.

    The status bar shows information about the program's current state.
    It is also used to write and send commands to the program.
    
    Methods:
        edit: Write a command for the user to edit.
        prompt: Show a message.
        create: Setup the status bar.
        update: Redraw the status bar.
        destroy: Close the status bar.
        get_cmd_name: Return the name of the last command entered.
        get_cmd_args: Return the arguements of the last command entered.
    """
    def __init__(self, position, cmd_map):
        """Constructor.

        Define the placement of the status bar.  The status bar always
        starts at column zero in the screen.

        Args:
            position: Where to place the status bar.  Valid values are
                StatusBar.TOP and StatusBar.BOTTOM for the top and
                bottom of the screen, respectively.
            cmd_map: The map from command names to Command objects.
        """
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
        ui.UIRegistry.get().register(self)
        settings.keys.cmd_map['next_browser'].register(self)
        settings.keys.cmd_map['prev_browser'].register(self)

    def _reposition(self, scr_row, cols):
        if positions.STATUS_BAR_POSITION == positions.SCREEN_TOP:
            return
        else:
            self._scr_right_col = curses.COLS
            self._scr_row = positions.STATUS_BAR_COORDS[0]
            self._win = curses.newwin(1, curses.COLS - 1, self._scr_row, 0)
            self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
            self.update()

    # TODO: this seems useless. update is a better fit for what this
    # tries to do.
    def create(self):
        """Update the status bar string.

        This method updates the string to be displayed in the status bar.
        """
        cur_browser = browser.BrowserRegistry.get_cur()
        name = cur_browser.get_name()
        idx = browser.BrowserRegistry.get_cur_idx() + 1
        browser_count = browser.BrowserRegistry.get_count()
        self._cur_str = '{}:{}/{}'.format(name, idx, browser_count)

    def update(self):
        """Update the status bar.

        This method updates the status bar to show the current values
        of each field.
        """
        self.create()
        self._clear(self._cur_str)

    def destroy(self):
        """Close the status bar."""
        curses.echo()

    def _clear(self, new_str=''):
        """Clear the status bar and add a new string.

        Args:
            new_str: The string to display in the status bar.
        """
        self._win.clear()
        self._win.addstr(0, 0, new_str)
        self._win.refresh()

    def edit(self, initial_str=''):
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
        input = self._text_pad.edit().strip()
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
            self.update()
        except KeyError:
            self.prompt('That command does not exist.', enums.Prompt.ERROR)

    def prompt(self, prompt_str, mode):
        """Show a message.

        Show a message in the status bar.  Depending on the mode,
        different actions will be performed.

        Args:
            prompt_str: The message to display.
            mode: Specifies what actions the status bar should take.

        Modes:
            enums.Prompt.CONFIRM: The prompt is meant to ask for
                confirmation.  The user must enter a 'y' or 'n',
                and the reply is returned.
            enums.Prompt.ERROR: The prompt is meant to notify the user
                that an error has occured.

        Returns:
            'y'/'n': If the mode is enums.Prompt.CONFIRM
            An empty string: If the mode is enums.Prompt.ERROR
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
        """Return the name of the last command entered."""
        return self._last_cmd_name

    def get_cmd_args(self):
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

        The status bar is created if it has not been already.  The
        status bar is returned.
        """
        if not StatusBarRegistry._status_bar:
            StatusBarRegistry._status_bar = StatusBar(position, cmd_map)
        return StatusBarRegistry._status_bar

    @staticmethod
    def destroy():
        """Destroy (close) the status bar."""
        StatusBarRegistry._status_bar.destroy()

    @staticmethod
    def destroy_all():
        StatusBarRegistry.destroy()


if __name__ == '__main__':
    print('Not a script.')
