# -*- coding: utf-8 -*-
import os

from google.appengine.api import users
from google.appengine.api import urlfetch
from google.appengine.api import memcache

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template

import re
import hashlib
import random
import string
import urllib
import traceback

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


def randstr(n=5):
    return ''.join(random.choice(string.ascii_letters + string.digits * 2) \
            for x in range(n))


def gen_modelhash(m, n=5):
    if not m:
        return None
    while True:
        id = randstr(n)
        if not m.all().filter("id =", id).count():
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


def get_recent_pivots(clear=False):
    if clear:
        memcache.delete("pivots_recent")
        return

    pivots = memcache.get("pivots_recent")
    if pivots:
        #logging.info("return cached pivots")
        return pivots

    pivots = []
    for pivot in Pivot.all().order("-date_submitted").fetch(20):
        pivots.append(pivot)
    memcache.set("pivots_recent", pivots)
    return pivots


def get_heavy_pivots(clear=False):
    if clear:
        memcache.delete("pivots_heavy")
        return

    pivots = memcache.get("pivots_heavy")
    if pivots:
        #logging.info("return cached pivots")
        return pivots
    pivots = []

    for pivot in Pivot.all():
        pivots.append((pivot.css.count(":"), pivot))
    pivots.sort(reverse=True)

    memcache.set("pivots_heavy", pivots[:20])
    return pivots


# Custom sites
class Main(webapp.RequestHandler):
    def head(self, screen_name=None):
        return

    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        invalid_url = decode(self.request.get('u'))

        recent = get_recent_pivots()[:10]
        heavy = get_heavy_pivots()[:10]

        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "index.html", \
                {"prefs": prefs, 'invalid_url': invalid_url, \
                'recent': recent, 'heavy': heavy}))

    def post(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        #logging.info("new pivot")

        # project
        title = decode(self.request.get('csspivot_title'))
        url = decode(self.request.get('csspivot_url'))
        # first css pivot
        css = decode(self.request.get('csspivot_css'))
        comment = decode(self.request.get('csspivot_comment'))
        new = decode(self.request.get('csspivot_new'))
        #logging.info("new: %s" % new)

        if not url:
            logging.info("- no css or url")
            self.response.out.write("no css or url")
            return

        if not css:
            css = ""

        if new and len(new) > 4:
            # Update an existing pivot
            p = Pivot.all().filter("id =", new).get()
            if not p:
                self.error(404)
                return
            if p.userprefs.key() != prefs.key():
                self.error(403)
                return
            p.css = css
        else:
            project = Project(userprefs=prefs, id=gen_modelhash(Project), \
                    title=title, url=url, rand=random.random())
            project.put()

            p = Pivot(userprefs=prefs, project=project, css=css, \
                    id=gen_modelhash(Pivot), comment=comment, \
                    rand=random.random())

        p.styles_count = p.css.count(":")
        p.put()

        # Clear Cache
        get_recent_pivots(clear=True)
        get_heavy_pivots(clear=True)

        self.redirect("/%s" % p.id)


class PivotView(webapp.RequestHandler):
    def get(self, id):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        pivot = Pivot.all().filter("id =", id).get()
        if not pivot:
            self.error(404)
            return

        key = random.randint(0, 100000000000000)
        memcache.set("_pivotpreview-%s" % key, pivot.css)

        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "pivot.html", \
                {"prefs": prefs, 'url': pivot.project.url, 'key': key, \
                'css': pivot.css, 'id': pivot.id, 'pivot': pivot}))


class PivotDetails(webapp.RequestHandler):
    def get(self, id):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        pivot = Pivot.all().filter("id =", id).get()

        self.response.out.write(template.render(tdir + "details.html", \
                {"prefs": prefs, 'pivot': pivot}))

    def post(self, id):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        #logging.info("update pivot")

        # project
        project_key = decode(self.request.get('project_key'))
        project = Project.get(db.Key(project_key))
        if not project:
            self.error(403)
            return

        # new css pivot
        css = decode(self.request.get('css'))
        comment = decode(self.request.get('comment'))
        if not css or not comment:
            logging.info("- no css or comment")
            return

        p = Pivot(userprefs=prefs, project=project, css=css, \
                id=gen_modelhash(Pivot), comment=comment,
                rand=random.random())
        p.put()

        self.redirect("/")


class Preview(webapp.RequestHandler):
    def post(self):
        return self.get()

    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        url = decode(self.request.get('url'))
        css = urllib.unquote(decode(self.request.get('css')))
        showdialog = False if css else True  # no css = new

        comment = decode(self.request.get('comment'))

        # have to memcache preview for proxy to pick it up
        key = random.randint(0, 100000000000000)
        memcache.set("_pivotpreview-%s" % key, css)
        #logging.info("set mc [%s]: %s" % (key, css))
        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "pivot.html", \
                {"prefs": prefs, 'url': url, 'key': key, 'css': css, \
                'id': None, 'showdialog': showdialog}))
        return


class UserView(webapp.RequestHandler):
    def get(self, username):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)


class AccountView(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "account.html", \
                {"prefs": prefs}))


class TourView(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "tour.html", \
                {"prefs": prefs}))


class ProxyView(webapp.RequestHandler):
    def post(self):
        return self.get()

    def get(self):
        """ Proxies the content for showing in an iframe """
        url = decode(self.request.get('url'))
        key = decode(self.request.get('key'))
        css = urllib.unquote(decode(self.request.get('css')))

        if not url:
            self.error(404)
            return

        if not "://" in url:
            url = "http://%s" % url

        headers = {}
        for header in ["User-Agent", "Cache-Control"]:
            if header in self.request.headers:
                headers[header] = self.request.headers[header]

        try:
            result = urlfetch.fetch(url, headers=headers, \
                    follow_redirects=True, deadline=10)
        except:
            logging.warning("urlfetch error [%s]: %s" % (url, \
                    traceback.format_exc()))
            return None

        for header in result.headers:
            self.response.headers.add_header(header, result.headers[header])

        try:
            encoding = result.headers['content-type'].split('charset=')[-1]
            #logging.info(encoding)
            res = unicode(result.content, encoding)
        except:
            res = unicode(result.content, errors='replace')

        # Update all links
        res = res.replace('src="', 'src="%s/' % url.strip("/"))
        res = res.replace("src='", "src='%s/" % url.strip("/"))
        #res = res.replace("'/", "'%s/" % url.strip("/"))
        res = res.replace('href="', 'href="%s/' % url.strip("/"))
        res = res.replace("href='", "href='%s/" % url.strip("/"))
        res = res.replace('url(', 'url(%s/' % url.strip("/"))

        # Revert absolute links
        res = res.replace("%s//" % url.strip("/"), "%s/" % url.strip("/"))
        res = res.replace("%s/http" % url.strip("/"), "http")
        res = res.replace("%s//" % url.strip("/"), "//")

        if not css:
            css = memcache.get("_pivotpreview-%s" % key)
            memcache.delete("_pivotpreview-%s" % key)

        # Inject css
        inject = """<style>%s</style>""" % css
        pos = re.search("</head", res, re.IGNORECASE)
        if not pos:
            # no /head tag
            pos = re.search("<body", res, re.IGNORECASE)
        if pos:
            res = """%s%s%s""" % (res[:pos.start()], inject, res[pos.start():])

        self.response.out.write(res)
