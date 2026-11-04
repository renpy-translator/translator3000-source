import urllib3
from os import path
from .. import utils, translator_abstract, current_session
from . import _paths, LOGGER


class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'google'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    FORCE_RPM = 8.0
    TOR_RPM = 300.0
    HOSTNAME = u'translate.googleapis.com'
    SYMB_LIMIT = 3000
    TOR_MODE = True

    def get_base_url(self):
        return urllib3.util.Url(scheme=u'https', auth=None, host=self.HOSTNAME, port=None, path=u'/translate_a/single', query=None, fragment=None)

    def _string_handler_pre(self, s, dest=None, src=None):
        if dest and dest == self.get_lang_code('zh-TW', True):
            s = s.replace(u'"', u'')
            return u'|{0}|'.format(s.strip())
        return s

    def _string_handler_post(self, s, dest=None, src=None):
        if dest and dest == self.get_lang_code('zh-TW', True):
            return s.strip(u'| ')
        return s

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        params = {u'client': u'gtx', u'dt': u't', u'sl': src, u'tl': dest, u'q': text}
        url = self.get_base_url().url
        resp = current_session.get(url, params=params, _tor_default_mode=self.TOR_MODE, _force_rpm=(self.FORCE_RPM, self.TOR_RPM))
        self.LOGGER.debug('Answer:\n%s', resp.text)
        _json = resp.json()
        result = u''
        for translate_part in _json[0]:
            result += translate_part[0]
        return result

