import time
import ssl
import os
import copy
import zlib
import random
import threading
import urllib3
import requests
import urllib3.util
from os import path
from selenium.webdriver.common.by import By
from . import utils, _paths, _proxy_handler
try:
    import rsa
except ImportError:
    rsa = None
ProxyMode = _proxy_handler.ProxyMode
DEFAULT_ACCEPT_ENCODING = 'gzip, deflate'
if hasattr(requests, 'utils'):
    if hasattr(requests.utils, 'DEFAULT_ACCEPT_ENCODING'):
        DEFAULT_ACCEPT_ENCODING = requests.utils.DEFAULT_ACCEPT_ENCODING

class Headers(object):
    __author__ = 'Vladya'
    GOOGLE_CHROME = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 'Accept-Encoding': DEFAULT_ACCEPT_ENCODING, 'Accept-Language': 'en-US,en;q=0.9', 'Dnt': '1', 'Priority': 'u=0, i', 'Sec-Ch-Ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"', 'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': 'Windows', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'}
    YANDEX_BROWSER = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 'Accept-Encoding': DEFAULT_ACCEPT_ENCODING, 'Accept-Language': 'en,ru;q=0.9', 'Dnt': '1', 'Priority': 'u=0, i', 'Sec-Ch-Ua': '"Not A(Brand";v="8", "Chromium";v="132", "Google Chrome";v="132"', 'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': '"Windows"', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36'}
    EDGE = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7', 'Accept-Encoding': DEFAULT_ACCEPT_ENCODING, 'Accept-Language': 'en-US,en;q=0.9', 'Priority': 'u=0, i', 'Sec-Ch-Ua': '"Chromium";v="134", "Not:A-Brand";v="24", "Microsoft Edge";v="134"', 'Sec-Ch-Ua-Mobile': '?0', 'Sec-Ch-Ua-Platform': '"Windows"', 'Sec-Fetch-Dest': 'document', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'none', 'Sec-Fetch-User': '?1', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36 Edg/134.0.0.0'}

class HostInfo(object):
    __author__ = 'Vladya'

    def __init__(self, host):
        self._host = host
        self._last_request = None
        self._lock = threading.Lock()

class HTTPSAdapter(requests.adapters.HTTPAdapter):
    __author__ = 'Vladya'

    def __init__(self, *args, **kwargs):
        _specific_tls_versions = kwargs.pop('specific_tls_versions', None)
        if _specific_tls_versions is not None:
            for v in _specific_tls_versions:
                assert v in (0, 1, 2, 3), v
            self.__specific_tls_versions = frozenset(_specific_tls_versions)
        else:
            self.__specific_tls_versions = None
        super(HTTPSAdapter, self).__init__(*args, **kwargs)

    def _get_context(self):
        if self.__specific_tls_versions and 3 in self.__specific_tls_versions:
            context = urllib3.util.ssl_.create_urllib3_context()
        else:
            try:
                context = urllib3.util.ssl_.create_urllib3_context(ssl_maximum_version=ssl.TLSVersion.TLSv1_2)
            except (AttributeError, TypeError):
                context = urllib3.util.ssl_.create_urllib3_context(ssl.PROTOCOL_TLSv1_2)
        ca_bundle = requests.utils.extract_zipped_paths(requests.utils.DEFAULT_CA_BUNDLE_PATH)
        context.load_verify_locations(ca_bundle)
        if self.__specific_tls_versions is not None:
            opts = ['OP_NO_TLSv1', 'OP_NO_TLSv1_1', 'OP_NO_TLSv1_2', 'OP_NO_TLSv1_3']
            for v in self.__specific_tls_versions:
                if v == 0:
                    opts.remove('OP_NO_TLSv1')
                elif v == 1:
                    opts.remove('OP_NO_TLSv1_1')
                elif v == 2:
                    opts.remove('OP_NO_TLSv1_2')
                elif v == 3:
                    opts.remove('OP_NO_TLSv1_3')
            for o in opts:
                if hasattr(ssl, o):
                    context.options |= getattr(ssl, o)
        return context

    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = self._get_context()
        return super(HTTPSAdapter, self).init_poolmanager(*args, **kwargs)

    def proxy_manager_for(self, *args, **kwargs):
        kwargs['ssl_context'] = self._get_context()
        return super(HTTPSAdapter, self).proxy_manager_for(*args, **kwargs)

class WebHandler(requests.Session):
    __author__ = 'Vladya'
    RPM = 100.0
    MAX_ATTEMPTS = 5
    LAST_TIMEOUT = 50.0
    CHUNK_SIZE_FOR_RANGED_REQUESTS = 16384
    RANGED_REQUESTS_DEFAULT = False
    create_lock = threading.Lock()
    instances = {}
    initialized = False
    _FORCE_VERIFY = None
    _PROJECT_SITE_KEY = None
    ENCODED_PREFIX = b'tr3000padding'
    UNIQUE_ID = None

    def __new__(cls, logger_object, unique_id=None, _headers=None, specific_tls_versions=None):
        with cls.create_lock:
            if unique_id not in cls.instances:
                cls.instances[unique_id] = super(WebHandler, cls).__new__(cls)
            return cls.instances[unique_id]

    def __init__(self, logger_object, unique_id=None, _headers=None, specific_tls_versions=None):
        if self.initialized:
            return
        super(WebHandler, self).__init__()
        if not _headers:
            _headers = Headers.GOOGLE_CHROME
        self.headers.clear()
        self.headers.update(_headers)
        self.UNIQUE_ID = unique_id
        self.LOGGER = logger_object.getChild('WebHandler')
        if self.UNIQUE_ID is not None:
            self.LOGGER = self.LOGGER.getChild(self.UNIQUE_ID)
        self.__request_lock = threading.Lock()
        self.__create_host_object_lock = threading.Lock()
        self.__hosts = {}
        self.__selenium_session = None
        self.__header_is_set = False
        self.__proxy_object = None
        self.set_tls_protocol(specific_tls_versions)
        self.initialized = True

    @property
    def selenium_session(self):
        return self.__selenium_session

    @property
    def proxy_object(self):
        return self.__proxy_object

    def set_tls_protocol(self, versions=None):
        self.__current_tls_protocol = versions
        return self.__remount_adapter(self.__current_tls_protocol)

    def __remount_adapter(self, versions=None):
        self.close()
        if versions is False:
            versions = self.__current_tls_protocol
        self.mount('https://', HTTPSAdapter(specific_tls_versions=versions))
        if versions is None:
            self.LOGGER.debug('Set default TLS version.')
        else:
            self.LOGGER.debug('Set TLS %s version.', versions)

    def set_selenium_session(self, selenium_session):
        self.__selenium_session = selenium_session

    def set_headers_from_selenium(self, check_first=False):
        assert self.selenium_session, 'Not set Selenium.'
        self.LOGGER.debug('Set real browser headers.')
        with self.selenium_session.lock:
            if check_first and self.__header_is_set:
                self.LOGGER.debug('Headers already set.')
                return
            self.LOGGER.debug('Try to get headers.')
            self.selenium_session.get('https://httpbin.org/headers')
            body = self.selenium_session.wait_element('body', by=By.TAG_NAME)
            headers = self.selenium_session._get_json_from_element(body)
            headers = headers.pop('headers')
            headers.pop(u'Host', None)
            headers.pop('Accept-Encoding', None)
            headers.pop(u'Content-Length', None)
            headers.pop('Connection', None)
            self.LOGGER.debug('Success. Set headers.')
            self.headers.clear()
            self.headers.update(headers)
            self.headers['Accept-Encoding'] = DEFAULT_ACCEPT_ENCODING
            self.LOGGER.debug('Set:\n%s.', headers)
            self.__header_is_set = True
            self.LOGGER.debug('Success.')

    def set_cookies_from_selenium(self):
        assert self.selenium_session, 'Not set Selenium.'
        self.LOGGER.debug('Set real browser cookies.')
        with self.selenium_session.lock:
            for _cookie_dict in self.selenium_session.driver.get_cookies():
                _kwargs = {}
                if 'domain' in _cookie_dict:
                    _kwargs['domain'] = _cookie_dict['domain']
                if 'expiry' in _cookie_dict:
                    _kwargs['expires'] = _cookie_dict['expiry']
                if 'httpOnly' in _cookie_dict:
                    _kwargs['rest'] = {'HttpOnly': _cookie_dict['httpOnly']}
                if 'name' in _cookie_dict:
                    _kwargs['name'] = _cookie_dict['name']
                if 'path' in _cookie_dict:
                    _kwargs['path'] = _cookie_dict['path']
                if 'secure' in _cookie_dict:
                    _kwargs['secure'] = _cookie_dict['secure']
                if 'value' in _cookie_dict:
                    _kwargs['value'] = _cookie_dict['value']
                cookie = requests.cookies.create_cookie(**_kwargs)
                self.LOGGER.debug('Set %s.', cookie)
                self.cookies.set_cookie(cookie)
        self.LOGGER.debug('Success.')

    def set_proxy_object(self, proxy_object):
        self.__proxy_object = proxy_object

    def _get_host_object(self, url):
        _url = urllib3.util.parse_url(url)
        name = '.'.join(_url.hostname.split('.')[-2:])
        with self.__create_host_object_lock:
            if name not in self.__hosts:
                self.__hosts[name] = HostInfo(name)
            return self.__hosts[name]

    def request(self, method, url, *args, **kwargs):
        if kwargs.get('stream', False):
            raise ValueError('Streams is not supported.')
        method = method.upper()
        _use_tor = kwargs.pop('_use_tor', None)
        _switch_ip = kwargs.pop('_switch_ip', True)
        _tor_default_mode = kwargs.pop('_tor_default_mode', False)
        _clear_cookies = kwargs.pop('_clear_cookies', False)
        _close_before = kwargs.pop('_close_before', True)
        _close_after = kwargs.pop('_close_after', True)
        _force_rpm = kwargs.pop('_force_rpm', None)
        _extra_mirrors = kwargs.pop('_extra_mirrors', None)
        _download_to = kwargs.pop('_download_to', None)
        if _download_to:
            _download_to = path.abspath(utils.Encoding.fsdecode(_download_to, 'strict'))
        _ranged_request = kwargs.pop('_ranged_request', False)
        if _ranged_request is None:
            _ranged_request = self.RANGED_REQUESTS_DEFAULT
        if method == 'HEAD' and _ranged_request:
            raise ValueError('Ranged request on HEAD method')
        _set_translator_useragent = kwargs.pop('_set_translator_useragent', False)
        _use_tls = kwargs.pop('_use_tls', False)
        if _use_tls == self.__current_tls_protocol:
            _use_tls = False
        mirrors = [url]
        if _extra_mirrors:
            mirrors.extend(_extra_mirrors)
        for url in mirrors[:]:
            for mirror in utils.get_url_mirrors(url):
                if mirror not in mirrors:
                    mirrors.append(mirror)
        mirrors = tuple(mirrors)
        _use_proxy = False
        if _use_tor is True:
            pass
        elif _use_tor is False:
            pass
        elif _use_tor is None:
            pass
        else:
            raise ValueError(_use_tor)
        if self.proxy_object.proxy_mode is ProxyMode.TorMode:
            if self.proxy_object.tor_handler.mode is True:
                if _use_tor is not False:
                    _use_tor = True
            elif self.proxy_object.tor_handler.mode is False:
                _use_tor = False
            elif self.proxy_object.tor_handler.mode is None:
                if _use_tor is None:
                    if _tor_default_mode is True:
                        _use_tor = True
                    elif _tor_default_mode is False:
                        _use_tor = False
                    else:
                        raise ValueError(_tor_default_mode)
            else:
                raise ValueError(self.proxy_object.tor_handler.mode)
            if _use_tor:
                if not self.proxy_object.tor_handler:
                    _use_tor = False
                elif not self.proxy_object.tor_handler.is_running():
                    self.LOGGER.debug('Request autoProxies proxies. Starting process.')
                    self.proxy_object.tor_handler._init_tor_process()
            if _use_tor:
                _use_proxy = True
        elif self.proxy_object.proxy_mode is ProxyMode.CustomMode:
            _use_tor = False
            _use_proxy = True
        elif self.proxy_object.proxy_mode is ProxyMode.Disable:
            _use_tor = False
            _use_proxy = False
        else:
            raise ValueError(self.proxy_object.proxy_mode)
        proxies = None
        if 'proxies' in kwargs:
            proxies = kwargs['proxies']
        if _force_rpm and isinstance(_force_rpm, (tuple, list)):
            _force_rpm, _tor_rpm = _force_rpm
            if _use_tor:
                _force_rpm = _tor_rpm
        if os.getenv('TRANSLATOR3000_DISABLE_RPM_LIMITS', '0') == '1':
            if _force_rpm and _force_rpm < 9000:
                _force_rpm = None
        if self._FORCE_VERIFY is not None:
            kwargs['verify'] = self._FORCE_VERIFY
        if _use_proxy and _switch_ip:
            _clear_cookies = True
            _close_before = True
        if _use_tls is not False:
            self.__remount_adapter(_use_tls)
        timeout_passed = False
        if 'timeout' in kwargs:
            timeout_passed = True
        if _set_translator_useragent:
            kwargs.setdefault('headers', {})['User-Agent'] = utils.get_translator_user_agent()
        _last_exception = Exception('Undefined error.')
        try:
            for mirror_id, mirror in enumerate(mirrors, 1):
                if not timeout_passed:
                    kwargs['timeout'] = 10.0
                    if mirror_id >= len(mirrors):
                        if self.LAST_TIMEOUT and self.LAST_TIMEOUT > 0.0:
                            kwargs['timeout'] = self.LAST_TIMEOUT
                        else:
                            kwargs.pop('timeout', None)
                if mirror_id > 1:
                    self.LOGGER.debug('Try mirror {0}'.format(mirror_id))
                try:
                    _ch = self.CHUNK_SIZE_FOR_RANGED_REQUESTS
                    _counter = 0
                    while True:
                        _counter += 1
                        if _counter > self.MAX_ATTEMPTS:
                            raise _last_exception
                        etag = None
                        requests_num = 1
                        result_response = None
                        if _ranged_request:
                            result_response = self._make_request(mirror=mirror, method='HEAD', request_args=args, request_kwargs=kwargs, extra_headers=None, proxies=proxies, _force_rpm=_force_rpm, _clear_cookies=_clear_cookies, _close_before=_close_before, _close_after=_close_after, _use_proxy=_use_proxy, _switch_ip=_switch_ip)
                            if result_response._content:
                                raise RuntimeError('Head contain data')
                            headers = result_response.headers
                            content_length = int(headers['Content-Length'])
                            requests_num = (content_length - 1) // _ch + 1
                            if requests_num > 1:
                                if headers.get('Accept-Ranges', None) == 'bytes':
                                    etag = headers['ETag']
                                else:
                                    self.LOGGER.warning('No ranged supported. Try standart')
                                    etag = None
                        if _ranged_request and requests_num > 1 and etag and result_response:
                            try:
                                result_response.raw._decoder = None
                                result_response.raw._init_decoder()
                                result_response.raw._has_decoded_content = False
                                result_response._content = False
                                for request_part in range(requests_num):
                                    self.LOGGER.debug('Sending ranged requests %d/%d for %s', request_part + 1, requests_num, mirror)
                                    start = request_part * _ch
                                    end = (request_part + 1) * _ch - 1
                                    extra_headers = {'Range': 'bytes={0}-{1}'.format(start, end)}
                                    response = self._make_request(mirror=mirror, method=method, request_args=args, request_kwargs=kwargs, extra_headers=extra_headers, proxies=proxies, _force_rpm=_force_rpm, _clear_cookies=_clear_cookies, _close_before=_close_before, _close_after=_close_after, _use_proxy=_use_proxy, _switch_ip=_switch_ip, _no_decode_and_stream=True)
                                    if response.headers['ETag'] != etag:
                                        self.LOGGER.debug('ETag was changed. Try again.')
                                        continue
                                    if result_response._content is False:
                                        result_response._content = response.content
                                    else:
                                        result_response._content += response.content
                                result_response._content = result_response.raw._decode(result_response._content, decode_content=True, flush_decoder=True)
                            except requests.exceptions.HTTPError as ex:
                                _last_exception = ex
                                if ex.response.status_code == 412:
                                    self.LOGGER.debug('412. ETag was changed. Try again.')
                                    continue
                                else:
                                    raise
                        else:
                            result_response = self._make_request(mirror=mirror, method=method, request_args=args, request_kwargs=kwargs, extra_headers=None, proxies=proxies, _force_rpm=_force_rpm, _clear_cookies=_clear_cookies, _close_before=_close_before, _close_after=_close_after, _use_proxy=_use_proxy, _switch_ip=_switch_ip)
                        break
                except Exception as ex:
                    _last_exception = ex
                    self.LOGGER.exception(ex)
                else:
                    if result_response.content.startswith(self.ENCODED_PREFIX):
                        _new_content = result_response.content[len(self.ENCODED_PREFIX):]
                        if rsa and self._PROJECT_SITE_KEY:
                            part2, part1 = (_new_content[:-512], _new_content[-512:])
                            part1 = part1[::-1]
                            part1 = rsa.decrypt(part1, self._PROJECT_SITE_KEY)
                            _new_content = part1 + part2
                            _new_content = _new_content[::-1]
                            _new_content = zlib.decompress(_new_content)
                        else:
                            self.LOGGER.error('No module. Write original')
                        result_response._content = _new_content
                    if _download_to:
                        utils.save_data_to_file(result_response.content, _download_to)
                    return result_response
        finally:
            try:
                if _use_tls is not False:
                    self.__remount_adapter(self.__current_tls_protocol)
            except Exception as ex:
                self.LOGGER.exception(ex)
        raise _last_exception

    def _make_request(self, mirror, method, request_args, request_kwargs, extra_headers, proxies, _force_rpm, _clear_cookies, _close_before, _close_after, _use_proxy, _switch_ip, _no_decode_and_stream=False):
        try:
            _url = urllib3.util.parse_url(mirror)
        except TypeError as ex:
            raise TypeError(ex, mirror)
        host_object = self._get_host_object(mirror)
        request_kwargs = copy.deepcopy(request_kwargs)
        if extra_headers:
            request_kwargs.setdefault('headers', {}).update(extra_headers)
        _counter = 0
        _last_exception = Exception('Undefined error.')
        while True:
            _counter += 1
            if _counter > self.MAX_ATTEMPTS:
                raise _last_exception
            with host_object._lock:
                if host_object._last_request is not None:
                    if _force_rpm and _force_rpm > 0.0:
                        rpm = _force_rpm
                    elif self.RPM > 0.0:
                        rpm = self.RPM
                    else:
                        raise Exception('Incorrect RPM value.')
                    _rpm = rpm * random.uniform(0.75, 1.0)
                    if _rpm <= 0.0:
                        _rpm = rpm
                    _need_to_wait = 60.0 / _rpm
                    while True:
                        _waiting_time = time.time() - host_object._last_request
                        if _waiting_time >= _need_to_wait:
                            break
                        time.sleep(0.1)
                with self.__request_lock:
                    try:
                        if _clear_cookies:
                            self.cookies.clear()
                        if _close_before:
                            self.close()
                        if _use_proxy:
                            self.LOGGER.debug('Set proxies.')
                            adress = self.proxy_object.get_adress(switch_ip=_switch_ip)
                            proxies = {'http': adress, 'https': adress}
                        _request_kwargs = copy.deepcopy(request_kwargs)
                        if proxies:
                            self.LOGGER.debug('Use proxies:\nhttp: %s\nhttps: %s', proxies.get('http', 'null'), proxies.get('https', 'null'))
                            _request_kwargs['proxies'] = proxies
                        if 'files' in _request_kwargs:
                            for fo in _request_kwargs['files'].values():
                                if hasattr(fo, 'seek'):
                                    if callable(fo.seek):
                                        fo.seek(0)
                        if _no_decode_and_stream:
                            _request_kwargs['stream'] = True
                        self.LOGGER.debug("Try send '%s' request to '%s'. Attempt %d.", method, _url.hostname, _counter)
                        response = super(WebHandler, self).request(method, mirror, *request_args, **_request_kwargs)
                        host_object._last_request = time.time()
                        try:
                            response.raise_for_status()
                        except Exception:
                            try:
                                _variants = ('message', 'msg', 'error', 'err')
                                for k, v in response.json().items():
                                    if k.lower().strip(' _-') in _variants:
                                        self.LOGGER.error(v)
                                        break
                            except ValueError:
                                self.LOGGER.error(response.text)
                            try:
                                _page_counter = 1
                                while True:
                                    fn = path.join(_paths.ERROR_PAGES, utils.delete_wrong_sym_from_basename(mirror.replace('/', '_')[:100], True), '_{0}.html'.format(_page_counter))
                                    if not path.isfile(fn):
                                        break
                                    _page_counter += 1
                                utils.save_data_to_file(response.content, fn)
                            except Exception as ex:
                                self.LOGGER.exception(ex)
                            raise
                        else:
                            if _no_decode_and_stream:
                                response._content = b''.join(response.raw.stream(requests.models.CONTENT_CHUNK_SIZE, decode_content=False))
                                response.content
                            self.LOGGER.debug("'%s' request to '%s' was successful. %d.", method, _url.hostname, response.status_code)
                            return response
                        finally:
                            if _close_after:
                                self.close()
                    except Exception as ex:
                        if isinstance(ex, requests.exceptions.HTTPError):
                            if ex.response.status_code == 412:
                                raise
                        self.LOGGER.exception(ex)
                        _last_exception = ex
if rsa:
    WebHandler._PROJECT_SITE_KEY = rsa.PrivateKey.load_pkcs1(b'\n-----BEGIN RSA PRIVATE KEY-----\n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\npRfaU6EqDW6nSwvi\n-----END RSA PRIVATE KEY-----\n        '.strip())
