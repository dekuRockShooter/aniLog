import enum

class Prompt(enum.Enum):
    ERROR = 1
    CONFIRM = 2


class Scroll(enum.Enum):
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
