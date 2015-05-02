import os
import sys

import xbmc
import xbmcaddon
import xbmcplugin
import xbmcgui

import urllib
import urlparse

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

xbmcplugin.setContent(addon_handle, 'movies')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

mode = args.get('mode', None)

if mode is None:
    url = build_url({'mode': 'newest'})
    li = xbmcgui.ListItem('Newest Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'popular'})
    li = xbmcgui.ListItem('Popular Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'category'})
    li = xbmcgui.ListItem('Courses By Category', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    url = build_url({'mode': 'search'})
    li = xbmcgui.ListItem('Search Courses', iconImage='DefaultFolder.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url,listitem=li, isFolder=True)

    xbmcplugin.endOfDirectory(addon_handle)

else:
    url = base_url
    li = xbmcgui.ListItem(mode[0] + ' Video', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url= url, listitem=li)
    xbmcplugin.endOfDirectory(addon_handle)