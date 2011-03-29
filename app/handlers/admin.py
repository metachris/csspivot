# -*- coding: utf-8 -*-
import os
import logging

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.api import memcache

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import mc

from models import *
from tools import *


tdir = os.path.join(os.path.dirname(__file__), '../templates/')


class AdminView(webapp.RequestHandler):
    def get(self):
        a = decode(self.request.get('a'))
        if a:
            # update projects -- add a domain
            start = int(a) * 500

        b = decode(self.request.get('b'))
        if b:
            # update pivots -- add a domain
            start = int(b) * 500

        self.response.out.write(template.render(tdir + "admin.html", {}))
