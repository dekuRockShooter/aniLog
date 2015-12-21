import curses

KEY_ALT = 123456789

def get_special_seq(key_str):
    """ Finds the numerical representation of a special key sequence.
    """
    ctrl_alt = '<Ctrl-Alt-'
    alt = '<Alt-'
    ctrl = '<Ctrl-'
    modifier = ''
    if key_str.startswith(ctrl_alt) and key_str.endswith('>'):
        modifier = ctrl_alt
    elif key_str.startswith(ctrl) and key_str.endswith('>'):
        modifier = ctrl
    elif key_str.startswith(alt) and key_str.endswith('>'):
        modifier = alt
    else:
        return []
    if len(key_str) == len(modifier) + 2:
        modified_key = key_str[-2]
        if (modifier == ctrl) and is_ctrl_modifiable(modified_key):
            return [ord(modified_key.lower()) - 96]
        elif (modifier == alt) and is_alt_modifiable(modified_key):
            return [KEY_ALT, ord(modified_key)]
    return []

def is_ctrl_modifiable(key):
    if key.isalpha():
        return True;

def is_alt_modifiable(key):
    if is_valid_key(key) or key.isdigit():
        return True;
    return False

def is_valid_key(key):
    key_num = ord(key)
    if (32 < key_num < 48) or (57 < key_num < 127):
        return True
    return False

def str_to_key_seq(key_str):
    key_seq = []
    for idx, key in enumerate(key_str):
        if not is_valid_key(key):
            key_seq[:] = []
            return key_seq
        elif key == '<':
            special_seq =get_special_seq(key_str[idx:])
            if special_seq:
                key_seq.extend(special_seq)
                return key_seq
        key_seq.append(ord(key))
    return key_seq

class KeyMap:
    def __init__(self):
        self._key_map = {}

    def add_key(self, key_str, cmd):
        key_seq = str_to_key_seq(key_str)
        if not key_seq:
            return False
        key_map = self._key_map
        prev_key_map = key_map
        for idx, x  in enumerate(key_seq):
            if x not in key_map.keys():
                break
            key_map = key_map[x][0]
        for x in key_seq[idx:]:
            prev_key_map = key_map
            key_map[x] = [{}, None]
            key_map = key_map[x][0]
        prev_key_map[key_seq[-1]][1] = cmd

    def get_command(self, key_seq):
        key_map = self._key_map
        prev_key_map = key_map
        for key in key_seq:
            prev_key_map = key_map
            try:
                key_map = key_map[key][0]
            except:
                return None
        return prev_key_map[key_seq[-1]][1]
#
#km = KeyMap()
#km.add_key('ciw', 'cmd1')
#km.add_key('ci)', 'cmd2')
#km.add_key('ci\'', 'cmd3')
#km.add_key('G', 'cmd4')
#print(km.get_command([71]))
#print(km.get_command([99, 105, 41]))
#print(km.get_command([99, 105, 39]))
#print(km.get_command([99, 105, 119]))
