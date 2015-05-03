import json

class Course:

    def __init__(self, name, title, description, modules, category):
        self.category = category
        self.description = description
        self.title = title
        self.name = name
        self.modules = modules

class Module:

    def __init__(self,name,tile, clips, author):
        self.author = author
        self.name = name
        self.title = tile
        self.clips = clips

class Author:

    def __init__(self,display_name, handle):
        self.handle = handle
        self.display_name = display_name


class Clip:

    def __init__(self, title, duration):
        self.duration = duration
        self.title = title


class Catalog:

    def __init__(self,data):
        raw_courses = data["Courses"]
        raw_modules = data["Modules"]
        raw_authors = data["Authors"]
        raw_categories = data["Categories"]

        courses = []
        for course in raw_courses:
            modules = course["Modules"]
            modules_indexes = modules.split(',')
            raw_course_modules = [raw_modules[int(x)] for x in modules_indexes]

            course_modules = []
            for module in raw_course_modules:
                clips = [Clip(y["Title"],y["Duration"]) for y in module["Clips"]]
                module_author = raw_authors[int(module["Author"])]
                author = Author(module_author["DisplayName"],module_author["Handle"])
                course_modules.append(Module(module["Name"],module["Title"],clips,author))


            courses.append(
                Course(course["Name"],
                       course["Title"],
                       course["Description"],
                       course_modules,
                       raw_categories[int(course["Category"])]))

        self.courses = courses

    def get_courses_by_title(self,title):
        return filter(lambda x: x.title == title,self.courses)

    def get_course_by_author(self,author):
        return filter(lambda x: x.author.display_name == author, self.courses)

    def get_course_by_category(self,category):
       return filter(lambda x: x.category == category, self.courses)



if __name__ == "__main__":
    raw = open("G:\Kodi Pluralsight Plugin\pluralsight\courses2.txt")
    catalog = Catalog(json.load(raw))
    for x in catalog.get_course_by_category(".NET") : print x.title
