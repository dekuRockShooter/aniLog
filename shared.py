"""Manage objects that are shared among various classes.

This module contains classes that manage shared resources.  Use these
classes to create and get objects, as doing so will ensure that
everything is accounted for and that no wasteful copies are lingering
about.

Classes:
    DBRegistry: manage database connections.
    CopyBuffer: manage the copy buffer.
    SelectBuffer: manage the select buffer.
"""
#cls class method
import db


# TODO: move DBRegistry to db.py.
# Rename module.
class DBRegistry:
    """Manage connections to databases.

    This class provides static methods for creating, accessing, and
    removing connections to databases.

    One connection per database is allowed, which can be shared among
    any classes.

    Methods:
        get: Return a database connection.
        create: Create a database connection.
        destroy: Close a database connection.
        destroy_add: Close all database connections.
    """
    _db_map = {}

    @staticmethod
    def create(name):
        """Open a database connection.

        If the connection already exists, then it is just returned.

        Args:
            name (path): The name of the database to connect to.

        Returns:
            The database connection.
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
                created.
        """
        return DBRegistry._db_map[name]

    @staticmethod
    def destroy(name):
        """Close a database connection.

        Args:
            name (path): The name of the database.

        Raises:
            KeyError: if no database with the given name has been
                created.
        """
        DBRegistry._db_map[name].close()
        DBRegistry._db_map.pop(name)

    @staticmethod
    def destroy_all():
        """Close all database connections."""
        for db in DBRegistry._db_map.values():
            db.close()
        DBRegistry._db_map.clear()


class CopyBuffer:
    """Manage the copy buffers.

    This class provides static methods to access and modify the copy
    buffers. The copy buffer is a map from a single character
    (English alphabet, upper or lower case) to a list of tuples.
    Use this class to copy rows from one table into another table
    (provided both have the same schema).

    Attributes:
        DEFAULT_BUFFER: The buffer that is used if none is given.

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
            val ([tuple]): The new content of the buffer.  Each tuple
                is a row in a database table, and each tuple element
                is a column's value.
        """
        CopyBuffer._copy_buffer[key] = val

    @staticmethod
    def get(key):
        """Return the contents of a buffer.

        Args:
            key: The name of the buffer.

        Returns:
            A list of tuples.  Each tuple is a row in a database table,
            and each tuple element is a column's value.

        Raises:
            KeyError: if no buffer with the given name exists.
        """
        return CopyBuffer._copy_buffer[key]


class SelectBuffer:
    """Manage the select buffer.

    This class provides static methods to access and modify the select
    buffer.  The select buffer holds the rows that are currently
    selected.  The rows are stored as a list of tuples, exactly as in
    CopyBuffer.

    Methods:
        set: Change the contents of the select buffer.
        get: Return the contents of the select buffer.
    """
    _select_buffer = []

    @staticmethod
    def set(rows):
        """Change the contents of the buffer.

        Args:
            rows ([tuple]): The new contents of the buffer.  Each tuple
                is a row in a database table, and each tuple element
                is a column's value.
        """
        SelectBuffer._select_buffer = rows

    @staticmethod
    def get():
        """Return the contents of the buffer.

        Returns:
            A list of tuples.  Each tuple is a row in a database table,
            and each tuple element is a column's value.
        """
        return SelectBuffer._select_buffer
