import os
import zipfile
import threading
from os import path
from . import utils

class FileAlreadyExists(Exception):
    pass

class FileIsNotExists(Exception):
    pass

class Zip(object):
    __author__ = 'Vladya'
    name_lock = threading.Lock()
    locks = {}

    def __init__(self, name):
        self.__name = path.abspath(utils.Encoding.utf8decode(name, 'strict'))
        with self.name_lock:
            if self.__name not in self.locks:
                self.locks[self.__name] = threading.RLock()
            self.__lock = self.locks[self.__name]

    def archive_is_exists(self):
        if path.isfile(self.__name):
            if zipfile.is_zipfile(self.__name):
                return True
        return False

    @staticmethod
    def _zipinfo_isdir(info_object):
        if hasattr(info_object, u'is_dir'):
            return info_object.is_dir()
        if info_object.filename[-1] in '\\/':
            return True
        return False

    @staticmethod
    def _normpath(name):
        name = path.normpath(name.replace('\\', '/'))
        return name.replace(u'\\', '/')

    def exists(self, name):
        name = self._normpath(name)
        with self.__lock:
            if not self.archive_is_exists():
                return False
            with zipfile.ZipFile(self.__name, 'r') as _zip:
                try:
                    _zip.getinfo(name)
                except KeyError:
                    return False
                else:
                    return True

    def isdir(self, name):
        name = self._normpath(name)
        with self.__lock:
            if not self.archive_is_exists():
                return False
            with zipfile.ZipFile(self.__name, 'r') as _zip:
                try:
                    info = _zip.getinfo(name)
                except KeyError:
                    return False
                else:
                    if self._zipinfo_isdir(info):
                        return True
                    return False

    def isfile(self, name):
        name = self._normpath(name)
        with self.__lock:
            if not self.archive_is_exists():
                return False
            with zipfile.ZipFile(self.__name, 'r') as _zip:
                try:
                    info = _zip.getinfo(name)
                except KeyError:
                    return False
                else:
                    if not self._zipinfo_isdir(info):
                        return True
                    return False

    def get_filenames(self):
        with self.__lock:
            result = []
            if not self.archive_is_exists():
                return result
            with zipfile.ZipFile(self.__name, 'r') as _zip:
                for info in _zip.infolist():
                    if self._zipinfo_isdir(info):
                        continue
                    result.append(info.filename)
            return tuple(sorted(result))

    def delete_file(self, name):
        name = self._normpath(name)
        with self.__lock:
            if not self.isfile(name):
                return
            _tmp = '{0}.tmp'.format(self.__name)
            utils.create_dir_for_file(_tmp)
            with zipfile.ZipFile(_tmp, 'w') as _new_zip:
                with zipfile.ZipFile(self.__name, 'r') as _old_zip:
                    delete_info = _old_zip.getinfo(name)
                    for info in _old_zip.infolist():
                        if info == delete_info:
                            continue
                        _new_zip.writestr(info, _old_zip.read(info))
            utils.remove_file(self.__name)
            utils.create_dir_for_file(self.__name)
            os.rename(_tmp, self.__name)
            utils.set_executable_flags(self.__name)

    def add_file(self, arch_name, fo_or_bytes, rewrite=True, is_fo=True):
        arch_name = self._normpath(arch_name)
        with self.__lock:
            if self.isfile(arch_name):
                if rewrite:
                    self.delete_file(arch_name)
                else:
                    raise FileAlreadyExists(self.__name, arch_name)
            if not self.archive_is_exists():
                utils.create_dir_for_file(self.__name)
                with zipfile.ZipFile(self.__name, 'w'):
                    pass
                utils.set_executable_flags(self.__name)
            if is_fo:
                data = utils._DataSaver._read_fo(fo_or_bytes, _return_if_empty=b'')
            else:
                if not isinstance(fo_or_bytes, bytes):
                    raise TypeError('Argument should be {0!r}, but {1!r}'.format(bytes, type(fo_or_bytes)))
                data = fo_or_bytes
            with zipfile.ZipFile(self.__name, 'a') as _zip:
                _zip.writestr(arch_name, data)

    def read_file(self, name):
        name = self._normpath(name)
        with self.__lock:
            if not self.isfile(name):
                raise FileIsNotExists(self.__name, name)
            with zipfile.ZipFile(self.__name, 'r') as _zip:
                return _zip.read(name)
