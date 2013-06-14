"""
Pythonfeed: flexible software for convenient webfeed reading.
Copyright 2013 Brandon J Van Vaerenbergh
All rights reserved.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""
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



