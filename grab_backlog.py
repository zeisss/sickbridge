import urllib


SICKBEARD_URL = "http://localhost:8081"
SICKBEARD_BACKLOG_PAGE = "/manage/backlogOverview"

def parse_season_html(html):
	i = html.find("<a") 
	
	i = html.find("show=", i)
	j = html.find("\"", i)
	seasonId = html[i+5:j]
	
	
	i = html.find(">", i)
	j = html.find("<",i)
	name = html[i+1:j]
	
	return (name, seasonId)
	
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
	
	episodeNo = 'S%02dE%02d' % (season, episode)
	
	return episodeNo, episodeName
	
def parse_backlog_page(html):
	SEASON_START = "<tr class=\"seasonheader\">";
	EP_START = "<tr class=\"wanted\">"
	EP_END = "</tr>"
	
	result = []
	offset = 0
	
	while 1:
		# Check for the series name
		seasonStart = html.find(SEASON_START, offset)
		if not(seasonStart >= 0):
			break;
		
		# Parse the series name
		seasonEnd = html.find("</tr>", seasonStart)
		seasonName, seasonId = parse_season_html(html[seasonStart:seasonEnd])
		#print "%s (%s)" % (seasonName, seasonId)
		offset = seasonEnd
		
		nextSeasonStart = html.find(SEASON_START, offset)
		
		while (1):
			# parse the episode blocks
			i = html.find(EP_START, offset)
			#print i
			if not (i >= 0) or nextSeasonStart < i:
				break
			j = html.find(EP_END, i)
			#print j
			episodeHtml = html[i:j]
			episodeNo, episodeName = parse_episode_html(episodeHtml)
			result.append((seasonName, seasonId, episodeName, episodeNo))
			offset = j
	return result
	
def get_backlog_list(server_url):
	page = urllib.urlopen("%s%s" % (server_url, SICKBEARD_BACKLOG_PAGE))
	html = page.read()
	page.close()
	
	episodes = parse_backlog_page(html)
	return episodes
	
def main():
	print "Scanning %s's backlog" % SICKBEARD_URL
	
	episodes = get_backlog_list(SICKBEARD_URL)
	for x in episodes:
		print x

if __name__ == "__main__":
	main()