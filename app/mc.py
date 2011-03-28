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
