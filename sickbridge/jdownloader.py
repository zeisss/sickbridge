import urllib

def is_jd_on(jdownloader_url):
    '''
    Check if JDownloader is running (the app, not the download)
    '''

    if jdownloader_url[-1] != '/':
        jdownloader_url = '%s/' % jdownloader_url
    try:
        request = urllib.urlopen('%sget/rcversion' % jdownloader_url)
    except IOError:
        return False
    return request.getcode() == 200

def add_link(jdownloader_url, link):
    '''
    Add given link to JDownloader.
    Returns False if something went wrong
    '''

    if jdownloader_url[-1] != '/':
        jdownloader_url = '%s/' % jdownloader_url
    try:
        request = urllib.urlopen('%s/action/add/links/%s' % (jdownloader_url, link))
    except IOError:
        return False
    return request.getcode() == 200

def in_queue(jdownloader_url, filename):
    '''
    Check if the given file is already in the JDownloader queue.
    Returns False if not in queue or something went wrong.
    '''

    if jdownloader_url[-1] != '/':
        jdownloader_url = '%s/' % jdownloader_url
    try:
        request = urllib.urlopen('%sget/downloads/alllist' % jdownloader_url)
    except IOError:
        return False
    return request.read().find('%s' % filename) >= 0

