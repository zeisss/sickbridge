from sickbridge import sickbeard
from sickbridge import jdownloader
from sickbridge import serienjunkies
from sickbridge import sickbridge
	

# Defaults / Globals
JDOWNLOADER_URL = "http://localhost:8765/"
SICKBEARD_URL = "http://localhost:8081/"
SICKBEARD_NAME = None
SICKBEARD_PASS = None
PREFERRED_HOSTER = "netload.in"
LANGUAGE = None
	
def parseOptions():
	"""Using command line arguments to change config file"""
	import argparse
	# set up the parser
	parser = argparse.ArgumentParser(description='Adds your sickbeard backlog to JDownloader by search serienjunkies.org.')
	parser.add_argument('-o', action='store', dest='host', help='set prefered hoster')
	parser.add_argument('-s', action='store', metavar='URL', dest='sburl', help='set sickbeard url')
	parser.add_argument('-j', action='store', metavar='URL', dest='jdurl', help='set jdownloader url')
	parser.add_argument('-n', action='store', metavar='NAME', dest='sbname', help='set sickbeard name')
	parser.add_argument('-p', action='store', metavar='PASSWORD', dest='sbpass', help='set sickbeard password')
	parser.add_argument('-l', action='store', choices=['en', 'de', 'both'], dest='language', help='set language')	
	parser.add_argument('-d', action='store_true', dest='defaults', help='use default settings (use -w to reset config. file)')	
	parser.add_argument('-w', action='store_true', dest='save', help='write arguments to the configuration file and exit')
	parser.add_argument('--delete', action='store_true', dest='clear', help='delete history and exit')	
	
	# parse
	return vars(parser.parse_args())
	
def action_default(config, history):
	# if name and / or password are saved, build the right url
	SICKBEARD_URL = config.get('sburl')
	
	if config.get('sbpass') != None and config.get('sbname') != None:
		SICKBEARD_URL_C = SICKBEARD_URL.replace('://', '://%s:%s@' % (config.get('sbname'), config.get('sbpass')))
	elif config.get('sbname') != None:
		SICKBEARD_URL_C = SICKBEARD_URL.replace('://', '://%s@' % config.get('sbname'))
	else:
		SICKBEARD_URL_C = SICKBEARD_URL
		
    # Counters for stat printing
	cBacklogSize = 0
	cNotDownloadedDueToCache = 0
	cAddedToDownloader = 0
	
	
	print "Scanning %s's backlog" % config.get('sburl')
	
	episodes = sickbeard.get_backlog_list(SICKBEARD_URL_C)
	cBacklogSize = len(episodes)
	
	# Foreach episode in the backlog 
	for x in episodes:
		(seriesName, seriesId, episodeName, episodeNo) = x
		
		# Print info header
		print "===="
		print "%s S%sE%s - %s" % (seriesName, episodeNo[0], episodeNo[1], episodeName)
		
		# Skip episode, if the history shows we already added it once to jdownloader
		# Possible reason for still beeing in the backlog:
		# - JDownloader is still downloader
		# - Files are offline
		# - many more ...
		if history.has_downloaded(seriesName, episodeNo, episodeName):
			print "Already in history. Delete %s to download again." % history.get_path(seriesName, episodeNo, episodeName)
			cNotDownloadedDueToCache = cNotDownloadedDueToCache + 1
			continue
		
		# Check if we have a specific URL to check for this TV-Serie (Sometimes the script cannot guess the page url correctly)
		specificUrl = config.get_mapping(seriesName)
			
		# Grab the page and parse it into a list of available episodes
		X = serienjunkies.get_download_links(seriesName, seriesId, episodeName, episodeNo, url=specificUrl, onlyLanguage=config.get('language'))
		
		# If none are found => Abort
		if X == None or len(X) == 0:
			print "Not found"
		# We found some downloads for our wished episode :D
		else:
			# Sort them (If we have a preferred hoster, this sorts it to the top)
			sortedDownloads = sorted(X, key=sickbridge.download_sorter(config))
			
			# Another check if we might already be downloading this file
			if jdownloader.in_queue(JDOWNLOADER_URL, sortedDownloads[0][5]):
				print "Already in queue"
			else:
				# Schedule the top download
				sickbridge.schedule_download(config, sortedDownloads[0])
				# Mark episode as downloaded by SickBridge
				history.add_download(seriesName, episodeNo, episodeName)
				cAddedToDownloader = cAddedToDownloader + 1
	
	# Print final results
	print 
	print
	print "==============================================================================="
	print "= %3d of %3d were previously added to queue.                                  =" % (cNotDownloadedDueToCache, cBacklogSize)
	print "= Successfully added %3d new links to queue.                                  =" % (cAddedToDownloader)
	print "==============================================================================="

def action_clear(config, history):
	history.clear()
	print "Cleared History"
	
def action_save(config, history):
	config.write_config()
	
def main():
	print "Sickbridge"
	print "=========="
	config = sickbridge.SickbridgeConfig()
	
	history = sickbridge.SickbridgeHistory(config)
	
	
	# Parse Options
	vargs = parseOptions()
	
	# react
	if vargs['defaults']:
		config.set('jdurl', "http://localhost:7151/")
		config.set('sburl', "http://localhost:8081/")
		config.set('sbname', None)
		config.set('sbpass', None)
		config.set('preferredhost', "rapidshare.com")
		config.set('language', None)
	
	if vargs['sburl'] != None:
		config.set('sburl', vargs['sburl'])
	if vargs['sbname'] != None:           	
		config.set('sbname', vargs['sbname'])
	if vargs['sbpass'] != None:
		config.set('sbpass', vargs['sbpass'])
	if vargs['jdurl'] != None:
		config.set('jdurl', vargs['jdurl'])
	if vargs['host'] != None:
		config.set('preferredhost', vargs['host'])
	if vargs['language'] != None:
		if vargs['language'] == 'en':
			config.set('language', 'Englisch')
		elif vargs['language'] == 'de':
			config.set('language', 'Deutsch')
		else:
			config.set('language', None)
	
	
	if vargs['save']:
		action_save(config, history)
	elif vargs['clear']:
		action_clear(config, history)
	else:
		action_default(config, history)
	
if __name__ == "__main__":
	main()