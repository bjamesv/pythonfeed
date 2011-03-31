from mod_python import apache
from latestposts import run

def handler(req):
  req.content_type = 'text/html'
  req.write( run())
  return apache.OK


