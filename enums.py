"""Define enumerations to use throughout the program.

    Classes:
       Prompt: Enumerate the modes for the status bar.
       Scroll: Enumerate the directions to scroll in.
"""
import enum

class Prompt(enum.Enum):
    """Enumerate the modes for the status bar.

    Enumerations:
        ERROR: Set the status bar to error mode.  Any string written
            to it will be prefaced by 'ERROR: '.
        CONFIRM: Set the status bar to confirmation mode.  After
            writing a string to the status bar, the user will need to
            enter a 'y' or 'n'.
    """
    ERROR = 1
    CONFIRM = 2


class Scroll(enum.Enum):
    """Enumerate the directions to scroll in.

    Enumerations:
        UP: Scroll up.
        LEFT: Scroll left.
        DOWN: Scroll down.
        RIGHT: Scroll right.
        PAGE_UP: Scroll one page up.
        PAGE_DOWN: Scroll one page down.
        HOME: Scroll to the top.
        END: Scroll to the bottom.
        PAGE_LEFT: Scroll left.
        PAGE_RIGHT: Scroll right.
        H_HOME: Scroll to the first column.
        H_END: Scroll to the last column.
    """
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4
    PAGE_UP = 5
    PAGE_DOWN = 6
    HOME = 7
    END = 8
    PAGE_LEFT = 9
    PAGE_RIGHT = 10
    H_HOME = 11
    H_END = 12
