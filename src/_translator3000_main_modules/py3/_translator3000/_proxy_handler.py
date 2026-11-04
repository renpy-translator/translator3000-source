import threading
from . import utils, _tor_handler

class ProxyMode(object):

    class CustomMode(object):
        pass

    class TorMode(object):
        pass

    class Disable(object):
        pass

    @classmethod
    def _get_mode(cls, _txt):
        txt = _txt.strip().lower()
        txt = txt.replace('mode', '')
        if txt == 'custom':
            return cls.CustomMode
        elif txt == 'tor':
            return cls.TorMode
        elif txt == 'disable':
            return cls.Disable
        raise ValueError(_txt)

class ProxyHandler(object):
    __author__ = 'Vladya'
    LOGGER = None
    single_instance = None
    is_initialized = False
    LOCK = threading.RLock()

    def __new__(cls, session=None, logger=None):
        if cls.single_instance is None:
            cls.single_instance = super(ProxyHandler, cls).__new__(cls)
        return cls.single_instance

    def __init__(self, session=None, logger=None):
        if self.is_initialized:
            return
        self.__session = session
        self.LOGGER = logger.getChild('ProxyHandler')
        self.is_initialized = True
        self.__mode = ProxyMode.Disable
        self.__tor_handler = _tor_handler.TorHandler(self.__session, self.LOGGER)
        self.__custom_proxies = ()
        self.__counter = None

    def __del__(self):
        self.__tor_handler.__del__()

    def is_proxy_enabled(self):
        if self.proxy_mode is ProxyMode.Disable:
            return False
        return True

    def set_custom_proxies(self, data):
        with self.LOCK:
            self.__custom_proxies = tuple(data)

    @property
    def proxy_mode(self):
        with self.LOCK:
            return self.__mode

    @proxy_mode.setter
    def proxy_mode(self, new_mode):
        with self.LOCK:
            new_mode = ProxyMode._get_mode(new_mode)
            self.__mode = new_mode

    @property
    def tor_handler(self):
        return self.__tor_handler

    def get_adress(self, switch_ip=True):
        with self.LOCK:
            if self.proxy_mode is ProxyMode.TorMode:
                return self.tor_handler.get_adress(switch_ip=switch_ip)
            elif self.proxy_mode is ProxyMode.Disable:
                return None
            if not self.__custom_proxies:
                return None
            _chrome_proxy = self.__custom_proxies[0]
            if switch_ip == 'chrome':
                return _chrome_proxy
            if len(self.__custom_proxies) > 1:
                other_proxies = self.__custom_proxies[1:]
            else:
                other_proxies = self.__custom_proxies[:]
            if self.__counter is None:
                self.__counter = 0
            elif switch_ip:
                self.__counter += 1
                self.__counter %= len(other_proxies)
            return other_proxies[self.__counter]
