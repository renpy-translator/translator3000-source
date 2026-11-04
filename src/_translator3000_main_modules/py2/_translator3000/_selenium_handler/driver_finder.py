import os
import re
import subprocess
import platform
import zipfile
from os import path
from .. import _paths, utils, pseudonyms


class SystemIsNotSupported(Exception):
    pass


class ChromeNotInstall(Exception):
    pass


class ChromeFinder(object):
    __author__ = 'Vladya'
    SEATCH_PATTERN = re.compile('\\d+\\.\\d+\\.\\d+\\.\\d+')
    WINDOWS_REG_KEY = 'HKLM\\SOFTWARE\\Wow6432Node\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Google Chrome'
    WINDOWS_CREATE_NO_WINDOW_FLAG = 134217728
    CHROME_DRIVERS_FOLDER = path.join(_paths.SELENIUM_FOLDER, u'chromedriver')
    LAST_VERSION_URL_OLD = u'https://chromedriver.storage.googleapis.com/LATEST_RELEASE_{0}'
    DOWNLOAD_URL_OLD = u'https://chromedriver.storage.googleapis.com/{version}/{filename}'
    GET_DOWNLOAD_URLS_URL = u'https://googlechromelabs.github.io/chrome-for-testing/{version}.json'
    GET_DOWNLOAD_URLS_URL_MIRROR = u'https://api.vladya.net/chromedriver.php?method=GET_DOWNLOAD_URLS_URL&version={version}&extra=1'
    VERSION_PER_BUILD = u'https://googlechromelabs.github.io/chrome-for-testing/latest-patch-versions-per-build-with-downloads.json'
    VERSION_PER_BUILD_MIRROR = u'https://api.vladya.net/chromedriver.php?method=VERSION_PER_BUILD&extra=1'
    USE_RECURSIVE_DOWNGRADE_IN_VERSION_CHOISING = True

    def __init__(self, session, logger):
        self.__session = session
        self._logger = logger.getChild('ChromeFinder')

    def get_executable(self, need_version=None):
        executable = self.__get_executable(need_version=need_version)
        utils.set_executable_flags(executable)
        return executable

    def __get_executable(self, need_version=None):

        def find_executable(directory):
            if not path.isdir(directory):
                return None
            for fn in os.listdir(directory):
                fn = path.join(directory, fn)
                if not path.isfile(fn):
                    continue
                basename, _ = path.splitext(path.basename(fn))
                if basename == u'chromedriver':
                    return fn
            return None
        if need_version is None:
            need_version = self.detect_chrome_version()
        major, minor, build, _ = need_version
        text_version = u'.'.join(map(pseudonyms.unicode, (major, minor, build)))
        self._logger.debug('GoogleChrome version: %s.', text_version)
        version_folder = path.join(self.CHROME_DRIVERS_FOLDER, text_version)

        def get_versions(_downgrade=True):
            _current_major = major
            yield text_version, _current_major
            while True:
                yield pseudonyms.unicode(_current_major), _current_major
                if not _downgrade:
                    break
                _current_major -= 1
                if _current_major <= 70:
                    break
        last_version = None
        builds_mapping = None
        _urls_list = None
        try:
            _exception = Exception('Undefined error')
            for version_variant, _current_major in get_versions(_downgrade=self.USE_RECURSIVE_DOWNGRADE_IN_VERSION_CHOISING):
                if _current_major <= 70:
                    raise RuntimeError('Too old chrome version')
                elif _current_major < 115:
                    try:
                        resp = self.__session.get(self.LAST_VERSION_URL_OLD.format(version_variant), _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
                    except Exception as ex:
                        self._logger.exception(ex)
                        _exception = ex
                    else:
                        last_version = resp.text
                        self._logger.debug("Last available 'chomedriver' version: %s.", last_version)
                        break
                    continue
                if builds_mapping is None:
                    resp = self.__session.get(self.VERSION_PER_BUILD, _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _extra_mirrors=(self.VERSION_PER_BUILD_MIRROR,), _ranged_request=None)
                    versions_mapping = resp.json()
                    builds_mapping = {}
                    for _ver, data in versions_mapping[u'builds'].items():
                        if u'downloads' not in data:
                            continue
                        if u'chromedriver' not in data[u'downloads']:
                            continue
                        maj_ver = int(_ver.split(u'.')[0])
                        builds_mapping.setdefault(maj_ver, {})[_ver] = data
                if _current_major not in builds_mapping:
                    continue
                if version_variant in builds_mapping[_current_major]:
                    data = builds_mapping[_current_major][version_variant]
                else:
                    _max_version = max(builds_mapping[_current_major].keys())
                    data = builds_mapping[_current_major][_max_version]
                last_version = data[u'version']
                _urls_list = data[u'downloads'][u'chromedriver']
                break
            else:
                raise _exception
        except Exception as ex:
            self._logger.exception(ex)
            last_version = None
            _urls_list = None
        if last_version:
            folder = path.join(version_folder, last_version)
            executable = find_executable(folder)
            if executable:
                self._logger.debug('File is already on the disk.')
                return executable
            try:
                zip_arch = self._download_version(last_version, folder, _urls_list)
                executable = self.save_driver_from_zip(zip_arch, folder)
            except Exception as ex:
                self._logger.exception(ex)
                _exception = ex
            else:
                utils.remove_file(zip_arch)
                self._logger.debug('The new version has been uploaded.')
                return executable
        if not path.isdir(version_folder):
            raise _exception
        for variant in sorted(os.listdir(version_folder), reverse=True):
            variant = path.join(version_folder, variant)
            executable = find_executable(variant)
            if executable:
                self._logger.debug('Suitable version was found.')
                return executable
        raise _exception

    @classmethod
    def save_driver_from_zip(cls, zipname, save_directory):
        zipname, save_directory = map(lambda x: path.abspath(utils.Encoding.fsdecode(x, 'strict')), (zipname, save_directory))
        assert path.isfile(zipname)
        with open(zipname, 'rb') as _file, zipfile.ZipFile(_file) as _zip:
            for _orig_name in _zip.namelist():
                orig_name = path.basename(path.normpath(utils.Encoding.fsdecode(_orig_name, 'strict')))
                check_name, _ = path.splitext(orig_name)
                if check_name.lower() == 'chromedriver':
                    write_name = path.join(save_directory, orig_name)
                    with _zip.open(_orig_name) as _drv:
                        utils.save_data_to_file(_drv, write_name)
                        return write_name
            raise Exception('No driver was found.')

    def _download_version(self, version, out_folder, _urls_list=None):
        bits, system_name, mac_m1 = self.get_system_name()
        system_name = utils.Encoding.utf8decode(system_name, 'strict')
        version = utils.Encoding.utf8decode(version, 'strict')
        out_folder = path.abspath(utils.Encoding.fsdecode(out_folder, 'strict'))
        bits_variants = 32,
        if bits == 64:
            bits_variants = 64, 32
        mac_m1_variants = None,
        if mac_m1 is True:
            mac_m1_variants = True, False
        elif mac_m1_variants is False:
            mac_m1_variants = False,
        last_version_major = int(version.split(u'.')[0])
        if last_version_major >= 115 and not _urls_list:
            resp = self.__session.get(self.GET_DOWNLOAD_URLS_URL.format(version=version), _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _extra_mirrors=(self.GET_DOWNLOAD_URLS_URL_MIRROR.format(version=version),), _ranged_request=None)
            _answer = resp.json()
            _urls_list = _answer[u'downloads'][u'chromedriver']
        template = u'chromedriver_{0}.zip'
        _exception = Exception('Undefined error.')
        for _mac_m1 in mac_m1_variants:
            for _bits in bits_variants:
                if _urls_list:
                    if system_name == u'mac':
                        if _mac_m1:
                            variant = u'{0}-arm{1}'.format(system_name, _bits)
                        else:
                            variant = u'{0}-x{1}'.format(system_name, _bits)
                    else:
                        variant = u'{0}{1}'.format(system_name, _bits)
                    url = None
                    filename = template.format(variant)
                    for _url_var in _urls_list:
                        if variant == _url_var[u'platform']:
                            url = _url_var[u'url']
                            break
                    else:
                        _exception = Exception('No version was found.')
                        continue
                elif last_version_major >= 115:
                    raise RuntimeError('Logic error.')
                else:
                    variant = u'{0}{1}'.format(system_name, _bits)
                    if _mac_m1:
                        variant += u'_m1'
                    filename = template.format(variant)
                    url = self.DOWNLOAD_URL_OLD.format(version=version, filename=filename)
                out_filename = path.join(out_folder, filename)
                try:
                    self.__session.get(url, _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None, _download_to=out_filename)
                except Exception as ex:
                    _exception = ex
                    continue
                else:
                    return out_filename
        raise _exception

    @staticmethod
    def get_system_name():
        bits = 32
        system_name = None
        mac_m1 = None
        _bits, _ = platform.architecture()
        if '64' in _bits:
            bits = 64
        _system_name = platform.system()
        if _system_name == 'Windows':
            system_name = 'win'
        elif platform.mac_ver()[0]:
            system_name = 'mac'
            mac_m1 = False
            processor = platform.processor()
            if 'm1' in processor.lower().split():
                mac_m1 = True
        elif _system_name == 'Linux':
            system_name = 'linux'
        return (bits, system_name, mac_m1)

    @classmethod
    def detect_chrome_version(cls):
        try:
            text_version = cls._detect_chrome_version()
        except SystemIsNotSupported:
            raise
        except Exception as ex:
            raise ChromeNotInstall(*ex.args)
        major, minor, build, patch = map(int, text_version.split('.'))
        return (major, minor, build, patch)

    @classmethod
    def _detect_chrome_version(cls):
        _, system_name, _ = cls.get_system_name()
        if system_name == 'win':
            return cls._detect_on_windows()
        elif system_name == 'linux':
            return cls._detect_on_linux()
        elif system_name == 'mac':
            return cls._detect_on_mac()
        raise SystemIsNotSupported()

    @classmethod
    def _detect_on_mac(cls):
        app = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        process = subprocess.Popen((app, '--version'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata = utils._process_communicate(process, None, True)
        version = cls.SEATCH_PATTERN.search(stdoutdata)
        if not version:
            raise RuntimeError(stdoutdata)
        return version.group()

    @classmethod
    def _detect_on_linux(cls):
        _exception = Exception('Undefined error.')
        for app_name in ('google-chrome', 'google-chrome-stable'):
            try:
                process = subprocess.Popen((app_name, '--version'), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdoutdata = utils._process_communicate(process, None, True)
            except Exception as ex:
                _exception = ex
                continue
            version = cls.SEATCH_PATTERN.search(stdoutdata)
            if not version:
                raise RuntimeError(stdoutdata)
            return version.group()
        raise _exception

    @classmethod
    def _detect_on_windows(cls):
        process = subprocess.Popen(('reg', 'query', cls.WINDOWS_REG_KEY, '/v', 'Version', '/t', 'REG_SZ'), creationflags=cls.WINDOWS_CREATE_NO_WINDOW_FLAG, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdoutdata = utils._process_communicate(process, WindowsError, True)
        version = cls.SEATCH_PATTERN.search(stdoutdata)
        if not version:
            raise RuntimeError(stdoutdata)
        return version.group()

