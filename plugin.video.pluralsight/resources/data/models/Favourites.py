import sys
import Catalog

course_name = sys.argv[1]
course_title = sys.argv[2]
database_path = sys.argv[3]

Catalog.Catalog.add_favourite(course_name, course_title, database_path)
