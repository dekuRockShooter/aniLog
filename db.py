import os
import sqlite3

class DBConnection:
    def __init__(self, name):
        self._name = name
        self._connection = None
        self._cursor = None

    def connect(self):
        if not os.path.exists(self._name):
            raise FileNotFoundError(self._name)
        self._connection = sqlite3.connect(self._name)
        self._cursor = self._connection.cursor()

    def close(self):
        if self._connection:
            self._connection.close()

    def select_all_from(self, table):
        self._cursor.execute('select * from {}'.format(table))
        return self._cursor.fetchall()

#db = DBConnection('Sybil.db')
#db.connect()
#print(db.select_all_from('watching'))
#db.close()
