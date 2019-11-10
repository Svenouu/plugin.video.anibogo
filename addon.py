# -*- coding: utf-8 -*-
"""
    anibogo
"""
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
from xbmcgui import ListItem
from xbmcplugin import addDirectoryItem, endOfDirectory
from xbmcswift2 import Plugin
import urllib
import sys
import os
import re
import web_pdb
from YDStreamExtractor import getVideoInfo

addon = xbmcaddon.Addon()
plugin = Plugin()
_L = plugin.get_string

plugin_path = addon.getAddonInfo('path')
url_root = addon.getSetting('root_url')
lib_path = os.path.join(plugin_path, 'resources', 'lib')
sys.path.append(lib_path)

import anibogo

tPrevPage = u"[B]<%s[/B]" % _L(30100)
tNextPage = u"[B]%s>[/B]" % _L(30101)

@plugin.route('/')
def main_menu():
    items = [
        {'label':u"Recherche", 'path':plugin.url_for('search_list', searchTerms='-', url='-', page=1)},
        {'label':u"방영중", 'path':plugin.url_for("prog_list", cate='status/ongoing', url='-', page=1)},        
        {'label':u"완결", 'path':plugin.url_for("prog_list", cate='status/complete', url='-', page=1)},
        {'label':u"영화", 'path':plugin.url_for("prog_list", cate='movies', url='-', page=1)},
        {'label':u"TOP 30", 'path':plugin.url_for("prog_list", cate='top10', url='-', page=1)}     
    ]
    return items

@plugin.route('/search/<searchTerms>/<url>/<page>/')
def search_list(searchTerms, url, page):
    anibogo.ROOT_URL = url_root
    if searchTerms == '-':
        keyboard = xbmc.Keyboard()
        keyboard.doModal()
        if (keyboard.isConfirmed()):
            search_list(keyboard.getText(), '-', page)
    else:
        url = anibogo.ROOT_URL+'search?q=%s&page=%s' % (urlEncodeNonAscii(searchTerms), page)        

        result = anibogo.parseProgList(url, page)
        createVideoDirectory(result, searchTerms, True)
    return main_menu()

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

@plugin.route('/category/<cate>/<url>/<page>/')
def prog_list(cate, url, page):
    #web_pdb.set_trace()
    anibogo.ROOT_URL = url_root
    url = anibogo.ROOT_URL+'%s?page=%s' % (cate, page)
    result = anibogo.parseProgList(url, page)
    createVideoDirectory(result, cate, False)

@plugin.route('/episode/<url>/<page>/')
def episode_list(url, page):
    if url.find('?') != -1:
        url = url[:url.find('?')]+'?page=%s' % (page)
    else:
        url = url+'?page=%s' % (page)
    result = anibogo.parseEpisodeList(url, page)
    createEpisodeDirectory(result)

def createVideoDirectory(result, cateOrSearchTerms, isSearch):
    listing = []
    for video in result['link']:
        list_item = xbmcgui.ListItem(label=video['title'], thumbnailImage=video['thumbnail'])
        list_item.setInfo('video', {'title': video['title']})
        if cateOrSearchTerms == 'movies':
            url = plugin.url_for('video_list', url=video['url'])
        else:
            url = plugin.url_for('episode_list', url=video['url'], page=video['page'])
        is_folder = True
        listing.append((url, list_item, is_folder))
    
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    
    if 'prevpage' in result:
        if isSearch:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('search_list', searchTerms=cateOrSearchTerms, url=result['prevpage']['url'], page=result['prevpage']['currentPage']),
                ListItem(tPrevPage), True)
        else:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('prog_list', cate=cateOrSearchTerms, url=result['prevpage']['url'], page=result['prevpage']['currentPage']),
                ListItem(tPrevPage), True)
    if 'nextpage' in result:
        if isSearch:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('search_list', searchTerms=cateOrSearchTerms, url=result['nextpage']['url'], page=result['nextpage']['currentPage']),
                ListItem(tNextPage), True)
        else:
            addDirectoryItem(
                plugin.handle,
                plugin.url_for('prog_list', cate=cateOrSearchTerms, url=result['nextpage']['url'], page=result['nextpage']['currentPage']),
                ListItem(tNextPage), True)

    xbmcplugin.endOfDirectory(plugin.handle)

def createEpisodeDirectory(result):
    listing = []
    for video in result['link']:
        list_item = xbmcgui.ListItem(label=video['title'], thumbnailImage=video['thumbnail'])
        list_item.setInfo('video', {'title': video['title']})
        url = plugin.url_for('video_list', url=video['url'])
        is_folder = True
        listing.append((url, list_item, is_folder))
    
    xbmcplugin.addDirectoryItems(plugin.handle, listing, len(listing))
    
    if 'prevpage' in result:
       addDirectoryItem(
                plugin.handle,
                plugin.url_for('episode_list', url=result['prevpage']['url'], page=result['prevpage']['currentPage']),
                ListItem(tPrevPage), True)
    if 'nextpage' in result:
        addDirectoryItem(
                plugin.handle,
                plugin.url_for('episode_list', url=result['nextpage']['url'], page=result['nextpage']['currentPage']),
                ListItem(tNextPage), True)

    xbmcplugin.endOfDirectory(plugin.handle)


@plugin.route('/episode/<url>/')
def video_list(url):
    info = anibogo.parseVideoList(url)

    items = []
    prev_vurl = ""
    for item in info:
        vurl = item['url']
        if vurl != prev_vurl:
            items.append({'label':item['title'], 'path':plugin.url_for('play_video', url=vurl)})
            prev_vurl = vurl
    return items

@plugin.route('/play/<url>/')
def play_video(url):
    url = anibogo.extract_video_url(url)
    
    plugin.play_video({'path':url, 'is_playable':True})
    return plugin.finish(None, succeeded=False)     # trick not to enter directory mode

if __name__ == "__main__":
    plugin.run()

# vim:sw=4:sts=4:et
