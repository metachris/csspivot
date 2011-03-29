# -*- coding: utf-8 -*-
from google.appengine.api import memcache
from models import *

# memcaching functions


def get_pivot_count(clear=False):
    if clear:
        memcache.delete("pivotcnt")
        return

    cnt = memcache.get("pivotcnt")
    if cnt:
        #logging.info("return cached pivots")
        return cnt

    cnt = 0
    offset = 0
    while True:
        _cnt = len(Pivot.all().fetch(1000, offset))
        if _cnt:
            offset += 1000
            cnt += _cnt
        else:
            break
    memcache.set("pivotcnt", cnt)
    return cnt


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
        memcache.delete("pivots_heavy2")
        return

    pivots = memcache.get("pivots_heavy2")
    if pivots:
        #logging.info("return cached pivots")
        return pivots

    pivots = []
    for pivot in Pivot.all().order("-date_submitted"):
        if pivot.styles_count > 2:
            pivots.append((pivot.styles_count, pivot))
            if len(pivots) == 20:
                break

    memcache.set("pivots_heavy2", pivots[:20])
    return pivots


def projects_for_domain(domain_base, offset=0, clear=False):
    # returns 100 projects, offset starts at 0
    if clear:
        memcache.delete("projects-domain_%s-%s" % (offset, domain_base))
        return

    projects = memcache.get("projects-domain_%s-%s" % (offset, domain_base))
    if projects:
        return projects

    projects = []
    for project in Project.all().filter("url_domain_base =", domain_base) \
            .fetch(100, offset * 100):
        projects.append(project)

    memcache.set("projects-domain_%s-%s" % (offset, domain_base), projects)
    logging.info("cached %s projects for %s" % (len(projects), domain_base))
    return projects


def pivots_for_domain(domain_base, offset=0, clear=False):
    # returns 100 pivots, offset starts at 0
    if clear:
        memcache.delete("pivots-domain_%s-%s" % (offset, domain_base))
        return

    pivots = memcache.get("pivots-domain_%s-%s" % (offset, domain_base))
    if pivots:
        return pivots

    pivots = []
    for pivot in Pivot.all().filter("url_domain_base =", domain_base) \
            .order("-styles_count").fetch(100, offset * 100):
        pivots.append(pivot)

    memcache.set("pivots-domain_%s-%s" % (offset, domain_base), pivots)
    logging.info("cached %s projects for %s" % (len(pivots), domain_base))
    return pivots


def get_topdomains(clear=False):
    if clear:
        memcache.delete("domains-top")
        return

    domains = memcache.get("domains-top")
    if domains:
        return domains

    domains = Domain.all().order("-pivot_count").fetch(70)
    memcache.set("domains-top", domains)
    logging.info("cached domains")
    return domains
