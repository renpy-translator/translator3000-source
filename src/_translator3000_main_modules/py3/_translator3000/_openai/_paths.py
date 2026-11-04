# -*- coding: utf-8 -*-
from os import path
from .. import _paths

_database_struct_version = u'1.2'
DATABASE_FOLDER = path.join(
    _paths.TRANSLATIONS_DB_DIR, u'OpenAI_api_contextual_v2', _database_struct_version)
LOCAL_DATABASE_FOLDER = path.join(
    _paths.LOCAL_DATABASE_FOLDER, u'OpenAI_api_contextual_v2', _database_struct_version)
DATABASE_FOLDER_CODEX = path.join(
    _paths.TRANSLATIONS_DB_DIR, u'OpenAI_codex_contextual_v2', _database_struct_version)
LOCAL_DATABASE_FOLDER_CODEX = path.join(
    _paths.LOCAL_DATABASE_FOLDER, u'OpenAI_codex_contextual_v2', _database_struct_version)
IMPORT_TRANSLATIONS_FOLDER = None
