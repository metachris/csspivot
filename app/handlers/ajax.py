# -*- coding: utf-8 -*-
import os

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import mail
from google.appengine.api import memcache

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import re
import hashlib
import random
import urllib
import traceback

from models import *
from tools import *
import mc

tdir = os.path.join(os.path.dirname(__file__), '../templates/')


class StarAction(webapp.RequestHandler):
    def post(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        if not prefs:
            self.error(404)
            return

        pivot_id = self.request.get('pivot_id')
        action = self.request.get('action')
        if action and pivot_id:
            pivot = Pivot.all().filter("id =", pivot_id).get()
            if not pivot:
                self.error(404)
                return

            star = Star.all().filter("userprefs =", prefs) \
                    .filter("pivot =", pivot).get()
            if action == "1":
                if star:
                    self.error(403)
                    return
                pivot.star_count += 1
                pivot.put()
                star = Star(userprefs=prefs, pivot=pivot)
                star.put()

            elif action == "-1":
                if not star:
                    self.error(403)
                    return
                star.delete()
                pivot.star_count -= 1
                pivot.put()

        logging.info("pivot %s has now %s star(s)" % (pivot.id, \
                pivot.star_count))
        self.response.out.write("")
