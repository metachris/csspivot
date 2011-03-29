# -*- coding: utf-8 -*-
import urllib
import logging
import random
import string

from os import environ


def is_textenv():
    """
    True if devserver, False if appengine server

    Appengine uses  'Google App Engine/1.4.2',
    Devserver  uses 'Development/1.0'
    """
    return environ.get('SERVER_SOFTWARE', '').startswith('Development')


def decode(var):
    """Decode form input"""
    if not var:
        return var
    return unicode(var, 'utf-8') if isinstance(var, str) else unicode(var)


def randstr(n=5):
    return ''.join(random.choice(string.ascii_letters + \
            string.ascii_lowercase + string.digits * 3) for x in range(n))


def gen_modelhash(m, n=5):
    if not m:
        return None

    while True:
        id = randstr(n)
        if not m.all().filter("id =", id).count():
            return id


def get_domains(url):
    base = urllib.unquote(url)
    if "://" in base:
        base = base[base.index("://") + 3:]
    if "/" in base:
        base = base[:base.index("/")]
    base = base.split(".")
    #logging.info(base)
    if len(base) < 3:
        # has no subdomain
        return ".".join(base), ".".join(base)
    else:
        # has subdomain
        return ".".join(base[-2:]), ".".join(base)
