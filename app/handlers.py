# -*- coding: utf-8 -*-
import os

from google.appengine.api import users
from google.appengine.api import urlfetch

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import re
import hashlib
import random
import string
import urllib

from models import *

# Setup jinja templating
#template_dirs = []
#template_dirs.append(os.path.join(os.path.dirname(__file__), 'templates'))
#env = Environment(loader=FileSystemLoader(template_dirs))

tdir = os.path.join(os.path.dirname(__file__), 'templates/')


def decode(var):
    """Decode form input"""
    if not var:
        return var
    return unicode(var, 'utf-8') if isinstance(var, str) else unicode(var)


def randstr(n=6):
    return ''.join(random.choice(string.ascii_letters + string.digits * 2) \
            for x in range(n))


def free_pivotid(n=6):
    while True:
        id = randstr(n)
        if not Pivot.all().filter("id =", id).count():
            return id


# OpenID Login
class LogIn(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        action = self.request.get('action')
        target_url = self.request.get('continue')
        if action and action == "verify":
            f = self.request.get('openid_identifier')
            url = users.create_login_url(target_url, federated_identity=f)
            self.redirect(url)
        else:
            self.response.out.write(template.render(tdir + "login.html", \
                    {"continue_to": target_url}))


class LogOut(webapp.RequestHandler):
    def get(self):
        url = users.create_logout_url("/")
        self.redirect(url)


# Custom sites
class Main(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        self.response.out.write(template.render(tdir + "index.html", \
                {"prefs": prefs}))

    def post(self):
        user = users.get_current_user()
        if not user:
            self.error(403)
            return

        prefs = InternalUser.from_user(user)
        logging.info("new pivot")

        url = decode(self.request.get('url'))
        css = decode(self.request.get('css'))

        if not url or not css:
            logging.info("- no css or url")
            return

        p = Pivot(userprefs=prefs, url=url, css=css, id=free_pivotid())
        p.put()

        self.redirect("/")


class Account(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.out.write(template.render(tdir + "index.html", \
                {"user": user}))


class AssestHandler(webapp.RequestHandler):
    def get(self):
        url = "http://news.ycombinator.com" + self.request.path
        if self.request.query_string is not None:
            url = url + '?' + self.request.query_string

        if 'user' in self.request.cookies:
            fetch_headers = {'Cookie': 'user=' + self.request.cookies['user']}
            result = urlfetch.fetch(url, headers=fetch_headers, \
                    follow_redirects=False, deadline=10)
        else:
            result = urlfetch.fetch(url, follow_redirects=False, deadline=10)

        if 'set-cookie' in result.headers:
            self.response.headers.add_header('set-cookie', \
                    result.headers.get('set-cookie'))

        if 'location' in result.headers:
            self.redirect(result.headers.get('location'))
        else:
            self.response.headers.add_header('content-type', \
                    result.headers['content-type'])
            self.response.out.write(result.content)

    def post(self):
        url = "http://news.ycombinator.com" + self.request.path
        post_data = ''
        for arg in self.request.arguments():
            post_data += arg + '=' + self.request.get(arg) + '&'
        post_data = post_data[:-1]
        if 'user' in self.request.cookies:
            fetch_headers = {'Cookie': 'user=' + self.request.cookies['user']}
            result = urlfetch.fetch(url, method=urlfetch.POST, \
                    headers=fetch_headers, payload=post_data, \
                    follow_redirects=False, deadline=10)
        else:
            result = urlfetch.fetch(url, method=urlfetch.POST, \
                    payload=post_data, follow_redirects=False, deadline=10)

        if 'set-cookie' in result.headers:
            self.response.headers.add_header('set-cookie', \
                    result.headers.get('set-cookie'))

        if 'location' in result.headers:
            self.redirect(result.headers.get('location'))
        else:
            self.response.out.write(result.content)


class PivotView(webapp.RequestHandler):
    def get(self, id):
        logging.info("load pivot %s" % id)
        pivot = Pivot.all().filter("id =", id).get()
        if not pivot:
            self.error(404)
            return

        # Read url and decode content
        result = urlfetch.fetch(pivot.url, follow_redirects=True, deadline=10)
        encoding = result.headers['content-type'].split('charset=')[-1]
        res = unicode(result.content, encoding)

        # Inject out header html
        pos = re.search("<body[^>]*>(.*?)", res)
        if pos:
            logging.info("pos1: %s" % pos)
            res = """%s<div id='csspivot'>css pivot</div><div style="clear:both;"></div>%s""" % \
                    (res[:pos.end()], res[pos.end():])

        # Inject css
        inject = """<style>%s</style>""" % pivot.css
        res = res.replace("</head", "%s</head" % inject)

        self.response.out.write(res)
