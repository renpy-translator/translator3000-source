from os import path
from .. import _paths
_database_struct_version = u'1.2'
_translator_folder_name = u'SeleniumDeepL'
DATABASE_FOLDER = path.join(_paths.TRANSLATIONS_DB_DIR, _translator_folder_name, _database_struct_version)
LOCAL_DATABASE_FOLDER = path.join(_paths.LOCAL_DATABASE_FOLDER, _translator_folder_name, _database_struct_version)
IMPORT_TRANSLATIONS_FOLDER = path.join(_paths.LOCAL_DATABASE_FOLDER, _translator_folder_name, u'imported translations')

def _get_old_db_folders():
    _old_structs = u'1.0', u'1.1'
    for _struct in _old_structs:
        var = path.join(_paths.TRANSLATIONS_DB_DIR, _translator_folder_name, _struct)
        if path.isdir(var):
            yield var

