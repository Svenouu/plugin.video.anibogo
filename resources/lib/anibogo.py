# -*- coding: utf-8 -*-
"""
    MaruTV - Korea Drama/TV Shows Streaming Service
"""
import web_pdb
import xbmcgui
import urllib2
import urlparse
import re
import requests
import json
from bs4 import BeautifulSoup
import resolveurl

ROOT_URL = ''
ROOT_URL_TV = ''
UserAgent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"

def parseProgList(main_url, currentPage):
    req = urllib2.Request(main_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')

    result = {'link':[]}
    for item in soup.find("div", {"class":"bao"}):
        thumb = ""
        imgHtml = item.find_next('img')
        if imgHtml:
            thumb = imgHtml['data-src']
        aHtml = item.find_next('a')
        if aHtml:
            pHtml = item.find_next('strong')
            if pHtml:
                title = pHtml.text
            url = ROOT_URL + aHtml['href']
            result['link'].append({'title':title, 'cate':'video', 'url':url, 'page':1, 'thumbnail':thumb})

    # navigation
    if currentPage:
        if currentPage != 1:
            result['prevpage'] = {'url': main_url, 'currentPage':currentPage - 1}
        
        result['nextpage'] = {'url': main_url, 'currentPage':currentPage + 1}
    return result

def parseEpisodeList(main_url, currentPage):
    req = urllib2.Request(main_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')

    result = {'link':[]}
    for item in soup.find("div", {"class":"thumbnail1"}):
        thumb = ""
        imgHtml = item.find_next('img')
        if imgHtml:
            thumb = imgHtml['src']
        aHtml = item.find_next('a')
        if aHtml:
            pHtml = item.find_next('strong')
            if pHtml:
                title = pHtml.text
            url = aHtml['href']
            result['link'].append({'title':title, 'cate':'video', 'url':url, 'thumbnail':thumb})

    # navigation
    if currentPage:
        if currentPage != 1:
            result['prevpage'] = currentPage - 1
        
        result['nextpage'] = currentPage + 1
    return result

def parseVideoList(main_url):
    req = urllib2.Request(main_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    result = []
    iframe = soup.find("iframe")
    
    #web_pdb.set_trace()
    if iframe:
        req = urllib2.Request(iframe['src'])
        req.add_header('User-Agent', UserAgent)
        req.add_header('Referer', 'http://www.marutv.org/')
        resp = urllib2.urlopen(req)
        doc = resp.read()
        resp.close()
        soup = BeautifulSoup(doc, from_encoding='utf-8')
        links = soup.find("div", {"id":"video_link_panel"})
        if links:
            for item in links.findAll("input", {"type":"hidden"}):
                result.append({'title':item["id"], 'url':item["value"]})
    return result

def extract_video_url(url):
    resolved = resolveurl.resolve(url)
    if not resolved:
        return tryresolveurl(url)
    return resolved

def tryresolveurl(vid_url):
    if 'k-vid.net' in vid_url or 'dramacool9' in vid_url:
        return resolveurl_kvid(vid_url)
    elif 'verystream' in vid_url:
        return resolveurl_verystream(vid_url)
    elif 'xstreamcdn.com' in vid_url:
        return resolveurl_xstreamcdn(vid_url)
    elif 'toctube.space' in vid_url:
        return resolveurl_peertube(vid_url, 'toctube.space')
    elif 'toctube.club' in vid_url:
        return resolveurl_peertube(vid_url, 'toctube.club')
    elif 'toctube.com' in vid_url:
        return resolveurl_peertube(vid_url, 'toctube.com')
    elif 'jetload' in vid_url:
        return resolveurl_jetload(vid_url)
    elif 'blob:' in vid_url:
        return resolveurl_blob(vid_url)
    elif 'kshows' in vid_url:
        return resolveurl_kshows(vid_url)
    elif 'kdrama.eu' in vid_url:
        return resolveurl_kdrama(vid_url)
    elif 'flashvid' in vid_url:
        return resolveurl_flashvid(vid_url)
    elif 'supervid' in vid_url:
        return resolveurl_supervid(vid_url)
    else:
        ips = re.findall( r'[0-9]+(?:\.[0-9]+){3}', vid_url )
        if ips:
            return resolveurl_peertube(vid_url, ips[0])

    return vid_url

def resolveurl_supervid(vid_url):
    response = requests.get(url = vid_url)

    html = response.content
    arr = re.search('var arr = \[\"(.+?)\"', html)
    sUrl = re.search('var sUrl = \"(.+?)\";', html)
    splitUrl = vid_url.split('/')
    if arr and sUrl:
        finalUrl = sUrl.group(1).replace('\"+ arr[sec]+\"', arr.group(1)) + splitUrl[-1] + '.m3u8?qa='
        return finalUrl
        

def resolveurl_jetload(vid_url):
    req = urllib2.Request(vid_url)
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    filename = soup.find("input", {"id": "file_name"})
    srv = soup.find("input", {"id": "srv_id"})
    
    if filename and srv:
        data = {'file_name':filename['value'] + '.mp4',
            'srv':srv['value']} 
  
        response = requests.post(url = 'https://jetload.net/api/download', data = data)
        return response.text
    else:
        return vid_url

def resolveurl_kdrama(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    
    m = re.findall('\"file\":\"(.+?)\",\"label\":', doc)
    if m:
        for decodedUrl in reversed(m):
            if 'redirector' in decodedUrl:
                response = requests.get(url = decodedUrl, allow_redirects=False)
                if response.status_code == 302:
                    soup = BeautifulSoup(response.content, from_encoding='utf-8')
                    ahref = soup.find("a")
                    if ahref :
                        return ahref["href"]
            else:
                return decodedUrl

def resolveurl_kshows(vid_url):
    #web_pdb.set_trace()
    if not 'http:' in vid_url and not 'https:' in vid_url:
        vid_url = 'http:'+vid_url
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    
    m = re.search('file: \'(.+?)\',label', doc)
    if m:
        return m.group(1)

def resolveurl_blob(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    
    m = re.search('var urlVideo = \\\'http://(.+?).m3u8', doc)
    if m:
        return 'http://' + m.group(1) + ".m3u8"


def resolveurl_peertube(vid_url, ip):
    #web_pdb.set_trace()
    uuid = vid_url.split('/')[-1].replace('?embed=', '')
    current_res = 0
    higher_res = -1
    file_url = ''
    resp = urllib2.urlopen('http://'+ ip +'/api/v1/videos/' + uuid)
    metadata = json.load(resp)
    
    for f in metadata['files']:
        # Get file resolution
        res = f['resolution']['id']
        if res > current_res:
            file_url = f['fileUrl'] 
            current_res = res
        elif ( res < higher_res or higher_res == -1 ):
            file_url = f['fileUrl'] 
            higher_res = res
    
    return file_url

def resolveurl_flashvid(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'https://www.flashvid.net/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    sources = soup.findAll("source")
    soup = None
    
    if sources:
        urlsFound = {}
        for source in sources:
            datavideo = source['src'] 
            if datavideo:
                urlsFound[source['title']] = datavideo
        if urlsFound:
            dialog = xbmcgui.Dialog()
            ret = dialog.select('Choose source', urlsFound.keys())
            if ret >= 0:
                return urlsFound.values()[ret]
    return vid_url

def resolveurl_xstreamcdn(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'https://xstreamcdn.com/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    video = soup.find("video")
    
    if video:
        return video['src']
    else:
        return vid_url

def resolveurl_verystream(vid_url):
    #web_pdb.set_trace()
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'https://verystream.com/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    videolink = soup.find(id="videolink")
    if videolink:
        response = requests.get(url = "https://verystream.com/gettoken/" + videolink.text, allow_redirects=False)
        return response.headers['Location']
    else:
        return vid_url

def resolveurl_kvid(vid_url):
    req = urllib2.Request(vid_url)
    req.add_header('User-Agent', UserAgent)
    req.add_header('Referer', 'http://www.marutv.org/')
    resp = urllib2.urlopen(req)
    doc = resp.read()
    resp.close()
    soup = BeautifulSoup(doc, from_encoding='utf-8')
    embedVids = soup.findAll("li", {"class":"linkserver"})

    soup = None
    #web_pdb.set_trace()
    if embedVids:
        urlsFound = {}
        for embedVid in embedVids:
            datavideo = embedVid['data-video'] 
            if datavideo:
                urlsFound[embedVid.text] = datavideo
        if urlsFound:
            dialog = xbmcgui.Dialog()
            ret = dialog.select('Choose source', urlsFound.keys())
            if ret >= 0:
                resolved = resolveurl.resolve(urlsFound.values()[ret])
                if resolved:
                    return resolved
                else:
                    return tryresolveurl(urlsFound.values()[ret])
    return vid_url
if __name__ == "__main__":
    pass

# vim:sts=4:sw=4:et
