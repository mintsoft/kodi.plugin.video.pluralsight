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
from resources.data.models import Catalog

start_time = time.time()

# region Constants
MODE_SEARCH = 'search'
MODE_CATEGORY = 'category'
MODE_COURSES = 'courses'
MODE_NEW_COURSES = 'new_courses'
MODE_MODULES = 'modules'
MODE_COURSE_BY_CATEGORY = 'courses_by_category'
MODE_CLIPS = 'clips'
MODE_FAVOURITES = 'favourites'
MODE_RANDOM = 'random'
MODE_PLAY = 'play'

DEBUG = False
# endregion
class AuthorisationError(Exception):
    """ Raise this exception when you cannot access a resource due to authentication issues """

# region Global Functions
def debug_log(string):
    xbmc.log(string, xbmc.LOGNOTICE)


def debug_log_duration(name):
    duration = time.time() - start_time
    xbmc.log("DURATION@" + name + " : " + str(duration))


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


def credentials_are_valid():
    dialog = xbmcgui.Dialog()
    if username == "" or password == "":
        dialog.ok("Credentials Error", "Username or password are empty, please configure these in the settings")
        return False
    elif "@" in username:
        dialog.ok("Login Error",
                  "You appear be attempting to use an email address to login\n\nPluralsight requires the username instead, please change this in the settings")
        return False
    return True


def login(catalog):
    debug_log("Starting login")
    login_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Password": password}
    login_url = "https://www.pluralsight.com/metadata/live/users/" + username + "/login"
    debug_log("Using url: " + login_url)
    response = requests.post(login_url, data=payload, headers=login_headers)
    debug_log("Completed login, Response Code:" + str(response.status_code))
    token = response.json()["Token"]
    catalog.update_token(token)
    return token


def get_video_url(video_url, token):
    video_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Token": token}
    response = requests.post(video_url, data=payload, headers=video_headers)
    if response.status_code == 403:
        raise AuthorisationError
    return response.json()["VideoUrl"]

def add_context_menu(li,course_name,course_title, database_path):
    li.addContextMenuItems([('Add to Favourite Courses',
                             'XBMC.RunScript(special://home/addons/plugin.video.pluralsight/resources/data/models/Favourites.py, %s, %s, %s)'
                             % (course_name, course_title.replace(",",""),database_path)),
                            ('Toggle watched', 'Action(ToggleWatched)')
                            ], replaceItems= True)

def search_for(search_criteria):
    search_safe = urllib.quote_plus(search_criteria)
    search_url = "http://www.pluralsight.com/metadata/live/search?query=" + search_safe
    search_headers = {
        "Accept-Language": "en-us",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Encoding": "gzip"
    }
    debug_log("Hitting: " + search_url)
    response = requests.get(search_url, headers=search_headers)
    return response.json()

def create_menu_item(name, mode):
    url = build_url({'mode': mode, 'cached': 'true'})
    li = xbmcgui.ListItem(name, iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

def create_courses_view(courses):
     for course in courses:
        url = build_url({'mode': MODE_MODULES, 'course_id': course["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(course["title"], iconImage='DefaultFolder.png')
        add_context_menu(li,course["name"],course["title"],database_path)
        li.setInfo('video', {'plot': course["description"], 'genre': course["category_id"], 'title':course["title"]})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)


# endregion


# region Kodi setup
__settings__ = xbmcaddon.Addon()
rootDir = __settings__.getAddonInfo('path')
if rootDir[-1] == ';':
    rootDir = rootDir[0:-1]
rootDir = xbmc.translatePath(rootDir)

LIB_DIR = xbmc.translatePath(os.path.join(rootDir, 'resources', 'lib'))
sys.path.append(LIB_DIR)

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
# endregion


debug_log_duration("PostKodiSetup")
# region Globals
temp_path = xbmc.translatePath("special://temp/")
etag_path = os.path.join(temp_path, "pluralsight_etag.pkl")
database_path = os.path.join(temp_path, 'pluralsight_catalog.db')

xbmcplugin.setContent(addon_handle, 'movies')
xbmcplugin.addSortMethod(addon_handle, xbmcplugin.SORT_METHOD_TITLE)

username = xbmcplugin.getSetting(addon_handle, "username")
password = xbmcplugin.getSetting(addon_handle, "password")
# endregion

debug_log_duration("PreMain")
# Main entry point
if not credentials_are_valid():
    xbmcplugin.endOfDirectory(addon_handle)

cached = args.get('cached', None)
debug_log_duration("pre-cache")
if cached is None and DEBUG is not True:
    catalog = Catalog.Catalog(database_path)

    cache_headers = {
        "Accept-Language": "en-us",
         "Content-Type": "application/json",
         "Accept": "application/json",
         "Accept-Encoding": "gzip",
         "If-None-Match": catalog.etag
    }

    debug_log_duration("pre-get")
    r = requests.get("http://www.pluralsight.com/metadata/live/courses/", headers=cache_headers)
    debug_log_duration("post-get")

    if r.status_code == 304:
        debug_log("Loading from cache as it has not modified")
    else:
        debug_log_duration("Re-priming from the response")
        catalog.update(r.headers["ETag"], r.json())

else:
    catalog = Catalog.Catalog(database_path)

debug_log_duration("catalog-loaded")
mode = args.get('mode', None)

debug_log_duration("Pre-mode switch")

if mode is None:
    debug_log("No mode, defaulting to main menu")

    create_menu_item('Courses', MODE_COURSES)
    create_menu_item('New Courses', MODE_NEW_COURSES)
    create_menu_item('Categories', MODE_CATEGORY)
    create_menu_item('Favourites', MODE_FAVOURITES)
    create_menu_item('Search', MODE_SEARCH)
    create_menu_item('Learn Something New', MODE_RANDOM)

    debug_log_duration("finished default mode")

elif mode[0] == MODE_COURSES:
    create_courses_view(catalog.courses)
    debug_log_duration("finished courses output")

elif mode[0] == MODE_NEW_COURSES:
    create_courses_view(catalog.new_courses)
    debug_log_duration("finished new courses output")

elif mode[0] == MODE_MODULES:
    course_id = args.get('course_id', None)[0]
    course = catalog.get_course_by_id(course_id)
    modules = catalog.get_modules_by_course_id(course_id)
    for module in modules:
        url = build_url({'mode': MODE_CLIPS, 'course_id': course_id, 'module_id': module["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(module["title"], iconImage='DefaultFolder.png')
        add_context_menu(li,course["name"],course["title"],database_path)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished modules output")

elif mode[0] == MODE_CATEGORY:
    for category in catalog.categories:
        url = build_url({'mode': MODE_COURSE_BY_CATEGORY, 'category_id': category["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(category["name"], iconImage='DefaultFolder.png')
        li.setInfo('video', {'title':category["name"]})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

elif mode[0] == MODE_COURSE_BY_CATEGORY:
    category_id = args.get('category_id', None)[0]
    create_courses_view(catalog.get_courses_by_category_id(category_id))

elif mode[0] == MODE_CLIPS:
    module_id = args.get('module_id', None)[0]
    course_id = args.get('course_id', None)[0]

    course = catalog.get_course_by_id(course_id)
    module = catalog.get_module_by_id(module_id)

    for clip in catalog.get_clips_by_module_id(module_id,course_id):
        url = build_url({'mode': MODE_PLAY, 'clip_title': clip.title ,'module_name': module["name"], 'course_name': course["name"], 'cached': 'true'})
        li = xbmcgui.ListItem(clip.title, iconImage='DefaultVideo.png')
        li.addStreamInfo('video', {'width': 1024, 'height': 768, 'duration': clip.duration})
        li.setProperty('IsPlayable', 'true')
        add_context_menu(li,course["name"],course["title"],database_path)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    debug_log_duration("finished clips output")

elif mode[0] == MODE_SEARCH:
    dialog = xbmcgui.Dialog()
    criteria = dialog.input("Search Criteria", type=xbmcgui.INPUT_ALPHANUM)
    debug_log_duration("pre-searching for: " + criteria)
    results = search_for(criteria)
    courses = [catalog.get_course_by_name(x) for x in results['Courses']]
    create_courses_view(courses)
    debug_log_duration("finished search output")

elif mode[0] == MODE_FAVOURITES:
    for favourite in catalog.favourites:
        course = catalog.get_course_by_name(favourite["course_name"])
        url = build_url({'mode': MODE_MODULES, 'course_id':course["id"], 'cached': 'true'})
        li = xbmcgui.ListItem(favourite["title"], iconImage='DefaultFolder.png')
        li.setInfo('video', {'plot': course["description"], 'genre': course["category_id"], 'title':course["title"]})
        li.addContextMenuItems([('Remove From Favourites',
                             'XBMC.RunScript(special://home/addons/plugin.video.pluralsight/resources/data/models/Favourites.py, %s, %s)'
                             % (course["name"],database_path))], replaceItems=True)
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

elif mode[0] == MODE_RANDOM:
    url1 = build_url({'mode': MODE_RANDOM, 'cached': 'true'})
    li1 = xbmcgui.ListItem('Pick a Different Course', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url1, listitem=li1, isFolder=True)

    course = catalog.get_random_course()
    create_courses_view([course,])

elif mode[0] == MODE_PLAY:
    module_name = args.get('module_name', None)[0]
    course_name = args.get('course_name', None)[0]
    clip_title = args.get('clip_title', None)[0]

    clip = catalog.get_clip_by_title(clip_title, module_name, course_name)
    url = clip.get_url(username)
    try:
        video_url = get_video_url(url, catalog.token)
    except AuthorisationError:
        debug_log("Session has expired, re-authorising.")
        token = login(catalog)
        video_url = get_video_url(url, token)

    li = xbmcgui.ListItem(label=clip_title, path=video_url)
    xbmcplugin.setResolvedUrl(handle=addon_handle, succeeded=True, listitem=li)

catalog.close_db()

xbmcplugin.endOfDirectory(addon_handle)
