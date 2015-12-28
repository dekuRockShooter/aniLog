import curses
import curses.textpad
import shared

# TODO: no hard coding
class StatusBar:
    """Display information or enter commands.

    The status bar shows information about the program's current state.
    It is also used to write and send commands to the program.
    
    Methods:
        edit: Write a command for the user to edit.
        create: Setup the status bar.
        update: Redraw the status bar.
        destroy: Close the status bar.
    """
    CONFIRM = 1
    ERROR = 2

    def __init__(self, scr_top_row, scr_right_col):
        curses.initscr()
        curses.noecho()
        self._win = curses.newwin(1, 80, scr_top_row, scr_right_col)
        self._text_pad = curses.textpad.Textbox(self._win, insert_mode=True)
        self._cur_str = ''
        self._scr_top_row = scr_top_row
        self._scr_right_col = scr_right_col

    def create(self):
        cur_browser = shared.BrowserFactory.get_cur()
        name = cur_browser.get_name()
        idx = shared.BrowserFactory.get_cur_idx() + 1
        browser_count = shared.BrowserFactory.get_count()
        self._cur_str = '{}:{}/{}'.format(name, idx, browser_count)

    def update(self):
        """Redisplays itself using updated information."""
        self._win.addstr(0,0, ''.join([' ' for i in range(79)]))#\
        self.create()
        self._win.addstr(0, 0, self._cur_str)
        self._win.refresh()

    def destroy(self):
        curses.echo()

    def _clear(self, new_str=''):
        self._win.clear()
        self._win.addstr(0, 0, new_str)
        self._win.refresh()

    def edit(self, initial_str=''):
        self._clear(initial_str)
        input = self._text_pad.edit().split()
        # TODO: get the command associated with input[0]
        # TODO: get flags
        self.update()
        return input

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

    def scroll(self, direction, quantifier=1):
        pass

    def on_browser_switch(self):
        """Switch to the new browser and display it.

        Assumes that the current browser has already had its create method
        called.
        """
        cur_browser = shared.BrowserFactory.get_cur()
        name = cur_browser.get_name()
        idx = shared.BrowserFactory.get_cur_idx() + 1
        browser_count = shared.BrowserFactory.get_count()
        self._cur_str = '{}:{}/{}'.format(name, idx, browser_count)
        self.update()
