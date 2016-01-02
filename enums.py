import enum

class Prompt(enum.Enum):
    ERROR = 1
    CONFIRM = 2


class Scroll(enum.Enum):
    UP = 1
    LEFT = 2
    DOWN = 3
    RIGHT = 4
