import re
import rsa
import base64
import hashlib
import codecs
import json
from os import path
from . import utils, _paths

class Ver2Reader(object):
    PADDING = u'\n\ntr3000dbver2\n\n'
    PART_SPLITTER = '\t'
    CACHE = {}
    initialized = False

    def __new__(cls, filename, logger, multi_setting=None):
        filename = path.abspath(utils.Encoding.fsdecode(filename, 'strict'))
        if filename not in cls.CACHE:
            cls.CACHE[filename] = super(Ver2Reader, cls).__new__(cls)
        return cls.CACHE[filename]

    def __init__(self, filename, logger, multi_setting=None):
        if self.initialized:
            return
        self._logger = logger.getChild('Ver2Reader')
        if 'local translations' in filename:
            self._logger = self._logger.getChild('Local')
        self._logger.debug('Initialize started.')
        self.__filename = filename
        self.__data = {}
        self.__multi_setting = multi_setting
        self.__update_db_from_file()
        self._logger.debug('Successful initialize.')
        self.initialized = True

    @classmethod
    def _clear_cache(cls):
        cls.CACHE.clear()

    def is_file_modified_by_user(self):
        if not path.isfile(self.__filename):
            return False
        if not path.isfile(_paths.FILES_LAST_MODIFIED_REGISTRY):
            return False
        registry = utils._DataSaver.read_json_from_file(_paths.FILES_LAST_MODIFIED_REGISTRY, compressed=True)
        fn = path.abspath(self.__filename)
        if fn not in registry:
            return False
        tstmp = path.getmtime(fn)
        if tstmp - 3.0 <= registry[fn] <= tstmp + 3.0:
            return False
        return True

    def write_file_timestamp_in_registry(self):
        if not path.isfile(self.__filename):
            return
        fn = path.abspath(self.__filename)
        current_timestamp = path.getmtime(fn)
        if path.isfile(_paths.FILES_LAST_MODIFIED_REGISTRY):
            registry = utils._DataSaver.read_json_from_file(_paths.FILES_LAST_MODIFIED_REGISTRY, compressed=True)
        else:
            registry = {}
        registry[fn] = current_timestamp
        utils._DataSaver.write_json_to_file(registry, _paths.FILES_LAST_MODIFIED_REGISTRY, compress=True)

    def get_db_in_translator_format(self):
        self._logger.debug('Requested database.')
        result = {}
        for key, dest_text in self.__data.items():
            source_lang, source_text, dest_lang = key
            result.setdefault(source_lang, {})
            result[source_lang].setdefault(source_text, {})
            result[source_lang][source_text][dest_lang] = dest_text
        self._logger.debug('Database prepared.')
        return result

    def _to_file_write(self, source_lang, source_text, dest_lang, dest_text):

        def _get_data(d):
            return json.dumps(utils.Encoding.utf8decode(d, 'strict'), ensure_ascii=True)
        return self.PART_SPLITTER.join(map(_get_data, (source_lang, source_text, dest_lang, dest_text)))

    def _update_file(self, db):
        self._logger.debug('Requested file update.')
        add_data = set()
        need_full_rewrite = False
        self._logger.debug('Collecting updates.')
        for source_lang, source_texts in db.items():
            for source_text, dest_langs in source_texts.items():
                for dest_lang, dest_text in dest_langs.items():
                    key = (source_lang, source_text, dest_lang)
                    if key in self.__data:
                        if self.__data[key] == dest_text:
                            continue
                        else:
                            need_full_rewrite = True
                    self.__data[key] = dest_text
                    data = self._to_file_write(source_lang, source_text, dest_lang, dest_text)
                    add_data.add(data)
        if need_full_rewrite:
            self.full_rewrite_file()
        else:
            self._logger.debug('Write %d elements on HDD.', len(add_data))
            utils.create_dir_for_file(self.__filename)
            with codecs.open(self.__filename, 'a', encoding='utf_8') as _file:
                for data in add_data:
                    _file.write(data)
                    _file.write(self.PADDING)
            self.write_file_timestamp_in_registry()
            self._logger.debug('File is updated.')

    def full_rewrite_file(self):
        self._logger.debug('Requested full file rewriting.')
        utils.create_dir_for_file(self.__filename)
        with codecs.open(self.__filename, 'w', encoding='utf_8') as _file:
            for key, dest_text in sorted(self.__data.items()):
                source_lang, source_text, dest_lang = key
                data = self._to_file_write(source_lang, source_text, dest_lang, dest_text)
                _file.write(data)
                _file.write(self.PADDING)
        self.write_file_timestamp_in_registry()
        self._logger.debug('File is rewrited.')

    def __update_db_from_file(self):
        if not path.isfile(self.__filename):
            self.full_rewrite_file()
            return
        is_modified = self.is_file_modified_by_user()
        if is_modified and self.__multi_setting:
            self.__multi_setting.use_edit = True
            self.__multi_setting.save()
        with codecs.open(self.__filename, 'r', encoding='utf_8') as _file:
            data = utils._DataSaver._read_fo(_file, _return_if_empty=u'')
        data = re.split(self.PADDING, data)
        part_splitter = re.compile(self.PART_SPLITTER)
        for translate in data[:-1]:
            source_lang, source_text, dest_lang, dest_text = map(json.loads, part_splitter.split(translate))
            self.__data[source_lang, source_text, dest_lang] = dest_text
        if data[-1]:
            self._logger.debug('DB file is broken. Start fixing.')
            self.full_rewrite_file()
_PUB = b'\nLS0tLS1CRUdJTiBSU0EgUFVCTElDIEtFWS0tLS0tCk1JSUNDZ0tDQWdFQXMyOVYvMUpubDljaWNZeGw3SFl6Qmh3MVNBc1VLSENyNkhOOWxSMDlxWTlLRHcwOWIveTQKaXFNbFVkc3hqMFFhSUxVbzI2VGtscWlSWktFUFQvRkV6cUptQnRFVmhIVjg0NnRaOTkrdDNNOG5KUkVxRmFZSwpZNExSa1M4VHo3MjUybnVZSnZpWlZrNEF5Qk4vRTRoQW5UeTZvd0FjZ0UwbkRwcGltT244OS91VVZNbUVkalZvCjJweHEyUW9hNklTNGN1WXNtWW5KZWlIdzZCTXA3djJtYk1VeXNmZnVtM0xWakROejdnVUJPSDFyanNwTDV6bUMKMVovQjNPWWpIbko3UEY2ZjJNOThXSUFWTTlGblVzVm9wcFhPSklGQm4vVCtrRDlIbDlMaDdSaGRsVTJPVWZHegpyaFBzTGRRNWh1ZTA3WTJuSkNuM2JTYUxwMGhIQTk5RDhUcUpGbnFYdDE0Ym5lN0ZKRStPVk5ZR3MwNS9lWFkzClZTNUFLbkVTeHBZcFl0ZWdjRnQrZ2xsRGVVUGl6dTNOc0VvWTVwK2hTZlh1NGYvZC9WZ0Rzb1V5QkpJMWxuNWsKcnBIQ1pYV29xT2ljZjNCY3JEaitqWkQ1WnNuaUtoOStnZHdKZVZFbm9yUUFpcXN1U1Z2T0Zqc0Z2RzAzYXhqTQpMNUc3T0xhRWpmRlJpcWEzMFZMS2V4YVlidENJaC9oYXR1ZUJjL2FlYlFKWXVnMGc5ZVVQYUs0V205WVF4K0Q3CjNIUVl5SE9ONE1aKzZKSURWc01nazVDZEhzdnJMbWJXRGpwRlFUenpPY0dGbVRDV0lqZXo5TFVlUGJQejZFTVIKclZrL2l5UkRhZGxIVktZV3EzeWhkV1NhZm1WMkpuOXdhaWRJZGhlUTJxRkpSZDM4V1BUYUM2MENBd0VBQVE9PQotLS0tLUVORCBSU0EgUFVCTElDIEtFWS0tLS0tCg==\n'.strip()
_PRIV = b'\nLS0tLS1CRUdJTiBSU0EgUFJJVkFURSBLRVktLS0tLQpNSUlKT0FJQkFBS0NBZ0VBczI5Vi8xSm5sOWNpY1l4bDdIWXpCaHcxU0FzVUtIQ3I2SE45bFIwOXFZOUtEdzA5CmIveTRpcU1sVWRzeGowUWFJTFVvMjZUa2xxaVJaS0VQVC9GRXpxSm1CdEVWaEhWODQ2dFo5OSt0M004bkpSRXEKRmFZS1k0TFJrUzhUejcyNTJudVlKdmlaVms0QXlCTi9FNGhBblR5Nm93QWNnRTBuRHBwaW1Pbjg5L3VVVk1tRQpkalZvMnB4cTJRb2E2SVM0Y3VZc21ZbkplaUh3NkJNcDd2Mm1iTVV5c2ZmdW0zTFZqRE56N2dVQk9IMXJqc3BMCjV6bUMxWi9CM09ZakhuSjdQRjZmMk05OFdJQVZNOUZuVXNWb3BwWE9KSUZCbi9UK2tEOUhsOUxoN1JoZGxVMk8KVWZHenJoUHNMZFE1aHVlMDdZMm5KQ24zYlNhTHAwaEhBOTlEOFRxSkZucVh0MTRibmU3RkpFK09WTllHczA1LwplWFkzVlM1QUtuRVN4cFlwWXRlZ2NGdCtnbGxEZVVQaXp1M05zRW9ZNXAraFNmWHU0Zi9kL1ZnRHNvVXlCSkkxCmxuNWtycEhDWlhXb3FPaWNmM0JjckRqK2paRDVac25pS2g5K2dkd0plVkVub3JRQWlxc3VTVnZPRmpzRnZHMDMKYXhqTUw1RzdPTGFFamZGUmlxYTMwVkxLZXhhWWJ0Q0loL2hhdHVlQmMvYWViUUpZdWcwZzllVVBhSzRXbTlZUQp4K0Q3M0hRWXlIT040TVorNkpJRFZzTWdrNUNkSHN2ckxtYldEanBGUVR6ek9jR0ZtVENXSWplejlMVWVQYlB6CjZFTVJyVmsvaXlSRGFkbEhWS1lXcTN5aGRXU2FmbVYySm45d2FpZElkaGVRMnFGSlJkMzhXUFRhQzYwQ0F3RUEKQVFLQ0FnRUFpb3l4YnBDR2hPd05JSGcwU3oySmNISmZnZDFzRnozSXY1aE5vOUlNUnR6cFptM212bzM1UUxOdwpvYUFLeUlEaFc5Z0dVSE1tUGw2eXhXekhrZ2JPQm0vSE1BUktCUmxpOGJqaG8xQUh3N1FBbWRLREdHdzVJVlZsCjFDRHh2enJVUXl1ajlKT0ljdWVRR3UxUzloWURMbVl5QnFLVFgwNHpsa2NIVXVONS9WRTQyNjh1cE1mZ3lzeDAKaEZvVkpPMDJMeUlqMWZwYW8vK0pNT2w3TzVxSDR2enhoQkhaSUJhdlphNWxHYWlycEo3VGFsSXlBYnlhbGJEaAoxRnV2U2xkRGFQMzNsMFcrMGVjMGQrcDlTYUE4aWtTcUErMzZhalNXUzNOUktKNGc3UjRmUktXNSt2UVN0WnVVCmhsNlVmT0owY3d3ZjJMdjhzOXpheW5XSkFiT1ptWUxHdnM1RmVnYmt1Q05IVXh3alA3VDZMZDhNUldSbHFBNzUKRk50ck9jZ2FxKytYSGhjRG1YeHh1c0pVc1dzZmlFamt2dGljVnRYc0JZNkd3SzFyeFFXMWIwTlhqaElCQTdUaApSMlcxSXE1U3NEbit1ZnBvSlBYenliaSs2L0MySnBrL1dSMzdCcGlZNE03clIvazNkZ1RVaU9sdFRHWG05QUpSCkdXNTJsWWxoK0hmWmJKWkJDK3g5MDhGcTBJSENwOENPYVo4ODAzbjNXYXUva2dCclRmYU1SMUFzQWhNZ1QvSWsKK2ZRSHhaclJieU1CY1VtQWZQZWc5YmlQam9aajJBaFVkb1FTcHYxMnAzalpDZTR3NjdBVzd4SXJCQkZTK0p1dgo4UDNYNWRvL3hKdnE0YkRRa1ZOVklETDNCUkFHVnpQQzBMdFlUMmFuK1ZPWXJSVnlJRkVDZ2dFUkFMNHpBTkltCmF3TTYxQTlLbTNFVWtjTTdPT0xrcjZ4MWNpRDZhSUw1dEcrS3lkdUxKYTNYRVh4NzB6eXdqaTVUVlI4TDVNOGsKRWROT0dRWG5LaHJkbk0vU3VyU1R2OSt4RnFGUytEM2t6WHN0R2VjTmtkUHQwckd2VkJFNG9FQkZ1UWorQ2ZwaQp5NE1Ld3FGWS90UkprQll5YjdGSFVrZFYwSkxGQU1MQ1BvbGppNUREQUwvU09nd2VvTzF6QU1vZWNDMVpFR0JZCjhsa2JoQ295OUIrQnFIV3JZTjVWUmM4WUhvMWM2NC9KTm5nazdpa0lrQng2NVhnaGFaNVNiLzVkYVdoN2RuY1QKczVDdTZDd2dUSlgyQSt6aFBuQWN3amlQR3krTGZJcjZZd05tcnVLbGNEN1NxQkxsNVIvN3Q3Q04wYlZJUkxzeQpsRHh2aVZMQm14ZnBkYjFqM1NoN01GK2pseWxsYzdwZ1dWMzdBb0h4QVBHQy9Yb0hSZEFMb0c0cCtITFhsTnlmCk5XaGtkV1hDdTRyNmJ5aXEvNmRXdUlCQTFPekZJcWNGclFSdDBhWWJQK3VuSXQ0U1hhbUlpbXZyYkdHZ0ZaNEEKV1RJZGxkYnVtOXk1aFArNDZTb3QvTkhYbDhQUFRLQWxyRWlRNnQ2OFduTDFPS2toNFZzYnU4TlNwdVExSkowKwpBb3pqMnRYTGJPK1BPbFRoQVFLMEtCVklNMSt2Z1hsRlZ2dlhFRTU1MHh1TWlrTm50eGs2eEZlNTZ3bmlKNUR0ClpmalBDV2VEMG5DQkpDZi80QURTV09jWDZER1lvNlZBd0ZyTHdUSjFWcGpOWnZrOVIwSWRMZGRlcE03T1k3dmkKMm9qTW1HUnRTWFVKQ1d3QkRaZzJha3FqOXh1YTNnS1JYN0hMblJ0VWR3S0NBUkVBaTZTOHhJNXFZVnV1Mkc5SgpneE84RldBRTJ5bFdCY1BSQUg5NWZqaEJqdWVTWHZ0aHRhbkM3K2VsNXRnbCs4TTVLdXM3bWczOGZHekptSGpwCmhBSVRvTTR5UUdSK0tvbEZlVHFHZ2tMYnpzVUZVSXU0OXFXVTNOcENXY1orZWRIM0ViQWF1VmdSM1d0b0RMaGYKbUpOT0U4NENEV0cwK2lUNlZ0Z0hQL2NIblMyV0NibnljZU95dExWRUtESVljVTA1eFVHdjhWMDh5Y21YRnJpRQpYaUYvQXEzS0dGTDVSeHlKU2ZiZ0NKaU53bFl5K2JPTXd5eEVFQmhRQ0dxMFNVaGlITkVRNEVwNXV3OS83TzNsCjdQQk1YMzNjcnNtZW01SU9QckVseHBBaFpCemU2QTdaUTNhODZlc2FkNG9EaXNBRktSa2ZSV1hVU2k4RjN0bkEKdWlTeFNsVG95bER2NmpnY3dzcjIxZTdwamtNQ2dmRUF2VG9xQ3JPcUVvRVptVmRQTUFRVHdlMElkcHZIbEF6SQp6dks3cDd5YmhPeWdzUFNiSUV5eGd2WWlnd2JjcmU1SjNnVGRmK3daOE54bndIajhPVjJwc2x1Smg0ZkF3Ri9DClJXWWlmQTdRdWRqQWIxWWh0aTAxVjRGTkJLcHZMRWVlQXRaNko2TEJKSmFOUGxRREtXa3VIL25YRzdibjNuMSsKQkJGUDNmTlJ6R0dGeW04QXVhY1VwZ1ViUzBWTnBIODFWaTkrb2FPZ3hhYlM4ZjFjMkNpWFlhbHdMVXRpamZXdQpLN0l6dHhkMzFvejVWVS9aQVFzY3BUMGZ1Y1JOd3BCSFlvQUZmNkZ3dEsrU0hGNHVlVThpdTdMYUVUZGs2OExwClBFYnhWK3RYVUh6S09XTlJHUkwxZ2tPUEhBcHlOVml2QW9JQkVHd1BzdDIrMUtidGs4UlVIOXFLWE5RdDVSVGUKZXlYai9YaXNYbkdJQ3h6eWN4cXFJVzBKRVN1TUw4c1V4K0JvU0V6MGlUTFA2RHFvTW5ZT2wydHJpYTV6Z20vcQpKVzFpNTdDcGRPSnUxNStocFZiT0pMejVpdmkvNVd3UEhJOWY4TTYzWmVBNVhWaWVaWWpCQ3ZqdVRqdFdJUElWClpPUElNN3VvSUZJK1hEMkoxUXRUYmhLRERBdFBmZVZvbWVpNElXZzJxNWk0SlRFNVdsMzdpWWZ1aENhNWVWRWcKTVVER0tVUHQ4N1g2TlcxMUNYUzJHWlpWQ3JzNWdaNGU4akJ5U2lpbndQWHl4cjVETnlaOU0zczdkUmp6cUpIWQptamlvNmFYWkJiV1JjZW4zSzVyUk9WYkV3bllmWUo2WG13M1RyL0ZsUGJnTUREVHg2THppN3hBdWhZNlBYWG12ClRoRHVzZmM1S0RjZ2NvS20KLS0tLS1FTkQgUlNBIFBSSVZBVEUgS0VZLS0tLS0K\n'
_PUB = rsa.PublicKey.load_pkcs1(base64.b64decode(_PUB))
_PRIV = rsa.PrivateKey.load_pkcs1(base64.b64decode(_PRIV))

class LocalDB(object):
    CACHE = {}
    initialized = False

    def __new__(cls, filename, logger):
        filename = path.abspath(utils.Encoding.fsdecode(filename, 'strict'))
        if filename not in cls.CACHE:
            cls.CACHE[filename] = super(LocalDB, cls).__new__(cls)
        return cls.CACHE[filename]

    def __init__(self, filename, logger):
        if self.initialized:
            return
        self.__filename = filename
        self._logger = logger.getChild('LocalDB')
        self.initialized = True

    def load_db(self):
        self._logger.debug('Requested database')
        if not path.isfile(self.__filename):
            self._logger.debug('No database was found')
            return {}
        data = utils.read_file(self.__filename)
        data, digest = (data[:-512], data[-512:])
        digest = rsa.decrypt(digest, _PRIV)
        if hashlib.md5(data).digest() != digest:
            self._logger.debug('Database is broken')
            return {}
        try:
            data = json.loads(data)
        except Exception:
            self._logger.debug('Reading database error')
            return {}
        self._logger.debug('Database was prepared')
        return data

    def write_db(self, db):
        data = utils.Encoding.utf8encode(json.dumps(db), 'strict')
        digest = hashlib.md5(data).digest()
        digest = rsa.encrypt(digest, _PUB)
        data += digest
        utils.save_data_to_file(data, self.__filename)
