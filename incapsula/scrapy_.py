import random
import time

from scrapy import Request
from BeautifulSoup import BeautifulSoup

from methods import *


class IncapsulaMiddleware(object):

    cookie_count = 0
    logger = logging.getLogger('incapsula')

    def _get_session_cookies(self, request):
        cookies_ = []
        for cookie_key, cookie_value in request.cookies.items():
            if 'incap_ses_' in cookie_key:
                cookies_.append(cookie_value)
        return cookies_

    def get_incap_cookie(self, request, response):
        extensions = load_plugin_extensions(navigator['plugins'])
        extensions.append(load_plugin(navigator['plugins']))
        extensions.extend(load_config())
        cookies = self._get_session_cookies(request)
        digests = []
        for cookie in cookies:
            digests.append(simple_digest(",".join(extensions) + cookie))
        res = ",".join(extensions) + ",digest=" + ",".join(str(digests))
        cookie = create_cookie('___utmvc', res, 20, request.url)
        return cookie

    def process_response(self, request, response, spider):
        # print 'processing %s - for %s' % (request.url, request.meta.get('org_req_url'))
        if not request.meta.get('incap_set', False):
            soup = BeautifulSoup(response.body.decode('ascii', errors='ignore'))
            meta = soup.find('meta', {'name': 'robots'})
            if not meta:
                return response
            self.logger.debug('setting incap cookie')
            cookie = self.get_incap_cookie(request, response)
            scheme, host = urlparse.urlsplit(request.url)[:2]
            url = '{scheme}://{host}/_Incapsula_Resource?SWKMTFSR=1&e={rdm}'.format(scheme=scheme, host=host, rdm=random.random())
            cpy = request.copy()
            cpy.meta['incap_set'] = True
            cpy.meta['org_req_url'] = request.url
            cpy.meta['org_body'] = response.decode('ascii', errors='ignore'),
            cpy.meta['org_request'] = request
            cpy.cookies.update(cookie)
            cpy._url = url
            return cpy
        self.logger.debug('incap set %s' % request.url)
        if request.meta.get('incap_set', False) and not request.meta.get('incap_request_1', False):
            self.logger.debug('incap set, fetching incap resource 1')
            timing = []
            start = now_in_seconds()
            timing.append('s:{}'.format(now_in_seconds() - start))
            code = get_obfuscated_code(request.meta.get('org_body'))
            parsed = parse_obfuscated_code(code)
            resource1, resource2 = get_resources(parsed, response.url)[1:]
            cpy = request.copy()
            cpy._url = str(resource1)
            cpy.meta['resource2'] = resource2
            cpy.meta['tstart'] = start
            cpy.meta['timing'] = timing
            cpy.meta['incap_request_1'] = True
            return cpy
        if request.meta.get('incap_request_1', False) and request.meta.get('incap_completed', False):
            self.logger.debug('incap resource 1 fetched, fetching incap resource 2')
            timing = request.meta.get('timing', [])
            resource2 = request.meta.get('resource2')
            start = request.meta.get('tstart')
            timing.append('c:{}'.format(now_in_seconds() - start))
            time.sleep(0.02)
            timing.append('r:{}'.format(now_in_seconds() - start))
            cpy = request.copy()
            cpy.meta['completed_incap'] = True
            cpy._url = str(resource2) + urllib.quote('complete ({})'.format(",".join(timing)))
            return cpy
        cpy = request.meta.get('org_request').copy()
        cpy._url = request.meta.get('org_req_url')
        cpy.dont_filter = True
        return cpy
        # return Request(request.meta.get('org_req_url'), cookies=request.cookies, meta=request.meta, dont_filter=True)
