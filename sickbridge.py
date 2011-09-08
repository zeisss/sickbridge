import os
import os.path
import hashlib

import sickbeard
import serienjunkies
import jdownloader

SICKBRIDGE_HOME = "%s/%s" % (os.getenv("USERPROFILE"), '.sickbridge')
SICKBEARD_URL = "http://localhost:8081"
JDOWNLOADER_URL = "http://localhost:8765"

PREFERRED_HOSTER = 'netload.in'

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
	
def main():
    # Counters for stat printing
	cBacklogSize = 0
	cNotDownloadedDueToCache = 0
	cAddedToDownloader = 0
	
	
	print "Sickbridge"
	print "=========="
	print "Creating history"
	history = SickbridgeHistory()
	
	print "Scanning %s's backlog" % SICKBEARD_URL
	
	episodes = sickbeard.get_backlog_list(SICKBEARD_URL)
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
		X = serienjunkies.get_download_links(seriesName, seriesId, episodeName, episodeNo, url=specificUrl)		
		
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