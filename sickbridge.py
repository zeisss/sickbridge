import os
import sys
import shutil
import os.path
import hashlib
import ConfigParser

import sickbeard
import serienjunkies
import jdownloader

if sys.platform == "darwin":
	# use ~/.sickbridge if on a mac
	SICKBRIDGE_HOME = "%s/%s" % (os.path.expanduser("~"), '.sickbridge')
elif sys.platform.startswith("win"):
	# this should work for windows
	SICKBRIDGE_HOME = "%s/%s" % (os.getenv("USERPROFILE"), '.sickbridge')
else:
	# let's assume everything else is linux...
	# then this should work...
	SICKBRIDGE_HOME = "%s/%s" % (os.path.expanduser("~"), '.sickbridge')

CONFIG_FILE = "%s/%s" % (SICKBRIDGE_HOME, "sickbridge.cfg")

# Defaults
JDOWNLOADER_URL = "http://localhost:8765/"
SICKBEARD_URL = "http://localhost:8081/"
SICKBEARD_NAME = None
SICKBEARD_PASS = None
PREFERRED_HOSTER = "netload.in"
LANGUAGE = None

# TODO move to config
# Provide URLs for series manually, if the script is unable to find them through the search
SERIES_MAPPING = {
	'Castle (2009)': 'http://serienjunkies.org/castle/'
}

class SickbridgeHistory:
	path = None
	def __init__(self):
		self.path = "%s/history" % SICKBRIDGE_HOME
		
		if not os.path.exists(self.path):
			os.makedirs(self.path)
	
	
	def has_downloaded(self, seriesName, episodeNo, episodeName):
		"""
		Returns True when there was a previous call to @add_download(). False otherwise.
		
		Implementation Note: This adds a md5 hashed file to the home of the current user.
		"""
			
		filePath = self.get_path(seriesName, episodeNo, episodeName)
		return os.path.exists(filePath)	
	
	def add_download(self, seriesName, episodeNo, episodeName):
		filePath = self.get_path(seriesName, episodeNo, episodeName)
		open(filePath, 'w').close() 
		
	def get_path(self, seriesName, episodeNo, episodeName):
		md5 = hashlib.md5()
		md5.update(seriesName)
		md5.update(str(episodeNo))
		return "%s/%s_%s_%s" % (self.path, seriesName.lower()[0:5], episodeNo, md5.hexdigest())

def link_sorter(item):
	"""Sorts the list of URLs by hosting name. If our preferred name is found, it is sorted to the front."""
	name, link = item
	# prefer one hoster over others
	if name == PREFERRED_HOSTER:
		return "aaa%s" % name
	else:
		return name
	
def download_sorter(a):
	length1, size1, language1, format1, uploader1, downloadName1, links1 = a
	
	sortedLinks = sorted(links1, key=link_sorter)
	if format1 == None:
		format1 = ""
	return (format1.lower().replace('.',''), size1, sortedLinks[0])


def schedule_download(download):
	print "Downloading %s" % download[5]
	
	sortedLinks = sorted(download[6], key=link_sorter)
	
	if sortedLinks[0][0] == PREFERRED_HOSTER: # if our preferred hoster is there, add it solely
		print "Adding %s" % sortedLinks[0][1]
		jdownloader.add_link(JDOWNLOADER_URL, sortedLinks[0][1])
	else: # else add all
		for name, link in sortedLinks:
			print "Adding %s" % link
			jdownloader.add_link(JDOWNLOADER_URL, link)
	print
	
def write_config():
	"""Write settings to configuration file"""
	config = ConfigParser.RawConfigParser()
	
	config.add_section('Sickbridge')
	config.set('Sickbridge', 'preferedhost', PREFERRED_HOSTER)
	config.set('Sickbridge', 'language', LANGUAGE)
	config.set('Sickbridge', 'sburl', SICKBEARD_URL)
	config.set('Sickbridge', 'sbname', SICKBEARD_NAME)
	config.set('Sickbridge', 'sbpass', SICKBEARD_PASS)
	config.set('Sickbridge', 'jdurl', JDOWNLOADER_URL)	
	
	with open(CONFIG_FILE, 'wb') as configfile:
		config.write(configfile)
		
def read_config():
	"""Read settings from configuration file"""
	global PREFERRED_HOSTER, LANGUAGE, SICKBEARD_URL, JDOWNLOADER_URL, SICKBEARD_NAME, SICKBEARD_PASS
	
	# set ConfigParser up with default values
	config = ConfigParser.ConfigParser({
		'preferedhost':PREFERRED_HOSTER,
		'language':LANGUAGE,
		'sburl':SICKBEARD_URL,
		'jdurl':JDOWNLOADER_URL,
		'sbname':SICKBEARD_NAME,
		'sbpass':SICKBEARD_PASS
		})
		
	# read the actual config file
	config.read(CONFIG_FILE)
	
	# set global variables to read values
	if config.has_section('Sickbridge'):
		section = 'Sickbridge'
	else:
		section = 'DEFAULT'
	PREFERRED_HOSTER = config.get(section,'preferedhost')
	if config.get(section,'language') == 'None':
		LANGUAGE = None
	else:
		LANGUAGE = config.get(section,'language')
	SICKBEARD_URL = config.get(section,'sburl')
	JDOWNLOADER_URL = config.get(section,'jdurl')
	SICKBEARD_NAME = config.get(section, 'sbname')
	SICKBEARD_PASS = config.get(section, 'sbpass')	
	
def parseOptions():
	"""Using command line arguments to change config file"""
	global PREFERRED_HOSTER, LANGUAGE, SICKBEARD_URL, JDOWNLOADER_URL, SICKBEARD_NAME, SICKBEARD_PASS
	
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
	vargs = vars(parser.parse_args())
	
	# react
	if vargs['defaults']:
		JDOWNLOADER_URL = "http://localhost:7151/"
		SICKBEARD_URL = "http://localhost:8081/"
		SICKBEARD_NAME = None
		SICKBEARD_PASS = None
		PREFERRED_HOSTER = "rapidshare.com"
		LANGUAGE = None
	
	if vargs['sburl'] != None:
		SICKBEARD_URL = vargs['sburl']
	if vargs['sbname'] != None:           	
		SICKBEARD_NAME = vargs['sbname']
	if vargs['sbpass'] != None:
		SICKBEARD_PASS = vargs['sbpass']
	if vargs['jdurl'] != None:
		JDOWNLOADER_URL = vargs['jdurl']
	if vargs['host'] != None:
		PREFERRED_HOSTER = vargs['host']
	if vargs['language'] != None:
		if vargs['language'] == 'en':
			LANGUAGE = 'Englisch'
		elif vargs['language'] == 'de':
			LANGUAGE = 'Deutsch'
		else:
			LANGUAGE = None
	
	if vargs['save']:
		write_config()
		print "Settings written to configuration file"
		sys.exit()
		
	if vargs['clear']:
		if os.path.exists("%s/history" % SICKBRIDGE_HOME):
			shutil.rmtree("%s/history" % SICKBRIDGE_HOME)
			print "Cleared History"
		else:
			print "History is already clear"
		sys.exit()
	
def main():
	print "Sickbridge"
	print "=========="
	
	# Read Config
	read_config()
	# Parse Options
	parseOptions()
	
	# if name and / or password are saved, build the right url
	SICKBEARD_URL_C = SICKBEARD_URL
	if SICKBEARD_PASS != None and SICKBEARD_NAME != None:
		SICKBEARD_URL_C = SICKBEARD_URL.replace('://', '://%s:%s@' % (SICKBEARD_NAME, SICKBEARD_PASS))
	elif SICKBEARD_NAME != None:
		SICKBEARD_URL_C = SICKBEARD_URL.replace('://', '://%s@' % SICKBEARD_NAME)
	
    # Counters for stat printing
	cBacklogSize = 0
	cNotDownloadedDueToCache = 0
	cAddedToDownloader = 0
	
	print "Creating history"
	history = SickbridgeHistory()
	
	print "Scanning %s's backlog" % SICKBEARD_URL
	
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
		if seriesName in SERIES_MAPPING:
			specificUrl = SERIES_MAPPING[seriesName]
		else:
			specificUrl = None
			
		# Grab the page and parse it into a list of available episodes
		X = serienjunkies.get_download_links(seriesName, seriesId, episodeName, episodeNo, url=specificUrl, onlyLanguage=LANGUAGE)
		
		# If none are found => Abort
		if X == None or len(X) == 0:
			print "Not found"
		# We found some downloads for our wished episode :D
		else:
			# Sort them (If we have a preferred hoster, this sorts it to the top)
			sortedDownloads = sorted(X, key=download_sorter)
			
			# Another check if we might already be downloading this file
			if jdownloader.in_queue(JDOWNLOADER_URL, sortedDownloads[0][5]):
				print "Already in queue"
			else:
				# Schedule the top download
				schedule_download(sortedDownloads[0])
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
	
if __name__ == "__main__":
	main()