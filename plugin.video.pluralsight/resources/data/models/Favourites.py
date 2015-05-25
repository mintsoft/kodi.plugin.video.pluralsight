import sys
import Catalog
import xbmc

if len(sys.argv) == 4:
    course_name = sys.argv[1]
    course_title = sys.argv[2]
    database_path = sys.argv[3]
    Catalog.Catalog.add_favourite(course_name, course_title, database_path)

if len(sys.argv) == 3:
    course_name = sys.argv[1]
    database_path = sys.argv[2]
    Catalog.Catalog.remove_favourite(course_name,database_path)
    xbmc.executebuiltin('XBMC.Container.Update(%s?mode=favourites)' % ('plugin://plugin.video.pluralsight'))