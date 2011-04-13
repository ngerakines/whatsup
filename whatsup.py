import os
import sys
import random

try:
    from hashlib import md5
except ImportError:
    from md5 import md5

import tornado.httpserver
import tornado.ioloop
import tornado.web

import urllib2

from pprint import pprint

import simplejson

realms = {}

class MainHandler(tornado.web.RequestHandler):
    def get(self, realm_slug = None):
        if not realm_slug:
            realm_slug = random.choice(realms.keys())
        elif realm_slug not in realms:
            raise tornado.web.HTTPError(404)
        self.output_message(realms[realm_slug], realm_slug)

    def output_message(self, realm, realm_slug):
        status = "down"
        if realm['status'] == True:
            status = "up"
        message = realm['name'] + " is " + status
        self.render('index.html', message = message, realm_slug = realm_slug)

class PlainTextHandler(MainHandler):
    def output_message(self, realm, realm_slug):
        self.set_header('Content-Type', 'text/plain')
        self.write(realm)

def populate_realms():
    data = simplejson.loads(get_json())
    for realm in data['realms']:
        realms[realm['slug']] = realm

def get_json():
    url = 'http://us.battle.net/api/wow/realm/status'
    return urllib2.urlopen(url).read()

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
}

application = tornado.web.Application([
    (r'/', MainHandler),
    (r'/([a-z0-9]+)', MainHandler),
    # (r'/index.txt', PlainTextHandler),
    # (r'/([a-z0-9]+)/index.txt', PlainTextHandler),
], **settings)

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    populate_realms()

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

