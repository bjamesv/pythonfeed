from urlparse import parse_qs
from latestposts import UrlHandler

def application(environ, start_response):
  keep_blank_values = True
  parameters = parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values)
    
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
  if 'DOCUMENT_ROOT' in environ:
      apache_location = ''.join([environ['DOCUMENT_ROOT'],environ.get('SCRIPT_NAME', '')])
      #we have the URL path which includes a nonexistant script "file name"
      apache_location = apache_location.rstrip('/')
      apache_location = ''.join([apache_location.rpartition('/')[0],"/"])
  else:
      apache_location = 'C:/Program Files/Apache Software Foundation/Apache2.2/htdocs/test/python//'                         
  start_response('200 OK', [('Content-Type', 'text/html')])
  handler = UrlHandler( parameters, req_uri, apache_location)
  return handler.run()

if __name__ == '__main__':
  from wsgiref.simple_server import make_server
  srv = make_server('localhost', 8080, application)
  srv.serve_forever()



