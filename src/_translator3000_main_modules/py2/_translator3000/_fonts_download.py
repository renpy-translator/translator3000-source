import os
import requests
import threading
from os import path
from . import utils, _paths, lang_codes


class FontStorage(object):
    __author__ = 'Vladya'
    BASE_URL = u'https://api.vladya.net'
    MAPPING = u'fonts_for_langs/lang_info.json'
    FONTS_FOLDER = path.join(_paths.DATABASE_FOLDER, 'fonts_storage')
    available_font_exts = frozenset(('.ttf', '.ttc', '.otf'))

    def __init__(self, session_object, logger):
        self.__lang_info = None
        self.__lock = threading.RLock()
        self.__logger = logger.getChild('FontStorage')
        self.__session = session_object

    @property
    def lang_info(self):
        with self.__lock:
            if self.__lang_info is None:
                loc_copy = path.join(self.FONTS_FOLDER, u'lang_info.tr3000_data')
                try:
                    self.__logger.debug('Try to download font mapping.')
                    _url = requests.compat.urljoin(self.BASE_URL, self.MAPPING)
                    resp = self.__session.get(_url, _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
                    result = resp.json()
                except Exception as ex:
                    self.__logger.exception(ex)
                    result = None
                else:
                    utils.write_json_to_file(result, loc_copy, compress=True, backup_original=True, indent=None)
                    self.__logger.debug('Succesfully.')
                if result is None:
                    self.__logger.debug('Try to found local backup on PC.')
                    if path.isfile(loc_copy):
                        try:
                            result = utils.read_json_from_file(loc_copy, compressed=True)
                        except Exception as ex:
                            self.__logger.error('Backup is broken.')
                            self.__logger.exception(ex)
                            result = None
                        else:
                            self.__logger.debug('Local backup was found.')
                    else:
                        self.__logger.error('No backup was found.')
                if result:
                    self.__lang_info = result
            return self.__lang_info

    def get_font(self, lang_name):
        lang_name = lang_codes.get_lang_name(lang_name)
        storage = path.join(self.FONTS_FOLDER, lang_name)

        def _get_font_name(font_fn):
            return path.abspath(path.join(storage, path.basename(path.normpath(font_fn.replace(u'\\', u'/')))))

        def _get_correct_lang_names(_lang_array):
            for lng_data in _lang_array:
                try:
                    lng_name = lang_codes.get_lang_name(lng_data)
                except Exception:
                    continue
                else:
                    yield lng_name
        with self.__lock:
            if self.lang_info:
                _fonts = set()
                for font_name, font_data in self.lang_info[u'fonts'].items():
                    _lngs = frozenset(_get_correct_lang_names(font_data[u'langs']))
                    if lang_name in _lngs:
                        _fonts.add(font_name)
                if not _fonts:
                    self.__logger.debug('No font is suitable for the selected language. Use the standard font.')
                    _fonts.add(self.lang_info['default'])
                for font_name in _fonts:
                    self.__logger.debug('Check local copy for font %s', font_name)
                    loc_copy = _get_font_name(self.lang_info[u'fonts'][font_name][u'filename'])
                    if path.isfile(loc_copy):
                        self.__logger.debug('Font %s is found.', font_name)
                        return loc_copy
                self.__logger.debug('No local copy was found. Try to download.')
                for font_name in _fonts:
                    self.__logger.debug('Try download: "%s".', font_name)
                    fn = self.lang_info[u'fonts'][font_name][u'filename']
                    _url = requests.compat.urljoin(self.BASE_URL, fn)
                    loc_copy = _get_font_name(fn)
                    try:
                        self.__logger.debug('Start downloading: "%s".', font_name)
                        self.__session.get(_url, _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None, _download_to=loc_copy)
                    except Exception as ex:
                        self.__logger.exception(ex)
                        continue
                    else:
                        self.__logger.debug('Succesful.')
                        return loc_copy
                self.__logger.error('Error on download. Attempting to search for available options.')
            else:
                self.__logger.error('Font mapping is not available. Search for local copies.')
            if path.isdir(storage):
                for fn in sorted(os.listdir(storage)):
                    fn = path.abspath(path.join(storage, fn))
                    if path.isfile(fn):
                        _ext = utils.get_ext(fn)
                        if _ext in self.available_font_exts:
                            self.__logger.debug('Found "%s". Try to use it.', path.basename(fn))
                            return fn
            raise RuntimeError('Unable to load the font file.')

