import urllib3
from os import path
from .. import utils, translator_abstract, current_session
from . import _paths, LOGGER

class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'google'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, 'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, 'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    HOSTNAME = 'clients5.google.com'
    FORCE_FIX_SENTENCES = True
    SYMB_LIMIT = 3000

    def get_base_url(self):
        return urllib3.util.Url(scheme='https', auth=None, host=self.HOSTNAME, port=None, path='/translate_a/t', query=None, fragment=None)

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        params = {'client': 'dict-chrome-ex', 'sl': src, 'tl': dest, 'q': text}
        url = self.get_base_url().url
        resp = current_session.get(url, params=params)
        self.LOGGER.debug('Answer:\n%s', resp.text)
        _json = resp.json()
        if isinstance(_json, dict):
            result = u''
            for answer in _json['sentences']:
                if 'trans' in answer:
                    result += answer['trans']
        else:
            result = u''.join(_json)
        return result
