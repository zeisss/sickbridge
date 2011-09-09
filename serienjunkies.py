###
# A little helper grabbing the links from serienjunkies.org
#

import string
import urllib

series_urls = {}

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
	#i = html.find('Dauer:')
	#if i >= 0:
	#	i = html.index(' ', i)
	#	j = html.index(' |', i)
	#	length = html[i+1:j]
	#
	#i = html.find('<strong>Gr')
	#if i >= 0:
	#	i = html.index(' ', i)
	#	j = html.index(' |', i)
	#	size= html[i+1:j]
	#
	#i = html.find('Sprache:')
	#if i >= 0:
	#	i = html.index(' ', i)
	#	j = html.index(' |', i)
	#	language = html[i+1:j]
	#
	#i = html.find('Format:')
	#if i >= 0:
	#	i = html.index(' ', i)
	#	j = html.index(' |', i)
	#	format = html[i+1:j]	
	#
	#i = html.find('Uploader:')
	#if i >= 0:
	#	i = html.index(' ', i)
	#	j = html.index('<', i)
	#	uploader = html[i+1:j]
	
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
		# print postDownloads
		# print "---"
		for (length, size, language, format, uploader, episodeName, urls) in postDownloads:
			links.append((length, size, language, format, uploader, episodeName, urls))
		offset = j
	return links
	
def myquote(name):
	result = ""
	for x in name:
		if x.isalpha() or x.isdigit():
			result = result + x
		else:
			result = result + "-"
	result = result.replace("--","-")
	return result.rstrip('-').strip('-')
	
def find_episode_no(name):
	i = name.find('.S')
	
	# Search for a ...S__E__...
	if i >= 0:
		
		s = name[i+1:i+7]
		
		if s[0] == 'S' and s[3] == 'E':
			se = int(s[1:3])
			ep = int(s[4:6])
			
			
			return (se, ep)
	
	offset = 0
	while 1:
		i = name.find('.', offset)
		if not (i>=0):
			break
		j = name.find('.',i+1)
		if not (j>=0):
			break
			
		offset = j
		
		s = name[i+1:j]
		k = s.find('&#215;')
		if not(k >= 0): # if there is no 'x', skip to next string part
			continue
		
		return (int(s[0:k]), int(s[k+6:]))
	return None
##
# The serie's download page must be available under http://www.serienjunkies.org/<SerieName>
#
# serieName = string
# serieId = thetvdb.com ID
# episodeName = Episodes Nae
# episodeNo = Number of Episode in the S__E__ format
# onlyLanguage = get only links for specified language (set to None for all languages)
def get_download_links(serieName, serieId, episodeName, episodeNo, url = None, onlyLanguage = None):
	if url == None:
		se = myquote(serieName)
		url = "http://serienjunkies.org/%s/" % se
	#print url
	s = urllib.urlopen(url)
	# assert s.getcode() == 200
	if ( s.getcode() != 200):
		print "Received code %d for %s" % (s.getcode(),  url)
	html = s.read()
	s.close()
	
	(seNo, epNo) = episodeNo
	
	downloads = parse_serienjunkies_html(html)
	
	result = []
	assert downloads != None
	for download in downloads:
		length, size, language, format, uploader, downloadName, links = download
		
		
		episodeNo = find_episode_no(downloadName)
		
		#print downloadName
		#print episodeNo
		
		if episodeNo == None:
			continue
		if onlyLanguage != None and string.lower(onlyLanguage) not in string.lower(language):
			continue
		if (episodeNo[0] == seNo and episodeNo[1] == epNo) or (downloadName.lower().find(episodeName.lower().replace(' ', '.')) >= 0):
			result.append(download)
	return result
	
	
	

