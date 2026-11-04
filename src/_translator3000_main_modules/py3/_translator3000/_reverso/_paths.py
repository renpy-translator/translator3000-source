from os import path
from .. import _paths
_database_struct_version = '1.1'
_translator_folder_name = u'Reverso'
DATABASE_FOLDER = path.join(_paths.TRANSLATIONS_DB_DIR, _translator_folder_name, _database_struct_version)
LOCAL_DATABASE_FOLDER = path.join(_paths.LOCAL_DATABASE_FOLDER, _translator_folder_name, _database_struct_version)
IMPORT_TRANSLATIONS_FOLDER = path.join(_paths.LOCAL_DATABASE_FOLDER, _translator_folder_name, u'imported translations')
