import time
import threading
import re
import json
import urllib3.util
from os import path
from .. import utils, translator_abstract, current_session
from . import _paths, LOGGER


class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'bing'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    SYMB_LIMIT = 500
    URL = 'https://www.bing.com/translator'
    AUTH_LOCK = threading.Lock()
    _AUTH_DATA = None

    @classmethod
    def _get_auth_data(cls, _force_update=False):
        with cls.AUTH_LOCK:
            _current_time = time.time()
            if not _force_update:
                if cls._AUTH_DATA is not None:
                    _expire = cls._AUTH_DATA['_expire']
                    if _current_time < _expire:
                        return cls._AUTH_DATA
            resp = current_session.get(cls.URL)
            _match_result = re.search(u'_G\\s*=\\s*(?P<data>\\{[^;]+\\});', resp.text)
            if not _match_result:
                cls.LOGGER.error(resp.content)
                raise Exception('Incorrect answer')
            result = {}
            for _match_result in re.finditer(u'(?P<key>[A-za-z]\\w*)\\s*:\\s*"(?P<value>[^"]+)",?', _match_result.group('data')):
                k, v = map(_match_result.group, ('key', 'value'))
                result[k] = v
            _match_result = re.search(u'var\\s+params_AbusePreventionHelper\\s*=\\s*(?P<params>\\[\\d+,\\s*"[^"]+",\\s*\\d+\\]);', resp.text)
            if not _match_result:
                cls.LOGGER.error(resp.content)
                raise Exception('Incorrect answer')
            _key, _token, _expire = json.loads(_match_result.group('params'))
            _expire = _current_time + float(_expire) / 1000.0 * 0.75
            result['key'] = _key
            result['token'] = _token
            result['_expire'] = _expire
            cls._AUTH_DATA = result
            return cls._AUTH_DATA

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        text_arr = list(re.split(u'[\\r\\n]+', text, flags=self._RE_FLAGS))
        if not text_arr:
            return u''
        result = []
        for _txt in text_arr:
            _exception = Exception('Undefined error')
            for _attempt in range(5):
                _force_update = False
                if _attempt > 0:
                    _force_update = True
                _auth_data = self._get_auth_data(_force_update=_force_update)
                query_data = u'isVertical=1', u'', u'IG={0}'.format(_auth_data[u'IG']), u'IID=translator.5026'
                url = urllib3.util.parse_url(self.URL)
                url = urllib3.util.Url(scheme=url.scheme, auth=url.auth, host=url.host, port=url.port, path=u'/ttranslatev3', query=u'&'.join(query_data), fragment=url.fragment).url
                params = (u'fromLang', src), (u'to', dest), (u'text', _txt), (u'tryFetchingGenderDebiasedTranslations', u'true'), (u'token', _auth_data[u'token']), (u'key', _auth_data[u'key'])
                kw = {u'data': self._urlencode(params, space_is_plus=True), u'headers': {u'Content-Type': u'application/x-www-form-urlencoded'}}
                resp = current_session.post(url, **kw)
                self.LOGGER.debug('Answer:\n%s', resp.text)
                try:
                    answer = resp.json()
                except Exception as ex:
                    self.LOGGER.exception(ex)
                    _exception = ex
                    time.sleep(1.5 ** float(_attempt))
                    continue
                for d in answer:
                    if u'translations' not in d:
                        continue
                    for t in d[u'translations']:
                        if u'text' not in t:
                            break
                        result.append(t[u'text'])
                break
            else:
                raise _exception
        return u'\n\n\n'.join(result)

