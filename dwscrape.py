import requests		# Handles all HTTP requests and socks proxy connection
import json
import re
from bs4 import BeautifulSoup
import sys


# CONSTANTS
INPUT_FILE = "testset" 		# Link to file that includes all .onion links 
SOCKS_IPV4 = "127.0.0.1" 	# IP address for TOR proxy
SOCKS_PORT = "9050" 		# Port for TOR proxy

# Optional
REQTIMEOUT = 5  			# 5 second default timeout, can be changed
OUTPUTJSON = "output.json" 	# Name of output file

USER_AGENT = "Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0"


def postReq(url, params):
# Returns the HTML page for the given URL
	headers = {'User-Agent':USER_AGENT, 'Content-Type':'application/x-www-form-urlencoded'}
	#params = {'q':'test', 't':'h_', 'ia':'web'}
	#r = requests.post(url, params=params, verify=True)
	#return r.content
	session = requests.session()	# New requests session objecte
	session.proxies = {}			# Create new blank dictionary
	session.proxies['http'] = 'socks5h://'+SOCKS_IPV4+':'+SOCKS_PORT	# Proxy adddress
	session.proxies['https'] = session.proxies['http']					# HTTPS proxy
	return str(session.post(url, headers=headers, params=params).content)

def getReq(url):
	session = requests.session()	# New requests session object
	session.proxies = {}			# Create new blank dictionary
	session.proxies['http'] = 'socks5h://'+SOCKS_IPV4+':'+SOCKS_PORT	# Proxy adddress
	session.proxies['https'] = session.proxies['http']	
	return str(session.get(url, timeout=REQTIMEOUT).content)

def getMaxPage(response):
	pages = re.findall(r"pg=(\d+)", response)
	try:
		max = pages[len(pages)-1]
		return int(max)
	except:
		return False

def returnQueryPage(query, page):
	# Please note that this has been redacted 
	dlinks = 'http://someonionaddres.onion'
	query = ({
	'action':'Search',
	'cat':'19',
	'pg':str(page),
	'lang':'en',
	'q':str(query)
	})
	try:
		return postReq(dlinks, query)
	except:
		print 'Could not retrieve page'
		return False
	#result = postReq(dlinks, query)
	#maxPages = getMaxPage(result)

def linksToArray(page):
	output = []
	try:
		soup = BeautifulSoup(page, "html.parser")
		mt = soup.find('table', id='maintable')
		rows = mt.find_all('tr')
		#
		for i in rows:
			buff2 = []
			for d in i.find_all('td'):
				buff2.append(d.text)
			if len(buff2) > 0:
				output.append(buff2)
		return output
	except:
		print 'Could not convert page to array'
		return False

def pageToCsv(page, filename, title=1):
	output = linksToArray(page)
	if output:#linksToArray(page)!=False:
		try:
			f=open(str(filename), 'a+')
			if title == 1:
				f.write(r""""Onion Link","Description","Last tested","Last seen","Added at","Actions" """)
				f.write('\n')
			for r in output:
				line = ''
				for d in r:
					line = line + '","' + d
				f.write(line[2:-3].encode('utf-8').strip())
				f.write("\n")
			f.close()
			return True
		except:
			print 'Failed to write to CSV...'
			return False
	else:
		print 'Could not convert page to array'
		return False


def main(args):
	if len(args) == 1:
		print "Too few arguments, expected: filename and an optional query..."

	elif len(args) == 2: # Get ALL data
		# Raw search
		filename = args[1]
		print('Retrieving ALL data and saving to CSV file: '+str(filename))
		print('This will take a while, please be patient. Failed requests will flag up in the console.')
		try:
			#print('STARTING - getReq')
			firstPage = getReq('http://someonionaddres.onion?cat=19&pg=1&lang=en')
			#print('2 - getMaxPage')
			maxPage = getMaxPage(firstPage)
			if maxPage > 1:
				#compPer = (1/float(maxPage))*100
				pgCount = 2
				#print('3 - Page to CSV')
				pageToCsv(firstPage, filename)
				for i in range(2, maxPage+1):
					#compPer = (float(i)/float(maxPage))*100
					#print('4 - Enter loop')
					url = 'http://someonionaddres.onion?cat=19&pg='+str(pgCount)+'&lang=en'
					try:
						page = getReq(url)
						pageToCsv(page, filename, title=0)
					except:
						print 'Failed to get request: '+url
					pgCount += 1
			print 'Task completed. Check the output file.'
		except:
			print 'Failed to get all data and write to CSV'

	elif len(args) == 3: # Search query
		# Query search
		filename = args[1]
		query = args[2]
		print('Beginning search for '+str(query)+', saving to CSV file: '+str(filename))
		search = returnQueryPage(query, "1")
		maxp = getMaxPage(search)
		print maxp
		if maxp > 1:
			try:
				print 'Multiple'
				pageToCsv(search, filename) # Write first page with heading
				for i in range(2,maxp+1):
					pageToCsv(returnQueryPage(query, i), filename, title=0) # from here on do not write the collumn titles
			except:
				print 'Failed to write multiple pages to CSV'
		else:
			pageToCsv(search, filename)


	else:
		print "Too many arguments, expected: filename and an optional query..."


main(sys.argv)
