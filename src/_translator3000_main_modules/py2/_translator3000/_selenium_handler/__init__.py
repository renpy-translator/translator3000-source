import re
import json
import time
import threading
from datetime import datetime
from os import path
from . import driver_finder
from .. import utils, pseudonyms
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.common import exceptions
UPDATED_SELENIUM = False
try:
    _wd_version = tuple(map(int, webdriver.__version__.split('.')))
except Exception:
    pass
else:
    if _wd_version >= (4, 24, 0):
        UPDATED_SELENIUM = True
__author__ = 'Vladya'


class IncorrectVersion(Exception):
    __author__ = 'Vladya'
    MSG_PATTERN = re.compile('browser\\s+version\\s+is\\s+(?P<version>\\d+\\.\\d+\\.\\d+\\.\\d+)', flags=re.IGNORECASE)

    def __init__(self, need_version):
        super(IncorrectVersion, self).__init__(need_version)
        self.__need_version = need_version

    @property
    def need_version(self):
        return self.__need_version

    @classmethod
    def get_exc(cls, exc_string):
        version_match = cls.MSG_PATTERN.search(exc_string)
        if not version_match:
            return None
        version = tuple(map(int, version_match.group('version').split('.')))
        return cls(need_version=version)


class ChromeSession(object):
    __author__ = 'Vladya'
    LAST_JS_REQUEST = None

    def __init__(self, logger_object, default_session, _mode='default', path_to_binary=None, user_agent=None, run_immediately=True, use_proxy=False):
        self.LOGGER = logger_object.getChild('ChromeSession')
        self.__default_session = default_session
        self.mode = _mode
        self.__quit_lock = threading.Lock()
        self.__not_create = False
        self.__driver_fn = None
        self.__finder = driver_finder.ChromeFinder(session=self.__default_session, logger=self.LOGGER)
        self.__url_get_counter = {}
        self.__lock = threading.RLock()
        self.__file_lock = threading.RLock()
        self.__binary_location = path_to_binary
        self.__use_proxy = use_proxy
        self.__user_agent = user_agent
        if run_immediately:
            self._set_and_run_browser()

    @property
    def lock(self):
        return self.__lock

    @property
    def driver(self):
        return self.__driver

    @property
    def mode(self):
        return self.__work_mode

    @mode.setter
    def mode(self, new_mode):
        new_mode = new_mode.strip().lower()
        if new_mode not in ('hide', 'minimized', 'default'):
            raise ValueError("Incorrect 'work_mode' - {0}.".format(new_mode))
        self.__work_mode = new_mode

    @property
    def driver_executable(self):
        with self.__file_lock:
            if not (self.__driver_fn and path.isfile(self.__driver_fn)):
                self.set_driver_fn()
            return self.__driver_fn

    def execute_js(self, script, *args):
        with self.lock:
            return self.driver.execute_script(script, *args)

    def execute_async_js(self, script, *args):
        with self.lock:
            return self.driver.execute_async_script(script, *args)

    def request_js(self, method, url, body=None, rpm=None):
        with self.lock:
            if rpm and self.LAST_JS_REQUEST is not None:
                wait_time = 60.0 / rpm
                while True:
                    elapsed = time.time() - self.LAST_JS_REQUEST
                    if elapsed >= wait_time:
                        break
                    time.sleep(0.05)
            script = 'let req = new XMLHttpRequest();req.open("{method}", "{url}", async=false);req.send({body});return req.response;'.format(method=method.upper(), url=url, body=body or u'')
            result = self.execute_js(script)
            self.LAST_JS_REQUEST = time.time()
            return result

    def set_driver_fn(self, need_version=None):
        with self.__file_lock:
            self.__driver_fn = self.__finder.get_executable(need_version=need_version)
            self.LOGGER.debug('Selenium executable is "%s".', utils.Encoding.utf8encode(self.__driver_fn))

    def __del__(self):
        with self.__quit_lock:
            self.__not_create = True
            try:
                self.quit()
            except Exception as ex:
                self.LOGGER.exception(ex)

    def print_driver_log(self):
        try:
            _log = self.driver.get_log('driver')
        except Exception:
            return
        else:
            if _log and isinstance(_log, list):
                for i, log_elem in enumerate(_log, 1):
                    _log_time = log_elem.get('timestamp', None)
                    if isinstance(_log_time, (int, float)):
                        _log_time = datetime.fromtimestamp(float(_log_time) / 1000.0)
                    else:
                        _log_time = u'Unrecognized time'
                    self.LOGGER.debug('''Driver log %d:
%s: %s
%s''', i, log_elem[u'level'], _log_time, log_elem[u'message'])

    def is_running(self):
        try:
            self.driver
        except AttributeError:
            return False
        self.print_driver_log()
        if not self.driver.service.process:
            return False
        if self.driver.service.process.poll() is not None:
            return False
        msg = u'Unable to evaluate script'.strip().lower()
        _log = self.driver.get_log('driver')
        if _log and isinstance(_log, list):
            for _log_el in _log[::-1]:
                if _log_el[u'message'].strip().lower().startswith(msg):
                    return False
        return True

    def _set_and_run_browser(self, _new_mode=None, path_to_binary=None, use_proxy=None):
        try:
            result = self.__set_and_run_browser(_new_mode, path_to_binary, use_proxy)
        except IncorrectVersion as ex:
            self.LOGGER.debug('Incorrect browser version has been detected. Start driver reinstallation.')
            self.set_driver_fn(ex.need_version)
            return self.__set_and_run_browser(_new_mode, path_to_binary, use_proxy)
        else:
            return result

    def __set_and_run_browser(self, _new_mode=None, path_to_binary=None, use_proxy=None):
        with self.__quit_lock:
            if self.__not_create:
                return
            if use_proxy is None:
                use_proxy = self.__use_proxy
            else:
                self.__use_proxy = use_proxy
            if _new_mode is not None:
                self.mode = _new_mode
            if path_to_binary is not None:
                self.__binary_location = path_to_binary
            options = webdriver.ChromeOptions()
            if self.__binary_location:
                _p = path.abspath(self.__binary_location)
                assert path.isfile(_p), 'No path to chrome was found'
                options.binary_location = _p
            options.add_argument('--start-maximized')
            options.add_argument('--incognito')
            options.add_argument('--disable-extensions')
            options.add_argument('--no-default-browser-check')
            options.add_argument('--no-first-run')
            options.add_argument('--no-sandbox')
            if self.__user_agent:
                options.add_argument('--user-agent={0}'.format(self.__user_agent))
            options.add_argument('--disable-blink-features={0}'.format('AutomationControlled'))
            options.add_experimental_option('excludeSwitches', ('enable-automation',))
            options.add_experimental_option('useAutomationExtension', False)
            if self.mode == 'hide':
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--window-position=-2400,-2400')
                options.add_argument('--headless=new')
            if use_proxy:
                adress = self.__default_session.proxy_object.get_adress(switch_ip='chrome')
                if adress is not None:
                    options.add_argument('--proxy-server={0}'.format(adress))
                    self.LOGGER.debug('Use chrome proxies: %s', adress)
            try:
                if UPDATED_SELENIUM:
                    self.__driver = webdriver.Chrome(options=options)
                else:
                    self.__driver = webdriver.Chrome(self.driver_executable, chrome_options=options)
            except exceptions.SessionNotCreatedException as ex:
                exc = IncorrectVersion.get_exc(ex.msg)
                if exc is not None:
                    raise exc
                raise ex
            time.sleep(0.5)
        if self.mode == 'minimized':
            self.driver.minimize_window()

    def reload_if_need(self):
        if not self.is_running():
            self.reload()
            return True
        return False

    def reload(self, _new_mode=None, path_to_binary=None, use_proxy=None):
        with self.lock:
            self.quit()
            _exception = Exception('Undefined error.')
            for _ in pseudonyms.xrange(10):
                try:
                    self._set_and_run_browser(_new_mode, path_to_binary, use_proxy)
                except Exception as ex:
                    self.LOGGER.exception(ex)
                    _exception = ex
                else:
                    return
            raise _exception

    def quit(self):
        self.__url_get_counter.clear()
        try:
            self.driver
        except AttributeError:
            return
        self.print_driver_log()
        _exception = Exception('Undefined error.')
        for _ in pseudonyms.xrange(10):
            try:
                self.driver.quit()
            except Exception as ex:
                self.LOGGER.exception(ex)
                _exception = ex
                continue
            else:
                return
        raise _exception

    def get_if(self, url):
        url = utils.normalize_url(url)
        self.reload_if_need()
        if self.driver.current_url != url:
            self.get(url)

    def get(self, url):
        url = utils.normalize_url(url)
        self.reload_if_need()
        self.driver.get(url)
        self.__url_get_counter.setdefault(url, 0)
        self.__url_get_counter[url] += 1

    def url_get_count(self, url):
        url = utils.normalize_url(url)
        return self.__url_get_counter.get(url, 0)

    @staticmethod
    def _get_text_from_element(elem, _need_strip=True):
        if not hasattr(elem, 'get_attribute'):
            return u''
        data = elem.get_attribute('textContent')
        if not data:
            return u''
        data = utils.Encoding.utf8decode(data, 'strict')
        if _need_strip:
            data = data.strip()
        return data

    @classmethod
    def _get_json_from_element(cls, elem):
        text_view = cls._get_text_from_element(elem)
        return json.loads(text_view)

    def find_element(self, data, by=None, _log=True, **kwargs):
        if by is None:
            by = By.XPATH
        if not isinstance(data, (list, tuple)):
            data = data,
        _exception = Exception('Undefined error.')
        for d in map(lambda _d: utils.Encoding.utf8decode(_d, 'strict'), data):
            try:
                element = self.driver.find_element(by, d)
            except Exception as ex:
                _exception = ex
            else:
                if _log:
                    if _log is True:
                        self.LOGGER.debug("Find element '%s' by %s.", d, by)
                    else:
                        self.LOGGER.debug("Find element '%s' by %s.", _log, by)
                return element
        if 'default' in kwargs:
            return kwargs['default']
        raise _exception

    def wait_element(self, data, timeout=30.0, by=None, move_to=False, _log=True):
        if by is None:
            by = By.XPATH
        if not isinstance(data, (list, tuple)):
            data = data,
        data = tuple(map(lambda d: utils.Encoding.utf8decode(d, 'strict'), data))
        error_message = u'''
            An error occurred while waiting for elements "{0!r}" by {1}.
        '''.strip().format(data, by)
        waiter = WebDriverWait(self.driver, timeout)
        element = waiter.until(lambda drv: self.find_element(data, by=by, _log=_log), error_message)
        if move_to:
            self.move_to_element(element, _log)
        return element

    def move_to_element(self, element, _log=None):
        if not isinstance(_log, pseudonyms.basestring):
            _log = element.tag_name
        self.LOGGER.debug("Trying scroll to element '%s'.", _log)
        try:
            action = webdriver.ActionChains(self.driver)
            if hasattr(action, 'scroll_to_element'):
                action = action.scroll_to_element(element)
            action = action.move_to_element(element)
            action.perform()
        except Exception as ex:
            self.LOGGER.exception(ex)
        else:
            self.LOGGER.debug('Successfull.')

