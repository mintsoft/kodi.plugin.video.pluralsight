import sqlite3
import os

class SQLLiteDB:

    def __init__(self, database_path):
        self.path = database_path
        self.__create_db()
        self.__migrate()
        pass

    def __create_db(self):
        if not os.path.exists(self.path):
            self.database = sqlite3.connect(self.path)
            cursor = self.database.cursor()
            cursor.execute('''CREATE TABLE course (name text, description text, category text) ''')
            cursor.execute('''CREATE TABLE author (name text, description text, category text) ''')
            cursor.execute('''CREATE TABLE module (name text, description text, category text) ''')
            cursor.execute('''CREATE TABLE category (name text, description text, category text) ''')
            self.database.commit()
        else:
            self.database = sqlite3.connect(self.path)

