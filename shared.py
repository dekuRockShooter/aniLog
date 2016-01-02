"""Manage objects that are shared among various classes.

This module contains classes that manage shared resources.  Use these
classes to create and get objects, as doing so will ensure that
everything is accounted for and that no wasteful copies are lingering
about.

Classes:
    UIRegistry: manage the user interface.
    DBRegistry: manage database connections.
    BrowserFactory: manage the browsers.
    StatusBarRegistry: manage the status bar.
    CopyBuffer: manage the copy buffer.
"""
#cls class method
import db


class DBRegistry:
    """Manage connections to databases.

    This class provides static methods for creating, accessing, and
    removing connections to databases.

    One connection per database is allowed, which can be shared by
    any class.

    Methods:
        get: Return a database connection.
        create: Create a database connection.
        destroy: Close a database connection.
    """
    _db_map = {}

    @staticmethod
    def create(name):
        """Open a database connection.

        A connection to the database is created and returned.  If the
        connection already exists, then it is just returned.

        Args:
            name (path): The name of the database to connect to.
        """
        if name not in DBRegistry._db_map:
            DBRegistry._db_map[name] = db.DBConnection(name)
        return DBRegistry._db_map[name]

    @staticmethod
    def get_db(name):
        """Return a database connection.

        Args:
            name (path): The name of the database.

        Raises:
            KeyError: if no database with the given name has been
                connected to.
        """
        return DBRegistry._db_map[name]

    @staticmethod
    def destroy(name):
        """Close a database connection.

        Args:
            name (path): The name of the database.

        Raises:
            KeyError: if no database with the given name has been
                connected to.
        """
        DBRegistry._db_map[name].close()
        DBRegistry._db_map.pop(name)

    @staticmethod
    def destroy_all():
        for db in DBRegistry._db_map.values():
            db.close()
        DBRegistry._db_map.clear()


class CopyBuffer:
    """Manage the copy buffers.

    This class provides static methods to access and modify the copy
    buffers. The copy buffer is simply a map from a single character
    (English alphabet, upper or lower case) to a tuple. The name of
    a buffer is thus the character used as the key, and the contents
    of a buffer is the tuple.  The tuple is intended to represent a row
    in a database table. Thus, its elements should be the values of
    each column.  Use this class to copy a row from one table into 
    another table (provided both have the same schema).

    Attributes:
        DEFAULT_BUFFER: The buffer that is used if no buffer is given.

    Methods:
        get: Return the contents of a copy buffer.
        set: Change the contents of a copy buffer.
    """
    DEFAULT_KEY = '0'
    _copy_buffer = {}

    @staticmethod
    def set(key, val):
        """Change the contents of a buffer.

        Args:
            key (char): The name of the buffer.
            val (tuple): The new content of the buffer. Each element is
                the value of a column in some database table.
        """
        CopyBuffer._copy_buffer[key] = val

    @staticmethod
    def get(key):
        """Return the contents of a buffer.

        Args:
            key: The name of the buffer.

        Raises:
            KeyError: if no buffer with the given name exists.
        """
        return CopyBuffer._copy_buffer[key]
