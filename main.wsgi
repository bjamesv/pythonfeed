from cgi import parse_qs, escape
from latestposts import run

def application(environ, start_response):
  parameters = parse_qs(environ.get('QUERY_STRING', ''))
  if 'urls' in parameters:
    url_file_name = escape(parameters['urls'][0])
  else:
    url_file_name='urls.ini'

  if 'window' in parameters:
    new_window= 'y'
  else:
    new_window='n'


  if 'start' in parameters:
    start_entry_to_display = int(escape(parameters['start'][0]))
  else:
    start_entry_to_display = 0
    
  if 'num' in parameters:
    num_entries_to_display = int(escape(parameters['num'][0]))
  else:
    num_entries_to_display = None
    
  from urllib import quote
  url = environ['wsgi.url_scheme']+'://'

  if environ.get('HTTP_HOST'):
    url += environ['HTTP_HOST']
  else:
    url += environ['SERVER_NAME']

  if environ['wsgi.url_scheme'] == 'https':
    if environ['SERVER_PORT'] != '443':
      url += ':' + environ['SERVER_PORT']
    else:
      if environ['SERVER_PORT'] != '80':
        url += ':' + environ['SERVER_PORT']

  url += quote(environ.get('SCRIPT_NAME', ''))
  url += quote(environ.get('PATH_INFO', ''))
  req_uri = url
  apache_location = '' #.join([req.document_root(),os.path.dirname(req.uri),"/"])
  start_response('200 OK', [('Content-Type', 'text/html')])
  return run( url_file_name, new_window, start_entry_to_display, num_entries_to_display, req_uri, apache_location)

if __name__ == '__main__':
  from wsgiref.simple_server import make_server
  srv = make_server('localhost', 8080, application)
  srv.serve_forever()



