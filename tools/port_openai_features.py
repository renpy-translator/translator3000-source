# -*- coding: utf-8 -*-
"""Port the OpenAI-edition features into this repo's native layout.

The sibling repo `translator3000-openai` ships the same features as loose
modules (`src/tr3000_*.py`) loaded on top of a stock Translator3000 archive.
This repo integrates them instead (see AGENTS.md):

    tr3000_ui.py            -> _translator3000/_openai_labels.py  (+ VI map)
    tr3000_openai.py        -> _translator3000/_openai/client.py
                               (+ native _openai/translator*.py, see below)
    tr3000_ui_translate.py  -> _translator3000/_ui_translate.py
    tr3000_mode_toggle.py   -> _translator3000/_mode_toggle.py
    tr3000_autofit.py       -> _translator3000/_autofit.py
    tr3000_transfer.py      -> _translator3000/_transfer.py
    tr3000_disable_update.py-> _translator3000/_disable_update.py

Every file is written into BOTH module trees (py2 and py3); the ported code
is dual-compatible, exactly as in the sibling repo. Registration in
`_translator3000/translator.py` and the screens/hooks in
`src/000translator3000_main.rpy` are maintained by hand in this repo and are
NOT touched by this script.

Usage:
    python tools/port_openai_features.py [--openai-src PATH]
"""
import argparse
import io
import os

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TREES = (
    os.path.join(REPO, "src", "_translator3000_main_modules", "py2", "_translator3000"),
    os.path.join(REPO, "src", "_translator3000_main_modules", "py3", "_translator3000"),
)

BANNER = (
    "# Integrated into translator3000-source (native _translator3000 module).\n"
    "# Ported from translator3000-openai by tools/port_openai_features.py;\n"
    "# keep feature behavior in sync between the two repos (see AGENTS.md).\n"
)


def read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    parent = os.path.dirname(path)
    if not os.path.isdir(parent):
        os.makedirs(parent)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print("wrote", os.path.relpath(path, REPO))


def add_banner(text):
    lines = text.split("\n")
    at = 1 if lines and lines[0].startswith("# -*- coding") else 0
    lines.insert(at, BANNER.rstrip("\n"))
    return "\n".join(lines)


VIETNAMESE = {
    'API-ключи': 'Khóa API',
    'Изменить ключ': 'Đổi khóa',
    'Ввести ключ': 'Nhập khóa',
    'Удалить ключ': 'Xóa khóa',
    'Ключ введён': 'Đã nhập khóa',
    'Ключ не введён': 'Chưa nhập khóa',
    'Готово': 'Xong',
    'Изменить Base URL': 'Đổi Base URL',
    'Сохранять ключ для текущего пользователя Windows': 'Lưu khóa cho người dùng Windows hiện tại',
    'OpenAI API оплачивается отдельно. Сохранённый ключ защищён Windows.': 'OpenAI API tính phí riêng. Khóa đã lưu được Windows bảo vệ.',
    'Учётная запись ChatGPT': 'Tài khoản ChatGPT',
    'Войти через ChatGPT': 'Đăng nhập bằng ChatGPT',
    'Проверить вход': 'Kiểm tra đăng nhập',
    'Отменить': 'Hủy',
    'Без API-ключа. Действуют доступные модели и лимиты вашего тарифа, включая Free.': 'Không cần khóa API. Áp dụng các mô hình và giới hạn của gói của bạn, kể cả Free.',
    'codex.exe: автоматически': 'codex.exe: tự động',
    'Указать путь к codex.exe': 'Chọn đường dẫn tới codex.exe',
    'Сохранить настройки': 'Lưu cài đặt',
    'Выбрать подключение для перевода': 'Chọn kết nối dịch',
    'OpenAI / ChatGPT — перевод': 'OpenAI / ChatGPT — dịch',
    'API-ключ / вход через ChatGPT': 'Khóa API / Đăng nhập ChatGPT',
    'Подключение': 'Kết nối',
    'ChatGPT: лимиты учётной записи. API: отдельная оплата.': 'ChatGPT: giới hạn theo tài khoản. API: tính phí riêng.',
    'Модель для ': 'Mô hình cho ',
    'Доступ к выбранной модели зависит от вашего аккаунта.': 'Quyền dùng mô hình đã chọn tùy thuộc vào tài khoản của bạn.',
    'Размышления': 'Suy luận',
    'Без размышлений': 'Không suy luận',
    'Лёгкие': 'Thấp',
    'Средние': 'Trung bình',
    'Глубокие': 'Cao',
    'Очень глубокие': 'Rất cao',
    'Максимальные': 'Tối đa',
    'Предельные': 'Cực hạn',
    'Пакеты GPT': 'Gói GPT',
    'До %d символов': 'Tối đa %d ký tự',
    'Сканирование: порядок сцен, целые строки, контекст соседних реплик.': 'Quét: theo thứ tự cảnh, trọn dòng, có ngữ cảnh các dòng thoại gần đó.',
    'API получает файл JSON целиком. ChatGPT получает тот же пакет целиком.': 'API nhận toàn bộ tệp JSON. ChatGPT nhận cùng gói đó.',
    'Ответ проверяется до последней строки. При обрыве пакет делится автоматически.': 'Kết quả được kiểm tra đến dòng cuối. Gói bị đứt sẽ tự động chia nhỏ.',
    'В живом переводе передаются доступные реплики. Для всей игры запустите предварительное сканирование.': 'Dịch trực tiếp gửi các dòng thoại khả dụng. Hãy chạy quét trước để dịch toàn bộ game.',
    'Проверка подключения': 'Kiểm tra kết nối',
    'Проверить перевод': 'Kiểm tra dịch',
    'Подогнать размер текста': 'Tự chỉnh cỡ chữ',
    'OpenAI API — перевод по ключу': 'OpenAI API — dịch bằng khóa',
    'ChatGPT — вход в учётную запись': 'ChatGPT — đăng nhập tài khoản',
    'Выберите подключение и модель, затем проверьте связь.': 'Chọn kết nối và mô hình, rồi kiểm tra kết nối.',
    'Вход через ChatGPT не проверен.': 'Chưa kiểm tra đăng nhập ChatGPT.',
    'Завершите вход в браузере.': 'Hoàn tất đăng nhập trong trình duyệt.',
    'Проверка входа...': 'Đang kiểm tra đăng nhập...',
    'Вход через ChatGPT выполнен.': 'Đã đăng nhập bằng ChatGPT.',
    'Не удалось выполнить вход. Проверьте путь к codex.exe.': 'Đăng nhập thất bại. Kiểm tra đường dẫn codex.exe.',
    'Не удалось прочитать настройки OpenAI. Введите ключ заново.': 'Không đọc được cài đặt OpenAI. Nhập lại khóa.',
    'Настройки сохранены.': 'Đã lưu cài đặt.',
    'Не удалось сохранить настройки OpenAI.': 'Không lưu được cài đặt OpenAI.',
    'Сначала выберите один из сервисов OpenAI.': 'Hãy chọn một dịch vụ OpenAI trước.',
    'Проверка связи…': 'Đang kiểm tra kết nối…',
    'Связь работает: ': 'Kết nối OK: ',
    'Ошибка подключения. Проверьте настройки и доступ к модели.': 'Lỗi kết nối. Kiểm tra cài đặt và quyền dùng mô hình.',
    'Перевод строк %d–%d из %d; %s, %s.': 'Đang dịch dòng %d–%d trong %d; %s, %s.',
    'Готово: %d строк, включая последнюю. Теги и переменные проверены.': 'Xong: %d dòng, kể cả dòng cuối. Đã kiểm tra thẻ và biến.',
    'OpenAI изменил теги или переменные. Ответ не сохранён.': 'OpenAI đã thay đổi thẻ hoặc biến. Không lưu kết quả.',
    'OpenAI добавил разметку. Ответ не сохранён.': 'OpenAI đã thêm markup. Không lưu kết quả.',
    'OpenAI изменил порядок тегов. Ответ не сохранён.': 'OpenAI đã thay đổi thứ tự thẻ. Không lưu kết quả.',
    'Сохранение ключа поддерживается только в Windows.': 'Lưu khóa chỉ hỗ trợ trên Windows.',
    'Windows не смогла обработать сохранённый ключ.': 'Windows không xử lý được khóa đã lưu.',
    'Введите ключ OpenAI API в настройках OpenAI.': 'Nhập khóa OpenAI API trong cài đặt OpenAI.',
    'Впишите api_key в общий _translator3000_openai.json Translator3000.': 'Điền api_key vào _translator3000_openai.json dùng chung của Translator3000.',
    'Base URL должен начинаться с http:// или https://.': 'Base URL phải bắt đầu bằng http:// hoặc https://.',
    'Ответ слишком большой; пакет будет разделён.': 'Kết quả quá lớn; gói sẽ được chia nhỏ.',
    'OpenAI не завершил перевод. Ответ не сохранён.': 'OpenAI chưa dịch xong. Không lưu kết quả.',
    'API не завершил перевод или отказал. Ответ не сохранён.': 'API chưa dịch xong hoặc từ chối. Không lưu kết quả.',
    'Ключ OpenAI недействителен.': 'Khóa OpenAI không hợp lệ.',
    'Лимит запросов или баланс OpenAI исчерпан.': 'Đã hết giới hạn yêu cầu hoặc số dư OpenAI.',
    'Модель недоступна этому API-аккаунту.': 'Tài khoản API này không dùng được mô hình đó.',
    'Нет доступа к OpenAI или выбранной модели.': 'Không truy cập được OpenAI hoặc mô hình đã chọn.',
    'Ошибка OpenAI API: HTTP %s.': 'Lỗi OpenAI API: HTTP %s.',
    'Не удалось проверить сертификат API. Проверьте Base URL и доверенный сертификат.': 'Không xác thực được chứng chỉ API. Kiểm tra Base URL và chứng chỉ tin cậy.',
    'Нет корректного ответа OpenAI. Проверьте интернет-соединение или Base URL.': 'Không có phản hồi hợp lệ từ OpenAI. Kiểm tra internet hoặc Base URL.',
    'Codex не найден. Укажите путь к codex.exe в настройках OpenAI.': 'Không tìm thấy Codex. Chọn đường dẫn codex.exe trong cài đặt OpenAI.',
    'Операция отменена или истекло время ожидания Codex.': 'Thao tác đã bị hủy hoặc Codex quá thời gian chờ.',
    'Не удалось запустить codex.exe.': 'Không chạy được codex.exe.',
    'Нажмите "Войти через ChatGPT" в разделе "OpenAI / ChatGPT — перевод".': 'Bấm "Đăng nhập bằng ChatGPT" trong mục "OpenAI / ChatGPT — dịch".',
    'Вход не завершён. Повторите вход через ChatGPT.': 'Đăng nhập chưa xong. Đăng nhập lại bằng ChatGPT.',
    'Лимит ChatGPT/Codex исчерпан. Дождитесь его обновления.': 'Đã hết giới hạn ChatGPT/Codex. Chờ giới hạn được làm mới.',
    'Codex не выполнил перевод. Проверьте вход и доступ к модели.': 'Codex không dịch được. Kiểm tra đăng nhập và quyền dùng mô hình.',
    'Неизвестная модель.': 'Mô hình không xác định.',
    'Неизвестное подключение или модель OpenAI.': 'Kết nối hoặc mô hình OpenAI không xác định.',
    'Модель отказалась переводить этот текст. Ответ не сохранён.': 'Mô hình từ chối dịch văn bản này. Không lưu kết quả.',
    'Неполный или некорректный перевод. Ответ не сохранён.': 'Bản dịch chưa trọn hoặc không hợp lệ. Không lưu kết quả.',
    'Перевод отменён.': 'Đã hủy dịch.',
    'Файл перевода': 'Tệp bản dịch',
    'Переводить интерфейс игры (меню, настройки, подсказки)': 'Dịch giao diện game (menu, cài đặt, gợi ý)',
    'Экспорт перевода': 'Xuất bản dịch',
    'Импорт перевода': 'Nhập bản dịch',
    'Файл остаётся на этом компьютере. Его можно передать другому человеку.': 'Tệp nằm trên máy này. Bạn có thể gửi cho người khác.',
    'Сначала выберите сервис перевода.': 'Hãy chọn dịch vụ dịch trước.',
    'Нет перевода для экспорта.': 'Chưa có bản dịch để xuất.',
    'Экспорт отменён.': 'Đã hủy xuất.',
    'Импорт отменён.': 'Đã hủy nhập.',
    'Экспортировано %d строк: %s': 'Đã xuất %d dòng: %s',
    'Импортировано %d новых строк. Уже было %d.': 'Đã nhập %d dòng mới. Đã có sẵn %d dòng.',
    'Файл перевода пуст или имеет неизвестный формат.': 'Tệp bản dịch trống hoặc định dạng lạ.',
    'Не найден сервис %s для импорта.': 'Không tìm thấy dịch vụ %s để nhập.',
    'Выбор файла поддерживается только в Windows.': 'Chọn tệp chỉ hỗ trợ trên Windows.',
    'Не удалось открыть окно выбора файла.': 'Không mở được hộp chọn tệp.',
    'Не удалось экспортировать перевод: %s': 'Không xuất được bản dịch: %s',
    'Не удалось импортировать перевод: %s': 'Không nhập được bản dịch: %s',
}

# UI-translation status strings are keyed by their English text in the labels
# module (they are generated in English by _ui_translate).
UI_STATUS_VIETNAMESE = {
    'UI translation: off (tick the checkbox in OpenAI settings to show UI translations).':
        'Dịch giao diện: tắt (tick ô trong cài đặt OpenAI để hiện bản dịch giao diện).',
    'UI translation: on, following Translator3000 mode (%s).':
        'Dịch giao diện: bật, theo chế độ Translator3000 (%s).',
    'UI translation: following Translator3000 mode (currently unknown).':
        'Dịch giao diện: theo chế độ Translator3000 (chưa rõ).',
    'UI translation: following Translator3000 mode.':
        'Dịch giao diện: theo chế độ Translator3000.',
    'UI translation: on. Open any screen - new labels are translated in the background.':
        'Dịch giao diện: bật. Mở màn hình bất kỳ - nhãn mới được dịch nền.',
    'UI translation: off. Dialogue translation is unaffected.':
        'Dịch giao diện: tắt. Dịch thoại không bị ảnh hưởng.',
    'UI translation: not installed yet.':
        'Dịch giao diện: chưa cài đặt.',
    'UI translation: no active Translator3000 provider - open Translator3000 and pick a service.':
        'Dịch giao diện: chưa có dịch vụ Translator3000 - mở Translator3000 và chọn dịch vụ.',
    "UI translation: Ren'Py text module not found.":
        "Dịch giao diện: không tìm thấy module text của Ren'Py.",
    "UI translation: Text.set_text not found in this Ren'Py version.":
        "Dịch giao diện: không tìm thấy Text.set_text trong phiên bản Ren'Py này.",
    'UI translation: uninstalled.':
        'Dịch giao diện: đã gỡ.',
}


def port_labels(src_dir):
    text = read(os.path.join(src_dir, "tr3000_ui.py"))
    assert "def translate(text):" in text
    head, tail = text.split("def translate(text):", 1)
    vi = dict(VIETNAMESE)
    vi.update(UI_STATUS_VIETNAMESE)
    vi_lines = ["\nVIETNAMESE = {"]
    for key in sorted(vi):
        vi_lines.append("    %r: %r," % (key, vi[key]))
    vi_lines.append("}\n")
    new_tail = (
        "def translate(text):\n"
        "    store = sys.modules.get('store')\n"
        "    translator = getattr(store, 'translator3000', None)\n"
        "    gui = getattr(translator, '_gui', None)\n"
        "    language = getattr(gui, 'gui_language', None)\n"
        "    if language in ('english', 'en'):\n"
        "        mapping = ENGLISH\n"
        "    elif language == 'vietnamese':\n"
        "        mapping = VIETNAMESE\n"
        "    else:\n"
        "        return text\n"
        "    if text in mapping:\n"
        "        return mapping[text]\n"
        "    if text in ENGLISH and text not in mapping:\n"
        "        return text\n"
        + tail.split("\n", 1)[1].replace(
            "    if text in ENGLISH:\n        return ENGLISH[text]\n", ""
        ).replace(
            "    if getattr(gui, 'gui_language', None) not in ('english', 'en'):\n"
            "        return text\n", ""
        ).replace(
            "        return ENGLISH[prefix] + text[len(prefix):]",
            "        return mapping.get(prefix, prefix) + text[len(prefix):]",
        ).replace(
            "    for original, english in ENGLISH.items():",
            "    for original, english in mapping.items():",
        )
    )
    return add_banner(head + "\n".join(vi_lines) + "\n" + new_tail)


def port_client(src_dir):
    text = read(os.path.join(src_dir, "tr3000_openai.py"))
    text = text.replace(
        "from tr3000_ui import translate as ui_translate",
        "from .._openai_labels import translate as ui_translate",
    )
    assert "from .._openai_labels import" in text
    # Native registration lives in _openai/translator.py; drop register().
    start = text.find("\ndef register():")
    assert start != -1
    text = text[:start] + "\n"
    return add_banner(text)


def simple_port(src_dir, name, replacements):
    text = read(os.path.join(src_dir, name))
    for old, new in replacements:
        if old not in text:
            assert new in text, (name, old)
            continue
        text = text.replace(old, new)
    return add_banner(text)


OPENAI_INIT = '''# -*- coding: utf-8 -*-
from .. import LOGGER as _parent_logger

__author__ = 'Translator3000 contributors'
LOGGER = _parent_logger.getChild('OpenAI')
'''

OPENAI_PATHS = '''# -*- coding: utf-8 -*-
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
'''

OPENAI_TRANSLATOR = '''# -*- coding: utf-8 -*-
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
                    text.split('\\n\\n\\n'), result.split('\\n\\n\\n'))][-2:]
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
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--openai-src",
        default=os.path.join(REPO, "..", "translator3000-openai", "src"),
        help="src/ folder of the translator3000-openai repo")
    args = ap.parse_args()
    src_dir = os.path.abspath(args.openai_src)
    if not os.path.isfile(os.path.join(src_dir, "tr3000_openai.py")):
        raise SystemExit("openai src not found: %s" % src_dir)

    files = {
        "_openai_labels.py": port_labels(src_dir),
        os.path.join("_openai", "client.py"): port_client(src_dir),
        os.path.join("_openai", "__init__.py"): OPENAI_INIT,
        os.path.join("_openai", "_paths.py"): OPENAI_PATHS,
        os.path.join("_openai", "translator.py"): OPENAI_TRANSLATOR,
        "_ui_translate.py": simple_port(src_dir, "tr3000_ui_translate.py", [
            ("        import tr3000_openai\n        folder = tr3000_openai.shared_config_dir()",
             "        from ._openai import client as tr3000_openai\n        folder = tr3000_openai.shared_config_dir()"),
            ("import tr3000_openai\n", "from ._openai import client as tr3000_openai\n"),
        ]),
        "_mode_toggle.py": simple_port(src_dir, "tr3000_mode_toggle.py", [
            ("        import tr3000_ui_translate\n",
             "        from . import _ui_translate as tr3000_ui_translate\n"),
            ("import tr3000_ui_translate\n",
             "from . import _ui_translate as tr3000_ui_translate\n"),
        ]),
        "_autofit.py": simple_port(src_dir, "tr3000_autofit.py", []),
        "_transfer.py": simple_port(src_dir, "tr3000_transfer.py", [
            ("        import tr3000_openai\n",
             "        from ._openai import client as tr3000_openai\n"),
            ("    import tr3000_openai\n",
             "    from ._openai import client as tr3000_openai\n"),
            ("import tr3000_openai\n",
             "from ._openai import client as tr3000_openai\n"),
        ]),
        "_disable_update.py": simple_port(src_dir, "tr3000_disable_update.py", []),
    }
    for tree in TREES:
        for rel, text in files.items():
            write(os.path.join(tree, rel), text)
    print("ported %d files x %d trees" % (len(files), len(TREES)))


if __name__ == "__main__":
    main()

