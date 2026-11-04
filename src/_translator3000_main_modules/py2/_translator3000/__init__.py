import logging
from . import _paths, utils, web_handler, _selenium_handler, _logging, _fonts_download, _proxy_handler
__author__ = 'Vladya'
__version__ = '1.45.11'
RENPY_WITH_REQUESTS = 7, 4, 0
utils.remove_dir(_paths.TEMP_FOLDER, True)
utils.remove_dir(_paths.DEBUG_FOLDER, True)
LOGGER = _logging.Logger.getLogger('translator3000')
LOGGER.setLevel(logging.DEBUG)
chrome_session = web_handler.WebHandler(logger_object=LOGGER, unique_id='Chrome', _headers=web_handler.Headers.GOOGLE_CHROME)
chrome_session.RPM = 100.0
yandex_session = web_handler.WebHandler(logger_object=LOGGER, unique_id='Yandex', _headers=web_handler.Headers.YANDEX_BROWSER)
yandex_session.RPM = 100.0
edge_session = web_handler.WebHandler(logger_object=LOGGER, unique_id='Edge', _headers=web_handler.Headers.EDGE)
edge_session.RPM = 100.0
current_session = chrome_session
_all_sessions = chrome_session, yandex_session, edge_session
try:
    selenium_session = _selenium_handler.ChromeSession(logger_object=LOGGER, default_session=chrome_session, user_agent=web_handler.Headers.GOOGLE_CHROME['User-Agent'], run_immediately=False)
except Exception as ex:
    LOGGER.exception(ex)
    selenium_session = None
proxy_handler = _proxy_handler.ProxyHandler(chrome_session, LOGGER)
for _session in _all_sessions:
    if selenium_session:
        _session.set_selenium_session(selenium_session)
    _session.set_proxy_object(proxy_handler)
font_storage = _fonts_download.FontStorage(chrome_session, LOGGER)

