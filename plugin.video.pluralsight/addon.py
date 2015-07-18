import os
import sys
import time
import urllib
import urlparse

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui
from resources.lib import requests
from resources.data.models import Catalogue

# region Constants
MODE_SEARCH = 'search'
MODE_SEARCH_HISTORY = 'search_history'
MODE_CATEGORY = 'category'
MODE_COURSES = 'courses'
MODE_NEW_COURSES = 'new_courses'
MODE_MODULES = 'modules'
MODE_COURSE_BY_CATEGORY = 'courses_by_category'
MODE_CLIPS = 'clips'
MODE_FAVOURITES = 'favourites'
MODE_RANDOM = 'random'
MODE_PLAY = 'play'
MODE_AUTHORS = 'authors'
MODE_COURSE_BY_AUTHOR = 'courses_by_author'

DEBUG = False
# endregion
# region Exceptions
class AuthorisationError(Exception):
    """ Raise this exception when you cannot access a resource due to authentication issues """
# endregion
# region Global Functions

def kodi_init():
    global base_url, addon_handle, args
    __settings__ = xbmcaddon.Addon()
    root_dir = __settings__.getAddonInfo('path')
    if root_dir[-1] == ';':
        root_dir = root_dir[0:-1]
    root_dir = xbmc.translatePath(root_dir)
    lib_dir = xbmc.translatePath(os.path.join(root_dir, 'resources', 'lib'))
    sys.path.append(lib_dir)
    base_url = sys.argv[0]
    addon_handle = int(sys.argv[1])
    args = urlparse.parse_qs(sys.argv[2][1:])


def debug_log_duration(name):
    duration = time.time() - start_time
    xbmc.log("PluralSight Duration@" + name + " : " + str(duration), xbmc.LOGNOTICE)

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def credentials_are_valid():
    credentials_dialog = xbmcgui.Dialog()
    if username == "" or password == "":
        credentials_dialog.ok("Credentials Error", "Username or password are empty, please configure these in the settings")
        return False
    elif "@" in username:
        credentials_dialog.ok("Login Error",
                  "You appear be attempting to use an email address to login\n\nPluralsight requires the username instead, please change this in the settings")
        return False
    return True

def login(login_catalog):
    debug_log_duration("Starting login")
    login_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Password": password}
    login_url = "https://www.pluralsight.com/metadata/live/users/" + username + "/login"
    debug_log_duration("Using url: " + login_url)
    response = requests.post(login_url, data=payload, headers=login_headers)
    debug_log_duration("Completed login, Response Code:" + str(response.status_code))
    login_token = response.json()["Token"]
    login_catalog.update_token(login_token)
    return login_token

def get_video_url(video_url, token):
    video_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Token": token}
    response = requests.post(video_url, data=payload, headers=video_headers)
    if response.status_code == 403:
        raise AuthorisationError
    return response.json()["VideoUrl"]

def add_context_menu(context_li,course_name,course_title, database_path, replace = True):
    context_li.addContextMenuItems([('Add to Favourite Courses',
                             'XBMC.RunScript(special://home/addons/plugin.video.pluralsight/resources/data/models/Favourites.py, %s, %s, %s)'
                             % (course_name, course_title.replace(",",""),database_path)),
                            ('Toggle watched', 'Action(ToggleWatched)')
                            ], replaceItems= replace)

def search_for(search_criteria):
    search_safe = urllib.quote_plus(search_criteria)
    search_url = "http://www.pluralsight.com/metadata/live/search?query=" + search_safe
    search_headers = {
        "Accept-Language": "en-us",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip"
    }
    debug_log_duration("Hitting: " + search_url)
    response = requests.get(search_url, headers=search_headers)
    return response.json()

def create_menu_item(name, mode):
    menu_url = build_url({'mode': mode, 'cached': 'true'})
    menu_li = xbmcgui.ListItem(name, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=menu_url, listitem=menu_li, isFolder=True)
# endregion
# region View Rendering
def default_view():
    debug_log_duration("No mode, defaulting to main menu")
    create_menu_item('Courses', MODE_COURSES)
    create_menu_item('New Courses', MODE_NEW_COURSES)
    create_menu_item('Categories', MODE_CATEGORY)
    create_menu_item('Favourites', MODE_FAVOURITES)
    create_menu_item('Authors', MODE_AUTHORS)
    create_menu_item('Search', MODE_SEARCH_HISTORY)
    create_menu_item('Learn Something New', MODE_RANDOM)
    debug_log_duration("finished default mode")

def author_view():
    global url, li
    for author in catalogue.authors:
        url = build_url({'mode': MODE_COURSE_BY_AUTHOR, 'author_id': author["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(author["displayname"], iconImage='DefaultFolder.png')
        li.setInfo('video', {'title': author["displayname"]})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished new courses output")

def course_by_author_view():
    global courses
    author_id = args.get('author_id', None)[0]
    courses = catalogue.get_course_by_author_id(author_id)
    courses_view(courses)

def module_view():
    global course_id, course, module, url, li
    course_id = args.get('course_id', None)[0]
    course = catalogue.get_course_by_id(course_id)
    modules = catalogue.get_modules_by_course_id(course_id)
    for module in modules:
        url = build_url({'mode': MODE_CLIPS, 'course_id': course_id, 'module_id': module["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(module["title"], iconImage='DefaultFolder.png')
        add_context_menu(li, course["name"], course["title"], database_path)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished modules output")

def category_view():
    global url, li
    for category in catalogue.categories:
        url = build_url({'mode': MODE_COURSE_BY_CATEGORY, 'category_id': category["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(category["name"], iconImage='DefaultFolder.png')
        li.setInfo('video', {'title': category["name"]})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def clip_view():
    global course_id, course, module, clip, url, li
    module_id = args.get('module_id', None)[0]
    course_id = args.get('course_id', None)[0]
    course = catalogue.get_course_by_id(course_id)
    module = catalogue.get_module_by_id(module_id)
    for clip in catalogue.get_clips_by_module_id(module_id, course_id):
        url = build_url(
            {'mode': MODE_PLAY, 'clip_id': clip.index, 'module_name': module["name"], 'course_name': course["name"],
             'cached': 'true'})
        li = xbmcgui.ListItem(clip.title, iconImage='DefaultVideo.png')
        li.addStreamInfo('video', {'width': 1024, 'height': 768, 'duration': clip.duration})
        li.setProperty('IsPlayable', 'true')
        add_context_menu(li, course["name"], course["title"], database_path, False)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    debug_log_duration("finished clips output")

def search_history_view():
    global url, li
    url = build_url({'mode': MODE_SEARCH, 'cached': 'true'})
    li = xbmcgui.ListItem('New Search', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    for search in catalogue.search_history:
        url = build_url({'mode': MODE_SEARCH, 'term': search['search_term'], 'cached': 'true'})
        li = xbmcgui.ListItem(search['search_term'], iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def search_view():
    global courses
    term = args.get('term', None)
    if term is None:
        dialog = xbmcgui.Dialog()
        criteria = dialog.input("Search Criteria", type=xbmcgui.INPUT_ALPHANUM)
        debug_log_duration("pre-searching for: " + criteria)
        results = search_for(criteria)
        catalogue.save_search(criteria)
    else:
        results = search_for(term[0])
    courses = [catalogue.get_course_by_name(x) for x in results['Courses']]
    courses_view(courses)
    debug_log_duration("finished search output")

def favourites_view():
    global course, url, li
    for favourite in catalogue.favourites:
        course = catalogue.get_course_by_name(favourite["course_name"])
        url = build_url({'mode': MODE_MODULES, 'course_id': course["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(favourite["title"], iconImage='DefaultFolder.png')
        li.setInfo('video',
                   {'plot': course["description"], 'genre': course["category_id"], 'title': course["title"]})
        li.addContextMenuItems([('Remove From Favourites',
                                 'XBMC.RunScript(special://home/addons/plugin.video.pluralsight/resources/data/models/Favourites.py, %s, %s)'
                                 % (course["name"], database_path))], replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def random_view():
    global course
    url1 = build_url({'mode': MODE_RANDOM, 'cached': 'true'})
    li1 = xbmcgui.ListItem('Pick a Different Course', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url1, listitem=li1, isFolder=True)
    course = catalogue.get_random_course()
    courses_view([course, ])

def play_view():
    global clip, url, li
    module_name = args.get('module_name', None)[0]
    course_name = args.get('course_name', None)[0]
    clip_id = args.get('clip_id', None)[0]
    clip = catalogue.get_clip_by_id(clip_id, module_name, course_name)
    url = clip.get_url(username)
    try:
        video_url = get_video_url(url, catalogue.token)
    except AuthorisationError:
        debug_log_duration("Session has expired, re-authorising.")
        token = login(catalogue)
        video_url = get_video_url(url, token)
    li = xbmcgui.ListItem(path=video_url)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)

def courses_view(courses):
     for this_course in courses:
        course_view_url = build_url({'mode': MODE_MODULES, 'course_id': this_course["id"], 'cached': 'true'})
        course_view_li = xbmcgui.ListItem(this_course["title"], iconImage='DefaultFolder.png')
        add_context_menu(course_view_li,this_course["name"],this_course["title"],database_path)
        course_view_li.setInfo('video', {'plot': this_course["description"], 'genre': this_course["category_id"], 'title':this_course["title"]})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=course_view_url, listitem=course_view_li, isFolder=True)

# endregion

def main():
    global base_url, addon_handle, args, database_path, username, password, catalogue

    kodi_init()

    debug_log_duration("PostKodiSetup")

    temp_path = xbmc.translatePath("special://temp/")
    database_path = os.path.join(temp_path, 'pluralsight_catalogue.db')
    xbmcplugin.setContent(addon_handle, 'movies')
    xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)
    username = xbmcplugin.getSetting(addon_handle, "username")
    password = xbmcplugin.getSetting(addon_handle, "password")

    debug_log_duration("PreMain")

    if not credentials_are_valid():
        xbmcplugin.endOfDirectory(addon_handle)
    cached = args.get('cached', None)
    debug_log_duration("pre-cache")
    if cached is None and DEBUG is not True:
        catalogue = Catalogue.Catalogue(database_path)

        cache_headers = {
            "Accept-Language": "en-us",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "If-None-Match": catalogue.etag
        }

        debug_log_duration("pre-get")
        r = requests.get("http://www.pluralsight.com/metadata/live/courses/", headers=cache_headers)
        debug_log_duration("post-get")

        if r.status_code == 304:
            debug_log_duration("Loading from cache as it has not modified")
        else:
            debug_log_duration("Re-priming from the response")
            catalogue.update(r.headers["ETag"], r.json())

    else:
        catalogue = Catalogue.Catalogue(database_path)
    debug_log_duration("catalogue-loaded")
    mode = args.get('mode', None)
    debug_log_duration("Pre-mode switch")

    if mode is None:
        default_view()

    elif mode[0] == MODE_COURSES:
        courses_view(catalogue.courses)
        debug_log_duration("finished courses output")

    elif mode[0] == MODE_NEW_COURSES:
        courses_view(catalogue.new_courses)
        debug_log_duration("finished new courses output")

    elif mode[0] == MODE_COURSE_BY_AUTHOR:
        course_by_author_view()

    elif mode[0] == MODE_AUTHORS:
        author_view()

    elif mode[0] == MODE_MODULES:
        module_view()

    elif mode[0] == MODE_CATEGORY:
        category_view()

    elif mode[0] == MODE_COURSE_BY_CATEGORY:
        category_id = args.get('category_id', None)[0]
        courses_view(catalogue.get_courses_by_category_id(category_id))

    elif mode[0] == MODE_CLIPS:
        clip_view()

    elif mode[0] == MODE_SEARCH_HISTORY:
        search_history_view()

    elif mode[0] == MODE_SEARCH:
        search_view()

    elif mode[0] == MODE_FAVOURITES:
        favourites_view()

    elif mode[0] == MODE_RANDOM:
        random_view()

    elif mode[0] == MODE_PLAY:
        play_view()
    catalogue.close_db()
    xbmcplugin.endOfDirectory(addon_handle)

start_time = time.time()
main()
