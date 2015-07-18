import sys
import Catalogue
import xbmc

if len(sys.argv) == 4:
    course_name = sys.argv[1]
    course_title = sys.argv[2]
    database_path = sys.argv[3]
    Catalogue.Catalogue.add_favourite(course_name, course_title, database_path)

if len(sys.argv) == 3:
    course_name = sys.argv[1]
    database_path = sys.argv[2]
    Catalogue.Catalogue.remove_favourite(course_name,database_path)
    xbmc.executebuiltin('XBMC.Container.Update(%s?mode=favourites)' % ('plugin://plugin.video.pluralsight'))