import os
import sqlite3

class NoConnectionError(Exception):
    def __init__(self, value):
        self._value = value

    def __str__(self):
        return repr(self._value)

class DBConnection:
    def __init__(self, name):
        self._name = name
        self._connection = None
        self._cursor = None
        self._no_connect_err = NoConnectionError(\
                'Database not connected. Call connect().')

    def connect(self):
        if not os.path.exists(self._name):
            raise FileNotFoundError(self._name)
        self._connection = sqlite3.connect(self._name)
        self._cursor = self._connection.cursor()

    def close(self):
        if self._connection:
            self._connection.close()

    def select_all_from(self, table):
        if not self._connection:
            raise self._no_connect_err
        self._cursor.execute('select * from {}'.format(table))
        return self._cursor.fetchall()

#db = DBConnection('Sybil.db')
#db.connect()
#print(db.select_all_from('watching'))
#db.close()
