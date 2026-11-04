import time
import ssl
import re
from os import path
from .. import utils, translator_abstract, edge_session, pseudonyms
from . import _paths, LOGGER


class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'reverso'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    SYMB_LIMIT = 2000
    FORCE_RPM = 80.0
    TOR_RPM = 300.0
    MAIN_URL = 'https://www.reverso.net'
    URL = 'https://api.reverso.net/translate/v1/translation'

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        super(Translator, self).__init__(setting_dict, multi_setting)
        self.__cookie_is_set = False

    def _set_cookie(self):
        with edge_session.selenium_session.lock:
            if not self.__cookie_is_set:
                edge_session.selenium_session.get(self.MAIN_URL)
                counter = 0
                while True:
                    counter += 1
                    area = edge_session.selenium_session.wait_element(('/html/body/app-root/app-translation-home-page/main/section/app-translation-box/div/div[1]/app-textarea/textarea', '/html/body/app-root/app-translation-page/main/section/app-translation-box/div/div[1]/app-textarea/textarea', '/html/body/app-root/app-translation/div/app-translation-box/div[1]/div[1]/div[2]/div[1]/div[1]/div/div[1]/textarea'))
                    try:
                        area.click()
                        area.send_keys('Test')
                    except Exception:
                        if counter >= 10:
                            raise
                        time.sleep(float(counter))
                    else:
                        break
                time.sleep(5.0)
                edge_session.set_cookies_from_selenium()
                self.__cookie_is_set = True

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        text = re.sub(u'\\.{3,}', pseudonyms.unichr(8230), text, flags=re.UNICODE)
        request_data = {u'format': u'text', u'from': src, u'to': dest, u'input': text, u'options': {u'sentenceSplitter': True, u'origin': u'translation.web', u'contextResults': False, u'languageDetection': False}}
        self._set_cookie()
        _kwargs = {'json': request_data, '_force_rpm': (self.FORCE_RPM, self.TOR_RPM)}
        if hasattr(ssl, 'OP_NO_TLSv1_3'):
            _kwargs['_use_tls'] = 3,
        resp = edge_session.post(self.URL, **_kwargs)
        self.LOGGER.debug('Answer:\n%s', resp.text)
        _json = resp.json()
        return u''.join(_json[u'translation'])

