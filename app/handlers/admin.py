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
        a2 = decode(self.request.get('a2'))
        b = decode(self.request.get('b'))
        c = decode(self.request.get('c'))
        if a:
            start = int(a) * 500
            # delete all empty pivots
            cnt = 0
            for pivot in Pivot.all().filter("styles_count =", None):
                if not pivot.styles_count:
                    pivot.delete()
                    cnt += 1
            logging.info("deleted %s empty pivots" % cnt)

        if a2:
            start = int(a2) * 500
            # delete all empty pivots
            cnt = 0
            for pivot in Pivot.all().filter("styles_count =", 0):
                if not pivot.styles_count:
                    pivot.delete()
                    cnt += 1
            logging.info("deleted %s empty pivots" % cnt)

        if b:
            # update projects
            start = int(c) * 100
            # problem: many duplicates
            cnt = 0
            for project in Project.all().fetch(500, start):
                project.pivot_count = Pivot.all().filter("project =", project).count()
                project.url = project.url.strip("/")
                project.put()
                cnt += 1
                logging.info("- %s: %s pivot" % (project.url, project.pivot_count))
            
        if c:
            start = int(b) * 500
            # update domain counts
            cnt = 0
            for domain in Domain.all().fetch(500, start):
                domain.pivot_count = Pivot.all().filter("domain =", domain).count()
                domain.project_count = Project.all().filter("domain =", domain).count()
                domain.put()
                #logging.info("- %s: %s pivot" % (domain.url_domain_base, domain.pivot_count))
                cnt += 1
            logging.info("- updated %s domains" % (cnt))

        self.response.out.write(template.render(tdir + "admin.html", {}))
