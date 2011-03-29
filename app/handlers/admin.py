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
        u = decode(self.request.get('u'))

        if u:
            start = int(u) * 500
            logging.info("start updating @ %s" % start)
            projects = Project.all().order("id").fetch(500, start)
            cnt = 0
            for p in projects:
                p.url_domain_base, p.url_domain_full = get_domains(p.url)
                p.put()
                cnt += 1

            logging.info("- %s projects updated" % cnt)
            if not cnt:
                self.error(404)
                return

        self.response.out.write(template.render(tdir + "admin.html", {}))
