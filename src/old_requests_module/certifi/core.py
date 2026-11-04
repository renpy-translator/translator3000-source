# -*- coding: utf-8 -*-

"""
certifi.py
~~~~~~~~~~

This module returns the installation location of cacert.pem or its contents.
"""

from os import path
from threading import Lock
from _translator3000 import (
    utils,
    _paths
)

_set_lock = Lock()

_CACERT_IS_SET = False


def where():


    with _set_lock:

        global _CACERT_IS_SET
        if _CACERT_IS_SET:
            return _paths.CERT_PATH

        cur_dir = path.dirname(__file__)
        cacert = path.normpath(
            path.join(cur_dir, "cacert.pem").replace('\\', '/')
        ).replace('\\', '/')

        with utils.renpy_open(cacert) as _cacert_file:
            utils.save_data_to_file(_cacert_file, _paths.CERT_PATH)

        _CACERT_IS_SET = True

        return _paths.CERT_PATH


def read_text(_module, _path, encoding="ascii"):
    with open(where(), "r", encoding=encoding) as data:
        return data.read()


def contents():
    return read_text("certifi", "cacert.pem", encoding="ascii")
