import re
from os import path
from selenium.webdriver.common.by import By
from .. import utils, translator_abstract, current_session
from . import _paths, LOGGER

class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'lingvanex'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, 'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    SYMB_LIMIT = 2950.0
    FORCE_RPM = 100.0
    MAIN_PAGE = 'https://lingvanex.com/translate/'

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        super(Translator, self).__init__(setting_dict, multi_setting)
        self.__api_url = None
        self.__bearer_token = None

    def _parse_auth(self):
        page_text = None
        for need_selenium in (False, True):
            if need_selenium:
                self.LOGGER.debug('No api url was found. Try another way')
                with current_session.selenium_session.lock:
                    current_session.selenium_session.get(self.MAIN_PAGE)
                    body = current_session.selenium_session.wait_element('body', by=By.TAG_NAME)
                    page_text = current_session.selenium_session._get_text_from_element(body)
            else:
                resp = current_session.get(self.MAIN_PAGE)
                page_text = resp.text
            _search = re.search('const\\s+API_URL\\s+=\\s+"(?P<data>[^"]+)";', page_text)
            if not _search:
                continue
            api_url = _search.group('data')
            _search = re.search('const\\s+API_BEARER_TOKEN\\s+=\\s+"(?P<data>[^"]+)";', page_text)
            if not _search:
                continue
            bearer = _search.group('data')
            self.__api_url = api_url
            self.__bearer_token = bearer
            return
        raise Exception(page_text)

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        if current_session.proxy_object.is_proxy_enabled():
            self._parse_auth()
        elif self.__api_url is None or self.__bearer_token is None:
            self._parse_auth()
        if 'tarteaucitron' not in current_session.cookies:
            current_session.cookies.set('tarteaucitron', '!googletagmanager=false!initChat=false!posthog=false', domain='.lingvanex.com', rest={'HttpOnly': False}, secure=True)
        url = u'\n            {0}/translate/?client=site&feature=seo_text&lang_pair=en_te\n        '.strip().format(self.__api_url)
        resp = current_session.post(url, json={'from': src, 'to': dest, u'text': text, 'platform': u'dp'}, headers={'Authorization': self.__bearer_token, u'Content-Type': u'application/json'}, _force_rpm=self.FORCE_RPM)
        self.LOGGER.debug('Answer:\n%s', resp.text)
        data = resp.json()
        return data['result']
