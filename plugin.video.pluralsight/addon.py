import os
import sys

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import urllib
import urlparse

from resources.lib import requests
from resources.data.models import Catalog
import json

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

temp_path = xbmc.translatePath("special://temp/")
catalog_path = os.path.join(temp_path, "catalog.txt")

xbmcplugin.setContent(addon_handle, 'movies')

debug = True

cached = args.get('cached', None)
if cached is None and debug is not True:
    headers = {"Accept-Language": "en-us", "Content-Type": "application/json", "Accept": "application/json",
               "Accept-Encoding": "gzip"}
    r = requests.get("http://www.pluralsight.com/metadata/live/courses/", headers=headers)

    with open(catalog_path,"w") as catalog_data:
        catalog_data.write(json.dumps(r.json()))

raw_catalog = open(catalog_path,"r")
catalog = Catalog.Catalog(json.load(raw_catalog))


def debug_log(string):
    xbmc.log(string, xbmc.LOGNOTICE)

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def login():
    debug_log("Starting login")
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    password = xbmcplugin.getSetting(addon_handle,"password")
    payload = {"Password":password}
    username = xbmcplugin.getSetting(addon_handle,"username")
    url = "https://www.pluralsight.com/metadata/live/users/" + username + "/login"
    debug_log("Using url: " + url)
    r = requests.post(url, data=payload,headers=headers)
    debug_log("Completed login")
    return r.json()

def get_video_url(url,token):
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {"Token": token}
    r = requests.post(url, data=payload,headers=headers)
    return r.json()

mode = args.get('mode', None)

if mode is None:
    debug_log("No mode, defaulting to main menu")
    url = build_url({'mode': 'courses', 'cached':'true'})
    li = xbmcgui.ListItem('Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'category', 'cached':'true'})
    li = xbmcgui.ListItem('Categories', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'search', 'cached':'true'})
    li = xbmcgui.ListItem('Search', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "courses":
    for course in catalog.courses:
        url = build_url({'mode': 'modules', 'course': course.name, 'cached': 'true'})
        li = xbmcgui.ListItem(course.title, iconImage='DefaultFolder.png')
        li.setInfo('video', {'plot': course.description, 'genre': course.category})
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "modules":
    title = args.get('course', None)
    for module in catalog.get_course_by_name(title[0]).modules:
        url = build_url({'mode': 'clips','course':title[0], 'module': module.title, 'cached': 'true'})
        li = xbmcgui.ListItem(module.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "category":
    for category in catalog.categories:
        url = build_url({'mode': 'courses_by_category', 'category':category, 'cached':'true'})
        li = xbmcgui.ListItem(category, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "courses_by_category":
    input_category = args.get('category', None)
    for course in catalog.get_courses_by_category(input_category[0]):
        url = build_url({'mode': 'modules', 'course': course.name, 'cached': 'true'})
        li = xbmcgui.ListItem(course.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "clips":
    auth = login()
    input_module = args.get('module', None)
    title = args.get('course', None)
    for module in catalog.get_course_by_name(title[0]).modules:
        if module.title == input_module[0]:
            for clip in module.clips:
                clip_url = clip.get_url(xbmcplugin.getSetting(addon_handle,"username"))
                url = get_video_url(clip_url, auth["Token"])["VideoUrl"]
                li = xbmcgui.ListItem(clip.title,  iconImage='DefaultVideo.png')
                li.addStreamInfo('video', {'width': 1024, 'height': 768, 'duration': clip.duration})
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)
