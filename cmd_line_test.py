import curses
import re
import settings.keys
import keymap
from commands import Command


class NextHistory(Command):
    def execute(self):
        pass


cmd_map = settings.keys.CommandMap.get()
km = keymap.KeyMap(keymap.AniLogKeyParser())
km.add_key('<Ctrl-n>', NextHistory('', ''))

cmd_line_history = open('cmd_line_history', 'r')
history = []
for line in cmd_line_history:
    history.append(line.strip())
cmd_line_history.close()
history_idx = -1
match_gen = None
match_idx = 0
curses.initscr()
curses.cbreak()
curses.noecho()
win = curses.newwin(1, curses.COLS, curses.LINES - 1, 0)
win.keypad(1)
key = 0
while key != ord('q'):
    key = win.getch()
    row, col = win.getyx()
    if key in (curses.KEY_BACKSPACE, curses.KEY_DC):
        win.delch(row, col - 1)
        match_gen = None
    elif key in (curses.KEY_ENTER, 10, 13):
        line = win.instr(0, 0)
        line = line.decode('utf-8').strip()
        history.insert(0, line)
        win.clear()
        history_idx = -1
        match_gen = None
    elif key == curses.KEY_LEFT:
        win.move(row, col - 1)
    elif key == curses.KEY_RIGHT:
        win.move(row, col + 1)
    elif key == curses.KEY_UP:
        match_gen = None
        history_idx = history_idx + 1
        if history_idx >= len(history):
            history_idx = len(history)
            continue
        win.clear()
        win.addstr(0, 0, history[history_idx])
    elif key == curses.KEY_DOWN:
        match_gen = None
        history_idx = history_idx - 1
        if history_idx <= -1:
            history_idx = -1
            continue
        win.clear()
        win.addstr(0, 0, history[history_idx])
    elif key == ord('\t'):
        if match_gen is None:
            match_idx = 0
            line = win.instr(0, 0)
            line = line.decode('utf-8').strip()
            pattern = re.compile('^{}'.format(line))
            # A generator would be preferable, but there is no reasonable
            # way to go back, which is needed for Shift+Tab.
            match_gen = [s for s in cmd_map.keys() if\
                         pattern.search(s) is not None]

        if match_idx >= len(match_gen):
            match_idx = 0
        match = match_gen[match_idx]
        win.clear()
        win.addstr(0, 0, match)
        match_idx = (match_idx + 1) % len(match_gen)
    elif key == curses.KEY_BTAB:
        if match_gen is None:
            match_idx = 0
            line = win.instr(0, 0)
            line = line.decode('utf-8').strip()
            pattern = re.compile('^{}'.format(line))
            match_gen = [s for s in cmd_map.keys() if\
                         pattern.search(s) is not None]
        if match_idx < 0:
            match_idx = len(match_gen) - 1
        match = match_gen[match_idx]
        win.clear()
        win.addstr(0, 0, match)
        match_idx = (match_idx - 1) % len(match_gen)
    else:
        match_gen = None
        win.insch(key)
        win.move(row, col + 1)

curses.nocbreak()
win.keypad(0)
curses.echo()
curses.endwin()
cmd_line_history = open('cmd_line_history', 'w')
for line in history:
    cmd_line_history.write(line)
    cmd_line_history.write('\n')
cmd_line_history.close()
