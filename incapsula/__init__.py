import logging
import json
import random
import re
import time
import os
import urllib
import datetime

from BeautifulSoup import BeautifulSoup
from config import config


logger = logging.getLogger('incapsula')

_nav_fp = os.path.join(os.path.dirname(__file__), 'navigator.json')

logger.debug('loading navigator.json')
with open(_nav_fp, 'r') as f:
    navigator = json.loads(f.read().decode('ascii', errors='ignore'))
    
    
def _load_plugin_extensions(plugins):
    _extensions = []
    for k, v in plugins.items():
        logger.debug('calculating plugin_extension key={}'.format(k))
        if not isinstance(v, dict):
            continue
        filename = v.get('filename')
        if not filename:
            _extensions.append(urllib.quote('plugin_ext=plugins[i] is undefined'))
            break
        if len(filename.split('.')) == 2:
            extension = filename.split('.')[-1]
            if extension not in _extensions:
                _extensions.append(extension)
    return [urllib.quote('plugin_ext={}'.format(x)) for x in _extensions]


def _load_plugin(plugins):
    for k, v in plugins.items():
        logger.debug('calculating plugin key={}'.format(k))
        if '.' in v.get('filename', ''):
            filename, extension = v['filename'].split('.')
            return urllib.quote('plugin={}'.format(extension))
    
        
def _load_config(conf=None):
    conf = config if not conf else conf
    data = []
    if conf['navigator']['exists']:
        data.append(urllib.quote('navigator=true'))
    else:
        data.append(urllib.quote('navigator=false'))
    data.append(urllib.quote('navigator.vendor=' + conf['navigator']['vendor']))
    if conf['navigator']['vendor'] is None:
        data.append(urllib.quote('navigator.vendor=nil'))
    else:
        data.append(urllib.quote('navigator.vendor=' + conf['navigator']['vendor']))
    if conf['opera']['exists']:
        data.append(urllib.quote('opera=true'))
    else:
        data.append(urllib.quote('opera=false'))
    if conf['ActiveXObject']['exists']:
        data.append(urllib.quote('ActiveXObject=true'))
    else:
        data.append(urllib.quote('ActiveXObject=false'))
    data.append(urllib.quote('navigator.appName=' + conf['navigator']['appName']))
    if conf['navigator']['appName'] is None:
        data.append(urllib.quote('navigator.appName=nil'))
    else:
        data.append(urllib.quote('navigator.appName=' + conf['navigator']['appName']))
    if conf['webkitURL']['exists']:
        data.append(urllib.quote('webkitURL=true'))
    else:
        data.append(urllib.quote('webkitURL=false'))
    if len(navigator.get('plugins', {})) == 0:
        data.append(urllib.quote('navigator.plugins.length==0=false'))
    else:
        data.append(urllib.quote('navigator.plugins.length==0=true'))
    if not navigator.get('plugins'):
        data.append(urllib.quote('navigator.plugins.length==0=nil'))
    else:
        data.append(
            urllib.quote(
                'navigator.plugins.length==0=' + 'false' if len(navigator.get('plugins', {})) == 0 else 'true'))
    if conf['_phantom']['exists']:
        data.append(urllib.quote('_phantom=true'))
    else:
        data.append(urllib.quote('_phantom=false'))
    return data
    
    
logger.debug('loading encapsula extensions and plugins')
extensions = _load_plugin_extensions(navigator['plugins'])
extensions.append(_load_plugin(navigator['plugins']))
extensions.extend(_load_config())


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def _get_obfuscated_code(html):
    code = re.findall('var\s?b\s?=\s?\"(.*?)\"', html)
    return code[0]


def _parse_obfuscated_code(code):
    data = []
    for chunk in chunks(code, 2):
        data.append(int("".join(chunk), 16))
    code = [unichr(x) for x in data]
    return ''.join(code)


def _get_resource(code):
    resources = re.findall('(/_Incapsula_Resource.*?)\"', code)
    return 'http://www.bjs.com' + resources[0], 'http://www.bjs.com' + resources[1]


def _now_in_seconds():
    return (datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds()


def _send_second_request(f):
    """
    wrap load_encapsula_resource so that the second request to fetch/set cookies can be completed with necessary timer.
    :param f:
    :return:
    """
    timing = []
    start = _now_in_seconds()
    timing.append('s:%d' % (_now_in_seconds() - start))

    def inner(*args, **kwargs):
        sess, resource = f(*args, **kwargs)
        timing.append('c:%d' % (_now_in_seconds() - start))
        time.sleep(0.02)  # simulate reload delay
        timing.append('r:%d' % (_now_in_seconds() - start))
        sess.get(resource + urllib.quote('complete (%s)' % ",".join(timing)))
    return inner


@_send_second_request
def _load_encapsula_resource(sess, encap_html):
    code = _get_obfuscated_code(encap_html)
    parsed = _parse_obfuscated_code(code)
    resource1, resource2 = _get_resource(parsed)
    sess.get(resource1)
    return sess, resource2


def crack(sess, response):
    """
    Pass a response object to this method to retry the url after the incapsula cookies have been set.

    Usage:
        >>> import incapsula
        >>> import requests
        >>> session = requests.Session()
        >>> response = incapsula.crack(session, session.get('http://www.incapsula-blocked-resource.com'))
        >>> print response.content  # response content should be incapsula free.
    :param sess: A requests.Session object.
    :param response: The response object from an incapsula blocked website.
    :return: Original response if not blocked, or new response after unblocked
    :type sess: requests.Session
    :type response: requests.Response
    :rtype: requests.Response
    """
    soup = BeautifulSoup(response.content)
    meta = soup.find('meta', {'name': 'robots'})
    if not meta:  # if the page is not blocked, then just return the original request.
        return response
    set_incap_cookie(sess)
    # populate first round cookies
    sess.get('http://www.bjs.com/_Incapsula_Resource?SWKMTFSR=1&e=%s' % random.random())
    # populate second round cookies
    _load_encapsula_resource(sess, response.content)
    return sess.get(response.url)


def _get_session_cookies(sess):
    cookies_ = []
    for cookie_key, cookie_value in sess.cookies.items():
        if 'incap_ses_' in cookie_key:
            cookies_.append(cookie_value)
    return cookies_


def _simple_digest(mystr):
    res = 0
    for c in mystr:
        res += ord(c)
    return res


def _create_cookie(name, value, seconds):
    cookie = {
        'version': '0',
        'name': name,
        'value': value,
        'port': None,
        'domain': 'www.bjs.com',
        'path': '/',
        'secure': False,
        'expires': ((datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds)) - datetime.datetime(1970, 1, 1)).total_seconds(),
        'discard': True,
        'comment': None,
        'comment_url': None,
        'rest': {},
        'rfc2109': False
    }
    return cookie


def set_incap_cookie(sess):
    cookies = _get_session_cookies(sess)
    digests = []
    for cookie in cookies:
        digests.append(_simple_digest(",".join(extensions) + cookie))
    res = ",".join(extensions) + ",digest=" + ",".join(digests)
    cookie = _create_cookie("___utmvc", res, 20)
    sess.cookies.set(**cookie)
