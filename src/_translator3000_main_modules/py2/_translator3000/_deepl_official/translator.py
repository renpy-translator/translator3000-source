import re
import threading
from os import path
from .. import utils, translator_abstract, lang_codes, chrome_session
from . import _paths, LOGGER


class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'deepl_web'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    SYMB_LIMIT = 10000.0
    FORCE_RPM = 9999.0
    DEST_VARIANTS = {'en': {'default': 'US', 'American': 'US', 'Britain': 'GB'}, 'pt': {'default': 'BR', 'Brazil': 'BR', 'Portugal': 'PT'}, 'zh': {'default': 'Hans', 'Simplified': 'Hans', 'Traditional': 'Hant'}}
    _NAMECODE_LOCK = threading.Lock()
    _NAMECODE_CACHE = {}
    MAIN_API_URL = u'https://api.deepl.com'
    FREE_API_URL = u'https://api-free.deepl.com'

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        super(Translator, self).__init__(setting_dict, multi_setting)
        self._endpoint = self.MAIN_API_URL
        self._auth_key = None
        if self._setting_dict:
            _data = self._setting_dict[u'apiData'][u'deepL']
            if _data[u'endpoint']:
                self._endpoint = _data[u'endpoint']
            if _data[u'authKey']:
                self._auth_key = _data[u'authKey']

    def get_lang_name_and_code(self, data, dest_direction=True):
        with self._NAMECODE_LOCK:
            _key = data, dest_direction
            if _key not in self._NAMECODE_CACHE:
                self._NAMECODE_CACHE[_key] = self._get_lang_name_and_code(data, dest_direction)
            return self._NAMECODE_CACHE[_key]

    def _get_lang_name_and_code(self, data, dest_direction=True):
        pure_code = lang_codes.get_lang_code(data, self.TRANSLATOR_GROUP)
        if pure_code == 'zh-Hant':
            data = pure_code
            pure_code = 'zh'
        pure_name = lang_codes.get_lang_name(data)
        if not dest_direction:
            return (pure_name, pure_code)
        code_addition = None
        name_addition = None
        if pure_code in self.DEST_VARIANTS:
            variants = self.DEST_VARIANTS[pure_code]
            check_data = data.strip().split('-')[-1]
            for name, variant in variants.items():
                if name == 'default':
                    continue
                if check_data.lower() == variant.lower():
                    code_addition = variant
                    name_addition = name
                    break
            else:
                code_addition = variants['default']
        result_code = pure_code
        if code_addition:
            result_code = '-'.join((pure_code, code_addition))
        result_name = pure_name
        if name_addition and pure_code != 'zh':
            result_name = '{0} ({1})'.format(result_name, name_addition)
        return (result_name, result_code)

    def get_lang_code(self, data, dest_direction=True):
        name, code = self.get_lang_name_and_code(data, dest_direction)
        return code

    def get_lang_name(self, data, dest_direction=True):
        name, code = self.get_lang_name_and_code(data, dest_direction)
        return name

    def get_all_lang_codes(self, dest_direction=True):
        result = set()
        codes = lang_codes.get_lang_codes_for_translator(self.TRANSLATOR_GROUP)
        for code in codes:
            if len(code.split(u'-')) == 2:
                result.add(code)
            else:
                additions = set()
                if code in self.DEST_VARIANTS:
                    additions.update(self.DEST_VARIANTS[code].values())
                else:
                    additions.add(code)
                for addition in additions:
                    result.add('-'.join((code.lower(), addition.upper())))
        return frozenset(map(lambda code: self.get_lang_code(code, dest_direction), result))

    def _web_translate(self, text, dest, src):
        if not self._auth_key:
            raise RuntimeError('No authentication key has been passed.')
        if not self._endpoint:
            raise RuntimeError('No endpoint was passed or incorrectly passed.')
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        texts = list(re.split(u'[\\r\\n]+', text, flags=re.UNICODE))
        url = utils.urljoin(self._endpoint, u'v2/translate')
        result = []
        STEP = 50
        OFFSET = 0
        while True:
            _texts = texts[STEP * OFFSET:STEP * (OFFSET + 1)]
            if not _texts:
                return u'\n'.join(map(lambda a: a[u'text'], result))
            resp = chrome_session.post(url, json={u'text': _texts, u'source_lang': src, u'target_lang': dest}, headers={u'Authorization': u'DeepL-Auth-Key {0}'.format(self._auth_key), u'Content-Type': u'application/json'}, _force_rpm=self.FORCE_RPM)
            self.LOGGER.debug('Answer:\n%s', resp.text)
            result.extend(resp.json()[u'translations'])
            OFFSET += 1

