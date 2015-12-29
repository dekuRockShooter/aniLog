KEY_ALT = 123456789

class AniLogKeyParser:
    def __call__(self, key_str):
        key_seq = []
        for idx, key in enumerate(key_str):
            if not self._is_valid_key(key):
                key_seq[:] = []
                return key_seq
            elif key == '<':
                special_seq = self._get_special_seq(key_str[idx:])
                if special_seq:
                    key_seq.extend(special_seq)
                    return key_seq
            key_seq.append(ord(key))
        return key_seq

    def _get_special_seq(self, key_str):
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
            if (modifier == ctrl) and self._is_ctrl_modifiable(modified_key):
                return [ord(modified_key.lower()) - 96]
            elif (modifier == alt) and self._is_alt_modifiable(modified_key):
                return [KEY_ALT, ord(modified_key)]
            # TODO: Add support for Ctrl+Alt
        return []

    def _is_ctrl_modifiable(self, key):
        if key.isalpha():
            return True;

    def _is_alt_modifiable(self, key):
        if self._is_valid_key(key) or key.isdigit():
            return True;
        return False

    def _is_valid_key(self, key):
        key_num = ord(key)
        if (32 < key_num < 48) or (57 < key_num < 127):
            return True
        return False



class KeyMap:
    """Map key sequences to commands.

    This class allows creating and getting key bindings.  A key binding
    is a mapping from key sequences to Commands.

    Methods:
        add_key: Bind a key sequence to a Command object.
        get_cmd: Return the Command bound to a key sequence.
    """
    def __init__(self, to_key_seq):
        """Constructor.

        Args:
            to_key_seq (Callable): This callable is used to convert
                a string of keys to a sequence of keys that are
                added to the map.  It should take a string and return
                a list.  If the map were a tree, think of the list as
                being a path, from the root to a leaf, that is inserted
                to the tree.
        """
        self._key_map = {}
        self._key_map_explorer = self._key_map
        self._to_key_seq = to_key_seq

    def add_key(self, key_str, cmd):
        """Bind a key sequence to a Command object.

        Calling get_cmd with a sequence added via this method will
        return the associated Command.

        Args:
            key_str (str): The key sequence as a string.  This is the
                sequence of keys that lead to cmd.  This is converted
                to a key sequence (a list of numbers) using the
                callable given to the constructor.
            cmd (Command): The Command object that is bound to the key
                sequence.

        Example:
            What each key is converted to depends on how the callable
            is implemented.  Here, it just returns their ASCII number.

            # This produces the map:
            #     (97, None) -> (115, None) -> (100, cmdX)
            km.add_key('asd', cmdX)

            # This produces the map:
            #     (97, None) -> (115, None) -> (100, cmdX)
            #                -> (100, cmdY)
            km.add_key('ad', cmdY)
        """
        key_seq = self._to_key_seq(key_str)
        if not key_seq:
            return False
        key_map = self._key_map
        prev_key_map = key_map
        # If a prefix of key_seq is in key_map, then go to the end of it,
        # otherwise, there would be ambiguous paths.
        for idx, x  in enumerate(key_seq):
            if x not in key_map.keys():
                break
            key_map = key_map[x][0]
        # Add the sequence after the prefix.
        for x in key_seq[idx:]:
            prev_key_map = key_map
            key_map[x] = [{}, None]
            key_map = key_map[x][0]
        prev_key_map[key_seq[-1]][1] = cmd

    def get_cmd(self, key_num):
        """Return the Command bound to a key sequence.

        This method returns the Command object that is bound to the
        current key sequence.  The current key sequence is the sequence
        of keys that were passed to the method since the previous valid
        or invalid sequence was passed.

        Args:
            key_num (int): The numerical representation of a key.

        Returns:
            A Command object: If key_num completes a sequence that is
                bounded to a Command (valid sequence).
            None: If key_num is not next in the current sequence (invalid
                sequence), or if key_num is next but does not complete
                the sequence.

        Example:
            # km has been initialized with a callable that converts a
            # string to a list of numbers.
            # c is 99, i is 105, w is 119, ) is 41, G is 71
            # The contents of the map after the two add_key calls:
            #     (99, None) -> (105, None) -> (119, cmd1)
            #                               -> (41, cmd2)
            >>> km.add_key('ciw', 'cmd1')
            >>> km.add_key('ci)', 'cmd2')

            # Get the command associated with 'ci)' (should be cmd2).
            >>> print(km.get_cmd(99))
            None
            >>> print(km.get_cmd(105))
            None
            >>> print(km.get_cmd(41))
            cmd2

            # Now get the command associated with 'cG' (should be None).
            >>> print(km.get_cmd(99))
            None
            >>> print(km.get_cmd(71))
            None

            # Finally, get the command associated with 'ciw' (should be cmd1).
            >>> print(km.get_cmd(99))
            None
            >>> print(km.get_cmd(105))
            None
            >>> print(km.get_cmd(119))
            cmd1
        """
        # The steps in the algorithm are as follows:
        #
        # 1) Go to the map with key key_num.
        # 2) If no such map exists, then the sequence is invalid, so reset
        #   _key_map_explorer and return None.
        # 3) If the map exists and has a non null Command, then the sequence
        #   is valid, so reset _key_map_explorer and return the Command.
        # 4) If the map exists and has a null Command, then leave
        #   _key_map_explorer where it is and return None.
        try:
            self._key_map_explorer, cmd = self._key_map_explorer[key_num]
        except KeyError:
            self._key_map_explorer = self._key_map
            return None
        if cmd:
            self._key_map_explorer = self._key_map
        return cmd


if __name__ == '__main__':
    km = KeyMap()
    km.add_key('ciw', 'cmd1')
    km.add_key('ci)', 'cmd2')
    km.add_key('ci\'', 'cmd3')
    km.add_key('G', 'cmd4')
    print(km.get_cmd(99))
    print(km.get_cmd(105))
    print(km.get_cmd(41))

    print(km.get_cmd(99))
    print(km.get_cmd(71))
    print(km.get_cmd(105))
    print(km.get_cmd(39))

    print(km.get_cmd(99))
    print(km.get_cmd(105))
    print(km.get_cmd(119))
    #print(km.get_command([71]))
    #print(km.get_command([99, 105, 41]))
    #print(km.get_command([99, 105, 39]))
    #print(km.get_command([99, 105, 119]))
