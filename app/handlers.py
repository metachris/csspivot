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


# Custom sites
class Main(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        invalid_url = decode(self.request.get('u'))
        self.response.out.write(template.render(tdir + "index.html", \
                {"prefs": prefs, 'invalid_url': invalid_url}))

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

        self.redirect("/%s" % p.id)


class Account(webapp.RequestHandler):
    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        self.response.out.write(template.render(tdir + "index.html", \
                {"prefs": prefs}))


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


def proxy(url, css, comment, id=None, showdialog=False):
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
        res = unicode(result.content)

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

    # Inject header html
    header = template.render(tdir + "inject_header.html", \
            {'id': id, 'url': url, 'css': css, 'comment': comment})
    pos = re.search("<body[^>]*>(.*?)", res, re.IGNORECASE)
    if pos:
        res = """%s%s%s""" % (res[:pos.end()], header, res[pos.end():])

    # Inject css
    inject = """<style>%s</style>""" % css
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
        logging.info("load pivot %s" % id)
        pivot = Pivot.all().filter("id =", id).get()
        if not pivot:
            self.error(404)
            return

        res = proxy(pivot.project.url, pivot.css, pivot.comment, id=id)
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
        res = proxy(url, css, comment, showdialog=showdialog)
        if res:
            self.response.out.write(res)
        else:
            self.redirect("/?u=%s" % url)
