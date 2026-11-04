import json
from ._google_gtx import translator as google_gtx_translator
from ._google_client5 import translator as google_client5_translator
from ._google_rpc import translator as google_rpc_translator
from ._selenium_deepl import translator as selenium_deepl_translator
from ._deepl_rpc import translator as deepl_rpc_translator
from ._deepl_official import translator as deepl_official_translator
from ._reverso import translator as reverso_translator
from ._bing_translator import translator as bing_translator
from ._lingvanex import translator as lingvanex_translator
from ._yandex_translate import translator as yandex_translator, translator_alt as yandex_translator_alt
from . import _all_sessions, selenium_session, LOGGER


class Translator(object):
    __author__ = 'Vladya'
    LOGGER = LOGGER.getChild('MainTranslator')
    CLASSES = {'google_gtx': google_gtx_translator.Translator, 'google_client5': google_client5_translator.Translator, 'google_rpc': google_rpc_translator.Translator, 'selenium_deepl': selenium_deepl_translator.Translator, 'deepl_official': deepl_official_translator.Translator, 'yandex_translate': yandex_translator.Translator, 'reverso': reverso_translator.Translator, 'bing': bing_translator.Translator, 'lingvanex': lingvanex_translator.Translator}
    ALT_CLASSES = {'yandex_translate': yandex_translator_alt.Translator}
    alias_mapping = {'google_client5': ('google',)}
    IS_PRINTED_DEBUG = False

    def __init__(self, setting_dict=None, multi_setting=None, _use_alts=None, _disable=None):
        self._setting_dict = setting_dict
        self._multi_setting = multi_setting
        _debug = True
        if self._setting_dict and not self._setting_dict[u'_debug_mode']:
            _debug = False
        if _use_alts:
            _use_alts = set(_use_alts)
        else:
            _use_alts = set()
        _classes = {}
        for translator_name, _Translator in self.CLASSES.items():
            if translator_name in _use_alts:
                if translator_name not in self.ALT_CLASSES:
                    raise ValueError('Incorrect alt name: {0}'.format(translator_name))
                _Translator = self.ALT_CLASSES[translator_name]
                _use_alts.discard(translator_name)
            _classes[translator_name] = _Translator
        if _use_alts:
            raise ValueError('Incorrect alt names: {0}'.format(_use_alts))
        _not_available_translators = set()
        if _disable:
            for translator_name in _disable:
                if translator_name in _classes:
                    _classes.pop(translator_name)
                    _not_available_translators.add(translator_name)
        if not selenium_session:
            if _debug:
                raise RuntimeError('Selenium install incorrect.')
            for translator_name, _Translator in _classes.copy().items():
                if _Translator.BROWSER_TRANSLATOR:
                    _classes.pop(translator_name)
                    _not_available_translators.add(translator_name)
        self.__translators = {}
        for translator_name, _Translator in _classes.items():
            try:
                _translator_object = _Translator(setting_dict=self._setting_dict, multi_setting=self._multi_setting)
            except Exception as ex:
                if hasattr(_Translator, 'LOGGER') and _Translator.LOGGER:
                    _Translator.LOGGER.exception(ex)
                if _debug:
                    raise
                _not_available_translators.add(translator_name)
                continue
            self.__translators[translator_name.lower()] = _translator_object
        self._not_available_translators = frozenset(_not_available_translators)

    def get_available_translator_services(self):
        result = {}
        for name, tr in self.__translators.items():
            result.setdefault(tr.TRANSLATOR_GROUP, set()).add(name)
        for _group, names in result.copy().items():
            result[_group] = tuple(sorted(names))
        return tuple(sorted(result.items()))

    def _get_translator(self, service):
        _service = service.strip().lower()
        if _service not in self.__translators:
            for new_name, aliases in self.alias_mapping.items():
                if _service in aliases:
                    _service = new_name.strip().lower()
                    break
            if _service not in self.__translators:
                raise ValueError("Translator '{0}' not found".format(service))
        return self.__translators[_service]

    def update_translator_symb_limit(self, service, new_limit):
        translator = self._get_translator(service)
        translator.update_limit(new_limit)

    def get_translate_symb_limit(self, service):
        translator = self._get_translator(service)
        return translator.SYMB_LIMIT or 1e999

    def get_string_len(self, service, text, dest=None, src=None):
        translator = self._get_translator(service)
        return translator.get_string_len(text, dest, src)

    def string_is_translated(self, service, text, dest, src):
        translator = self._get_translator(service)
        return translator.string_is_translated(text, dest, src)

    def translate(self, service, text, dest, src, req_id, _use_database_only, _update_on_hdd=True):
        if not Translator.IS_PRINTED_DEBUG:
            _debug_data = {}
            for _session in _all_sessions:
                try:
                    resp = _session.get(u'https://httpbin.org/get', _force_rpm=9999.0, _use_tor=False, timeout=2.0).json()
                    resp.pop(u'url', None)
                    resp[u'headers'].pop(u'Host', None)
                except Exception:
                    continue
                else:
                    _debug_data[_session.UNIQUE_ID] = resp
            if _debug_data:
                _debug_data = json.dumps(_debug_data, ensure_ascii=True, indent=4)
                self.LOGGER.debug('Network debug data: %s', _debug_data)
            Translator.IS_PRINTED_DEBUG = True
        translator = self._get_translator(service)
        return translator.translate(text, dest, src, None, _use_database_only, _update_on_hdd)

    def interrupt_all_translations(self):
        for translator in self.__translators.values():
            translator.interrupt_web_translation()

    def get_lang_code(self, service, data, dest_direction=True):
        translator = self._get_translator(service)
        return translator.get_lang_code(data, dest_direction)

    def get_lang_name(self, service, data, dest_direction=True):
        translator = self._get_translator(service)
        return translator.get_lang_name(data, dest_direction)

    def get_all_lang_codes(self, service, dest_direction=True):
        translator = self._get_translator(service)
        return translator.get_all_lang_codes(dest_direction)

    def backup_database(self, service):
        translator = self._get_translator(service)
        return translator.backup_database()

    def clear_cache(self, service, local):
        translator = self._get_translator(service)
        return translator.clear_cache(local)

