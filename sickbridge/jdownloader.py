import urllib

def add_link(jdownloader_url, link):
	url = "%s/link_adder.tmpl" % jdownloader_url
	
	data = urllib.urlencode({'do':'Add', 'addlinks': link})
	
	s = urllib.urlopen(url, data)
	
	code = s.getcode()
	#print "Jdownloader: %s" % code
	
	return code == 200

def in_queue(url, filename):
	s = urllib.urlopen(url)
	html = s.read()
	s.close()
	
	return html.find(">%s<" % filename) >= 0