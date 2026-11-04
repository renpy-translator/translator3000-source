import os
import time
import stat
import sys
import copy
import json
import zlib
import urllib3
import codecs
import hashlib
import re
import shutil
import posixpath
import threading
from os import path
from . import pseudonyms
try:
    from renpy import defaultstore as store
    from renpy import exports as renpy
    from renpy import display as renpy_display
except ImportError:
    renpy = store = renpy_display = None
PY3 = True
if sys.version_info.major != 3:
    PY3 = False
RE_PATTERN_TYPE = type(re.compile('\\w+', flags=re.UNICODE))
_USER_AGENT = 'Translator3000'

class Encoding(object):
    __author__ = 'Vladya'

    @staticmethod
    def assert_string(data):
        if not isinstance(data, pseudonyms.basestring):
            raise TypeError('A string is required.')

    @classmethod
    def get_error_handler_name(cls, name):
        if name is None:
            return 'ignore'
        cls.assert_string(name)
        if name.lower() == 'strict':
            return cls.get_error_handler_name('python_strict')
        try:
            codecs.lookup_error(name)
        except LookupError:
            if name.lower() == 'python_strict':
                return 'strict'
            raise
        else:
            return name

    @staticmethod
    def _get_filesystemencoding():
        return sys.getfilesystemencoding() or 'utf_8'

    @classmethod
    def cmd_decode(cls, data, if_error=None, _force_string=False):
        try:
            cls.assert_string(data)
        except TypeError:
            if not _force_string:
                raise
            data = pseudonyms.unicode(data)
        if_error = cls.get_error_handler_name(if_error)
        if isinstance(data, bytes):
            _enc = 'utf_8'
            if hasattr(sys.stdin, 'encoding'):
                _enc = sys.stdin.encoding
            data = data.decode(_enc, if_error)
        return data

    @classmethod
    def fsdecode(cls, data, if_error=None, _force_string=False):
        try:
            cls.assert_string(data)
        except TypeError:
            if not _force_string:
                raise
            data = pseudonyms.unicode(data)
        if_error = cls.get_error_handler_name(if_error)
        if isinstance(data, bytes):
            data = data.decode(cls._get_filesystemencoding(), if_error)
        return data

    @classmethod
    def fsencode(cls, data, if_error=None, _force_string=False):
        try:
            cls.assert_string(data)
        except TypeError:
            if not _force_string:
                raise
            data = pseudonyms.bytes(data)
        if_error = cls.get_error_handler_name(if_error)
        if isinstance(data, pseudonyms.unicode):
            data = data.encode(cls._get_filesystemencoding(), if_error)
        return data

    @classmethod
    def utf8decode(cls, data, if_error=None, _force_string=False):
        try:
            cls.assert_string(data)
        except TypeError:
            if not _force_string:
                raise
            data = pseudonyms.unicode(data)
        if_error = cls.get_error_handler_name(if_error)
        if isinstance(data, bytes):
            data = data.decode('utf-8', if_error)
        return data

    @classmethod
    def utf8encode(cls, data, if_error=None, _force_string=False):
        try:
            cls.assert_string(data)
        except TypeError:
            if not _force_string:
                raise
            data = pseudonyms.bytes(data)
        if_error = cls.get_error_handler_name(if_error)
        if isinstance(data, pseudonyms.unicode):
            data = data.encode('utf-8', if_error)
        return data

class _DataSaver(object):
    __author__ = 'Vladya'
    EXECUTABLE_FLAGS = stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
    CREATE_LOCK = threading.RLock()
    LOCKS = {}

    def __init__(self, data, out_fn):
        if isinstance(data, pseudonyms.basestring):
            self.__bytedata = data
        elif hasattr(data, 'read') and hasattr(data, 'seek'):
            try:
                data.seek(0)
            except Exception:
                pass
            self.__bytedata = self._read_fo(data, _return_if_empty=b'')
        else:
            raise ValueError("'data' should be file-like object or string.")
        self.__bytedata = Encoding.utf8encode(self.__bytedata, 'strict')
        self.__filename = path.abspath(Encoding.fsdecode(out_fn, 'strict'))

    @classmethod
    def get_lock(cls, fn):
        fn = path.abspath(fn).strip().lower()
        with cls.CREATE_LOCK:
            if fn not in cls.LOCKS:
                cls.LOCKS[fn] = threading.RLock()
            return cls.LOCKS[fn]

    @classmethod
    def write_json_to_file(cls, data, filename, compress=True, backup_original=False, **dump_kwargs):
        if 'ensure_ascii' not in dump_kwargs:
            dump_kwargs['ensure_ascii'] = True
        data = json.dumps(data, **dump_kwargs)
        data = Encoding.utf8encode(data, 'strict')
        if compress:
            data = zlib.compress(data, zlib.Z_BEST_COMPRESSION)
        cls.save(data, filename, backup_original=backup_original)

    @classmethod
    def read_json_from_file(cls, filename, compressed=None, **load_kwargs):
        _is_fo = load_kwargs.pop('_is_fo', False)
        if _is_fo:
            data = filename.read()
        else:
            data = cls.read_file(filename)
        if compressed:
            data = zlib.decompress(data)
        elif compressed is None:
            try:
                _data = zlib.decompress(data)
            except Exception:
                pass
            else:
                data = _data
        data = Encoding.utf8decode(data, 'strict')
        return json.loads(data, **load_kwargs)

    @classmethod
    def _get_hashsum_from_fn(cls, filename, hashclass):
        filename = path.abspath(Encoding.fsdecode(filename, 'strict'))
        if not path.isfile(filename):
            raise ValueError('File is not found.')
        hash_object = hashclass()
        with cls.get_lock(filename):
            with open(filename, 'rb') as _file:
                while True:
                    chunk = _file.read(1073741824)
                    if not chunk:
                        return hash_object.hexdigest()
                    hash_object.update(chunk)

    @staticmethod
    def _delete_wrong_sym_from_basename(_basename, not_split_ext=True, spaces_as_underline=True, delete_pattern=None):
        _basename = path.basename(Encoding.fsdecode(_basename, 'strict'))
        if not_split_ext:
            ext = None
        else:
            _basename, ext = path.splitext(_basename)
        if spaces_as_underline:
            _basename = re.sub(u'\\s+', u'_', _basename)
        if not delete_pattern:
            delete_pattern = '[^a-zA-Z0-9_]'
        if not isinstance(delete_pattern, RE_PATTERN_TYPE):
            delete_pattern = re.compile(delete_pattern, flags=re.UNICODE | re.DOTALL)

        def _repl(match_obj):
            symb = hex(ord(match_obj.group()))
            return Encoding.utf8decode(symb, 'replace')
        _basename = delete_pattern.sub(_repl, _basename)
        if not_split_ext:
            return _basename
        return u''.join((_basename, ext))

    @classmethod
    def _get_sha512sum_from_fn(cls, filename):
        return cls._get_hashsum_from_fn(filename, hashlib.sha512)

    @classmethod
    def _get_md5sum_from_fn(cls, filename):
        return cls._get_hashsum_from_fn(filename, hashlib.md5)

    @classmethod
    def _get_renpy_basedir(cls):
        if renpy:
            return path.abspath(Encoding.fsdecode(renpy.config.basedir, 'strict'))
        result = path.abspath(Encoding.fsdecode(__file__, 'strict'))
        for _ in pseudonyms.xrange(6):
            result = path.dirname(result)
        return result

    @classmethod
    def set_executable_flags(cls, filename):
        filename = path.abspath(Encoding.fsdecode(filename, 'strict'))
        if not path.exists(filename):
            raise ValueError('"{0}" is not found.'.format(filename))
        os.chmod(filename, cls.EXECUTABLE_FLAGS)

    @staticmethod
    def _read_fo(fo, _return_if_empty=None):
        if sys.maxsize >= 4294967296:
            return fo.read()
        result = None
        step = 16777216
        while True:
            chunk = fo.read(step)
            if not chunk:
                if result:
                    return result
                return _return_if_empty
            if result is None:
                result = chunk
            else:
                result += chunk
            time.sleep(0.0001)

    @classmethod
    def read_file(cls, filename, get_unicode=False):
        filename = path.abspath(Encoding.fsdecode(filename, 'strict'))
        if not path.isfile(filename):
            raise ValueError('File is not found.')
        with cls.get_lock(filename):
            with open(filename, 'rb') as _file:
                result = cls._read_fo(_file, _return_if_empty=b'')
        if get_unicode:
            result = Encoding.utf8decode(result, 'strict')
        return result

    @classmethod
    def save(cls, data, out_fn, backup_original=False):
        saver_object = cls(data, out_fn)
        return saver_object._save(backup_original=backup_original)

    @classmethod
    def _create_dir_for_file(cls, filename):
        filename = path.abspath(Encoding.fsdecode(filename, 'strict'))
        directory = path.dirname(filename)
        cls._create_dir(directory)

    @classmethod
    def _create_dir(cls, directory):
        directory = path.abspath(Encoding.fsdecode(directory, 'strict'))
        with cls.get_lock(directory):
            if not path.isdir(directory):
                os.makedirs(directory)

    def _save(self, backup_original=False):
        temp_fn = '{0}.temporaryFile'.format(self.__filename)
        with self.get_lock(self.__filename):
            with self.get_lock(temp_fn):
                self._create_dir_for_file(temp_fn)
                offset = 0
                step = 32768
                with open(temp_fn, 'wb') as _write_file:
                    while True:
                        _chunk = self.__bytedata[offset:offset + step]
                        if not _chunk:
                            break
                        _write_file.write(_chunk)
                        time.sleep(0.0001)
                        offset += step
                self.set_executable_flags(temp_fn)
                if backup_original and path.isfile(self.__filename):
                    _backup_fn = '{0}.oldBackup'.format(self.__filename)
                    self._remove_file(_backup_fn)
                    self._create_dir_for_file(_backup_fn)
                    self.set_executable_flags(self.__filename)
                    os.rename(self.__filename, _backup_fn)
                    self.set_executable_flags(_backup_fn)
                self._remove_file(self.__filename)
                self._create_dir_for_file(self.__filename)
                os.rename(temp_fn, self.__filename)
                self.set_executable_flags(self.__filename)

    @classmethod
    def _remove_dir(cls, dirname, ignore_errors=False):
        dirname = path.abspath(Encoding.fsdecode(dirname, 'strict'))
        with cls.get_lock(dirname):
            if path.isdir(dirname):
                shutil.rmtree(dirname, ignore_errors=ignore_errors)

    @classmethod
    def _remove_file(cls, filename):
        filename = path.abspath(Encoding.fsdecode(filename, 'strict'))
        with cls.get_lock(filename):
            if path.isfile(filename):
                os.remove(filename)

def get_userfolder(if_error='strict'):
    return Encoding.fsdecode(path.abspath(path.expanduser(b'~')), if_error)

def get_ext(fn):
    fn = posixpath.normpath(Encoding.fsdecode(fn, 'strict').replace(u'\\', u'/'))
    name, ext = posixpath.splitext(posixpath.basename(fn))
    return ext.strip().lower()

def normalize_url(url):
    url = Encoding.utf8decode(url, 'strict')
    _url = urllib3.util.parse_url(url)
    _url = urllib3.util.Url(scheme=_url.scheme or u'https', auth=_url.auth, host=_url.host, port=_url.port, path=_url.path.strip('/') if _url.path else None, query=_url.query, fragment=_url.fragment)
    return _url.url.strip()

def renpy_open(fn):
    if not renpy:
        raise RuntimeError("Run not in Ren'Py.")
    if hasattr(renpy, 'open_file'):
        return renpy.open_file(fn, False)
    return renpy.file(fn)

def renpy_get_displayable(data):
    if not renpy:
        raise RuntimeError("Run not in Ren'Py.")
    result = renpy.displayable(data)
    if not isinstance(result, renpy_display.core.Displayable):
        raise ValueError("{0} isn't a displayable.".format(data))
    return result

def _process_communicate(process, exception_type=None, force_decode=False):
    if exception_type is None:
        exception_type = Exception
    if not issubclass(exception_type, Exception):
        exception_type = Exception
    stdoutdata, stderrdata = process.communicate()
    if process.returncode == 0:
        stdoutdata = stdoutdata or stderrdata or b''
        stderrdata = b''
    else:
        stderrdata = stderrdata or stdoutdata or b'Undefined error'
        stdoutdata = b''
    if stderrdata:
        try:
            stderrdata = stderrdata.decode(sys.stdin.encoding)
        except Exception:
            if force_decode:
                stderrdata = stderrdata.decode('utf_8', 'ignore')
        raise exception_type(stderrdata)
    try:
        stdoutdata = stdoutdata.decode(sys.stdin.encoding)
    except Exception:
        if force_decode:
            stdoutdata = stdoutdata.decode('utf_8', 'ignore')
    return stdoutdata

def iter_for_slice(_arr_like, slice_size):
    step = 0
    while True:
        result = _arr_like[step * slice_size:(step + 1) * slice_size]
        if not result:
            break
        yield result
        step += 1

def zip_with_none(*iterables):
    iterables = tuple(map(iter, iterables))
    while True:
        result = []
        _continue = False
        for _iterable in iterables:
            try:
                _next = next(_iterable)
            except StopIteration:
                _next = None
            else:
                _continue = True
            result.append(_next)
        if not _continue:
            break
        yield tuple(result)

def urljoin(*parts, **urljoin_kw):
    import requests.compat
    result = None
    for part in parts:
        if result is None:
            result = part
            continue
        result = requests.compat.urljoin('{0}/'.format(result.strip(u'/')), part.strip(u'/'), **urljoin_kw)
    return result

def get_url_mirrors(url):
    result = [url]
    _url = urllib3.util.parse_url(url)
    host_parts = _url.host.strip().split('.')
    path_parts = tuple(filter(None, map(lambda a: a.strip(), _url.path.split('/'))))
    return tuple(delete_duplicates_from_list(result))

def delete_duplicates_from_list(source):
    result = []
    for data in source:
        if data in result:
            continue
        result.append(data)
    return result

def _get_username():
    names = set()
    for name in ('LOGNAME', 'USER', 'LNAME', 'USERNAME'):
        result = os.getenv(name, None)
        if result:
            names.add(result)
    try:
        user_catalog = path.basename(get_userfolder())
        user_catalog = user_catalog.strip('/')
        if user_catalog:
            names.add(user_catalog)
    except Exception:
        pass
    try:
        import pwd
        name = pwd.getpwuid(os.getuid())[0]
        if name:
            names.add(name)
    except Exception:
        pass
    if not names:
        return None
    names = frozenset(map(Encoding.fsdecode, names))
    return '/'.join(sorted(names))
_UN = _get_username()
del _get_username

def get_translator_user_agent():
    _ua = _USER_AGENT
    if _UN:
        _ua += '; {0}'.format(_UN)
    _ua = Encoding.utf8encode(_ua)
    try:
        import requests.compat
        _ua = requests.compat.quote(_ua, safe='; ')
    except Exception:
        pass
    return Encoding.utf8encode(_ua)

def merge_dicts(*dicts):

    def is_dict(data):
        if isinstance(data, dict):
            return True
        return False
    for _dct in dicts:
        if not is_dict(_dct):
            raise TypeError('Wrong type {0!r}. dict is expected'.format(_dct))
    result = {}
    for _dct in map(copy.deepcopy, dicts):
        for key, new_value in _dct.items():
            if key not in result:
                result[key] = new_value
                continue
            current_value = result[key]
            if not (is_dict(current_value) and is_dict(new_value)):
                result[key] = new_value
                continue
            new_value = merge_dicts(current_value, new_value)
            result[key] = new_value
    return result
save_data_to_file = _DataSaver.save
create_dir_for_file = _DataSaver._create_dir_for_file
create_dir = _DataSaver._create_dir
remove_dir = _DataSaver._remove_dir
remove_file = _DataSaver._remove_file
read_file = _DataSaver.read_file
set_executable_flags = _DataSaver.set_executable_flags
getsha512hash = _DataSaver._get_sha512sum_from_fn
getmd5hash = _DataSaver._get_md5sum_from_fn
write_json_to_file = _DataSaver.write_json_to_file
read_json_from_file = _DataSaver.read_json_from_file
delete_wrong_sym_from_basename = _DataSaver._delete_wrong_sym_from_basename
