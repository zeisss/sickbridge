import grab_backlog
import serienjunkies
import jdownloader

SICKBEARD_URL = "http://localhost:8081"
JDOWNLOADER_URL = "http://localhost:8765"

def link_sorter(a):
	name, link = a
	
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
	print "Sickbridge"
	print "=========="
	print "Scanning %s's backlog" % SICKBEARD_URL
	
	episodes = grab_backlog.get_backlog_list(SICKBEARD_URL)
	
	for x in episodes:
		(seriesName, seriesId, episodeName, episodeNo) = x
		#print seriesName, episodeNo
		#if seriesName != 'Fringe' or episodeNo != (1,7):
		#	continue
		#continue
		
		X = serienjunkies.get_download_links(seriesName, seriesId, episodeName, episodeNo)
		print "===="
		print "%s S%sE%s - %s" % (seriesName, episodeNo[0], episodeNo[1], episodeName)
		#print X
		if X == None or len(X) == 0:
			print "Not found"
		else:
			sortedDownloads = sorted(X, key=download_sorter)
			if jdownloader.in_queue(JDOWNLOADER_URL, sortedDownloads[0][5]):
				print "Already in queue"
			else:
				schedule_download(sortedDownloads[0])
	
if __name__ == "__main__":
	main()