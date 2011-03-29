# -*- coding: utf-8 -*-
import os
from google.appengine.dist import use_library
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

# Load database models
from models import *

# Load request handlers
from handlers import *

urls = [
    (r'/admin', AdminView),
    (r'/login', LogIn),
    (r'/_ah/login_required', LogIn),
    (r'/logout', LogOut),
    (r'/account', AccountView),
    (r'/preview', Preview),
    (r'/proxy', ProxyView),
    (r'/tour', TourView),
    (r'/about', AboutView),
    (r'/proxy/([-\w]+)[/]?', ProxyView),
    (r'/', Main),
    (r'/d/(.*)', DomainView),
    (r'/([-\w]{5,6})[/]?', PivotView),
    (r'/([-\w]{5,6})[/]?/details', PivotDetails),
    #(r'/(.*)', UserView),
]

application = webapp.WSGIApplication(urls, debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
