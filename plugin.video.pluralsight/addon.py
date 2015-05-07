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
MODE_MODULES = 'modules'
MODE_COURSE_BY_CATEGORY = 'courses_by_category'
MODE_CLIPS = 'clips'

DEBUG = False
# endregion


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


def login():
    debug_log("Starting login")
    login_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Password": password}
    login_url = "https://www.pluralsight.com/metadata/live/users/" + username + "/login"
    debug_log("Using url: " + login_url)
    response = requests.post(login_url, data=payload, headers=login_headers)
    debug_log("Completed login, Response Code:" + str(response.status_code))
    return response.json()


def get_video_url(video_url, token):
    video_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Token": token}
    response = requests.post(video_url, data=payload, headers=video_headers)
    return response.json()

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

    etag = catalog.get_etag()
    cache_headers = {"Accept-Language": "en-us",
                     "Content-Type": "application/json",
                     "Accept": "application/json",
                     "Accept-Encoding": "gzip",
                     "If-None-Match": etag}

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


def search_for(search_criteria):
    search_safe = urllib.quote_plus(search_criteria)
    search_url = "http://www.pluralsight.com/metadata/live/search?query=" + search_safe
    search_headers = {"Accept-Language": "en-us", "Content-Type": "application/json", "Accept": "application/json",
                      "Accept-Encoding": "gzip"}
    debug_log("Hitting: " + search_url)
    response = requests.get(search_url, headers=search_headers)
    return response.json()


debug_log_duration("Pre-mode switch")
if mode is None:
    debug_log("No mode, defaulting to main menu")
    url = build_url({'mode': MODE_COURSES, 'cached': 'true'})
    li = xbmcgui.ListItem('Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': MODE_CATEGORY, 'cached': 'true'})
    li = xbmcgui.ListItem('Categories', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': MODE_SEARCH, 'cached': 'true'})
    li = xbmcgui.ListItem('Search', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished default mode")

elif mode[0] == MODE_COURSES:
    for course in catalog.get_courses():
        url = build_url({'mode': MODE_MODULES, 'course': course[0].encode('UTF8'), 'cached': 'true'})
        li = xbmcgui.ListItem(course[0], iconImage='DefaultFolder.png')
        li.setInfo('video', {'plot': course[1], 'genre': course[2]})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished courses output")

elif mode[0] == MODE_MODULES:
    title = args.get('course', None)
    for module in catalog.get_course_by_name(title[0]).modules:
        url = build_url({'mode': MODE_CLIPS, 'course': title[0], 'module': module.title, 'cached': 'true'})
        li = xbmcgui.ListItem(module.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished modules output")

elif mode[0] == MODE_CATEGORY:
    for category in catalog.categories:
        url = build_url({'mode': MODE_COURSE_BY_CATEGORY, 'category': category, 'cached': 'true'})
        li = xbmcgui.ListItem(category, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

elif mode[0] == MODE_COURSE_BY_CATEGORY:
    input_category = args.get('category', None)
    for course in catalog.get_courses_by_category(input_category[0]):
        url = build_url({'mode': MODE_MODULES, 'course': course.name, 'cached': 'true'})
        li = xbmcgui.ListItem(course.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

elif mode[0] == MODE_CLIPS:
    auth = login()
    input_module = args.get('module', None)
    title = args.get('course', None)
    for module in catalog.get_course_by_name(title[0]).modules:
        if module.title == input_module[0]:
            for clip in module.clips:
                clip_url = clip.get_url(xbmcplugin.getSetting(addon_handle, "username"))
                url = get_video_url(clip_url, auth["Token"])["VideoUrl"]
                li = xbmcgui.ListItem(clip.title, iconImage='DefaultVideo.png')
                li.addStreamInfo('video', {'width': 1024, 'height': 768, 'duration': clip.duration})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    debug_log_duration("finished clips output")

elif mode[0] == MODE_SEARCH:
    dialog = xbmcgui.Dialog()
    search_criteria = dialog.input("Search Criteria", type=xbmcgui.INPUT_ALPHANUM)
    debug_log_duration("pre-searching for: " + search_criteria)
    results = search_for(search_criteria)
    for course_name in results['Courses']:
        course = catalog.get_course_by_name(course_name)
        url = build_url({'mode': MODE_MODULES, 'course': course_name, 'cached': 'true'})
        li = xbmcgui.ListItem(course.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    debug_log_duration("finished search output")


catalog.close_db()

xbmcplugin.endOfDirectory(addon_handle)
