import feedparser
import os.path
import time
import calendar
import urlparse
import mod_python

def run( req):
  apache_fields = mod_python.util.FieldStorage(req)
  url_file_name='urls.ini'
  if( apache_fields.has_key('urls')): url_file_name=apache_fields.getfirst('urls')
  new_window='n'
  if( apache_fields.has_key('window')): new_window='y'
  apache_location = ''.join([req.document_root(),os.path.dirname(req.uri),"/"])
  apache_file_name = ''.join([ apache_location, url_file_name])
  url_file = open( apache_file_name,'r')
  urls = url_file.readlines()
  url_file.close()

  feeds =[]

  for url in urls:
    url_six_tuple = urlparse.urlparse(url)
    six_tuple_filename = ''.join(  url_six_tuple )
    if( os.path.exists( ''.join( [apache_location,]) )):
      pass
    fp = feedparser.parse( url)
    feeds.append(fp)


  def formatEntry( entry, make_grey_tuple, source_feed, epoch):
    make_grey =  make_grey_tuple[0]
    
    #does the entry include a title?
    which_feed = "notitle"
    if ( source_feed.feed.has_key('title') ):
      which_feed = source_feed.feed.title
    
    #what about a date?
    secs = time.localtime(epoch)
    print_more_date = time.strftime("%b, %y %Z" , secs) #Jan, 10 GMT
    print_date = time.strftime("%A - %I:%M%p" , secs) #Monday - 12:00PM

    if (make_grey == True):
      p_tag = "<table bgcolor=#DDDDDD>"
      make_grey_tuple[0] = False
    else:
      p_tag = "<table>"
      make_grey_tuple[0] = True
    if ( entry.has_key('link')): print_link = entry.link
    else:
      print_link = 'None'
      #print ''.join( ["no link ", which_feed])
    if ( entry.has_key('title')): print_title = entry.title
    else:
      print_title = 'None'
      #print ''.join( ["no title ", which_feed])
    

    
    if ( source_feed.feed.has_key('icon') ):
      print_image = source_feed.feed.icon
      #print source_feed.feed.icon
    #elif( source_feed.feed.has_key('image') ):
    #  if( source_feed.feed.image.has_key('href')):
    #    print_image = source_feed.feed.image.href
    #    print source_feed.feed.image.href
    else:
      url = urlparse.urlparse(print_link)
      print_image = ''.join(["http://",url.hostname,"/favicon.ico"])
      #print ''.join( ["no icon ", str(which_feed)])
      
    if ( entry.has_key('description')): print_description = entry.description
    else:
      print_description = 'None'
      #print ''.join( ["no description ", which_feed])
      
    print_content = ''
    if ( entry.has_key('content') ):
      for c in entry.content:
        print_content = ''.join( [print_content, c.value] )
    else:
      print_content = print_description
      
    href_target = ''
    if(new_window == 'y'):href_target = "target=\"_blank\""
    return ''.join( [ "<h3> &nbsp; ",print_date,"</h3>",
                    "<h5><img height=16 width=16 src=\"",print_image,"\"></img> <a ",href_target," href=\"",
                                        print_link,"\">",print_title,"</a> - ",which_feed," - ",print_more_date,"</h5>",
                        p_tag,"<tr><td><small>", 
                        print_content,"<br></small></td></tr></table>"])

  def formatString( string):
    return ''.join( ["<p>",string,"</p>"])


  entries = []
  for feedparser_obj in feeds:
    for entry in feedparser_obj.entries:
      if( entry.has_key('published_parsed') ):
        epoch_time_or_zero = calendar.timegm(entry.published_parsed)
      elif( entry.has_key('updated_parsed')):
        epoch_time_or_zero = calendar.timegm(entry.updated_parsed)
      elif( entry.has_key('created_parsed')):
        epoch_time_or_zero = calendar.timegm(entry.created_parsed)
      else:
        epoch_time_or_zero = 0
      entries.append( ( entry, epoch_time_or_zero, feedparser_obj ))

       
  entries.sort( key=lambda entries_tuple: entries_tuple[1], reverse=True)

  header = "<html><body>"
  footer = "</body></html>"
  html = header

  grey_status = [True]
  for entry in entries:
    html = ''.join( [ html, formatEntry( entry[0], grey_status, entry[2], entry[1])])

  html = ''.join( [ html, footer])
  return html.encode('ascii', 'ignore')


