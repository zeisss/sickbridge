# Imports
import os
import sys
import shutil
import os.path
import hashlib
import ConfigParser

import sickbeard
import serienjunkies
import jdownloader


class SickbridgeHistory:
	"""
	Keeps a persistent history of what urls where previously downloaded.
	"""
	path = None
	config = None
	def __init__(self, config):
		self.config = config
		self.path = os.path.join(self.config.home, "history")
		
		if not os.path.exists(self.path):
			os.makedirs(self.path)
	
	def clear(self):
		shutil.rmtree(self.path)
	
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

class SickbridgeConfig:
	"""
	Utility class to store configuration values like preferred hoster and urls.
	"""
	home = None
	configFile = None
	
	config = None
	def __init__(self):
		if sys.platform == "darwin":
			# use ~/.sickbridge if on a mac
			self.home = os.path.join(os.path.expanduser("~"), '.sickbridge')
		elif sys.platform.startswith("win"):
			# this should work for windows
			self.home = os.path.join(os.getenv("USERPROFILE"), '.sickbridge')
		else:
			# let's assume everything else is linux...
			# then this should work...
			self.home = os.path.join(os.path.expanduser("~"), '.sickbridge')
		
		self.configFile = os.path.join(self.home, "sickbridge.cfg")
		
		self.config = {}
		self.read_config()
		
	def write_config(self):
		"""Write settings to configuration file"""
		config = ConfigParser.RawConfigParser()
		
		config.add_section('Sickbridge')
		for x in ['firsttime', 'preferredhost', 'language', 'sburl', 'jdurl', 'sbname', 'sbpass']:
			config.set('Sickbridge', x, self.config[x]);
			
		if not os.path.exists(self.home):
			print "Creating %s" % self.home
			os.makedirs(self.home)
		
		with open(self.configFile, 'wb') as fp:
			config.write(fp)
		
		print "Settings written to configuration file %s" % self.configFile
		
	def read_config(self):
		"""Read settings from configuration file"""
		
		# set ConfigParser up with default values
		config = ConfigParser.ConfigParser({
			'preferredhost': 	None,
			'language': 		None,
			'sburl': 			"http://localhost:8081/",
			'jdurl': 			"http://localhost:7151/",
			'sbname': 			None,
			'sbpass': 			None,
			'firsttime':		'yes'
		})
			
		# read the actual config file
		config.read(self.configFile)
		
		# set global variables to read values
		if config.has_section('Sickbridge'):
			section = 'Sickbridge'
		else:
			section = 'DEFAULT'
		
		for x in ['firsttime', 'preferredhost', 'language', 'sburl', 'jdurl', 'sbname', 'sbpass']:
			self.config[x] = config.get(section, x);
			if self.config[x] == "None":
				self.config[x] = None

	def set(self, key, value):
		self.config[key] = value
	def get(self, key):
		return self.config[key]
	def get_mapping(self, serieName):
		# TODO move to config
		# Provide URLs for series manually, if the script is unable to find them through the search
		SERIES_MAPPING = {
			'Castle (2009)': 'http://serienjunkies.org/castle/'
		}
		
		if serieName in SERIES_MAPPING:
			return SERIES_MAPPING[serieName]
		else:
			return None
		
def link_sorter(config):
	PREFERRED_HOSTER = config.get('preferredhost')
	def helper(item):
		"""Sorts the list of URLs by hosting name. If our preferred name is found, it is sorted to the front."""
		name, link = item
		# prefer one hoster over others
		if name == PREFERRED_HOSTER:
			return "aaa%s" % name
		else:
			return name
	return helper
	
def download_sorter(config):
	def helper(a):
		length1, size1, language1, format1, uploader1, downloadName1, links1 = a
		
		sortedLinks = sorted(links1, key=link_sorter(config))
		if format1 == None:
			format1 = ""
		return (format1.lower().replace('.',''), size1, sortedLinks[0])

	return helper

def schedule_download(config, download):
	print "Downloading %s" % download[5]
	
	sortedLinks = sorted(download[6], key=link_sorter(config))
	
	if sortedLinks[0][0] == config.get('preferredhost'): # if our preferred hoster is there, add it solely
		print "Adding %s" % sortedLinks[0][1]
		jdownloader.add_link(config.get('jdurl'), sortedLinks[0][1])
	else: # else add all
		for name, link in sortedLinks:
			print "Adding %s" % link
			jdownloader.add_link(config.get('jdurl'), link)
	print
	

