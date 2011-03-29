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
    def head(self, screen_name=None):
        return

    def get(self):
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)
        invalid_url = decode(self.request.get('u'))

        recent = mc.get_recent_pivots()[:10]
        heavy = mc.get_heavy_pivots()[:10]

        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "index.html", \
                {"prefs": prefs, 'invalid_url': invalid_url, \
                'recent': recent, 'heavy': heavy, \
                'pivot_count': mc.get_pivot_count()}))

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
        orig = decode(self.request.get('csspivot_orig'))
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
            # Create a new pivot. Reference parent pivot+project if exits
            parent_pivot = None
            if orig:
                # pivot has a parent. find that and reference it
                parent_pivot = Pivot.all().filter("id =", orig).get()
                if parent_pivot:
                    project = parent_pivot.project

            d_base, d_full = get_domains(url)

            domain_created = False
            domain = Domain.all().filter("url_domain_base =", d_base).get()
            if not domain:
                domain = Domain(url=url, url_domain_base=d_base, \
                        url_domain_full=d_full)
                domain.put()
                domain_created = True

            if not parent_pivot:
                # create a new project. first check if domain exists
                project = Project(userprefs=prefs, id=gen_modelhash(Project), \
                        title=title, url=url, rand=random.random())

                domain.project_count += 1
                project.domain = domain
                project.url_domain_base = d_base
                project.url_domain_full = d_full
                project.put()

            p = Pivot(userprefs=prefs, project=project, css=css, \
                    id=gen_modelhash(Pivot), comment=comment, \
                    rand=random.random())

            p.domain = domain
            p.url = url
            p.url_domain_base = project.url_domain_base
            p.url_domain_full = project.url_domain_full

            if parent_pivot:
                p.parent_pivot = parent_pivot
                logging.info("parent pivot set")

            if not domain_created:
                # to not save domain twice within very short time when created
                domain.pivot_count += 1
                domain.put()

        if p.css:
            p.styles_count = p.css.count(":")

        p.put()

        # Clear Cache
        mc.get_recent_pivots(clear=True)
        mc.get_heavy_pivots(clear=True)
        mc.get_pivot_count(clear=True)

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
                {"prefs": prefs, 'url': pivot.url, 'key': key, \
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
            logging.warning("no encoding found. decode replace [%s]" % url)
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


class AboutView(webapp.RequestHandler):
    def post(self):
        # feedback form submit
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        msg = decode(self.request.get('msg'))
        #logging.info("msg: %s" % msg)
        if msg:
            if prefs:
                sender = "%s (%s)" % (prefs.nickname, prefs.email)
            else:
                sender = decode(self.request.get('email'))
            logging.info("feedback '%s' from %s" % (msg, sender))
            message = mail.EmailMessage()
            message.sender = "CSS Pivot <hello@csspivot.com>"
            message.to = "metakaram@gmail.com"
            message.subject = "CSS Pivot Feedback"
            message.body = "Feedback from '%s':\n\n%s" % (sender, msg)
            message.send()


class DomainView(webapp.RequestHandler):
    def get(self, domain):
        # feedback form submit
        user = users.get_current_user()
        prefs = InternalUser.from_user(user)

        domain_base, domain_full = get_domains(domain)
        logging.info("base: %s, full: %s" % (domain_base, domain_full))
        if not domain_base or len(domain_base) < 5:
            self.error(404)
            return

        #projects = mc.projects_for_domain(domain_base)
        pivots = mc.pivots_for_domain(domain_base)
        logging.info("--> %s pivots" % len(pivots))

        webapp.template.register_template_library('common.templateaddons')
        self.response.out.write(template.render(tdir + "domain.html", \
                {"prefs": prefs, 'pivots': pivots, 'count': len(pivots),\
                'domain_base': domain_base}))
