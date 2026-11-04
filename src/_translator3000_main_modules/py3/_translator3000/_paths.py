from os import path
from . import utils
PROJECTS_FOLDER = path.join(utils.get_userfolder(), "vladya's projects database")
DATABASE_FOLDER = path.join(PROJECTS_FOLDER, u'translator3000')
SELENIUM_FOLDER = path.join(PROJECTS_FOLDER, 'selenium')
TOR_FOLDER = path.join(PROJECTS_FOLDER, u'autoProxies')
if utils.renpy:
    _translator_data_folder = path.abspath(path.join(utils.renpy.config.basedir, u'_translator3000Data'))
    LOCAL_DATABASE_FOLDER = path.abspath(path.join(utils.renpy.config.basedir, 'tr3000_local_translations'))
    if utils.renpy.config.save_directory:
        _SAVEDIR = path.normpath(utils.renpy.config.save_directory)
    else:
        _SAVEDIR = u'NoGame'
else:
    _translator_data_folder = path.join(DATABASE_FOLDER, '_AppData')
    LOCAL_DATABASE_FOLDER = path.join(_translator_data_folder, 'tr3000_local_translations')
    _SAVEDIR = 'NoGame'
TRANSLATIONS_DB_DIR = path.join(DATABASE_FOLDER, u'translations', utils.delete_wrong_sym_from_basename(_SAVEDIR, True))
RENPY_BASEDIR = utils._DataSaver._get_renpy_basedir()
TEMP_FOLDER = path.join(_translator_data_folder, 'temp')
TOR_DATA_FOLDER = path.join(_translator_data_folder, u'autoProxies_data')
DEBUG_FOLDER = path.join(_translator_data_folder, 'debug')
ERROR_PAGES = path.join(DEBUG_FOLDER, 'error_pages')
CERT_PATH = path.join(_translator_data_folder, u'cacert.pem')
_logfile = path.join(DEBUG_FOLDER, 'lastLog.log')
_ssl_logfile = path.join(DEBUG_FOLDER, 'ssl_keys.log')
FILES_LAST_MODIFIED_REGISTRY = path.join(DATABASE_FOLDER, 'fn_mod.data')
