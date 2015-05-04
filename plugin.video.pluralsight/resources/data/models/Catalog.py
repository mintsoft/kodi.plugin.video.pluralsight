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
    def __init__(self, data):
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
                module_author = raw_authors[int(module["Author"])]

                clips = []
                for i, clip in enumerate(module["Clips"]):
                    clips.append(Clip(clip["Title"], clip["Duration"], i, course["Name"], module_author["Handle"], module["Name"]))

                author = Author(module_author["DisplayName"], module_author["Handle"])
                course_modules.append(Module(module["Name"], module["Title"], clips, author, module["Duration"]))

            courses.append(
                Course(course["Name"],
                       course["Title"].encode('UTF8'),
                       course["Description"],
                       course_modules,
                       raw_categories[int(course["Category"])]))
        self.authors = sorted([Author(x["DisplayName"], x["Handle"]) for x in raw_authors], key=lambda author : author.display_name)
        self.categories = [x for x in raw_categories]
        self.courses = sorted(courses, key=lambda course: course.title)

    def get_course_by_name(self, name):
        return filter(lambda x: x.name == name, self.courses)[0]

    def get_course_by_title(self, title):
        return filter(lambda x: x.title == title, self.courses)[0]

    def get_courses_by_author(self, author):
        return filter(lambda x: x.author.display_name == author, self.courses)

    def get_courses_by_category(self, category):
        return filter(lambda x: x.category == category, self.courses)


