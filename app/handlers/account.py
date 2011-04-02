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


class AccountSettingsView(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        logging.info(prefs)
        error = decode(self.request.get('e'))
        action = decode(self.request.get('a'))

        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + \
                "account_settings.html",
                {"prefs": prefs, "error": error, "action": action}))

    def post(self):
        # update user profile
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        username = decode(self.request.get('username'))
        logging.info("update username for %s to %s" % (prefs, username))

        if username and len(username) > 2:
            if username == prefs.nickname:
                self.redirect("/account/settings")
                return

            # check
            q = InternalUser.all().filter("nickname =", username).get()
            if q:
                # nickname already taken
                self.redirect("/account/settings?e=u2")
                return

            # update nickname now
            prefs.nickname = username
            prefs.put()
            self.redirect("/account/settings?a=u")

        else:
            self.redirect("/account/settings?e=u1")
            return
