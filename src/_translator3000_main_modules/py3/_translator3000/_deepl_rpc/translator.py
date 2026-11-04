import re
import time
import random
import threading
from os import path
from .. import utils, translator_abstract, lang_codes, edge_session, _proxy_handler
from . import _paths, LOGGER
ProxyMode = _proxy_handler.ProxyMode

class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'deepl_web'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, 'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    SYMB_LIMIT = 1425
    FORCE_RPM = 8.0
    TOR_RPM = 300.0
    DEST_VARIANTS = {'en': {'default': 'US', 'American': 'US', 'Britain': 'GB'}, 'pt': {'default': 'BR', 'Brazil': 'BR', 'Portugal': 'PT'}, 'zh': {'default': 'Hans', 'Simplified': 'Hans', 'Traditional': 'Hant'}}
    _NAMECODE_LOCK = threading.Lock()
    _NAMECODE_CACHE = {}
    URL = u'https://www2.deepl.com/jsonrpc?method={method}'
    SPLIT_METHOD = u'LMT_split_text'
    TRANSLATE_METHOD = u'LMT_handle_jobs'

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        super(Translator, self).__init__(setting_dict, multi_setting)
        self.__last_id = None
        self.__last_update = None
        self.__id_lock = threading.Lock()

    def get_lang_name_and_code(self, data, dest_direction=True):
        with self._NAMECODE_LOCK:
            _key = (data, dest_direction)
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

    def _send_post(self, method, params, switch_ip, _use_force_rpm=True):
        _kwargs = {'json': params, 'headers': {'Connection': 'keep-alive', 'DNT': '1', 'Origin': 'https://www.deepl.com', 'Sec-Fetch-Site': 'same-site', 'Sec-Fetch-Mode': 'cors', 'Sec-Fetch-Dest': 'empty', 'Referer': 'https://www.deepl.com/', 'Sec-GPC': '1'}, '_switch_ip': switch_ip, '_use_tls': (2,)}
        if _use_force_rpm:
            _kwargs['_force_rpm'] = (self.FORCE_RPM, self.TOR_RPM)
        return edge_session.post(self.URL.format(method=method), **_kwargs)

    def get_id(self, can_update=True):
        with self.__id_lock:
            if can_update and self.__last_update is not None:
                _elapsed = time.time() - self.__last_update
                if _elapsed >= 120.0:
                    self.__last_id = None
                    self.__last_update = None
            if self.__last_id is None:
                self.__last_id = random.randint(1111, 9999) * 10000
            self.__last_id += 1
            self.__last_update = time.time()
            return self.__last_id

    @staticmethod
    def generate_time_token(_sentences):
        n = 1
        for part in _sentences:
            for _sent in part['sentences']:
                n += _sent['text'].count('i')
        r = int(time.time() * 1000.0)
        return r - r % n + n

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        _weights = {}
        for _code in self.get_all_lang_codes(False):
            if _code == src:
                value = random.uniform(15.0, 20.0)
            elif self.get_lang_code(_code, True) == dest:
                value = random.uniform(5.0, 10.0)
            else:
                value = random.uniform(0.02, 0.5)
            _weights.setdefault(_code.upper(), value)
        params = {'jsonrpc': '2.0', u'method': self.SPLIT_METHOD, 'params': {u'commonJobParams': {u'mode': u'translate', u'textType': 'plaintext'}, 'lang': {'lang_user_selected': src.upper(), u'preference': {'default': u'default', u'weight': _weights}}, 'texts': list(re.split(u'[\\r\\n]+', text, flags=re.UNICODE))}, 'id': self.get_id(can_update=True)}
        with edge_session.proxy_object.LOCK:
            resp = self._send_post(self.SPLIT_METHOD, params, switch_ip=True, _use_force_rpm=True)
            self.LOGGER.debug('Answer 1:\n%s', resp.text)
            answer = resp.json()
            _sentences = []
            for counter, _txt in enumerate(answer['result']['texts'], 1):
                _result = u''
                for chunk in _txt['chunks']:
                    for sent in chunk[u'sentences']:
                        _result += sent['prefix']
                        _result += sent['text']
                _sentence = {u'kind': 'default', 'preferred_num_beams': 1, u'raw_en_context_before': [], 'raw_en_context_after': [], u'sentences': [{u'prefix': u'', u'text': _result, 'id': counter}]}
                _sentences.append(_sentence)
            params = {u'jsonrpc': answer['jsonrpc'], 'method': self.TRANSLATE_METHOD, 'params': {'commonJobParams': {'quality': u'fast', u'mode': u'translate', 'browserType': 1, 'textType': 'plaintext'}, u'lang': {u'target_lang': dest.upper(), 'preference': {u'default': u'default', 'weight': {}}, 'source_lang_computed': src.upper()}, u'jobs': _sentences, u'priority': -1, u'timestamp': self.generate_time_token(_sentences)}, u'id': self.get_id(can_update=False)}
            resp = self._send_post(self.TRANSLATE_METHOD, params, switch_ip=False, _use_force_rpm=True)
            self.LOGGER.debug('Answer 2:\n%s', resp.text)
            answer = resp.json()
            result_parts = []
            for translation_part in answer['result']['translations']:
                _result = []
                for beam in translation_part['beams']:
                    for sentence in beam['sentences']:
                        _result.append(sentence['text'])
                    break
                result_parts.append(' '.join(_result))
            return '\n'.join(result_parts)
