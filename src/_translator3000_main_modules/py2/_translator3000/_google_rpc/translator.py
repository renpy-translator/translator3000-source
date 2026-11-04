import json
import urllib3
from os import path
from .. import utils, pseudonyms, translator_abstract, current_session
from . import _paths, LOGGER


class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'google'
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, u'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    HOSTNAME = 'translate.google.com'
    FORCE_FIX_SENTENCES = True
    SYMB_LIMIT = 4500
    RPC_TOKEN = u'MkEWBc'

    def get_base_url(self):
        hostname = self.HOSTNAME
        if self._setting_dict is not None:
            hostname = self._setting_dict.get(u'googleHost', None)
            if not isinstance(hostname, pseudonyms.basestring):
                hostname = self.HOSTNAME
        return urllib3.util.Url(scheme='https', auth=None, host=hostname, port=None, path='/_/TranslateWebserverUi/data/batchexecute', query=None, fragment=None)

    def _web_translate(self, text, dest, src):
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        rpc_q_data = utils.Encoding.utf8decode(json.dumps([[text, src, dest, True], [None]], separators=(u',', u':')))
        rpc_data = json.dumps([[[self.RPC_TOKEN, rpc_q_data, None, u'generic']]], separators=(u',', u':'))
        post_data = {'f.req': utils.Encoding.utf8decode(rpc_data)}
        post_params = {'rpcids': self.RPC_TOKEN, 'bl': 'boq_translate-webserver_20210421.14_p0', 'soc-app': 1, 'soc-platform': 1, 'soc-device': 1, 'rt': 'c'}
        url = self.get_base_url().url
        resp = current_session.post(url, params=post_params, data=post_data)
        self.LOGGER.debug('Answer:\n%s', resp.text)
        result = ''
        _start = False
        for string in resp.text.split('\n'):
            if string.strip().isdigit():
                if _start:
                    break
                _start = True
                continue
            if not _start:
                continue
            result += string
        result = json.loads(result)
        result = json.loads(result[0][2])
        final_result = []
        for part in result[1][0][0][5]:
            high_priority = None
            string = None
            if len(part) < 5:
                final_result.append(part[0])
                continue
            for variant in part[4]:
                variant, priority = variant[:2]
                priority = max(priority)
                if high_priority is None:
                    high_priority = priority
                if priority <= high_priority:
                    high_priority = priority
                    string = variant
            final_result.append(string)
        return u' '.join(final_result)

