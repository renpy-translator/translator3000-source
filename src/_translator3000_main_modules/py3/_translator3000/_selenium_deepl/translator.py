import time
import re
import random
import threading
from os import path
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from .. import utils, pseudonyms, translator_abstract, selenium_session, lang_codes
from . import _paths, LOGGER
XPATHS = {'cookie_banner': '//div[@data-testid="dl-cookieBanner"]/div[1]', 'cookiebanner_close_button': ('//button[@data-testid="cookie-banner-lax-close-button"]', '//button[@data-testid="cookie-banner-strict-accept-selected"]'), 'ext_banner': '//div[@data-testid="chrome-extension-toast"]', 'source_lang_button': '//button[@data-testid="translator-source-lang-btn"]', 'dest_lang_button': '//button[@data-testid="translator-target-lang-btn"]', 'source_lang_select_listbox': '//div[@data-testid="translator-source-lang-list-all-languages-grid"]', 'dest_lang_select_listbox': '//div[@data-testid="translator-target-lang-list-all-languages-grid"]', 'progress_translate_text': '//div[@id="progress-text"]', 'translate_progress_status': '//div[@data-testid="translator-progress-popup"]', 'translate_progress_indicator': '//div[@data-testid="translator-inline-loading-indicator"]', 'input_area': '//d-textarea[@data-testid="translator-source-input"]/div[1]', 'output_area': '//d-textarea[@data-testid="translator-target-input"]/div[1]', 'text_limit': ('//div[@class="font-normal text-sm flex items-center space-x-1 h-full text-roman"]', '//div[@class="font-normal text-sm flex items-center space-x-1 h-full"]'), 'unsupported_lang_error': '//div[@data-testid="unsupported-language-hint-banner"]', 'limit_proad': '//div[@data-testid="translator-character-limit-proad"]', 'login_button': '//button[@data-testid="menu-account-out-btn"]', 'login_username_area': '//input[@data-testid="menu-login-username"]', 'login_password_area': '//input[@data-testid="menu-login-password"]', 'login_submit_button': '//button[@data-testid="menu-login-submit"]', 'server_ban': '//*[@id="dl-banned-1"]'}
BanOnServer = translator_abstract.BanOnServer
ShadowBan = translator_abstract.ShadowBan
SymbolLimitExceeded = translator_abstract.SymbolLimitExceeded

class RestartInput(Exception):
    pass

class Translator(translator_abstract.TranslatorAbstract):
    __author__ = 'Vladya'
    TRANSLATOR_GROUP = 'deepl_web'
    BROWSER_TRANSLATOR = True
    LOGGER = LOGGER.getChild('Translator')
    DATABASE_FN = path.join(_paths.DATABASE_FOLDER, 'translations.dbformat')
    LOCAL_DATABASE_FN = path.join(_paths.LOCAL_DATABASE_FOLDER, u'translations.dbformat')
    IMPORT_TRANSLATIONS_DIR = _paths.IMPORT_TRANSLATIONS_FOLDER
    SYMB_LIMIT = 1425
    DEST_VARIANTS = {'en': {'default': 'US', 'American': 'US', 'Britain': 'GB'}, 'pt': {'default': 'BR', 'Brazil': 'BR', 'Portugal': 'PT'}, 'zh': {'default': 'Hans', 'Simplified': 'Hans', 'Traditional': 'Hant'}}
    _NAMECODE_LOCK = threading.Lock()
    _NAMECODE_CACHE = {}

    def __init__(self, setting_dict=None, multi_setting=None):
        if self.is_initialized:
            return
        super(Translator, self).__init__(setting_dict, multi_setting)
        self._max_get = None
        self._last_input = None
        self._need_interrupt = False

    def _get_old_database_folders(self):
        for _pth in _paths._get_old_db_folders():
            yield _pth

    def _fix_old_database(self, db):
        result = {}
        for src_lang, src_db in db.items():
            for src_text, dest_langs in src_db.items():
                for dest_lang, translation in dest_langs.items():
                    if src_text == translation:
                        continue
                    result.setdefault(src_lang, {})
                    result[src_lang].setdefault(src_text, {})
                    result[src_lang][src_text][dest_lang] = translation
        return result

    def get_lang_name_and_code(self, data, dest_direction=True):
        with self._NAMECODE_LOCK:
            _key = (data, dest_direction)
            if _key not in self._NAMECODE_CACHE:
                self._NAMECODE_CACHE[_key] = self._get_lang_name_and_code(data, dest_direction)
            return self._NAMECODE_CACHE[_key]

    def _get_lang_name_and_code(self, data, dest_direction=True):
        pure_code = lang_codes.get_lang_code(data, self.TRANSLATOR_GROUP)
        if pure_code == 'zh-Hant':
            data = pure_code
            pure_code = 'zh'
        pure_name = lang_codes.get_lang_name(data)
        if not dest_direction:
            return (pure_name, pure_code)
        code_addition = None
        name_addition = None
        if pure_code in self.DEST_VARIANTS:
            variants = self.DEST_VARIANTS[pure_code]
            check_data = data.strip().split('-')[-1]
            for name, variant in variants.items():
                if name == 'default':
                    continue
                if check_data.lower() == variant.lower():
                    code_addition = variant
                    name_addition = name
                    break
            else:
                code_addition = variants['default']
        result_code = pure_code
        if code_addition:
            result_code = '-'.join((pure_code, code_addition))
        result_name = pure_name
        if name_addition and pure_code != 'zh':
            result_name = '{0} ({1})'.format(result_name, name_addition)
        return (result_name, result_code)

    def get_lang_code(self, data, dest_direction=True):
        name, code = self.get_lang_name_and_code(data, dest_direction)
        return code

    def get_lang_name(self, data, dest_direction=True):
        name, code = self.get_lang_name_and_code(data, dest_direction)
        return name

    def get_all_lang_codes(self, dest_direction=True):
        result = set()
        codes = lang_codes.get_lang_codes_for_translator(self.TRANSLATOR_GROUP)
        for code in codes:
            if len(code.split('-')) == 2:
                result.add(code)
            else:
                additions = set()
                if code in self.DEST_VARIANTS:
                    additions.update(self.DEST_VARIANTS[code].values())
                else:
                    additions.add(code)
                for addition in additions:
                    result.add('-'.join((code.lower(), addition.upper())))
        return frozenset(map(lambda code: self.get_lang_code(code, dest_direction), result))

    def __get_lang_button(self, need_lang, is_dest):
        if is_dest:
            choose_lang_button = self.wait_element('dest_lang_button', move_to=True)
            choose_lang_button.click()
            lang_list_element = self.wait_element('dest_lang_select_listbox', move_to=True)
        else:
            choose_lang_button = self.wait_element('source_lang_button', move_to=True)
            choose_lang_button.click()
            lang_list_element = self.wait_element('source_lang_select_listbox', move_to=True)
        _lang_prefix = 'translator-lang-option-'
        need_lang = self.get_lang_code(need_lang, is_dest)
        for button in lang_list_element.find_elements(By.TAG_NAME, 'button'):
            lang_name = button.get_attribute('data-testid')
            if not lang_name:
                continue
            if not lang_name.startswith(_lang_prefix):
                continue
            lang_name = lang_name[len(_lang_prefix):]
            if lang_name == 'auto':
                continue
            try:
                lang_name = self.get_lang_code(lang_name, is_dest)
            except Exception:
                continue
            if need_lang == lang_name:
                return button
        else:
            raise RuntimeError('Language is not found', lang_list_element)

    def assert_limit(self, wait=0.5):
        limit_panel = None
        for arg, by in (('text_limit', 'xpath_name'),):
            try:
                limit_panel = self.wait_element(arg, by=by, _log=False, timeout=wait)
            except exceptions.TimeoutException:
                continue
            else:
                break
        if limit_panel is None:
            return None
        _limit = selenium_session._get_text_from_element(limit_panel)
        result = re.search('\\s*(?P<done>\\d+)\\s*/\\s*(?P<total>\\d+)\\s*', _limit)
        if result:
            _limit = float(result.group('total'))
            _current = float(self.SYMB_LIMIT)
            if not _limit * 0.9 <= _current < _limit:
                raise SymbolLimitExceeded(_limit * 0.95)
            self.LOGGER.debug('Limit value is correct')
            return True
        elif _limit:
            self.LOGGER.error('Limit value is %s', _limit)
            return None
        else:
            self.LOGGER.debug('Limit panel is empty.')
            return None

    def _send_text(self, text_area, text, _force_input_logic=None, _check_limit=True):
        text = utils.Encoding.utf8decode(text, 'strict')
        self._last_input = None

        def _send_keys(keys, wait_after_prev=None):
            if not keys:
                return
            if wait_after_prev is None:
                wait_after_prev = random.uniform(0.001, 0.005)
            if wait_after_prev <= 0.0:
                wait_after_prev = 0.0
            _progress_panel_counter = 0
            while True:
                self.check_and_raise_interrupt()
                if self.is_banned(0.0):
                    raise BanOnServer()
                is_disabled = text_area.get_attribute('aria-disabled')
                if is_disabled:
                    if is_disabled.strip().lower() != 'false':
                        time.sleep(0.001)
                        continue
                progress_translate_text = self.find_element('progress_translate_text', default=None)
                if progress_translate_text:
                    if _progress_panel_counter > 10:
                        raise RestartInput()
                    time.sleep(random.uniform(1.0, 2.0))
                    _progress_panel_counter += 1
                _progress_panel_counter = 0
                translate_bar = self.find_element('translate_progress_status', default=None)
                if translate_bar:
                    if selenium_session._get_text_from_element(translate_bar):
                        time.sleep(0.001)
                        continue
                if self._last_input is not None:
                    _elapsed = time.time() - self._last_input
                    if _elapsed <= wait_after_prev:
                        time.sleep(0.001)
                        continue
                try:
                    text_area.send_keys(keys)
                except Exception as ex:
                    self.LOGGER.exception(ex)
                    continue
                else:
                    self._last_input = time.time()
                    break
        _input_logic = 'strings'
        if _force_input_logic:
            _input_logic = _force_input_logic
        elif self._setting_dict:
            _input_logic = self._setting_dict[u'seleniumInputSplitMethod']
        _input_logic = _input_logic.strip()
        if _input_logic == 'all':
            _send_keys(text, 0.0)
            if _check_limit:
                self.assert_limit(3.0)
            return
        elif _input_logic == 'strings':
            _first_string = True
            for string in text.split('\n'):
                if not _first_string:
                    _send_keys(u'\n')
                _first_string = False
                _send_keys(string)
                if _check_limit:
                    _attempt = self.assert_limit(0.1)
                    if _attempt:
                        _check_limit = False
            return
        elif _input_logic in ('symbols', 'humanTyping'):
            for symb in text:
                wait_time = 0.0
                if _input_logic == u'humanTyping':
                    symb_per_minute = random.uniform(300.0, 800.0)
                    wait_time = 60.0 / symb_per_minute
                _send_keys(symb, wait_time)
                if _check_limit:
                    _attempt = self.assert_limit(0.01)
                    if _attempt:
                        _check_limit = False
            return
        _input_logic = utils.Encoding.utf8encode(_input_logic)
        raise RuntimeError('Incorrect input mode: {0}.'.format(_input_logic))

    @classmethod
    def _get_text_from_area(cls, area):
        while True:
            result = []
            try:
                for p_el in area.find_elements(By.TAG_NAME, 'p'):
                    parts = []
                    for span_el in p_el.find_elements(By.XPATH, "span[contains(@class, 'container-target')]"):
                        txt = selenium_session._get_text_from_element(span_el, True)
                        if txt:
                            parts.append(txt)
                        if span_el.find_elements(By.TAG_NAME, 'br'):
                            complete_part = u' '.join(parts)
                            if complete_part:
                                result.append(complete_part)
                            parts = []
                    if parts:
                        complete_part = ' '.join(parts)
                        if complete_part:
                            result.append(complete_part)
            except exceptions.StaleElementReferenceException:
                time.sleep(0.01)
                continue
            else:
                return u'\n'.join(result)

    def __wait_output_text(self, wait_time=10.0):
        last_content = None
        last_update = None
        output_area = self.wait_element('output_area', move_to=True)
        _progress_panel_counter = 0
        while True:
            self.check_and_raise_interrupt()
            if self.is_banned(0.0):
                raise BanOnServer()
            if last_update is None:
                last_update = time.time()
                continue
            time.sleep(0.05)
            is_disabled = output_area.get_attribute('aria-disabled')
            if is_disabled.strip().lower() != 'false':
                last_update = time.time()
                continue
            progress_translate_text = self.find_element('progress_translate_text', default=None)
            if progress_translate_text:
                if _progress_panel_counter > 10:
                    raise RestartInput()
                time.sleep(random.uniform(1.0, 2.0))
                _progress_panel_counter += 1
            _progress_panel_counter = 0
            translate_bar = self.find_element('translate_progress_status', default=None)
            if translate_bar:
                if selenium_session._get_text_from_element(translate_bar):
                    last_update = time.time()
                    continue
            translate_indicator = self.find_element('translate_progress_indicator', default=None)
            if translate_indicator:
                last_update = time.time()
                continue
            text_content = self._get_text_from_area(output_area)
            if '[...]' in text_content:
                last_update = time.time()
                continue
            if last_content is None or text_content != last_content:
                last_content = text_content
                last_update = time.time()
                continue
            elapsed = time.time() - last_update
            if elapsed >= wait_time:
                return text_content

    @staticmethod
    def is_banned(check_time=0.5):

        def _check_func():
            xpath = XPATHS['server_ban']
            try:
                selenium_session.driver.find_element(By.XPATH, xpath)
            except exceptions.NoSuchElementException:
                return False
            else:
                return True
        _start_time = time.time()
        while True:
            if _check_func():
                return True
            elapsed = time.time() - _start_time
            if elapsed >= check_time:
                return False
            time.sleep(0.05)

    def _try_login(self):
        self.LOGGER.debug('Try login on site.')
        if selenium_session.driver.get_cookie('dl_session'):
            self.LOGGER.debug('Already logged.')
            return
        if self._setting_dict:
            _data = self._setting_dict[u'deeplLoginData']
        else:
            _data = None
        if _data is None:
            self.LOGGER.debug('No login data is specified. Use anonym mode.')
            return
        if isinstance(_data, (list, tuple)) and len(_data) == 2:
            try:
                _login, _pass = map(utils.Encoding.utf8decode, _data)
            except Exception as ex:
                self.LOGGER.exception(ex)
                return
            login_button = self.wait_element('login_button', move_to=True)
            login_button.click()
            input_area = self.wait_element('login_username_area', move_to=True)
            input_area.clear()
            input_area.click()
            self._send_text(input_area, _login, 'humanTyping', False)
            input_area = self.wait_element('login_password_area', move_to=True)
            input_area.clear()
            input_area.click()
            self._send_text(input_area, _pass, 'humanTyping', False)
            submit_b = self.wait_element('login_submit_button', move_to=True)
            submit_b.click()
            self.LOGGER.debug('Successfully logged.')
            return
        else:
            self.LOGGER.error('login data is in an incorrect format.')
            return

    def __close_cookie_banner(self):
        self.LOGGER.debug('Starting close cookie banner')
        try:
            self.LOGGER.debug('Try variant 1')
            close_button = self.wait_element('cookiebanner_close_button')
        except exceptions.TimeoutException:
            self.LOGGER.debug('Not found. Try variant 2')
            try:
                _cookie_banner = self.wait_element('cookie_banner')
            except exceptions.TimeoutException:
                self.LOGGER.debug('No cookie banner was found')
                return
            if not _cookie_banner.is_displayed():
                self.LOGGER.debug('Already closed')
                return
            try:
                close_button = _cookie_banner.find_element(By.TAG_NAME, 'button')
            except BanOnServer:
                raise
            except Exception:
                self.LOGGER.debug('No close button was found')
                return
        self.LOGGER.debug('Close button was found. Try to close')
        try:
            close_button.click()
        except BanOnServer:
            raise
        except Exception:
            self.LOGGER.debug('Button is not interactable')
        else:
            self.LOGGER.debug('Successfully closed')

    def interrupt_web_translation(self):
        self._need_interrupt = True

    def check_and_raise_interrupt(self):
        if self._need_interrupt:
            self._need_interrupt = False
            self._raise_interrupt_exception()

    def _web_translate(self, text, dest, src, _force_input_logic=None, check_limit=True):
        if not selenium_session:
            raise RuntimeError('Selenium install is incorrect.')
        dest = self.get_lang_code(dest, True)
        src = self.get_lang_code(src, False)
        text, dest, src = map(utils.Encoding.utf8decode, (text, dest, src))
        text = text.replace(u'[', u'(').replace(']', u')')
        with selenium_session.lock:
            self._need_interrupt = False
            URL = 'https://www.deepl.com/translator'
            _counter = 0
            while True:
                self.check_and_raise_interrupt()
                if _counter >= 2:
                    break
                _reloaded = selenium_session.reload_if_need()
                _url_count = selenium_session.url_get_count(URL)
                if self._max_get is None or not _url_count:
                    self._max_get = random.randint(15, 30)
                if not _reloaded and _url_count >= self._max_get:
                    self.LOGGER.debug('Preventive browser reloading.')
                    selenium_session.reload()
                    time.sleep(5.0)
                _exception = Exception('Undefined error.')
                for _attempt_count in pseudonyms.xrange(10):
                    self.check_and_raise_interrupt()
                    selenium_session.get(URL)
                    self.check_and_raise_interrupt()
                    if self.is_banned(0.5):
                        raise BanOnServer()
                    self.__close_cookie_banner()
                    try:
                        ext_banner = self.wait_element('ext_banner')
                    except exceptions.TimeoutException:
                        self.LOGGER.debug('No ext banner was found')
                    else:
                        self.LOGGER.debug('Try close ext banner')
                        try:
                            for _variant in ext_banner.find_elements(By.TAG_NAME, 'button'):
                                if _variant.get_attribute('aria-label'):
                                    _variant.click()
                                    self.LOGGER.debug('Successfully closed')
                                    break
                            else:
                                self.LOGGER.debug('No close button was found')
                        except Exception as ex:
                            self.LOGGER.exception(ex)
                    break
                else:
                    raise _exception
                self._try_login()
                source_lang_button = self.__get_lang_button(src, False)
                selenium_session.move_to_element(source_lang_button, 'source_lang_button')
                source_lang_button.click()
                self.LOGGER.debug('Source language selected.')
                dest_lang_button = self.__get_lang_button(dest, True)
                selenium_session.move_to_element(dest_lang_button, 'dest_lang_button')
                dest_lang_button.click()
                self.LOGGER.debug('Destination language selected.')
                input_area = self.wait_element('input_area', move_to=True)
                input_area.clear()
                input_area.click()
                self.LOGGER.debug('Start text typing.')
                try:
                    self._send_text(input_area, text, _force_input_logic, check_limit)
                except RestartInput:
                    self.LOGGER.debug('Found page block. Reload page.')
                    continue
                else:
                    self.LOGGER.debug('The text is typed.')
                try:
                    result = u''
                    for _attempt in pseudonyms.xrange(5):
                        _attempt += 1
                        if self.find_element('limit_proad', default=None):
                            raise Exception('limit_proad')
                        self.LOGGER.debug('Wait output text. Attempt %d.', _attempt)
                        result = self.__wait_output_text(7.0)
                        result = utils.Encoding.utf8decode(result)
                        if not result and text.strip():
                            self.LOGGER.debug('No result. Try again.')
                            continue
                        self.LOGGER.debug('Successful.')
                        input_area.clear()
                        return result.strip()
                except RestartInput:
                    self.LOGGER.debug('Found page block. Reload page.')
                    continue
                if len(text.strip().split(u'\n\n\n')) > 1:
                    if self.find_element('unsupported_lang_error', default=None):
                        raise Exception('unsupported_lang_error')
                    raise Exception('Page markup has been changed.')
                input_area.clear()
                self.LOGGER.debug('No result. Try again.')
                _counter += 1
                continue
            return u''

    def find_element(self, data, by='xpath_name', **kwargs):
        self.check_and_raise_interrupt()
        if self.is_banned(0.0):
            raise BanOnServer()
        if by == 'xpath_name':
            if kwargs.get('_log', True):
                kwargs['_log'] = data
            data = XPATHS[data]
            by = By.XPATH
        return selenium_session.find_element(data, by=by, **kwargs)

    def wait_element(self, data, by='xpath_name', **kwargs):
        self.check_and_raise_interrupt()
        if self.is_banned(0.0):
            raise BanOnServer()
        if by == 'xpath_name':
            if kwargs.get('_log', True):
                kwargs['_log'] = data
            data = XPATHS[data]
            by = By.XPATH
        kwargs['by'] = by
        return selenium_session.wait_element(data, **kwargs)
