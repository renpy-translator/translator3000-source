import threading
from . import consts, pseudonyms

def _format(text):
    text = text.lower().strip()
    check_double_format = text.replace('_', '-').split('-')
    if len(check_double_format) == 2:
        a, b = check_double_format
        if a == b:
            text = a
    return text.replace('-', '_')

def _get_available_translators():
    variants = set()
    for translators_dict in consts.LANG_CODES.values():
        variants.update(translators_dict.keys())
    return frozenset(variants)
_names_format_mapping = dict(map(lambda x: (_format(x), x), consts.LANG_CODES.keys()))
_available_translators = _get_available_translators()

def get_languages_for_translator(translator_name):
    if translator_name not in _available_translators:
        raise ValueError("Translator '{0}' is not found.".format(translator_name))
    for lang_name, translators_variants in consts.LANG_CODES.items():
        if translator_name in translators_variants:
            yield lang_name

def get_lang_codes_for_translator(translator_name):
    if translator_name not in _available_translators:
        raise ValueError("Translator '{0}' is not found.".format(translator_name))
    for translators_variants in consts.LANG_CODES.values():
        if translator_name in translators_variants:
            yield translators_variants[translator_name][0]
_NAMES_LOCK = threading.Lock()
_NAMES_CACHE = {}

def get_lang_name(language_data):
    with _NAMES_LOCK:
        if language_data not in _NAMES_CACHE:
            if not isinstance(language_data, pseudonyms.basestring):
                raise TypeError('Language id should be a string.')
            _language_data = _format(language_data)
            for lang_name, translators_variants in consts.LANG_CODES.items():
                variants = set()
                variants.add(_format(lang_name))
                for _variants in translators_variants.values():
                    variants.update(map(_format, _variants))
                if _language_data in variants:
                    _NAMES_CACHE[language_data] = lang_name
                    break
            else:
                raise ValueError('Language "{0}" is not detected.'.format(language_data))
        return _NAMES_CACHE[language_data]

def get_lang_code(language_data, translator_name):
    if translator_name not in _available_translators:
        raise ValueError("Translator '{0}' is not found.".format(translator_name))
    lang_name = get_lang_name(language_data)
    if translator_name not in consts.LANG_CODES[lang_name]:
        raise ValueError("'{0}' translator does not support the {1} language.".format(translator_name, lang_name))
    return consts.LANG_CODES[lang_name][translator_name][0]

