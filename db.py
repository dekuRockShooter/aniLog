import os
import sqlite3

class NoConnectionError(Exception):
    """Error for accessing an unconnected database."""

    def __init__(self):
        pass

    def __str__(self):
        return 'Database not connected. Call connect().'

class DBConnection:
    """Interface for an sqlite3 database."""

    def __init__(self, name):
        self._name = name
        self._connection = None
        self._cursor = None
        self._no_connect_err = NoConnectionError()

    def connect(self):
        """Connect to the database.

        Raises;
            FileNotFoundError: If the database does not exist.
        """
        if not os.path.exists(self._name):
            raise FileNotFoundError(self._name)
        self._connection = sqlite3.connect(self._name)
        self._cursor = self._connection.cursor()

    def close(self):
        """Close the connection to the database."""
        if self._connection:
            self._connection.close()

    def select_all_from(self, table):
        """Return every row from the table.

        All rows are queried and returned as a list of tuples.  The
        elements of the tuple are the columns' values.

        Args:
            table (str): The name of the table to query.

        Raises;
            NoConnectionError: If the database has not been connected
                to.
            sqlite3.OperationalError: If the table does not exist.
        """
        if not self._connection:
            raise self._no_connect_err
        self._cursor.execute('select * from {}'.format(table))
        return self._cursor.fetchall()

    def get_newest(self, table_name):
        """Return the newest row in the table.

        Since the rowid is automatically incremented whenever a new
        row is inserted, the newest row is the one with the highest
        rowid. The row is returned as a tuple.

        Args:
            table (str): The name of the table to query.

        Raises;
            NoConnectionError: If the database has not been connected
                to.
            sqlite3.OperationalError: If the table does not exist.
        """
        if not self._connection:
            raise self._no_connect_err
        s = 'select * from "{table}" where rowid=\
                (select max(rowid) from "{table}")'.format(table=table_name)
        self._cursor.execute(s)
        return self._cursor.fetchone()

    def execute(self, statement):
        """Execute an arbitrary sqlite statement.

        The result of the statement is returned as a list of tuples.

        Args:
            statement (str): The sqlite statement to execute. This is
                any valid sqlite statement.

        Raises;
            NoConnectionError: If the database has not been connected
                to.
        """
        if not self._connection:
            raise self._no_connect_err
        self._cursor.execute(statement)
        return self._cursor.fetchall()

    def commit(self):
        """Save changes done to the database.

        When executing a statement that modifies the database, such as
        inserting, updating, deleting, etc, this method should always
        be called so as to write the changes to disk and update all
        aother connections that are connected to the same database,

        Raises;
            NoConnectionError: If the database has not been connected
                to.
        """
        if not self._connection:
            raise self._no_connect_err
        self._connection.commit()


if __name__ == '__main__':
    db = DBConnection('Sybil.db')
    db.connect()
    #print(db.execute('select name from watching where rowid=82')[0])
    #print(db.execute('pragma table_info(watching)'))
    print(db.get_newest('watching'))
    db.close()
