# -*- coding: utf-8 -*-
import logging

from hashlib import md5

from google.appengine.ext import db
from google.appengine.api import users


class InternalUser(db.Model):
    nickname = db.StringProperty()
    email = db.StringProperty(required=False)
    email_md5 = db.StringProperty(required=False)  # used for gravatar

    federated_identity = db.StringProperty()
    federated_provider = db.StringProperty()

    # google user id is only used on the dev server
    google_user_id = db.StringProperty()

    date_joined = db.DateTimeProperty(auto_now_add=True)
    date_lastlogin = db.DateTimeProperty(auto_now_add=True)  # TODO
    date_lastactivity = db.DateTimeProperty(auto_now_add=True)

    email = db.StringProperty(required=True)

    date_joined = db.DateTimeProperty(auto_now_add=True)
    date_lastlogin = db.DateTimeProperty(auto_now_add=True)

    boolean_property = db.BooleanProperty(default=True)

    @staticmethod
    def from_user(user):
        if not user:
            return None

        if not user.federated_identity():
            logging.warning("_ user has no fed id [%s]" % user)

        if user.federated_identity():
            q = db.GqlQuery("SELECT * FROM InternalUser WHERE \
                federated_identity = :1 AND federated_provider = :2", \
                user.federated_identity(), user.federated_provider())
        else:
            q = db.GqlQuery("SELECT * FROM InternalUser WHERE \
                google_user_id = :1", user.user_id())

        prefs = q.get()

        if not prefs:
            # create regular new userpref object now
            nick = user.nickname()
            if user.email():
                if not nick or "http://" in nick:
                    nick = user.email()

            mail = user.email().strip()
            m = md5(mail.lower()).hexdigest() if mail else ""
            if not mail:
                mail = " "  # bugfix for InternalUser requires email...

            logging.info("_ create new internaluser")
            fed_id = user.federated_identity()
            fed_prov = user.federated_provider()
            prefs = InternalUser(federated_identity=fed_id,\
                federated_provider=fed_prov, nickname=nick, email=mail)
            prefs.email_md5 = m

            prefs.google_user_id = user.user_id()
            prefs.put()

        return prefs


class Domain(db.Model):
    url = db.StringProperty(required=True)  # eg. www.google.com/about
    url_domain_full = db.StringProperty()   # eg. www.google.com
    url_domain_base = db.StringProperty()   # eg. google.com

    date_submitted = db.DateTimeProperty(auto_now_add=True)


class Project(db.Model):
    userprefs = db.ReferenceProperty(InternalUser)
    domain = db.ReferenceProperty(Domain)
    rand = db.FloatProperty()

    id = db.StringProperty(required=True)
    title = db.StringProperty()
    url = db.StringProperty(required=True)  # eg. www.google.com/about
    url_domain_full = db.StringProperty()   # eg. www.google.com
    url_domain_base = db.StringProperty()   # eg. google.com

    date_submitted = db.DateTimeProperty(auto_now_add=True)


class Pivot(db.Model):
    userprefs = db.ReferenceProperty(InternalUser)
    project = db.ReferenceProperty(Project, required=True)
    domain = db.ReferenceProperty(Domain)
    parent_pivot = db.SelfReferenceProperty()

    comment = db.StringProperty()
    css = db.TextProperty()

    id = db.StringProperty(required=True)
    rand = db.FloatProperty()
    date_submitted = db.DateTimeProperty(auto_now_add=True)
    views = db.IntegerProperty(default=0)

    url = db.StringProperty()  # eg. www.google.com/about
    url_domain_full = db.StringProperty()  # eg. www.google.com
    url_domain_base = db.StringProperty()  # eg. google.com

    # number of : characters (single styles)
    styles_count = db.IntegerProperty(default=0)
