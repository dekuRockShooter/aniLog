import curses

KEY_ALT = 123456789

def get_special_seq(special_key, key_str):
    """ Finds the numerical representation of a special key sequence.
    """
    #special_key = '<Ctrl-Alt'
    #special_key = 'Alt'
    #special_key = 'Ctrl'
    is_special = key_str.startswith('<' + special_key + '-')\
            and key_str[-1] == '>'
    if is_special and (len(key_str) == len(special_key) + 4):
        modified_key = key_str[-2]
        if (special_key == 'Ctrl') and is_ctrl_modifiable(modified_key):
            return [ord(modified_key.lower()) - 96]
        elif (special_key == 'Alt') and is_alt_modifiable(modified_key):
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
            special_num =get_special_seq(key_str[idx:])
        key_seq.append(ord(key))
    return key_seq

class KeyMap:
    def __init__(self):
        self.key_map = {}

    def add_key(self, key_str, cmd):
        key_map = self.key_map
        prev_key_map = key_map
        for idx, x  in enumerate(key_str):
            if x not in key_map.keys():
                break
            key_map = key_map[x][0]
        for x in key_str[idx:]:
            prev_key_map = key_map
            key_map[x] = [{}, None]
            key_map = key_map[x][0]
        prev_key_map[key_str[-1]][1] = cmd

    def add_special_key(self, key_str):
        if len(key_str) == 1:
            return False
        #if key_str.startswith('ctrl'):
            #if add

    def get_command(self, key_str):
        key_map = self.key_map
        prev_key_map = key_map
        value = []
        for key in key_str:
            prev_key_map = key_map
            try:
                key_map = key_map[key][0]
            except:
                return None
        return prev_key_map[key_str[-1]][1]

km = KeyMap()
for i in range(1,6):
    km.add_key('key'+str(i), 'cmd'+str(i))
km.add_key('e', 'lol')
print(km.get_command('e'))
for i in range(1,6):
    print(km.get_command('key'+str(i)))
print(get_special_seq('Alt', '<Alt-19>'))
