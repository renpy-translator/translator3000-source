import time
import os
import io
import re
import logging
import threading
from . import _paths, utils, pseudonyms
TOR_REPLACE_PATTERN = re.compile('(^|\\s|\\.)tor(?=($|\\s|c|project))', flags=re.IGNORECASE)
utils.create_dir_for_file(_paths._ssl_logfile)
os.environ['SSLKEYLOGFILE'] = _paths._ssl_logfile
GLOBAL_SETTING = True
if utils.renpy:
    GLOBAL_SETTING = True

class Logger(logging.Logger):
    __author__ = 'Vladya'
    root = logging.RootLogger(logging.INFO)
    manager = logging.Manager(root)
    STREAM_HANDLER = None

    @classmethod
    def getLogger(cls, name):
        _global_root = logging.getLogger()
        cls.manager.setLoggerClass(cls)
        _logger = cls.manager.getLogger(name)
        _formatter = logging.Formatter(u'%(asctime)s %(levelname)s:%(name)s\n%(message)s\n')
        if cls.STREAM_HANDLER is None:
            cls.STREAM_HANDLER = logging.StreamHandler(io.StringIO())
            cls.STREAM_HANDLER.setFormatter(_formatter)
        cls.root.addHandler(cls.STREAM_HANDLER)
        if GLOBAL_SETTING:
            _global_root.addHandler(cls.STREAM_HANDLER)
        utils.create_dir_for_file(_paths._logfile)
        _handler = logging.FileHandler(_paths._logfile, mode='a', encoding='utf_8')
        _handler.setFormatter(_formatter)
        cls.root.addHandler(_handler)
        if GLOBAL_SETTING:
            _global_root.addHandler(_handler)
        if not utils.renpy:
            _handler = logging.StreamHandler()
            _handler.setFormatter(_formatter)
            cls.root.addHandler(_handler)
            if GLOBAL_SETTING:
                _global_root.addHandler(_handler)
        return _logger

    def setLevel(self, *args, **kwargs):
        if GLOBAL_SETTING:
            _global_root = logging.getLogger()
            _global_root.setLevel(*args, **kwargs)
        return self.root.setLevel(*args, **kwargs)

    def _log(self, level, msg, args, *other_args, **other_kwargs):
        new_msg = msg
        new_args = []
        if isinstance(new_msg, pseudonyms.basestring):
            new_msg = utils.Encoding.utf8decode(new_msg, 'replace')
        for _arg in args:
            if isinstance(_arg, pseudonyms.basestring):
                _arg = utils.Encoding.utf8decode(_arg, 'replace')
            new_args.append(_arg)
        new_args = tuple(new_args)
        try:
            if new_args:
                new_msg % new_args
        except Exception:
            new_msg = msg
            new_args = args
        msg = new_msg
        args = new_args

        def _replace(data):
            if not isinstance(data, pseudonyms.basestring):
                return data
            for _match1 in TOR_REPLACE_PATTERN.finditer(data):
                data = data.replace(_match1.group().strip(), 'AutoProxies')
            return data
        msg = _replace(msg)
        args = tuple(map(_replace, args))
        try:
            result = super(Logger, self)._log(level, msg, args, *other_args, **other_kwargs)
        except Exception as ex:
            if other_kwargs.get('exc_info', False):
                other_kwargs.pop('exc_info', None)
                try:
                    result = super(Logger, self)._log(level, msg, args, *other_args, **other_kwargs)
                except Exception as ex2:
                    return self.exception(ex2)
            else:
                return self.exception(ex)
        return result

    def get_log_daemon(self, process):
        return _LoggingThread(process, self)

class _LoggingThread(threading.Thread):
    __author__ = 'Vladya'

    def __init__(self, process, logger_object):
        super(_LoggingThread, self).__init__()
        self.daemon = True
        self.__process = process
        self.__logger_object = logger_object
        self.__current_buffer = b''
        self.__stop_trigger = False
        self.__io_logger = self.__logger_object.getChild('IO')

    def _set_stop(self):
        self.__stop_trigger = True

    def run(self):
        while True:
            if self.__stop_trigger:
                return
            try:
                line = self.__process.stdout.readline()
                line = utils.Encoding.cmd_decode(line.strip())
                line = utils.Encoding.utf8encode(line)
                if line:
                    self.__logger_object.debug(line)
            except Exception as ex:
                self.__io_logger.exception(ex)
            time.sleep(0.1)
