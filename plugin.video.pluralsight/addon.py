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


def build_url(query):
    return base_url + '?' + urllib.urlencode(query)


mode = args.get('mode', None)

if mode is None:
    url = build_url({'mode': 'courses', 'cached':'true'})
    li = xbmcgui.ListItem('Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'category', 'cached':'true'})
    li = xbmcgui.ListItem('Courses By Category', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'search', 'cached':'true'})
    li = xbmcgui.ListItem('Search Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "courses":
    for course in catalog.courses:
        url = build_url({'mode': 'modules', 'course': course.title.encode('UTF8'), 'cached': 'true'})
        li = xbmcgui.ListItem(course.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "modules":
    title = args.get('course', None)
    print title
    for module in catalog.get_courses_by_title(title[0])[0].modules:
        url = build_url({'mode': 'clips','course':title[0], 'module': module.title, 'cached': 'true'})
        li = xbmcgui.ListItem(module.title, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "clips":
    input_module = args.get('module', None)
    title = args.get('course', None)
    for module in catalog.get_courses_by_title(title[0])[0].modules:
        if module.title == input_module[0]:
            for clip in module.clips:
                url = build_url({'mode': 'play'})
                li = xbmcgui.ListItem(clip.title, iconImage='DefaultFolder.png')
                xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == "category":
    for cat in catalog.categories:
        url = build_url({'mode': 'newest', 'cached':'true'})
        li = xbmcgui.ListItem(cat, iconImage='DefaultFolder.png')
        xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addon_handle)

else:
    url = build_url({'cache':'true'})
    li = xbmcgui.ListItem(mode[0] + ' Video', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)