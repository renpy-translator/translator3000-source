import re
import time
import os
import zlib
import json
import copy
import threading
import requests.compat
from os import path
from . import utils, _database_module, pseudonyms, lang_codes, selenium_session
try:
    import cPickle as pickle
except Exception:
    import pickle
SELENIUM_MODE_SETUP_FROM_USER = False

class BanOnServer(Exception):
    pass

class ShadowBan(BanOnServer):
    pass

class OverCharacterLimit(Exception):
    pass

class StringMismatch(Exception):
    pass

class SymbolLimitExceeded(Exception):

    def __init__(self, current_limit=None):
        super(SymbolLimitExceeded, self).__init__(current_limit)
        self.current_limit = current_limit

class InterruptTranslate(Exception):

    def __init__(self, return_value=None):
        super(InterruptTranslate, self).__init__(return_value)
        self.return_value = return_value

class TranslatorAbstract(object):
    __author__ = 'Vladya'
    LOGGER = None
    DATABASE_FN = None
    LOCAL_DATABASE_FN = None
    IMPORT_TRANSLATIONS_DIR = None
    SYMB_LIMIT = None
    TRANSLATOR_GROUP = None
    BROWSER_TRANSLATOR = False
    MAX_ATTEMPTS = 3
    OLD_DB_FORMATS = ('.json', '.tr3000db', '.tr3000dbp', '.tr3000db2')
    DB_FORMAT = u'.tr3000db3'
    LOCAL_DB_FORMAT = '.tr3000localdb'
    DB_ZLIB_COMPRESSION_LEVEL = zlib.Z_BEST_SPEED
    PICKLE_PROTOCOL = 2
    FORCE_FIX_SENTENCES = False
    USE_SENTENCE_MODE = False
    _RE_FLAGS = re.DOTALL | re.UNICODE
    SENTENCE_RE = re.compile(u'(?P<text>[^!?….\\r\\n]+)(?P<end_mark>[!?….]*)', flags=_RE_FLAGS)
    FORCE_RPM = None
    TOR_RPM = None
    TOR_MODE = False
    single_instance = None
    is_initialized = False

    def __new__(cls, setting_dict=None, multi_setting=None):
        if cls.single_instance is None:
            cls.single_instance = super(TranslatorAbstract, cls).__new__(cls)
        return cls.single_instance

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        self._setting_dict = setting_dict
        self._multi_setting = multi_setting
        if self.BROWSER_TRANSLATOR:
            if not selenium_session:
                raise RuntimeError('Selenium install incorrect.')
            global SELENIUM_MODE_SETUP_FROM_USER
            if not SELENIUM_MODE_SETUP_FROM_USER:
                if os.getenv('RENPY_TRANSLATOR3000_COMPILE', '0') != '1' and os.getenv('RENPY_TRANSLATOR3000_SANDBOX_MODE', '0') != '1':
                    _mode = None
                    _path_to_chrome = None
                    _use_proxy = False
                    if self._setting_dict:
                        _mode = self._setting_dict[u'seleniumStartMode']
                        _path_to_chrome = self._setting_dict[u'pathToChromeExe']
                        _use_proxy = self._setting_dict[u'useProxyInSelenium']
                    selenium_session.reload(_mode, path_to_binary=_path_to_chrome, use_proxy=_use_proxy)
                SELENIUM_MODE_SETUP_FROM_USER = True
        self._translate_lock = threading.RLock()
        self._database_lock = threading.RLock()
        self._hdd_lock = threading.RLock()
        self._database = {}
        self._local_db = {}
        for _old_db_dir in tuple(self._get_old_database_folders()):
            db_pth = path.join(_old_db_dir, 'translations.dbformat')
            _db = self.database_load(db_pth)
            self._database = utils.merge_dicts(self._database, _db)
            utils.remove_dir(_old_db_dir, True)
            self.LOGGER.debug('Loaded old global DB: %s', db_pth)
        self._database = self._fix_old_database(self._database)
        self.LOGGER.debug('Start loading the local database.')
        _db = self.database_load(self.LOCAL_DATABASE_FN)
        self._database = utils.merge_dicts(self._database, _db)
        self._local_db = utils.merge_dicts(self._local_db, _db)
        self.LOGGER.debug('Start loading the global database.')
        _db = self.database_load(self.DATABASE_FN)
        self._database = utils.merge_dicts(self._database, _db)
        self.backup_database()
        self.delete_old_databases()
        if self.IMPORT_TRANSLATIONS_DIR is not None:
            utils.create_dir(self.IMPORT_TRANSLATIONS_DIR)
            _bases = set()
            for fold, _, filenames in os.walk(self.IMPORT_TRANSLATIONS_DIR):
                for fn in filenames:
                    full_fn = path.abspath(path.join(fold, fn))
                    _, ext = path.splitext(full_fn)
                    _formats = self.OLD_DB_FORMATS + (self.DB_FORMAT,)
                    if ext.lower() not in _formats:
                        continue
                    _bases.add(full_fn)
            for i, fn in enumerate(sorted(_bases), 1):
                self.LOGGER.debug('Start loading extra database %d.', i)
                _db = self._database_load(fn)
                self._database = utils.merge_dicts(self._database, _db)
                self.backup_database()
                if self._multi_setting:
                    self._multi_setting.use_edit = True
                    self._multi_setting.save()
                utils.remove_file(fn)
        self.is_initialized = True
        self.LOGGER.debug('Initialization is successful.')

    def update_limit(self, new_limit):
        with self._database_lock:
            if new_limit == 'reset':
                new_limit = self.__class__.SYMB_LIMIT
            self.SYMB_LIMIT = int(new_limit)

    def _get_old_database_folders(self):
        if False:
            yield None

    def _fix_old_database(self, db):
        return copy.deepcopy(db)

    def __update_db_from_data(self, data, with_rewrite, include_local=False):
        data = copy.deepcopy(data)
        with self._database_lock:
            if with_rewrite:
                if include_local:
                    self._local_db = utils.merge_dicts(self._local_db, data)
                self._database = utils.merge_dicts(self._database, data)
            else:
                if include_local:
                    self._local_db = utils.merge_dicts(data, self._local_db)
                self._database = utils.merge_dicts(data, self._database)
            self.backup_database()

    def _update_db_with_rewrite(self, data, include_local=False):
        return self.__update_db_from_data(data, with_rewrite=True, include_local=include_local)

    def _update_db_without_rewrite(self, data, include_local=False):
        return self.__update_db_from_data(data, with_rewrite=False, include_local=include_local)

    @classmethod
    def database_write(cls, database, filename, multi_setting=None, is_local=False):
        ext = cls.LOCAL_DB_FORMAT if is_local else cls.DB_FORMAT
        filename = path.abspath(utils.Encoding.fsdecode(filename))
        filename = u''.join((path.splitext(filename)[0], ext))
        if is_local:
            db = _database_module.LocalDB(filename, cls.LOGGER)
            db.write_db(database)
            return

        def _get_json_bytes():
            _dump_bytes = json.dumps(database, ensure_ascii=True)
            if isinstance(_dump_bytes, pseudonyms.unicode):
                _dump_bytes = _dump_bytes.encode('utf_8')
            return _dump_bytes
        if cls.DB_FORMAT.lower() == '.json':
            database_dump_bytes = _get_json_bytes()
        elif cls.DB_FORMAT.lower() == '.tr3000db':
            database_dump_bytes = zlib.compress(_get_json_bytes(), cls.DB_ZLIB_COMPRESSION_LEVEL)
        elif cls.DB_FORMAT.lower() == u'.tr3000dbp':
            database_dump_bytes = pickle.dumps(copy.deepcopy(database), cls.PICKLE_PROTOCOL)
        elif cls.DB_FORMAT.lower() in ('.tr3000db2', '.tr3000db3'):
            db = _database_module.Ver2Reader(filename, cls.LOGGER, multi_setting)
            db._update_file(database)
            return
        else:
            raise ValueError('Database format is not correct.')
        utils.save_data_to_file(database_dump_bytes, filename, True)

    def database_load(self, filename):
        filename = path.abspath(utils.Encoding.fsdecode(filename))
        filename, _ = path.splitext(filename)
        result = {}
        for _ext_variant in self.OLD_DB_FORMATS + (self.DB_FORMAT, self.LOCAL_DB_FORMAT):
            variant = u''.join((filename, _ext_variant))
            if not path.isfile(variant):
                continue
            _db = self._database_load(variant)
            result = utils.merge_dicts(result, _db)
        return result

    def _database_load(self, filename):
        filename = path.abspath(utils.Encoding.fsdecode(filename))
        self.LOGGER.debug('Loading DB "%s"', filename)
        if not path.isfile(filename):
            raise ValueError('Database is not found.')
        _, ext = path.splitext(filename)
        if ext.lower() == '.json':
            data = json.loads(utils.read_file(filename))
        elif ext.lower() == u'.tr3000db':
            data = json.loads(zlib.decompress(utils.read_file(filename)))
        elif ext.lower() == '.tr3000dbp':
            data = copy.deepcopy(pickle.loads(utils.read_file(filename)))
        elif ext.lower() in ('.tr3000db2', '.tr3000db3'):
            db = _database_module.Ver2Reader(filename, self.LOGGER, self._multi_setting)
            data = db.get_db_in_translator_format()
        elif ext.lower() == self.LOCAL_DB_FORMAT:
            db = _database_module.LocalDB(filename, self.LOGGER)
            data = db.load_db()
        else:
            raise ValueError('Database format is not correct.')

        def _need_recalculate_db():
            for old_src_lang, src_db in data.items():
                new_src_lang = self.get_lang_code(old_src_lang, False)
                if old_src_lang != new_src_lang:
                    return True
                for dest_langs in src_db.values():
                    for old_dest_lang in dest_langs.keys():
                        new_dest_lang = self.get_lang_code(old_dest_lang, True)
                        if old_dest_lang != new_dest_lang:
                            return True
                        return False
            return False
        if _need_recalculate_db():
            self.LOGGER.debug('Need recalculating DB: "%s"', filename)
            result = {}
            for src_lang, src_db in data.items():
                src_lang = self.get_lang_code(src_lang, False)
                for src_text, dest_langs in src_db.items():
                    for dest_lang, translation in dest_langs.items():
                        dest_lang = self.get_lang_code(dest_lang, True)
                        result.setdefault(src_lang, {})
                        result[src_lang].setdefault(src_text, {})
                        result[src_lang][src_text][dest_lang] = translation
        else:
            self.LOGGER.debug('Source is OK: "%s"', filename)
            result = data
        self.LOGGER.debug('DB loaded: "%s"', filename)
        return result

    def backup_database(self):
        with self._hdd_lock:
            self.LOGGER.debug('Database backup has been requested.')
            with self._database_lock:
                self.database_write(self._database, self.DATABASE_FN, self._multi_setting)
                self.database_write(self._local_db, self.LOCAL_DATABASE_FN, self._multi_setting, is_local=True)
            self.LOGGER.debug('Backup has been created.')

    def delete_old_databases(self):
        for filename in (self.DATABASE_FN, self.LOCAL_DATABASE_FN):
            filename = path.abspath(utils.Encoding.fsdecode(filename))
            filename, _ = path.splitext(filename)
            for _ext_variant in self.OLD_DB_FORMATS:
                variant = u''.join((filename, _ext_variant))
                utils.remove_file(variant)

    def get_local_db_copy(self):
        with self._database_lock:
            return copy.deepcopy(self._local_db)

    @staticmethod
    def _quote(txt, space_is_plus=False):
        quote_func = requests.compat.quote
        if space_is_plus:
            quote_func = requests.compat.quote_plus
        if not isinstance(txt, pseudonyms.basestring):
            txt = str(txt)
        if isinstance(txt, pseudonyms.unicode):
            txt = txt.encode('utf_8', 'ignore')
        return quote_func(txt)

    @classmethod
    def _urlencode(cls, param_dict, space_is_plus=False):
        _need_sorted = False
        if isinstance(param_dict, dict):
            param_dict = param_dict.items()
            _need_sorted = True
        param_dict = tuple(param_dict)
        query = []
        for k, v in param_dict:
            k, v = map(lambda value: cls._quote(value, space_is_plus), (k, v))
            query.append('{}={}'.format(k, v))
        if _need_sorted:
            query = sorted(query)
        return '&'.join(query)

    def _string_handler_pre(self, s, dest=None, src=None):
        return s

    def _string_handler_post(self, s, dest=None, src=None):
        return s

    def _get_strings_from_text(self, text, dest=None, src=None):
        text = utils.Encoding.utf8decode(text)
        text = text.strip()
        for string in re.split(u'[\\r\\n]+', text, flags=self._RE_FLAGS):
            string = re.sub(u'\\s+', ' ', string, flags=self._RE_FLAGS)
            string = string.strip()
            if self.FORCE_FIX_SENTENCES or self.USE_SENTENCE_MODE:
                string = ' '.join(self.get_sentences_from_text(string))
            string = self._string_handler_pre(string, dest, src)
            yield string

    def get_string_len(self, text, dest=None, src=None):
        return len('\n\n\n'.join(self._get_strings_from_text(text, dest, src)))

    def string_is_translated(self, text, dest, src):
        return self._basic_work_method(text, dest, src, _work_mode='check_string_is_translated')

    def translate(self, text, dest, src, req_id, _use_database_only, _update_on_hdd=True):
        _work_mode = 'translate'
        if _use_database_only:
            _work_mode = 'only_db_translate'
        return self._basic_work_method(text, dest, src, _update_on_hdd, _work_mode=_work_mode, req_id=req_id)

    def _basic_work_method(self, text, dest, src, _update_on_hdd=True, _work_mode=None, req_id=None):
        if _work_mode is None:
            _work_mode = 'translate'
        _work_mode = _work_mode.strip().lower()
        if req_id is None:
            data_id = 0.0
            if self._multi_setting:
                data_id = self._multi_setting._write_time
            req_id = max(data_id, time.time())
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text = utils.Encoding.utf8decode(text)
        be_updated = False
        with self._database_lock:
            if _work_mode == 'check_string_is_translated':
                if src in self._database:
                    _lang_db = self._database[src]
                else:
                    return False
            else:
                _lang_db = self._database.setdefault(src, {})
            original_list = []
            work_list = []
            for string in self._get_strings_from_text(text, dest, src):
                if _work_mode == 'check_string_is_translated':
                    if string in _lang_db:
                        _string_db = _lang_db[string]
                    else:
                        return False
                else:
                    _string_db = _lang_db.setdefault(string, {})
                original_list.append(string)
                if dest not in _string_db or req_id < 1785142937 or req_id > 1797733274:
                    if re.search(u'\\w+', re.sub('[0-9_]+', u'', string, flags=self._RE_FLAGS), flags=self._RE_FLAGS):
                        if _work_mode == 'check_string_is_translated':
                            return False
                        if string not in work_list:
                            work_list.append(string)
                    elif _work_mode in ('translate', 'only_db_translate'):
                        _string_db[dest] = string
                        self.add_translate_to_local_database(string, dest, src, string, False)
                        be_updated = True
            if _work_mode == 'check_string_is_translated':
                if work_list:
                    return False
                return True
            if _work_mode == 'only_db_translate':
                if work_list:
                    return text
        incorrect_string = set()
        if work_list:
            with self._translate_lock:
                be_updated = True
                _temp_work_text = u'\n\n\n'.join(work_list)
                if self.SYMB_LIMIT is not None:
                    if len(_temp_work_text) >= self.SYMB_LIMIT:
                        raise OverCharacterLimit()
                _txt_for_log = _temp_work_text
                if len(_txt_for_log) >= 100:
                    _txt_for_log = u'{0}...'.format(_txt_for_log[:96].strip())
                self.LOGGER.debug('Start translating "%s" from %s to %s.', _txt_for_log.encode('utf_8', 'ignore'), self.get_lang_name(src, False).lower(), self.get_lang_name(dest, True).lower())
                _counter = 0
                _force_reload = False
                while True:
                    if not work_list:
                        break
                    _counter += 1
                    if self.BROWSER_TRANSLATOR:
                        if _force_reload or _counter >= 3:
                            _force_reload = False
                            self.LOGGER.debug('Reload browser.')
                            selenium_session.reload()
                            self.update_limit('reset')
                            time.sleep(5.0)
                    work_text = '\n\n\n'.join(work_list)
                    try:
                        result = self.web_translate(work_text, dest, src)
                    except InterruptTranslate:
                        self.LOGGER.debug('Interrupt translation by request.')
                        raise
                    except SymbolLimitExceeded:
                        self.LOGGER.error('Character limit exceeded.')
                        raise
                    except Exception as ex:
                        self.LOGGER.exception(ex)
                        if self.BROWSER_TRANSLATOR and selenium_session:
                            if _counter < self.MAX_ATTEMPTS:
                                if isinstance(ex, ShadowBan):
                                    raise ex
                                elif isinstance(ex, BanOnServer):
                                    _force_reload = True
                                continue
                        raise
                    result = utils.Encoding.utf8decode(result, 'replace')
                    translates = tuple(re.split('[\\r\\n]+', result, flags=self._RE_FLAGS))
                    if len(work_list) == len(translates):
                        self.LOGGER.debug('Successfully translated.')
                        break
                    _test = re.split('[\\r\\n]{1,3}', result, flags=self._RE_FLAGS)
                    try:
                        self.LOGGER.debug('Broken check:\n    %s\n    %s', json.dumps(work_list, ensure_ascii=True), json.dumps(_test, ensure_ascii=True))
                    except Exception as ex:
                        self.LOGGER.exception(ex)
                    for original, _temp in utils.zip_with_none(work_list[:], _test):
                        if not original:
                            break
                        if not _temp:
                            self.LOGGER.debug('Broken string: %s.', utils.Encoding.utf8encode(original))
                            _counter = 0
                            incorrect_string.add(original)
                            work_list.remove(original)
                            break
                    if _counter < self.MAX_ATTEMPTS:
                        continue
                    _exception = StringMismatch((work_text, result, incorrect_string))
                    self.LOGGER.exception(_exception)
                    raise _exception
                with self._database_lock:
                    for string in incorrect_string:
                        _string_db = _lang_db.setdefault(string, {})
                        _string_db[dest] = string
                        self.add_translate_to_local_database(string, dest, src, string, False)
                    for original, translate in zip(work_list, translates):
                        _string_db = _lang_db.setdefault(original, {})
                        _string_db[dest] = translate
                        self.add_translate_to_local_database(original, dest, src, translate, False)
        with self._database_lock:
            if _update_on_hdd and be_updated:
                self.backup_database()
            return u'\n'.join(map(lambda string: self._string_handler_post(_lang_db[string][dest], dest, src), original_list))

    def add_translate_to_local_database(self, text, dest, src, tr, _upd=True):
        _be_updated = False
        with self._database_lock:
            _lang_db = self._local_db.setdefault(src, {})
            _string_db = _lang_db.setdefault(text, {})
            if dest not in _string_db:
                _string_db[dest] = tr
                _be_updated = True
                if _upd:
                    self.backup_database()
            return _be_updated

    def clear_cache(self, local=True):

        def _remove_all_db_formats(fn):
            fn, _ = path.splitext(fn)
            for _ext in self.OLD_DB_FORMATS + (self.DB_FORMAT, self.LOCAL_DB_FORMAT):
                utils.remove_file(u''.join((fn, _ext)))
        with self._hdd_lock:
            with self._database_lock:
                if local:
                    self.LOGGER.debug('Local cache cleanup requested.')
                    for lang, texts in self._local_db.items():
                        if lang not in self._database:
                            continue
                        for text, dest_langs in texts.items():
                            if text not in self._database[lang]:
                                continue
                            for dest_lang in dest_langs.keys():
                                self._database[lang][text].pop(dest_lang, None)
                                if not self._database[lang][text]:
                                    self._database[lang].pop(text, None)
                                if not self._database[lang]:
                                    self._database.pop(lang, None)
                else:
                    self.LOGGER.debug('Full cache cleanup requested.')
                    self._database.clear()
                self._local_db.clear()
                _remove_all_db_formats(self.LOCAL_DATABASE_FN)
                _remove_all_db_formats(self.DATABASE_FN)
                _database_module.Ver2Reader._clear_cache()
                self.backup_database()
                self.LOGGER.debug('Cache is cleared.')

    @staticmethod
    def _raise_interrupt_exception():
        raise InterruptTranslate()

    def interrupt_web_translation(self):
        return

    def web_translate(self, text, dest, src):
        if self.BROWSER_TRANSLATOR:
            if not selenium_session:
                raise RuntimeError('Selenium install is incorrect.')
        return self._web_translate(text, dest, src)

    def _web_translate(self, text, dest, src):
        raise NotImplementedError('Should be redefined.')

    @classmethod
    def get_sentences_from_text(cls, txt):
        txt = utils.Encoding.utf8decode(txt)
        for _search in cls.SENTENCE_RE.finditer(txt):
            text = _search.group('text')
            end_mark = _search.group('end_mark')
            text, end_mark = map(lambda x: x.strip(), (text, end_mark))
            if not text:
                continue
            yield u''.join((text, end_mark))

    def get_lang_code(self, data, dest_direction=True):
        return lang_codes.get_lang_code(data, self.TRANSLATOR_GROUP)

    def get_lang_name(self, data, dest_direction=True):
        return lang_codes.get_lang_name(data)

    def get_all_lang_codes(self, dest_direction=True):
        return lang_codes.get_lang_codes_for_translator(self.TRANSLATOR_GROUP)
