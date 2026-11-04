# -*- coding: utf-8 -*-
"""Native OpenAI providers (stock-style TranslatorAbstract subclasses).

Registered in `_translator3000/translator.py` like every other provider:
`openai_api` (OpenAI API key / custom Base URL) and `openai_chatgpt`
(ChatGPT account through codex). Translation itself lives in
`_openai/client.py`; settings are shared across games via
`_translator3000_openai.json` in the Translator3000 database folder.
"""
import threading

from .. import translator_abstract, lang_codes, _paths as _root_paths, LOGGER
from . import client, _paths

client.use_shared_settings(_root_paths.RENPY_BASEDIR)
client.settings.cert_path = _root_paths.CERT_PATH


class _OpenAIBase(translator_abstract.TranslatorAbstract):
    __author__ = 'Translator3000 contributors'
    TRANSLATOR_GROUP = 'OpenAI'
    BROWSER_TRANSLATOR = False
    SYMB_LIMIT = 96001
    FORCE_RPM = None
    BACKEND = None
    IMPORT_TRANSLATIONS_DIR = None
    single_instance = None
    is_initialized = False

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        self._openai_cancel = threading.Event()
        self._openai_context = []
        self._openai_language = None
        super(_OpenAIBase, self).__init__(setting_dict, multi_setting)

    def get_lang_code(self, data, dest_direction=True):
        return lang_codes.get_lang_code(data, 'google')

    def get_all_lang_codes(self, dest_direction=True):
        return lang_codes.get_lang_codes_for_translator('google')

    def interrupt_web_translation(self):
        self._openai_cancel.set()

    def _web_translate(self, text, dest, src):
        self._openai_cancel.clear()
        try:
            if self._openai_language != (dest, src):
                self._openai_context = []
                self._openai_language = (dest, src)
            result = client.translate_text(
                text, dest, src, self.BACKEND,
                client.selected_model(self.BACKEND),
                self._openai_cancel, self._openai_context)
            self._openai_context = [
                {'source': original, 'translation': translated}
                for original, translated in zip(
                    text.split('\n\n\n'), result.split('\n\n\n'))][-2:]
            return result
        except client.TranslationError as ex:
            client.settings.status = client.text_type(ex)
            raise translator_abstract.InterruptTranslate()


class Translator(_OpenAIBase):
    """OpenAI API provider (service name: openai_api)."""
    BACKEND = 'api'
    LOGGER = LOGGER.getChild('OpenAI.api')
    DATABASE_FN = _paths.path.join(_paths.DATABASE_FOLDER, 'translations.dbformat')
    LOCAL_DATABASE_FN = _paths.path.join(
        _paths.LOCAL_DATABASE_FOLDER, 'translations.dbformat')


class ChatGPTTranslator(_OpenAIBase):
    """ChatGPT account provider (service name: openai_chatgpt)."""
    BACKEND = 'codex'
    LOGGER = LOGGER.getChild('OpenAI.codex')
    DATABASE_FN = _paths.path.join(_paths.DATABASE_FOLDER_CODEX, 'translations.dbformat')
    LOCAL_DATABASE_FN = _paths.path.join(
        _paths.LOCAL_DATABASE_FOLDER_CODEX, 'translations.dbformat')
