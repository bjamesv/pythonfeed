import feedparser
import os.path
import time
import calendar
import urlparse
import pickle
import sys
import threading
import Queue

import logging

def dump_feed( fp, six_tuple_fullpath):
  if(fp.has_key('etag')):e_tag=fp.etag
  else: e_tag=''
  if(fp.has_key('modified')): mod=fp.modified
  else: mod=''
  stored_fields = { 'xml':fp.xml, 'etag':e_tag, 'modified':mod}
  #sys.stderr.write(''.join( ["dumping: ",fp.xml, "etag", str(e_tag), "mod", str(mod) ]))
  logging.debug(''.join( ["dumping: ",fp.xml, "etag", str(e_tag), "mod", str(mod) ]))
  out_file = open(six_tuple_fullpath, 'w')
  pickle.dump( stored_fields,out_file)
  out_file.close()

def load_feed( url, six_tuple_fullpath):
  stored_fields = pickle.load(open(six_tuple_fullpath, 'r'))
  re_request_fp = feedparser.parse( url, etag=stored_fields['etag'], modified=stored_fields['modified'])
  #sys.stderr.write(''.join( ["pre status ",url ]))
  logging.warning(''.join( ["pre status ",url ]))
  if(re_request_fp.has_key('status')):
    #sys.stderr.write(''.join( ["pre 304 ",url, str(re_request_fp.status) ]))
    logging.warning(''.join( ["pre 304 ",url, str(re_request_fp.status) ]))
    if( re_request_fp.status == 304):
      #sys.stderr.write(''.join( ["304! ",url ]))
      logging.warning(''.join( ["304! ",url ]))
      return feedparser.parse(stored_fields['xml'])
  #else
  re_request_fp = feedparser.parse( url)
  #sys.stderr.write(''.join( [" dumping fresh url INSIDE load_feed", url ]))
  logging.warning(''.join( [" dumping fresh url INSIDE load_feed", url ]))
  dump_feed( re_request_fp, six_tuple_fullpath)
  return re_request_fp


def fetch_process( queue, url, apache_location):
    #fp = feedparser.parse( url)
    #queue.put(fp)
    #return fp
    url_six_tuple = urlparse.urlparse(url)
    six_tuple_filename = str.replace(''.join(  url_six_tuple ),'/','')
    six_tuple_fullpath = ''.join( [apache_location,six_tuple_filename])
    six_tuple_fullpath = six_tuple_fullpath.rstrip()
    if( os.path.exists( six_tuple_fullpath )):
      #sys.stderr.write(''.join( [" loading feed", six_tuple_fullpath ]))
      logging.warning(''.join( [" loading feed", six_tuple_fullpath ]))
      fp = load_feed( url, six_tuple_fullpath)
    else:
      fp = feedparser.parse( url)
      #sys.stderr.write(''.join( [" dumping fresh url", url ]))
      logging.warning(''.join( [" dumping fresh url", url ]))
      dump_feed( fp, six_tuple_fullpath)
    queue.put(fp)
    return fp
    
def clean( processes):
  for p in processes[:]:
    if (p.is_alive()):
      pass
    else:
      processes.remove(p)

def run( url_file_name, new_window, start_entry_to_display, num_entries_to_display, req_uri, apache_location):
  #logging.basicConfig(level=logging.DEBUG, filename='debug.log')
  logging.basicConfig(level=logging.WARNING, filename='C:/Program Files/Apache Software Foundation/Apache2.2/htdocs/test/python/debug.log')
  logging.warning("Begin opening urls file") 
  apache_file_name = ''.join([ apache_location, url_file_name])
  url_file = open( apache_file_name,'r')
  urls = url_file.readlines()
  url_file.close()
  logging.warning("Done with urls file") 

  feeds =[]
  header = "<html><head><title>Python Feeds</title></head><body>"
  q = Queue.Queue()
  threads =[]
  def profile_threads():
    for url in urls:
      p = threading.Thread(target=fetch_process, args=(q, url, apache_location))
      p.start()
      #feeds.append(fetch_process(q, url))
      threads.append(p)
      
    #out = ""
    #for a in threads:
    #  out = ''.join( [out, a.name, " - " ])
    ##return out
    ##begin fetching results from the queue, until all subprocesses are done
    while not (q.empty()) or not ( len(threads) == 0):
      try:
        fp = q.get(False)
        feeds.append(fp)
      except (Queue.Empty):
        clean(threads)
      except:
        pass
    return str(len(feeds))
  
  def profile_no_threads():
    for url in urls:
      #p = threading.Thread(target=fetch_process, args=(q, url))
      #p.start()
      feeds.append(fetch_process(q, url, apache_location))
      #threads.append(p)
      
    #out = ""
    #for a in threads:
    #  out = ''.join( [out, a.name, " - " ])
    ##return out
    ##begin fetching results from the queue, until all subprocesses are done
    #while not (q.empty()) or not ( len(threads) == 0):
    #  try:
    #    fp = q.get(False)
    #    feeds.append(fp)
    #    clean(threads)
    #  except:
    #    pass
    #return str(len(feeds))
  import cProfile
  prof = cProfile.Profile()
  logging.warning("Beginning Threaded fetch of data")
  #prof.runcall( profile_threads )
  #prof.print_stats()#'C:/Program Files/Apache Software Foundation/Apache2.2/htdocs/test/python/profout.txt')
  profile_threads()
  logging.warning("Threaded fetch of data Complete")

  def formatListEditor( ):
    html = ''
    return html

  def formatEntry( entry, make_grey_tuple, source_feed, epoch):
    make_grey =  make_grey_tuple[0]
    
    #does the entry include a title?
    which_feed = "notitle"
    if ( source_feed.feed.has_key('title') ):
      which_feed = source_feed.feed.title
    
    #what about a date?
    secs = time.localtime(epoch)
    print_more_date = time.strftime("%b %d, %Y %Z" , secs) #Jan, 10 GMT
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
  
  def formatPageControls( num, total, req_uri, url_file_name, new_window, starting_entry):
    l = ''
    for a in range(total/num):
      for entry in range(a*num):
        l = ''.join( [ "page ", ])
    for a in range(total/num):
      l = ''.join( [l, "<a href=\"",os.path.split(req_uri)[1],
                    "?urls=",url_file_name,
                    "&window=",new_window,
                    "&start=",str(a*num),
                    "&num=",str(num),
                    "\">",str(a),"</a>, "])
    return ''.join( ["<p><small>< ",l," ></small></p>"])
  def formatString( string):
    return ''.join( ["<p>",string,"</p>"])

  
  logging.warning("Begin combining many feeds into one list") 
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
  logging.warning("Done combining many feeds into one list")
  
  logging.warning("Beginning Entries Sort")     
  entries.sort( key=lambda entries_tuple: entries_tuple[1], reverse=True)
  logging.warning("Entries Sort Completed")
  
  if ( num_entries_to_display == None):
    num_entries_to_display = len(entries)+1
  
  footer = "</body></html>"
  html = header

  grey_status = [True]
  html = ''.join( [html, formatPageControls(num_entries_to_display, len(entries),req_uri,url_file_name, new_window, start_entry_to_display)])
  logging.warning("Beginning Entry HTML formatting")
  for entry in entries[start_entry_to_display:num_entries_to_display+start_entry_to_display]:
    html = ''.join( [ html, formatEntry( entry[0], grey_status, entry[2], entry[1])])
  logging.warning("Entry HTML formatting Completed")
  
  html = ''.join( [ html, footer])
  return html.encode('ascii', 'ignore')


