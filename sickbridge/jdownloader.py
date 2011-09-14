import urllib

def add_link(jdownloader_url, link):
    if jdownloader_url[-1] != '/':
        jdownloader_url = '%s/' % jdownloader_url
    try:
        request = urllib.urlopen('%s/action/add/links/%s' % (jdownloader_url, link))
    except IOError:
        return False
    return request.getcode() == 200

def in_queue(jdownloader_url, filename):
    if jdownloader_url[-1] != '/':
        jdownloader_url = '%s/' % jdownloader_url
    try:
        request = urllib.urlopen('%sget/downloads/alllist' % jdownloader_url)
    except IOError:
        return False
    return request.read().find('%s' % filename) >= 0

