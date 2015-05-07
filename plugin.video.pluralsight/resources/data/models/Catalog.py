import sqlite3
import os


class Course:
    def __init__(self, name, title, description, modules, category):
        self.category = category
        self.description = description
        self.title = title
        self.name = name
        self.modules = modules


class Module:
    def __init__(self, name, tile, clips, author, duration):
        self.duration = duration
        self.author = author
        self.name = name
        self.title = tile
        self.clips = clips


class Author:
    def __init__(self, display_name, handle):
        self.handle = handle
        self.display_name = display_name


class Clip:
    def __init__(self, title, duration, index, course_name, author_handle, module_name):
        self.module_name = module_name
        self.author_handle = author_handle
        self.course_name = course_name
        self.index = index
        self.duration = duration
        self.title = title

    def get_url(self, username):
        return "http://www.pluralsight.com/metadata/live/users/{username}/" \
               "viewclip/{courseName}/{authorHandle}/{moduleName}/{clipIndex}" \
               "/1024x768mp4".format(username=username, courseName=self.course_name, authorHandle=self.author_handle,
                                     moduleName=self.module_name, clipIndex=self.index)


class Catalog:
    def __init__(self, database_path):
        if not os.path.exists(database_path):
            database = sqlite3.connect(database_path)

            database.execute('''
                CREATE TABLE cache_status (
                    etag TEXT
                ) ''')
            database.execute('''
                CREATE TABLE author (
                    id INTEGER PRIMARY KEY ASC,
                    handle TEXT,
                    displayname TEXT
                ) ''')
            database.execute('''
                CREATE TABLE course (
                    id INTEGER PRIMARY KEY ASC,
                    name TEXT,
                    description TEXT,
                    category_id INTEGER
                ) ''')
            database.execute('''
                CREATE TABLE category (
                    id INTEGER PRIMARY KEY ASC,
                    name TEXT
                ) ''')
            database.execute('''
                CREATE TABLE module (
                    id INTEGER PRIMARY KEY ASC,
                    author INT,
                    name TEXT,
                    title TEXT,
                    duration INT
                ) ''')
            database.execute('''
                CREATE TABLE clip (
                    id INTEGER PRIMARY KEY ASC,
                    module_id INT,
                    title TEXT,
                    duration TEXT
                ) ''')

            database.commit()
        else:
            database = sqlite3.connect(database_path)

        self.database = database

    def update(self, etag, data):

        raw_courses = data["Courses"]
        raw_modules = data["Modules"]
        raw_authors = data["Authors"]
        raw_categories = data["Categories"]
        # cursor = database.cursor()

        self.database.execute('DELETE FROM cache_status')
        self.database.execute('DELETE FROM category')
        self.database.execute('DELETE FROM course')
        self.database.execute('DELETE FROM clip')
        self.database.execute('DELETE FROM module')
        self.database.execute('DELETE FROM author')
        
        self.database.execute('INSERT INTO cache_status (etag) VALUES(?)', (etag,))

        for author in raw_authors:
            self.database.execute('INSERT INTO author(handle, displayname) VALUES(?,?)',
                                  (author["Handle"], author["DisplayName"]))

        for category in raw_categories:
            self.database.execute('INSERT INTO category(name) VALUES(?)', (category,))

        for module in raw_modules:
            result = self.database.execute('INSERT INTO module(author, name, title, duration) VALUES(?,?,?,?)',
                                           (int(module["Author"]), module["Name"], module["Title"], module["Duration"]))
            module_id = result.lastrowid
            for clip in module["Clips"]:
                self.database.execute('INSERT INTO clip (module_id, title, duration) VALUES(?,?,?)',
                                      (module_id, clip["Title"], clip["Duration"]))

        for course in raw_courses:
            self.database.execute('INSERT INTO course(name, description, category_id) VALUES (?,?,?)',
                                  (course["Title"], course["Description"], int(course["Category"])))

        self.database.commit()

    def get_etag(self):
        return self.database.cursor().execute('SELECT etag FROM cache_status').fetchone()

    def get_courses(self):
        return self.database.cursor().execute('SELECT * FROM course').fetchall()

    def get_course_by_name(self, name):
        return self.database.cursor().execute('SELECT * FROM course WHERE name=?', name).fetchone()

    def get_course_by_title(self, title):
        return self.database.cursor().execute('SELECT * FROM course WHERE title=?', title).fetchone()

    def get_courses_by_category(self, category):
        return self.database.cursor().execute('SELECT * FROM course WHERE category_id=?', int(category)).fetchall()

    def close_db(self):
        self.database.close()