import time
import re
import copy
import json
import random
import urllib3
from os import path
from .. import utils, pseudonyms, translator_abstract, yandex_session, selenium_session, _proxy_handler
from . import _paths, LOGGER
ProxyMode = _proxy_handler.ProxyMode

class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'yandex'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    HOSTNAME = u'browser.translate.yandex.net'
    CURRENT_VERSION = u'7.1'
    VERSION_IS_CHECKED = False
    SYMB_LIMIT = 10000
    URL_LIMIT = 1000
    FORCE_RPM = 100.0
    TOR_RPM = 300.0

    def __create_url(self, text_arr, dest, src, _version, _yandex_id):
        query_data = (u'translateMode=context', u'context_title=', 'id={0}'.format(_yandex_id), 'srv=yabrowser')
        if text_arr:
            query_data += tuple(map(lambda t: u'text={0}'.format(self._quote(t)), text_arr))
        query_data += (u'lang={0}-{1}'.format(src, dest), 'format=html', 'options=2', u'version={0}'.format(_version), u'')
        return urllib3.util.Url(scheme='https', auth=None, host=self.HOSTNAME, port=None, path='/api/v1/tr.json/translate', query=u'&'.join(query_data), fragment=None)

    @staticmethod
    def generate_id():
        result = hex(int(time.time() * 1000.0))[2:]
        result += ''.join(map(lambda _i: hex(random.randint(0, 15))[2:], pseudonyms.xrange(16 - len(result))))
        return result

    def _get_urls_from_text_arr(self, text_arr, dest, src):
        _time_id = self.generate_id()

        def get_url(_text_arr, _counter_value):
            return self.__create_url(text_arr=_text_arr, dest=dest, src=src, _version=self.CURRENT_VERSION, _yandex_id='-'.join((_time_id, '{0}'.format(_counter_value), '0'))).url

        def get_slice(_text_arr, _counter_value):
            result = []
            for text_element in _text_arr:
                result.append(text_element)
                if len(get_url(result, _counter_value)) >= self.URL_LIMIT:
                    break
            while True:
                if len(get_url(result, _counter_value)) < self.URL_LIMIT:
                    return result
                if not result:
                    raise RuntimeError('Too big empty URL')
                if len(result) == 1:
                    if not result[0]:
                        raise RuntimeError("Too big empty URL (with 'text')")
                    result[0] = result[0][:-1].strip()
                    continue
                result.pop(-1)
                continue
        text_arr = list(copy.deepcopy(text_arr))
        _counter = 0
        while True:
            if not text_arr:
                break
            text_part = get_slice(text_arr, _counter)
            yield get_url(text_part, _counter)
            _counter += 1
            text_arr = text_arr[len(text_part):]

    def _web_translate(self, text, dest, src, _use_selenium=False):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        text_arr = list(re.split('[\\r\\n]+', text, flags=self._RE_FLAGS))
        if not text_arr:
            return u''
        url = u'https://browser.translate.yandex.net/v{0}/dist/scripts/addons/tr_page_bundle_with_images.js'.format(self.CURRENT_VERSION)
        switch_ip = True
        with yandex_session.proxy_object.LOCK:
            if yandex_session.proxy_object.proxy_mode is not ProxyMode.Disable:
                Translator.VERSION_IS_CHECKED = False
            if _use_selenium:
                selenium_session.get_if(url)
                time.sleep(5.0)
            elif not Translator.VERSION_IS_CHECKED:
                try:
                    yandex_session.get(url, _force_rpm=(self.FORCE_RPM, self.TOR_RPM), _switch_ip=switch_ip)
                except Exception as ex:
                    self.LOGGER.exception(ex)
                switch_ip = False
                Translator.VERSION_IS_CHECKED = True
            result = []
            for url in self._get_urls_from_text_arr(text_arr, dest, src):
                if _use_selenium:
                    resp = selenium_session.request_js('GET', url, rpm=self.FORCE_RPM)
                    self.LOGGER.debug('Answer:\n%s', resp)
                    _json = json.loads(resp)
                else:
                    resp = yandex_session.get(url, _force_rpm=(self.FORCE_RPM, self.TOR_RPM), _switch_ip=switch_ip)
                    switch_ip = False
                    self.LOGGER.debug('Answer:\n%s', resp.text)
                    _json = resp.json()
                _code = _json.get(u'code', 404)
                if 400 <= _code < 600:
                    raise Exception(_json)
                if 'text' not in _json:
                    raise Exception(_json)
                result.extend(_json[u'text'])
            return u'\n\n\n'.join(result)
