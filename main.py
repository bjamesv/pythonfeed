from urlparse import parse_qs
from latestposts import UrlHandler

if __name__ == '__main__':
	parms = parse_qs("urls=test.ini")
	loc="/home/bjv/Downloads/python_feeds/"
	print(parms)
	handler = UrlHandler( 	parms=parms
				, request="file://"
				, loc=loc)
	html = handler.run()
	out_file = open( loc+"out.html", 'w')
	out_file.write(html)
	out_file.close()
