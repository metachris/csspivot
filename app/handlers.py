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
        logging.info("return cached pivots")
        return pivots
    pivots = []
    for pivot in Pivot.all().order("-date_submitted").fetch(10):
        pivots.append(pivot)
    memcache.set("pivots_recent", pivots)
    return pivots


# Custom sites
class Main(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        invalid_url = decode(self.request.get('u'))
        recent = get_recent_pivots()[:5]

        self.response.out.write(template.render(tdir + "index.html", \
                {"prefs": prefs, 'invalid_url': invalid_url, \
                'recent': recent}))

    def post(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        logging.info("new pivot")

        # project
        title = decode(self.request.get('csspivot_title'))
        url = decode(self.request.get('csspivot_url'))
        # first css pivot
        css = decode(self.request.get('csspivot_css'))
        comment = decode(self.request.get('csspivot_comment'))

        if not url:
            logging.info("- no css or url")
            self.response.out.write("no css or url")
            return

        if not css:
            css = ""

        project = Project(userprefs=prefs, id=gen_modelhash(Project), \
                title=title, url=url, rand=random.random())
        project.put()

        p = Pivot(userprefs=prefs, project=project, css=css, \
                id=gen_modelhash(Pivot), comment=comment, \
                rand=random.random())
        p.put()

        # Clear Cache
        get_recent_pivots(clear=True)

        self.redirect("/%s" % p.id)


def proxy(url, css, comment, id=None, showdialog=False, prefs=None):
    if not url:
        return "Not a valid url (%s)" % url

    if not "://" in url:
        url = "http://%s" % url
    logging.info("proxy: %s" % url)

    # Read url and decode content
    try:
        result = urlfetch.fetch(url, follow_redirects=True, deadline=10)
    except:
        logging.warning("urlfetch error [%s]" % url)
        return None

    logging.info(result.headers)
    try:
        encoding = result.headers['content-type'].split('charset=')[-1]
        logging.info(encoding)
        res = unicode(result.content, encoding)
    except:
        #res = unicode(result.content)
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

    # Inject header html
    header = template.render(tdir + "inject_header.html", \
            {'id': id, 'url': url, 'css': css, 'comment': comment, \
            'prefs': prefs})
    pos = re.search("<body[^>]*>(.*?)", res, re.IGNORECASE)
    if pos:
        res = """%s%s%s""" % (res[:pos.end()], header, res[pos.end():])

    # Inject css
    inject = """<style>%s body { margin:0px; padding:0px; }</style>""" % css
    pos = re.search("</head", res, re.IGNORECASE)
    if not pos:
        # no /head tag
        pos = re.search("<body", res, re.IGNORECASE)
    if pos:
        res = """%s%s%s""" % (res[:pos.start()], inject, res[pos.start():])

    # Inject footer html
    footer = template.render(tdir + "inject_footer.html", \
            {'id': id, 'url': url, 'css': css, 'comment': comment,
            'showdialog': showdialog})
    pos = re.search("</body", res, re.IGNORECASE)
    if not pos:
        pos = re.search("</html", res, re.IGNORECASE)
    if pos:
        res = """%s%s%s""" % (res[:pos.start()], footer, res[pos.start():])
    else:
        # eg. Google.com
        res += footer

    pos = re.search("<title>", res, re.IGNORECASE)
    if pos:
        res = """%s%s%s""" % (res[:pos.end()], "CSS Pivot: ", res[pos.end():])

    return res


class PivotView(webapp.RequestHandler):
    def get(self, id):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        pivot = Pivot.all().filter("id =", id).get()
        if not pivot:
            self.error(404)
            return

        res = proxy(pivot.project.url, pivot.css, pivot.comment, id=id, \
                prefs=prefs)
        self.response.out.write(res)


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
        logging.info("update pivot")

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
        comment = decode(self.request.get('comment'))
        showdialog = False if decode(self.request.get('s')) else True

        #self.response.out.write(template.render(tdir + "pivot_preview.html", \
        #        {"prefs": prefs, 'url': url, 'css': css}))
        #return
        res = proxy(url, css, comment, showdialog=showdialog, prefs=prefs)
        if res:
            self.response.out.write(res)
        else:
            self.redirect("/?u=%s" % url)


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
