import grab_backlog

SICKBEARD_URL = "http://localhost:8081"

def main():
	print "Sickbridge"
	print "=========="
	print "Scanning %s's backlog" % SICKBEARD_URL
	
	episodes = grab_backlog.get_backlog_list(SICKBEARD_URL)
	for x in episodes:
		print x	
	
if __name__ == "__main__":
	main()