###
# A little helper grabbing the links from serienjunkies.org
#

import string
import urllib
import httplib

def debug(msg):
	# print "[DEBUG] %s" % msg
	pass

def parse_field(html, text):
	i = html.find(text)
	if i >= 0:
		beginSpace = html.find(' ', i)
		beginTagCloser = html.find('>', i)

		begin = -1
		endTag = -1
		if beginSpace >= 0:
			begin = beginSpace + 1
		else:
			begin = beginTagCloser + 1

		endSeparator = html.find(' |', begin)
		endTag = html.find('<', begin)

		if endSeparator >= 0:
			end = endSeparator
		else:
			end = endTag

		return html[begin:end]
	else:
		return None

def parse_author_line(html):
	length = None
	size = None
	language = None
	format = None
	uploader = None

	#print html

	length = parse_field(html, 'Dauer:')
	size = parse_field(html, '<strong>Gr')
	language = parse_field(html, 'Sprache:')
	format = parse_field(html, 'Format:')
	uploader = parse_field(html, 'Uploader:')

	return length, size, language, format, uploader

def parse_download_links(html):
	links = []
	offset = 0
	# parse the name
	i = html.find('<strong>')
	if not (i>=0): # seems to be no episode download
		return None
	j = html.index('</strong>', i)
	name = html[i+8:j]

	# now parse the links
	while 1:
		i = html.find("<a", offset)
		if not(i>=0):
			break
		i = html.index('href="', i)+6
		j = html.index('"', i)

		link = html[i:j]

		i = html.find('|', j)
		if i >= 0:
			j = html.index('<',i)
			serviceName = html[i+2:j]
		else:
			serviceName = None

		links.append((serviceName, link))

		offset = j
	return (name, links)

def parse_post_html(html):
	AUTHOR_START = 'Dauer:'
	AUTHOR_END = '</p>'

	links = []

	offset = 0
	while 1:
		i = html.find(AUTHOR_START, offset)
		if not (i>=0):
			break;
		j = html.index(AUTHOR_END,i)
		author_line = html[i:j+4]

		length, size, language, format, uploader = parse_author_line(author_line)

		#print length
		#print size
		#print language
		#print format
		#print uploader

		offset = j
		while 1:
			i = html.find('<p', offset)
			if not (i>=0):
				break;

			j = html.index('</p>', i)
			blockHtml = html[i:j + 4]

			# abort if on the next author line
			if blockHtml.find('Dauer') >= 0:
				break;

			X = parse_download_links(blockHtml)
			offset = j
			if X == None:
				continue
			episodeName, urls = X

			foundEpisode = (length, size, language, format, uploader, episodeName, urls)
			#print foundEpisode
			#print
			links.append(foundEpisode)
	return links

def parse_serienjunkies_html(html):
	POST_BEGIN = '<div class="post">'
	POST_END = '<p class="post-info-co">'

	links = []
	offset = 0
	while 1:
		i = html.find(POST_BEGIN, offset)
		if not (i >= 0):
			break
		j = html.index(POST_END, i)

		postDownloads = parse_post_html(html[i:j])
		
		for (length, size, language, format, uploader, episodeName, urls) in postDownloads:
			links.append((length, size, language, format, uploader, episodeName, urls))
		offset = j
	return links

def escape_show_name(name):
	'''
	Tries to replace all special chars as best as possible to mimick the url names of tv show names at serienjunkies.org
	'''
	result = ""
	for x in name:
		if x.isalpha() or x.isdigit():
			result = result + x
		else:
			result = result + "-"
	result = result.replace("--","-")
	return result.rstrip('-').strip('-').lower()

def parse_episode_no(name):
	# debug("Searching for episode no in %s" % name)
	
	offset = 0
	
	while True:
		i = name.find('.S', offset)
		if i < 0:
			break

		# Search for a ...S__E__...
		if i + 8 < len(name):
			s = name[i+1:i+7]
			if s[0] == 'S' and s[3] == 'E':
				se = int(s[1:3])
				ep = int(s[4:6])
				return (se, ep)
		
		offset = i + 1
	
	
	offset = 0

	for part in name.split('.'):
		k = part.find('&#215;')
		if not(k >= 0): # if there is no 'x', skip to next string part
			continue

		try:
			return (int(part[0:k]), int(part[k+6:]))
		except ValueError:
			None
	return None

def parse_next_page_link(html):
	NAVIGATION_START = "<div class=\"navigation\">"
	NAVIGATION_END = "</div>"
	NEXT_IDENTIFIER = " class=\"next\">&raquo;</a>"

	navStart = html.find(NAVIGATION_START)
	if not(navStart >= 0): return None
	navEnd = html.find(NAVIGATION_END, navStart)
	assert(navEnd >= 0)
	navigationBlock = html[navStart:navEnd]

	if navigationBlock.find(NEXT_IDENTIFIER) >= 0: # we have a next link
		a = navigationBlock.rfind("<a href=\"")
		assert(a >= 0)
		b = navigationBlock.find("\" class=\"next\">", a)
		assert(b >= 0)
		return navigationBlock[a + 9:b]

CACHE = {}


def get_download_links(showName, showId, episodeName, episodeId, url = None):
	'''
	Returns all downloads for the given show and with the given episode.

	The serie's download page must be available under http://www.serienjunkies.org/serie/<ShowName>

	- showName = string
	- showId = thetvdb.com ID
	- episodeName = Episodes Nae
	- episodeId <=> (seasonNo, episodeNo)
	'''
	if url == None:
		se = escape_show_name(showName)
		# /serie/ must be part of the URL, otherwise the generated next-links  do not work.
		url = "http://serienjunkies.org/serie/%s/" % se
	#print url

	result = []
	_collect_download_links(showName, showId, episodeName, episodeId, url, result)
	return result

def _collect_download_links(showName, showId, episodeName, episodeId, url, result):
	# print "'%s' %d '%s' %s %s %d" % (showName, showId, episodeName, str(episodeId), url, len(result))
	# Check if we have the page content in the CACHE or download it
	if url in CACHE:
		html = CACHE[url]
	else:
		print "[INFO] Fetching %s" % url
		resp = urllib.urlopen(url)
		if (resp.getcode() != 200):
			print "[ERROR] Received code %d for %s" % (resp.getcode(), url)

		if 'content-type' not in resp.headers:
			print "[WARN] Result has no content-type!"
		elif (resp.headers['content-type'][0:9] != "text/html"):
			print "[WARN] Content-type is unexpected: %s" % resp.headers['content-type']
			
		if 'content-encoding' in resp.headers and resp.headers['content-encoding'] == 'gzip':
			# See http://stackoverflow.com/questions/2423866/python-decompressing-gzip-chunk-by-chunk/2424549#2424549
			import zlib
			html = zlib.decompress(resp.read(), 16+zlib.MAX_WBITS)			
		else:
			html = resp.read()
		resp.close()

		CACHE[url] = html

	if html[0:14] != '<!DOCTYPE html':
		print "[ERROR] Result page for %s does not look like HTML: %s" % (url, html[0:20])

	# print html[0:1000]
	# Now parse the page content
	(seasonNo, episodeNr) = episodeId

	allDownloads = parse_serienjunkies_html(html)

	assert allDownloads != None
	for download in allDownloads:
		length, size, language, format, uploader, downloadName, links = download

		downloadEpisodeNr = parse_episode_no(downloadName)
		if downloadEpisodeNr == None:
			print "[WARN] Skipping download %s without episode-no" % downloadName
			continue

		# We do not allow searching for episodeName, when the episodeName is part of the showName 
		# e.g. for the S01E01 of Dexter this was the case and resulted in wrong downloads
		if not (episodeName.lower() in showName.lower()):
			episodeNameMatch = (downloadName.lower().find(episodeName.lower().replace(' ', '.')) >= 0)
		else:
			episodeNameMatch = False
		episodeIdMatch = (downloadEpisodeNr[0] == seasonNo and downloadEpisodeNr[1] == episodeNr)		
		if episodeIdMatch or episodeNameMatch:
			result.append(download)

	nextUrl = parse_next_page_link(html)
	if nextUrl != None:
		# Recursively collect links from the next page as well.
		_collect_download_links(showName, showId, episodeName, episodeId, nextUrl, result)

