import urllib


SICKBEARD_SHOW_PAGE = "/home/displayShow?show="
SICKBEARD_BACKLOG_PAGE = "/manage/backlogOverview"

cache = dict()

def debug(msg):
	# print '[DEBUG] %s' % msg
	pass

def parse_show_html(html):
	i = html.find("<a")

	i = html.find("show=", i)
	j = html.find("\"", i)
	showId = int(html[i+5:j])
	
	i = html.find(">", i)
	j = html.find("<",i)
	name = html[i+1:j]

	return (name, showId)

def parse_episode_html(html):
	i = html.find('<td align="center">')
	i = html.find('>',i)
	j = html.find('</td>')

	episodeNo = html[i+1:j]

	i = html.find('<td>', j)
	j = html.find('</td>', i)
	episodeName = html[i+4:j]

	# We pimp the episodeNo now
	# Is: A'x'B
	# Becomes: 'S'AA'E'BB
	i = episodeNo.find('x')
	season = int(episodeNo[0:i])
	episode = int(episodeNo[i+1:])

	# episodeNo = 'S%02dE%02d' % (season, episode)

	return ((season, episode), episodeName)

def parse_backlog_page(html):
	SHOW_START = "<h2 class=\"backlogShow\">"
	SHOW_END = "</h2>"
	EP_START = "<tr class=\"wanted\">"
	EP_END = "</tr>"

	result = []
	offset = 0

	while 1:
		# Check for the series name
		showStart = html.find(SHOW_START, offset)
		if not(showStart >= 0):
			debug('No more shows found.')
			break;

		# Parse the series name
		showEnd = html.find(SHOW_END, showStart)
		showName, showId = parse_show_html(html[showStart:showEnd])

		offset = showEnd

		nextShowStart = html.find(SHOW_START, offset)
		if nextShowStart < 0:
			nextShowStart = html.index('</table>', offset)

		debug('Found show %s (%d)' % (showName, showId))

		while (1):
			# parse the episode blocks
			i = html.find(EP_START, offset)
			# print i

			if not (i >= 0) or nextShowStart < i:
				debug('No more episodes found.')
				break
			j = html.index(EP_END, i)
			#print j
			episodeHtml = html[i:j]
			(episodeNo, episodeName) = parse_episode_html(episodeHtml)
			#print episodeName
			debug("Found %2dx%2d %s" % (episodeNo[0], episodeNo[1], episodeName))
			result.append((showName, showId, episodeName, episodeNo))
			offset = j
	return result

def get_backlog_list(server_url):
	page = urllib.urlopen("%s%s" % (server_url, SICKBEARD_BACKLOG_PAGE))
	html = page.read()
	page.close()

	episodes = parse_backlog_page(html)
	#print
	return episodes

def parse_show_page(html, show_id):
	def parse_field(htmlsnippet, label):
		a = htmlsnippet.find(">%s:" % label)
		if not (a >= 0):
			print "ERR-005: No start found for label %s" % label
			return None

		b = htmlsnippet.find("<td>", a) + 4
		c = htmlsnippet.find("</td>", b)

		# if custom quality is choosen, sickbeard lists the chosen qualities
		# instead of showing "Custom". In this case we should cut the string
		# so, that we get the chosen qualities.
		if label == 'Quality':
			snip = htmlsnippet[b:c].strip()
			if '<b>' in snip:
				start = snip.find('<b>') + 3
				end = snip.find('</b>', start)
				return snip[start:end]

		# The language field has a an image. Cut it out, if there is text afterwards
		if label == 'Language' and htmlsnippet[b] == '<':
			b = htmlsnippet.find('>', b+1) + 1
		return htmlsnippet[b:c].strip()

	SUMMARY_START="id=\"summary\""
	SUMMARY_END="</div>"

	TITLE_START = "<h1 class=\"title\">"
	TITLE_END = "</a>"

	titleStart = html.find(TITLE_START)
	if not(titleStart >= 0):
		print "ERR-003: No start-title tag found for show."
		return None
	titleStart = html.find(">", titleStart + len(TITLE_START)) + 1
	titleEnd = html.find(TITLE_END, titleStart)
	if not(titleEnd >= 0):
		print "ERR-004: No end-title tag found for show."
		return None

	showName = html[titleStart:titleEnd]

	summaryStart = html.find(SUMMARY_START)
	if not (summaryStart >= 0):
		print "ERR-001: No summary found"
		return None

	summaryEnd = html.find(SUMMARY_END, summaryStart)
	if not (summaryEnd >= 0):
		print "ERR-002: No end summary found"
		return None

	summary = html[summaryStart:summaryEnd]
	#print summaryStart, summaryEnd
	return (
		show_id, # show id
		showName, # official name
		parse_field(summary, 'Location'), # Storage path
		parse_field(summary, 'Quality'),
		parse_field(summary, 'Language'),
		parse_field(summary, 'Status'),
		parse_field(summary, 'Paused').find('no') >= 0, # active, so check for paused=No
		parse_field(summary, 'Air-by-Date').find('yes') >= 0,
		parse_field(summary, 'Flatten Folders').find('no') >= 0 # was: "Season Folders", so check for Flatten=No
	)

def get_show_settings(server_url, show_id):
	'''
	Returns a tuple with the following fields:
	- ShowID
	- Official Name
	- Storage Path
	- Quality
	- Language
	- Status ("Continuing", ..)
	- Active (True, False)
	- Air By Date (True, False)
	- Season Folders (True, False)
	'''
	sUrl = "%s%s%s" % (server_url, SICKBEARD_SHOW_PAGE, show_id)
	if sUrl in cache:
		return cache[sUrl]
	else:
		print "[INFO] Fetching show-page %s" % sUrl
		page = urllib.urlopen(sUrl)
		html = page.read()
		page.close()

		result = parse_show_page(html, show_id)
		if result:
			cache[sUrl] = result
		return result
