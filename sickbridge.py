import os
import os.path
import hashlib

import sickbeard
import serienjunkies
import jdownloader

SICKBRIDGE_HOME = "%s/%s" % (os.getenv("USERPROFILE"), '.sickbridge')
SICKBEARD_URL = "http://localhost:8081"
JDOWNLOADER_URL = "http://localhost:8765"

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

def link_sorter(a):
	name, link = a
	# prefer netload.in over others
	if name == 'netload.in':
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
	
	if sortedLinks[0][0] == 'netload.in': # if our preferred hoster is there, add it solely
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
	for x in episodes:
		(seriesName, seriesId, episodeName, episodeNo) = x
		
		print "===="
		print "%s S%sE%s - %s" % (seriesName, episodeNo[0], episodeNo[1], episodeName)
		if history.has_downloaded(seriesName, episodeNo, episodeName):
			print "Already in history. Delete %s to download again." % history.get_path(seriesName, episodeNo, episodeName)
			cNotDownloadedDueToCache = cNotDownloadedDueToCache + 1
			continue
			
		if seriesName in SERIES_MAPPING:
			specificUrl = SERIES_MAPPING[seriesName]
		else:
			specificUrl = None
		X = serienjunkies.get_download_links(seriesName, seriesId, episodeName, episodeNo, url=specificUrl)		
		if X == None or len(X) == 0:
			print "Not found"
		else:
			#print X
			sortedDownloads = sorted(X, key=download_sorter)
			if jdownloader.in_queue(JDOWNLOADER_URL, sortedDownloads[0][5]):
				print "Already in queue"
			else:
				schedule_download(sortedDownloads[0])
				history.add_download(seriesName, episodeNo, episodeName)
				cAddedToDownloader = cAddedToDownloader + 1
	
	print 
	print
	print "==============================================================================="
	print "= %3d of %3d were previously added to queue.                                  =" % (cNotDownloadedDueToCache, cBacklogSize)
	print "= Successfully added %3d new links to queue.                                  =" % (cAddedToDownloader)
	print "==============================================================================="
if __name__ == "__main__":
	main()