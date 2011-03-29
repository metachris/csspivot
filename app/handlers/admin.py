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
            cnt1 = cnt2 = 0
            for project in Project.all().order("id").fetch(500, start):
                if not project.domain:
                    d = Domain.all().filter("url_domain_base =", project.url_domain_base).get()
                    if not d:
                        d = Domain()
                        d.url_domain_base = project.url_domain_base
                        d.url_domain_full = project.url_domain_full
                        d.put()
                        cnt1 += 1
                    project.domain = d
                    project.put()
                    cnt2 += 1
            logging.info("updated %s projects, created %s domains" % (cnt2, cnt1))

        a2 = decode(self.request.get('a2'))
        if a2:
            # now set the project count
            for domain in Domain.all():
                domain.project_count = Project.all().filter("domain =", domain).count()
                domain.put()
                logging.info("- %s: %s projects" % (domain.url_domain_base, domain.project_count))


        b = decode(self.request.get('b'))
        if b:
            # update projects -- add a domain
            start = int(b) * 500
            cnt1 = cnt2 = 0
            for pivot in Pivot.all().order("id").fetch(500, start):
                if not pivot.domain:
                    d = Domain.all().filter("url_domain_base =", pivot.url_domain_base).get()
                    if not d:
                        d = Domain()
                        d.url_domain_base = pivot.url_domain_base
                        d.url_domain_full = pivot.url_domain_full
                        d.put()
                        cnt1 += 1
                    pivot.domain = d
                    pivot.put()
                    cnt2 += 1
            logging.info("updated %s pivot, created %s domains" % (cnt2, cnt1))

        b2 = decode(self.request.get('b2'))
        if b2:
            # now set the project count
            for domain in Domain.all():
                domain.pivot_count = Pivot.all().filter("domain =", domain).count()
                domain.put()
                logging.info("- %s: %s pivot" % (domain.url_domain_base, domain.pivot_count))



        self.response.out.write(template.render(tdir + "admin.html", {}))
