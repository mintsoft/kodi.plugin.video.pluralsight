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
    def __init__(self, database_path, data=None):
        if not os.path.exists(database_path):
            database = sqlite3.connect(database_path)
            cursor = database.cursor()
            cursor.execute('''CREATE TABLE course (name text, description text, category text) ''')
            database.commit()
        else:
            database = sqlite3.connect(database_path)

        if data is not None:
            raw_courses = data["Courses"]
            raw_modules = data["Modules"]
            raw_authors = data["Authors"]
            raw_categories = data["Categories"]
            cursor = database.cursor()

            courses = []
            for course in raw_courses:

                courses.append((
                    course["Title"],
                    course["Description"],
                    raw_categories[int(course["Category"])]))

            cursor.executemany('INSERT INTO course VALUES (?,?,?)', courses)
            database.commit()

        self.database = database

    def get_courses(self):
        cursor = self.database.cursor()
        return cursor.execute('SELECT * FROM course').fetchall()

    def get_course_by_name(self, name):
        return filter(lambda x: x.name == name, self.courses)[0]

    def get_course_by_title(self, title):
        return filter(lambda x: x.title == title, self.courses)[0]

    def get_courses_by_author(self, author):
        return filter(lambda x: x.author.display_name == author, self.courses)

    def get_courses_by_category(self, category):
        return filter(lambda x: x.category == category, self.courses)

    def close_db(self):
        self.database.close()

