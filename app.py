from urlparse import parse_qs
from latestposts import UrlHandler
import webapp2

class MainPage(webapp2.RequestHandler):
  def get(self):
    query_string = self.request.query_string
    keep_blank_values = True
    parameters = parse_qs( query_string, keep_blank_values)

    req_uri = self.request.path_url
    pickle_and_ini_location = ''
    handler = UrlHandler( parameters, req_uri, pickle_and_ini_location)

    self.response.headers['Content-Type'] = 'text/html'
    self.response.write(handler.run())

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)



