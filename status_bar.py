import curses
import curses.textpad
import shared

# TODO: no hard coding
class StatusBar:
    """Display information or enter commands.

    The status bar shows information about the program's current state.
    It is also used to write and send commands to the program.
    
    Class Attributes:
        CONFIRM: Show a prompt in confirmation mode.
        ERROR: Show a prompt in error mode.

    Methods:
        edit: Write a command for the user to edit.
        prompt: Show a message.
        create: Setup the status bar.
        update: Redraw the status bar.
        destroy: Close the status bar.
        get_cmd_name: Return the name of the last command entered.
        get_cmd_args: Return the arguements of the last command entered.
    """
    CONFIRM = 1
    ERROR = 2
    BOTTOM = 1
    TOP = 2

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
        if position == StatusBar.TOP:
            self._win = curses.newwin(1, curses.COLS, 0, 0)
            self._scr_row = 0
        else:
            self._win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
            self._scr_row = curses.LINES - 1
        self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
        self._cur_str = ''
        self._last_cmd_name = ''
        self._last_cmd_args = ''
        self._cmd_map = cmd_map
        self._position = position

    def _reposition(self, scr_row, cols):
        self._scr_right_col = cols
        if self._position == StatusBar.TOP:
            return
        else:
            if scr_row - 1 != self._scr_row:
                self._scr_row = scr_row - 1
                self._win = curses.newwin(1, cols, self._scr_row, 0)
                self._text_pad = curses.textpad.Textbox(
                    self._win, insert_mode=True)
                self.update()

    # TODO: this seems useless. update is a better fit for what this
    # tries to do.
    def create(self):
        """Update the status bar string.

        This method updates the string to be displayed in the status bar.
        """
        cur_browser = shared.BrowserFactory.get_cur()
        name = cur_browser.get_name()
        idx = shared.BrowserFactory.get_cur_idx() + 1
        browser_count = shared.BrowserFactory.get_count()
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
            self.prompt('That command does not exist.', StatusBar.ERROR)

    def prompt(self, prompt_str, mode):
        """Show a message.

        Show a message in the status bar.  Depending on the mode,
        different actions will be performed.

        Args:
            prompt_str: The message to display.
            mode: Specifies what actions the status bar should take.

        Modes:
            StatusBar.CONFIRM: The prompt is meant to ask for
                confirmation.  The user must enter a 'y' or 'n',
                and the reply is returned.
            StatusBar.ERROR: The prompt is meant to notify the user
                that an error has occured.

        Returns:
            'y'/'n': If the mode is StatusBar.CONFIRM
            An empty string: If the mode is StatusBar.ERROR
        """
        ret_str = ''
        if mode == StatusBar.CONFIRM:
            self._clear(prompt_str)
            ret_str = 0
            while not (ret_str == ord('y') or ret_str == ord('n')):
                ret_str = self._win.getch()
            self.update()
        elif mode == StatusBar.ERROR:
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

    def on_screen_resize(self, new_rows, new_cols):
        self._reposition(new_rows, new_cols)
        #if self._position == StatusBar.TOP:
            #return
        #if new_rows != self._scr_row:
            #self._scr_row = new_rows - 1
        ## TODO: reformat cur_str
        #if new_cols != self._scr_right_col:
            #self._scr_right_col = new_cols
        #self.update()
