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
    return ''.join(random.choice(string.ascii_letters + string.digits * 2) \
            for x in range(n))


def gen_modelhash(m, n=5):
    if not m:
        return None

    while True:
        id = randstr(n)
        if not m.all().filter("id =", id).count():
            return id
