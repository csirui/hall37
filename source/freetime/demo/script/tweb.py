import time
import struct
import urllib
import urllib2
posturl = "http://127.0.0.1:10001/"
def post(url, data):
  req = urllib2.Request(url)
  req.add_header('log-type', 'chip')
  req.add_header('log-group', 'user1')
  #data = urllib.urlencode(data)
  #enable cookie
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
  response = opener.open(req, data)
  return response.read()

def get(url):
  return urllib2.urlopen(url).read()

def main():
  ret = post(posturl, _BIDATA)
  if len(ret)!=0:
    print ret

if __name__ == '__main__':
  for x in xrange(10000000):
    get(posturl)
