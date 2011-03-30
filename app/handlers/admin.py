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
        b2 = decode(self.request.get('b2'))
        if b2:
            # now set the project count
            for domain in Domain.all():
                domain.pivot_count = Pivot.all().filter("styles_count >", 0).filter("domain =", domain).count()
                domain.put()
                logging.info("- %s: %s pivot" % (domain.url_domain_base, domain.pivot_count))

        self.response.out.write(template.render(tdir + "admin.html", {}))
