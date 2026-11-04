import os
import re
import json
import base64
import tarfile
import random
import threading
import subprocess
from os import path
from . import _paths, _selenium_handler, utils, pseudonyms
try:
    import rsa
except ImportError:
    rsa = None
if hasattr(subprocess, 'CREATE_NO_WINDOW'):
    CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW
else:
    CREATE_NO_WINDOW = 134217728
_ALTREPO_KEY = '''
-----BEGIN RSA PRIVATE KEY-----
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
usDBWsM6NM+gEY4=
-----END RSA PRIVATE KEY-----
'''.strip()
ALTREPO_KEY = None
if rsa:
    ALTREPO_KEY = rsa.PrivateKey.load_pkcs1(_ALTREPO_KEY)

def _decrypt(data):
    if not (rsa and ALTREPO_KEY):
        return None
    data = base64.b64decode(data)
    data1, data2 = data[:512], data[512:]
    data1 = rsa.decrypt(data1, ALTREPO_KEY)
    data = data1 + data2
    data = base64.b64decode(data)
    return data


class ServiceBlocked(Exception):
    MSG = 'Probably "autoproxies" site blocked by your internet service provider. Specify the path to the folder manually.'
    USE_ALT_MSG = 'Probably "autoproxies" site blocked by your internet service provider. Try to use alternate repo.'

    def __init__(self, *args, **kwargs):
        return super(ServiceBlocked, self).__init__(self.MSG, *args, **kwargs)


class TorHandler(object):
    __author__ = 'Vladya'
    LOGGER = None
    SKIP_MAIN_REPO = True
    IP = '127.0.0.1'
    PORTS_OPEN = 15
    USE_BRIDGES = u'meek-azure', u'meek', u'snowflake'
    BUNDLES_DIR = path.join(_paths.TOR_FOLDER, u'bundles')
    STATUS_FILE_NAME = u'bundle_status.status'
    STATUS_OK = 'OKver.1'
    MAIN_REPO = u'https://archive.torproject.org/tor-package-archive/torbrowser/'
    DIR_HREF_PATTERN = re.compile(u'''
            <a\\s+href="(?P<href>[0-9a-z./\\-_]+)">
                (?P<name>\\d+\\.?\\d*\\.?\\d*)/?
            </a>
        ''', flags=re.UNICODE | re.IGNORECASE | re.VERBOSE)
    _name_pattern_string = u'''
        (?P<name>
            tor-expert-bundle
            -
            (?P<os>(windows|linux|macos))
            -
            (?P<processor>\\w+)
            -
            \\d+\\.?\\d*\\.?\\d*
            \\.tar\\.gz
        )
    '''
    NAME_ONLY_PATTERN = re.compile(_name_pattern_string, flags=re.UNICODE | re.IGNORECASE | re.VERBOSE)
    BUNDLE_NAME_PATTERN = re.compile(u'''
            <a\\s+href="(?P<href>[0-9a-z./\\-_]+)">
                {0}
            </a>
        '''.format(_name_pattern_string), flags=re.UNICODE | re.IGNORECASE | re.VERBOSE)
    ALTERNATE_REPO = u'https://api.vladya.net/tBundles/versionsSummary'
    BOOTSTRAP_PATTERN = re.compile(u'Bootstrapped\\s+(?P<perc>\\d+)%')
    LOG_PATTERN = re.compile(u'\\[(?P<level>\\w+)\\]\\s+(?P<msg>.*)$')
    single_instance = None
    is_initialized = False
    mode = False

    def __new__(cls, session=None, logger=None):
        if cls.single_instance is None:
            cls.single_instance = super(TorHandler, cls).__new__(cls)
        return cls.single_instance

    def __init__(self, session=None, logger=None):
        if self.is_initialized:
            return
        self.__session = session
        self.LOGGER = logger.getChild('AutoProxiesHandler')
        self.__file_lock = threading.RLock()
        self.__bundle_directory = None
        self.__torcc = None
        self.__process_lock = threading.RLock()
        self.__process = None
        self.__ports_counter = None
        self.is_initialized = True

    @property
    def process_lock(self):
        return self.__process_lock

    @property
    def process(self):
        with self.__process_lock:
            return self.__process

    def get_adress(self, switch_ip=True):
        with self.__process_lock:
            if not self.is_running():
                return None
            if switch_ip == 'chrome':
                port = 9050
            else:
                if self.__ports_counter is None:
                    self.__ports_counter = 0
                elif switch_ip:
                    self.__ports_counter += 1
                self.__ports_counter %= self.PORTS_OPEN
                port = 9052 + self.__ports_counter
            return u'socks5://{0}:{1}'.format(self.IP, port)

    def __del__(self):
        self.quit()

    def is_running(self):
        with self.__process_lock:
            if not self.__process:
                return False
            if self.__process.poll() is not None:
                return False
            return True

    def quit(self):
        with self.__process_lock:
            if self.process:
                self.process.stdout.close()
                self.process.stderr.close()
                self.process.terminate()
                self.process.kill()
                self.process.wait()

    def _restart_process(self, custom_bridges=None):
        with self.__process_lock:
            self.quit()
            self._init_tor_process(custom_bridges=custom_bridges)

    def _init_tor_process(self, check_already_run=True, custom_bridges=None):
        with self.__process_lock:
            if check_already_run and self.is_running():
                return
            if custom_bridges is None:
                torcc = self.torcc
            else:
                with self.__file_lock:
                    torcc = self.__get_torcc_fn(custom_bridges)
            _args = self.tor_executable, u'-f', torcc
            _kwargs = {'stdout': subprocess.PIPE, 'stdin': subprocess.PIPE, 'stderr': subprocess.PIPE}
            ChromeFinder = _selenium_handler.driver_finder.ChromeFinder
            _, system_name, _ = ChromeFinder.get_system_name()
            if system_name == 'win':
                _kwargs['creationflags'] = CREATE_NO_WINDOW
            LOGGER = self.LOGGER.getChild('AutoProxiesProcess')
            tor_process = subprocess.Popen(_args, **_kwargs)
            last_problem = u'Timed out'
            try:
                while True:
                    init_line = utils.Encoding.utf8decode(tor_process.stdout.readline(), 'replace').strip()
                    if not init_line:
                        raise RuntimeError(last_problem)
                    bootstrap_match = self.BOOTSTRAP_PATTERN.search(init_line)
                    log_str = self.LOG_PATTERN.search(init_line)
                    logger_func = LOGGER.info
                    msg = init_line
                    if log_str:
                        level = log_str.group('level')
                        msg = log_str.group('msg')
                        if level == 'warn':
                            logger_func = LOGGER.warning
                            last_problem = msg
                        elif level == 'err':
                            logger_func = LOGGER.error
                            last_problem = msg
                        elif level == 'notice':
                            logger_func = LOGGER.info
                        else:
                            msg = init_line
                    logger_func(msg)
                    if bootstrap_match:
                        state = int(bootstrap_match.group(u'perc'))
                        if state >= 100:
                            break
            except Exception:
                tor_process.stdout.close()
                tor_process.stderr.close()
                tor_process.terminate()
                tor_process.kill()
                tor_process.wait()
                raise
            else:
                self.__process = tor_process

    @property
    def tor_executable(self):
        with self.__file_lock:
            for variant in os.listdir(self.bin_directory):
                variant = path.join(self.bin_directory, variant)
                if not path.isfile(variant):
                    continue
                name, _ = path.splitext(path.basename(variant))
                if name.lower() == u'autoproxies':
                    return variant
            raise RuntimeError('No "autoProxies" exe was found')

    @property
    def torcc(self):
        with self.__file_lock:
            if self.__torcc is not None:
                if path.isfile(self.__torcc):
                    return self.__torcc
            self.__torcc = self.__get_torcc_fn()
            return self.__torcc

    @property
    def bundle_directory(self):
        with self.__file_lock:
            if self.__bundle_directory is not None:
                if path.isdir(self.__bundle_directory):
                    return self.__bundle_directory
            self.__bundle_directory = self.__get_bundle_dir()
            return self.__bundle_directory

    @property
    def bin_directory(self):
        with self.__file_lock:
            return path.join(self.bundle_directory, u'autoProxies')

    @property
    def data_directory(self):
        with self.__file_lock:
            return path.join(self.bundle_directory, u'data')

    @property
    def pluggable_transports_directory(self):
        with self.__file_lock:
            return path.join(self.bin_directory, u'pluggable_transports')

    def __get_bundle_dir(self):
        self.LOGGER.debug('Searching for bundles.')
        local_max, local_dir_name = self._get_max_local_versions()
        if local_max:
            self.LOGGER.debug('Found version %s on local storage', local_max)
        self.LOGGER.debug('Check last version on repo.')
        try:
            last_version, href, fn, is_alt = self.__get_last_version_data()
        except Exception as ex:
            if local_max:
                self.LOGGER.exception(ex)
                self.LOGGER.error('Unsuccessful. Use local version.')
                return local_dir_name
            self.LOGGER.error('Repo check failed. No local version detected.')
            raise
        if last_version == local_max:
            self.LOGGER.debug('Local version is up to date.')
            return local_dir_name
        self.LOGGER.debug('Version %s has been found. Trying to download.', last_version)
        version_dir = path.join(self.BUNDLES_DIR, u'.'.join(map(pseudonyms.unicode, last_version)))
        out_filename = path.join(version_dir, fn.replace(u'tor', u'autoProx'))
        utils.remove_dir(version_dir)
        try:
            self.__session.get(href, _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None, _download_to=out_filename)
        except Exception as ex:
            if local_max:
                self.LOGGER.exception(ex)
                self.LOGGER.error('Unsuccessful. Use local version.')
                return local_dir_name
            raise
        self.LOGGER.debug('Download was successful. Unpacked.')
        if is_alt:
            data = utils.read_file(out_filename)
            data = _decrypt(data)
            if data is None:
                raise RuntimeError('No necessary module was found.')
            utils.save_data_to_file(data, out_filename)
        utils.create_dir(version_dir)
        utils.set_executable_flags(version_dir)
        with tarfile.open(out_filename, 'r') as _tarfile:
            for _tarinfo in _tarfile.getmembers():
                if not _tarinfo.isfile():
                    continue
                fo = _tarfile.extractfile(_tarinfo)
                if not fo:
                    continue
                bytes_data = fo.read()
                fo.close()
                fn = path.normpath(utils.Encoding.utf8decode(_tarinfo.name))
                fn = fn.replace(u'tor', u'autoProxies')
                _dest = path.abspath(path.join(version_dir, fn))
                utils.save_data_to_file(bytes_data, _dest)
        utils.remove_file(out_filename)
        _check_file = path.abspath(path.join(version_dir, self.STATUS_FILE_NAME))
        utils.save_data_to_file(self.STATUS_OK, _check_file)
        self.LOGGER.debug('Unpacked was successful. Done.')
        return version_dir

    def _get_max_local_versions(self):
        if not path.isdir(self.BUNDLES_DIR):
            return (None, None)
        max_version = None
        dir_name = None
        for version in os.listdir(self.BUNDLES_DIR):
            _vr = re.search(u'\\d+\\.?\\d*\\.?\\d*', version)
            if not _vr:
                continue
            _version = tuple(map(int, _vr.group().split('.')))
            if max_version is None or _version > max_version:
                _check_file = path.abspath(path.join(self.BUNDLES_DIR, version, self.STATUS_FILE_NAME))
                if not path.isfile(_check_file):
                    continue
                if utils.read_file(_check_file) != self.STATUS_OK:
                    continue
                max_version = _version
                dir_name = path.abspath(path.join(self.BUNDLES_DIR, version))
        return (max_version, dir_name)

    def __get_last_version_data(self):
        ChromeFinder = _selenium_handler.driver_finder.ChromeFinder
        bits, sys_name, _mac_m1 = ChromeFinder.get_system_name()
        sys_name = {u'win': u'windows', u'linux': u'linux', u'mac': u'macos'}.get(sys_name)
        if sys_name == u'macos' and _mac_m1:
            arch = u'aarch64'
        else:
            arch = {64: u'x86_64', 32: u'i686'}.get(bits)
        if not self.SKIP_MAIN_REPO:
            try:
                result = self.__get_last_version_data_official(sys_name, arch)
            except ServiceBlocked:
                self.LOGGER.error(ServiceBlocked.USE_ALT_MSG)
            except Exception:
                raise
            else:
                return result + (False,)
        return self.__get_last_version_data_alt(sys_name, arch) + (True,)

    def __get_last_version_data_alt(self, sys_name, arch):
        resp = self.__session.get(self.ALTERNATE_REPO, _force_rpm=9999.0, _use_tor=False, _set_translator_useragent=True, _ranged_request=None)
        data = _decrypt(resp.content)
        if data is None:
            raise RuntimeError('Not found version for {0} ({1})'.format(sys_name, arch))
        versions = json.loads(data)

        def _key(arg):
            version, _ = arg
            return tuple(map(int, version.split(u'.')))
        for _ver, bundles in sorted(versions.items(), key=_key, reverse=True):
            version = _key((_ver, bundles))
            for name, url in bundles.items():
                _bundle = self.NAME_ONLY_PATTERN.search(name)
                if sys_name != _bundle.group(u'os'):
                    continue
                if arch != _bundle.group(u'processor'):
                    continue
                return (version, url, name)
        raise RuntimeError('Not found version for {0} ({1})'.format(sys_name, arch))

    def __get_last_version_data_official(self, sys_name, arch):
        try:
            resp = self.__session.get(self.MAIN_REPO, _force_rpm=9999.0, _use_tor=False, timeout=3.0, _ranged_request=None)
        except Exception:
            raise ServiceBlocked()
        max_version = None
        href = None
        for _version in self.DIR_HREF_PATTERN.finditer(resp.text):
            version = tuple(map(int, _version.group(u'name').split('.')))
            if max_version is None or version > max_version:
                href = _version.group(u'href')
                max_version = version
        assert max_version
        assert href
        url = utils.urljoin(self.MAIN_REPO, href)
        try:
            resp = self.__session.get(url, _force_rpm=9999.0, _use_tor=False, timeout=3.0, _ranged_request=None)
        except Exception:
            raise ServiceBlocked()
        for _bundle in self.BUNDLE_NAME_PATTERN.finditer(resp.text):
            if sys_name != _bundle.group(u'os'):
                continue
            if arch != _bundle.group(u'processor'):
                continue
            return (max_version, utils.urljoin(url, _bundle.group(u'href')), _bundle.group(u'name'))
        raise RuntimeError('Not found version for {0} ({1})'.format(sys_name, arch))

    def __get_torcc_fn(self, custom_bridges=None):

        def q(t):
            t = path.abspath(t)
            t = t.replace(u'\\', u'\\\\')
            return t
        torcc_fn = path.join(_paths.TOR_FOLDER, u'temp', u'autoProxConf{0}'.format(u'Custom' if custom_bridges else u''))
        pt_config_path = path.join(self.pluggable_transports_directory, u'pt_config.json')
        pt_config = utils.read_json_from_file(pt_config_path, compressed=False)
        torcc_params = []
        assert self.PORTS_OPEN > 0, self.PORTS_OPEN
        for p in range(self.PORTS_OPEN + 2):
            port = 9050 + p
            if port == 9051:
                continue
            torcc_params.append(u'SocksPort {0}:{1} NoOnionTraffic'.format(self.IP, port))
        torcc_params += [u'DataDirectory "{0}"'.format(q(self.data_directory)), u'GeoIPFile "{0}"'.format(q(path.join(self.data_directory, u'geoip'))), u'GeoIPv6File "{0}"'.format(q(path.join(self.data_directory, u'geoip6'))), u'ClientOnly 1', u'CellStatistics 0', u'PaddingStatistics 0', u'DirReqStatistics 0', u'EntryStatistics 0', u'ExitPortStatistics 0', u'ConnDirectionStatistics 0', u'HiddenServiceStatistics 0', u'ExtraInfoStatistics 0', u'UseBridges 1']
        for _config_string in pt_config[u'pluggableTransports'].values():
            parts = tuple(re.split(u'\\s+', _config_string))
            _command, transports, _exec, path_to_exe = parts[:4]
            options = parts[4:]
            path_to_exe = q(path.join(self.pluggable_transports_directory, path_to_exe.replace(u'${pt_path}', u'')))
            for transport in re.split(u',', transports):
                torcc_params.append(u' '.join((_command, transport, _exec, path_to_exe) + options))
        if custom_bridges:
            for bridge in custom_bridges:
                torcc_params.append(u'Bridge {0}'.format(bridge))
        else:
            for bridge_name in self.USE_BRIDGES:
                if bridge_name not in pt_config[u'bridges']:
                    continue
                bridges = pt_config[u'bridges'][bridge_name]
                _bridges_variants = []
                for bridge in bridges:
                    _bridges_variants.append(u'Bridge {0}'.format(bridge))
                for _ in range(random.randint(1, 3)):
                    if not _bridges_variants:
                        break
                    bridge = random.choice(_bridges_variants)
                    torcc_params.append(bridge)
                    _bridges_variants.remove(bridge)
        utils.remove_file(torcc_fn)
        utils.save_data_to_file(u'\n'.join(torcc_params), torcc_fn)
        return torcc_fn

