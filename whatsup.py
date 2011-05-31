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

import simplejson
import time

from threading import Thread, Lock

realms = {}
myLock = Lock()

def synchronized(lock):
    """ WHEE! """
    def wrap(f):
    	def new_function(*args, **kw):
    	    lock.acquire()
    	    try:
    	        return f(*args, **kw)
    	    finally:
                lock.release()
    	return new_function
    return wrap

class MyThread(Thread):
    def run(self):
        self.populate_realms()
        time.sleep(180)
        self.run()

    @synchronized(myLock)
    def populate_realms(self):
        data = simplejson.loads(self.get_json())
        for realm in data['realms']:
            realms[realm['slug']] = realm

    def get_json(self):
        url = 'http://us.battle.net/api/wow/realm/status'
        return urllib2.urlopen(url).read()
        

class MainHandler(tornado.web.RequestHandler):
    def get(self, realm_slug = None):
        now = time.time()
        (realm_slug, realm) = select_realm(realm_slug)
        if realm_slug == None:
            raise tornado.web.HTTPError(404)
        status = "down"
        if realm['status'] == True:
            status = "up"
        message = realm['name'] + " is " + status
        self.output_message(message, realm_slug)

    def output_message(self, message, realm_slug):
        self.render('index.html', message = message, realm_slug = realm_slug)

class PlainTextHandler(MainHandler):
    def output_message(self, message, realm_slug):
        self.set_header('Content-Type', 'text/plain')
        self.write(message)


@synchronized(myLock)
def select_realm(realm_slug = None):
    if not realm_slug:
        realm_slug = random.choice(realms.keys())
    elif realm_slug not in realms:
        return (None, None)
    return (realm_slug, realms[realm_slug])


settings = {
    'static_path': os.path.join(os.path.dirname(__file__), 'static'),
}

application = tornado.web.Application([
    (r'/', MainHandler),
    (r'/([a-z0-9\-]+)', MainHandler),
    (r'/index.txt', PlainTextHandler),
    (r'/([a-z0-9\-]+)/index.txt', PlainTextHandler),
], **settings)

if __name__ == '__main__':
    port = 8000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    thread = MyThread()
    thread.daemon = True
    thread.start()

    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(port)
    tornado.ioloop.IOLoop.instance().start()

