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
from cgi import escape

def dump_feed( fp, six_tuple_fullpath):
  if(fp.has_key('etag')):e_tag=fp.etag
  else: e_tag=''
  if(fp.has_key('modified')): mod=fp.modified
  else: mod=''
  stored_fields = { 'xml':fp.xml, 'etag':e_tag, 'modified':mod}
  #sys.stderr.write(''.join( ["dumping: ",fp.xml, "etag", str(e_tag), "mod", str(mod) ]))
  logging.debug(''.join( ["dumping: ",fp.xml, "etag", str(e_tag), "mod", str(mod) ]))
  out_file = open(six_tuple_fullpath, 'wb')
  pickle.dump( stored_fields,out_file)
  out_file.close()

def load_feed( url, six_tuple_fullpath):
  stored_fields = pickle.load(open(six_tuple_fullpath, 'rb'))
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

def add_url( url, filename):
  with open(filename, 'a') as f:
    logging.warning("Writing to urls file")
    f.write(url + '\r\n')
  f.close()
  logging.warning("Done writing to urls file")
  

  
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
class UrlHandler():
  def __init__(self, parms, request, loc):
    self.apache_parameters = parms
    self.req_uri = request
    self.apache_location = loc
  def load_urls(self):
    with open( self.apache_file_name,'r') as url_file:
      logging.warning("Reading urls file")
      self.urls = url_file.readlines()
    url_file.close()
    logging.warning("Done reading urls file")

  def del_url( self, url, row):
    logging.warning( "Delete row: "+str(row)+ " Url: "+url)
    if len(self.urls) is 0:
      return '<div style="color:#FF0000"><p>Remove Not executed: loaded Url list contains 0 entries.</p></div>'
    del self.urls[row]
    with open(self.apache_file_name, 'w') as f:
      logging.warning("Erasing & writing to urls file")
      f.writelines(self.urls)
    f.close()
    logging.warning("Done writing to urls file")
    return '<div style="color:#00FF00"><p>Url: "'+ url +'" (row '+str(row)+') removed.</p></div>'
  
  def generatePythonURL(self):
      pythonURL = self.getPythonURL_host() + '?' + 'urls' '=' + self.url_file_name +\
                                        '&' + 'window' '=' + self.new_window +\
                                        '&' + 'start' '=' + str(self.start_entry_to_display) +\
                                        '&' + 'num' '=' + str(self.num_entries_to_display)
      return pythonURL 
  def getPythonURL_host(self):
      return os.path.split(self.req_uri)[1] 
  def formatListEditor( self):
      error_html = ""
      if self.flag_add_url in self.parameters and self.flag_edit_urls in self.parameters:
        f = self.apache_file_name
        add_url( self.parameters[self.flag_add_url], f )
        self.load_urls()
      if self.flag_del_url in self.parameters and self.flag_del_row in self.parameters and \
          self.flag_edit_urls in self.parameters:
        u = self.parameters[self.flag_del_url]
        r = self.parameters[self.flag_del_row]
        error_html = self.del_url(u, r)
        self.load_urls()
      back_url = self.generatePythonURL()
      file_name = self.url_file_name
      header = "<html><head><title>Python Feeds</title>"\
               "<h3>Editing urls list: %(file_name)s</h3><table>"\
               '<p><a href="%(back_url)s">Back to Python Feeds</p>' %locals()
      html = header + error_html
      hidden_fields = '<input type="hidden" name="urls" value="'+ self.url_file_name +'"/>'\
             '<input type="hidden" name="window" value="'+ self.new_window +'"/>'\
             '<input type="hidden" name="start" value="'+ str(self.start_entry_to_display) +'"/>'\
             '<input type="hidden" name="num" value="'+ str(self.num_entries_to_display) +'"/>'\
             '<input type="hidden" name="edit_urls" value=""/>'
      for i,url in enumerate(self.urls):
        url = url.rstrip()
        html = html + '<tr><td><a href="'+ url +'">'+ url+'</a> '\
               '<form id="id_del_'+str(i)+'" name="del_url" action="feed" method="get">'\
               '<input type="button" value="remove" onclick="show_delete_confirm('+str(i)+')" />'\
               '<input type="hidden" name="del_row" value="'+str(i)+'"/>'\
               '<input type="hidden" name="del_url" value="'+url+'"/>'\
               + hidden_fields + '</form></td></tr>'
      html = html + '<script type="text/javascript">'\
                        'function show_confirm() {'\
                          'var r=confirm("Add URL to '+ self.url_file_name +'?");'\
                          'if (r==true) {'\
                             'add_form = document.forms["id_add_url"];'\
                             'add_form.submit();'\
                          '}else{}'\
                        '} '\
                        'function show_delete_confirm(line) {'\
                          'var r=confirm("Remove URL: " +line+ "?");'\
                          'if (r==true) {'\
                             'del_form = document.forms["id_del_"+line];'\
                             'del_form.submit(); '\
                          '}else{}'\
                        '} '\
                      '</script>'
        
      #'add_form.elements.push(window.location.search.substring(1));'\
      html = html + '<tr><td><form id="id_add_url" name="add_url" action="feed" method="get">'\
             '<input type="text" name="add_url" /><input type="button" value="Add" onclick="show_confirm()"/>'
      
      html = html + hidden_fields
      html = html + '</form></td></tr></table></body></html>'
      return html
  def profile_threads(self):
      for url in self.urls:
        p = threading.Thread(target=fetch_process, args=(self.q, url, self.apache_location))
        p.start()
        self.threads.append(p)
      ##begin fetching results from the queue, until all subprocesses are done
      while not (self.q.empty()) or not ( len(self.threads) == 0):
        try:
          fp = self.q.get(False)
          self.feeds.append(fp)
        except (Queue.Empty):
          clean(self.threads)
        except:
          pass
      return str(len(self.feeds))
    
  def profile_no_threads(self):
      for url in self.urls:
        self.feeds.append(fetch_process(self.q, url, self.apache_location))
  def formatEntry(self, entry, make_grey_tuple, source_feed, epoch):
      """
      

      Uses 'self' only once, to check state of new window linking/target.
      (? could be moved out of UrlHandler object)
      """
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
        p_tag = "make_grey"
        make_grey_tuple[0] = False
      else:
        p_tag = "non_grey"
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
      if(self.new_window == 'y'):href_target = "target=\"_blank\""
      hidden_header = ''.join( ['<p class="hidden_header"><br>[',which_feed,']<span class="show_button">[Hidden: ',\
                                print_title,'</span> - ',print_more_date,'',print_date,'][show full]<br><br></p>'])
      return ''.join( [ hidden_header,'<div class="hidden_post"><h3  class="title"> &nbsp; ',print_date,' <span class="hide_button">(hide)</span></h3>',
                      '<img height=16 width=16 src=\"',print_image,"\"></img> <a ",href_target," href=\"",
                                          print_link,"\">",print_title,"</a> - ",which_feed," - ",print_more_date,"",
                          '<small><br><p class="',p_tag,'">', 
                          print_content,"</p></small></div>"])
    
  def generatePythonEdit_URL(self):
      editURL = self.generatePythonURL()
      return editURL + '&edit_urls'
      
  def formatPageControls(self, num, total, req_uri, url_file_name, new_window, starting_entry):
      """
      Does not use 'self', could be moved out of UrlHandler object.

      
      """
      html_prev = "&lt; prev"
      html_next = "next &gt;"
      l = ''.join( [ "page ", ])
      for a in range(total/num):
        link_start = a*num
        link_name = str(a+1)
        if( link_start == starting_entry):
            link_name = "Current page (" + str(a+1) + ")"
        elif ( link_start == starting_entry-num):
            html_prev = ''.join( ["<a href=\"",os.path.split(req_uri)[1],
                      "?urls=",url_file_name,
                      "&window=",new_window,
                      "&start=",str(link_start),
                      "&num=",str(num),
                      "\">","&lt; prev","</a>, "])
        elif ( link_start == starting_entry+num):
            html_next = ''.join( ["<a href=\"",os.path.split(req_uri)[1],
                      "?urls=",url_file_name,
                      "&window=",new_window,
                      "&start=",str(link_start),
                      "&num=",str(num),
                      "\">","next &gt;","</a>, "])
        
        l = ''.join( [l, "<a href=\"",os.path.split(req_uri)[1],
                      "?urls=",url_file_name,
                      "&window=",new_window,
                      "&start=",str(link_start),
                      "&num=",str(num),
                      "\">",link_name,"</a>, "])
      return ''.join( ["<p>",html_prev," ",l," ",html_next,"</p>"])
    
  def formatUrlsEditControl(self):
      edit_url = '<p><a href="%s">Add/modify Subscribed feeds.</a></p>' % ( self.generatePythonEdit_URL())
      return edit_url
  def formatString( self, string):
      """
      Does not use 'self', could be moved out of UrlHandler object.

      
      """
      return ''.join( ["<p>",string,"</p>"])
  def run( self):
    #logging.basicConfig(level=logging.DEBUG, filename='debug.log')
    #logging.basicConfig(level=logging.WARNING, filename=self.apache_location+'debug.log')
    logging.warning("Begin opening urls file")

    self.parameters = dict()
    if 'urls' in self.apache_parameters:
      self.url_file_name = escape(self.apache_parameters['urls'][0])
    else:
      self.url_file_name='urls.ini'

    self.apache_file_name = ''.join([ self.apache_location, self.url_file_name])

    if 'window' in self.apache_parameters:
      if  escape(self.apache_parameters['window'][0]) == 'y':
          self.new_window= 'y'
      else:
          self.new_window= 'n'
    else:
      self.new_window='n'


    if 'start' in self.apache_parameters:
      self.start_entry_to_display = int(escape(self.apache_parameters['start'][0]))
    else:
      self.start_entry_to_display = 0
      
    if 'num' in self.apache_parameters:
      self.num_entries_to_display = int(escape(self.apache_parameters['num'][0]))
    else:
      self.num_entries_to_display = None

    
    self.load_urls()
    logging.warning("Done with urls file" +str(self.urls))
    
    self.flag_add_url = 'add_url'
    if self.flag_add_url in self.apache_parameters:
      self.parameters[self.flag_add_url] = escape(self.apache_parameters[self.flag_add_url][0])
    
    self.flag_del_url = 'del_url'
    if self.flag_del_url in self.apache_parameters:
      self.parameters[self.flag_del_url] = escape(self.apache_parameters[self.flag_del_url][0])

    self.flag_del_row = 'del_row'
    if self.flag_del_row in self.apache_parameters:
      self.parameters[self.flag_del_row] = int(escape(self.apache_parameters[self.flag_del_row][0]))
    
    self.flag_edit_urls = 'edit_urls'
    if self.flag_edit_urls in self.apache_parameters:
      self.parameters[self.flag_edit_urls] = escape(self.apache_parameters[self.flag_edit_urls][0])
      return self.formatListEditor()
    

    

    self.feeds =[]
    header = "<html><head><title>Python Feeds</title>"\
"""
<style type="text/css"> 
body {
	margin: 20px auto;
}
.make_grey {
background-color:#DDDDDD;
}
 
.heading {
margin: 1px;
color: #fff;
padding: 3px 10px;
cursor: pointer;
position: relative;
background-color:#c30;
}
.hide_button {
color: #888;
padding: 10px 3px;
margin: 3px;
}
.show_button {
color: #888;
padding: 10px 3px;
margin: 3px;
}
.content {
padding: 5px 10px;
background-color:#fafafa;
}
.hidden_post {
display: none;
}
.hidden_header_unshown {
margin: 0px;
padding: 0px 0px;
}
.hidden_header {
margin: 0px;
padding: 0px 5px;
}
p { padding: 5px 0; }
</style> 
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>
<script type="text/javascript">
jQuery(document).ready(function() {
  //jQuery(".hidden_header_unshown").slideToggle("fast");
  //jQuery(".hidden_post").slideToggle("fast");
  //toggle the componenet with class msg_body
  jQuery(".hide_button").click(function()
  {
    jQuery(this).closest(".post").prev(".hidden_header_unshown").slideToggle("fast").removeClass("hidden_header_unshown").addClass("hidden_header");
    jQuery(this).closest(".post").slideToggle("fast").removeClass("post").addClass("hidden_post");
  });
  jQuery(".show_button").click(function()
  {
    jQuery(this).closest(".hidden_header").next(".hidden_post").slideToggle("fast").removeClass("hidden_post").addClass("post");
    jQuery(this).closest(".hidden_header").slideToggle("fast").removeClass("hidden_header").addClass("hidden_header_unshown");
  });
});
</script>
"""\
             '<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.3.2/jquery.min.js"></script>'\
               '</head><body>'
    self.q = Queue.Queue()
    self.threads =[]
    
        
    import cProfile
    prof = cProfile.Profile()
    logging.warning("Beginning Threaded fetch of data")
    #prof.runcall( profile_threads )
    #prof.print_stats()#'C:/Program Files/Apache Software Foundation/Apache2.2/htdocs/test/python/profout.txt')
    self.profile_threads()
    logging.warning("Threaded fetch of data Complete")


    


    
    logging.warning("Begin combining many feeds into one list") 
    entries = []
    for feedparser_obj in self.feeds:
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
    
    if ( self.num_entries_to_display == None):
      self.num_entries_to_display = len(entries)+1
    
    footer = "</body></html>"
    html = header

    logging.warning("Beginning Entry HTML formatting")
    grey_status = [True]
    i = self.start_entry_to_display
    j = self.num_entries_to_display+self.start_entry_to_display
    elist = [ self.formatEntry( e[0], grey_status, e[2], e[1]) for e in entries[i:j]]
    separator = ""
    eblock = separator.join(elist)
    #for entry in entries[start_entry_to_display:num_entries_to_display+start_entry_to_display]:
    #  html = ''.join( [ html, formatEntry( entry[0], grey_status, entry[2], entry[1])])
    logging.warning("Entry HTML formatting Completed")
    
    pageControls = self.formatPageControls(self.num_entries_to_display,
                                           len(entries),self.req_uri,
                                           self.url_file_name, self.new_window,
                                           self.start_entry_to_display)
    urlsEditControl = self.formatUrlsEditControl()
    
    html = "%(html)s%(pageControls)s%(urlsEditControl)s%(eblock)s%(pageControls)s%(footer)s" % locals()
    return html.encode('ascii', 'ignore')


