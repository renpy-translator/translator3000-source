# -*- coding: utf-8 -*-
"""Generate src/translations/translator3000_vietnamese.rpy.

Reads the English translation file (Russian old -> English new) and emits
Russian old -> Vietnamese new. VI is keyed by the English text; the script
fails if any English string has no Vietnamese translation or if format
placeholders differ.
"""
import ast
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.dirname(HERE)
EN_FILE = os.path.join(SRC, "src", "translations", "translator3000_english.rpy")
OUT_FILE = os.path.join(SRC, "src", "translations", "translator3000_vietnamese.rpy")

VI = {
    "{0:.0f} requests per minute.": "{0:.0f} yêu cầu mỗi phút.",
    "{0:.2f} Mbit/sec.": "{0:.2f} Mbit/giây.",
    "{0} the prescan.": "{0} quét trước.",
    "Raise traceback.": "Hiện traceback.",
    "Boolean parameters.": "Tham số boolean.",
    "Version {0}.{1}.{2}.": "Phiên bản {0}.{1}.{2}.",
    "An error has occurred in the prescan thread.": "Đã xảy ra lỗi trong luồng quét trước.",
    "An error occurred while trying to read a configuration file. Double-check the entered data (commas, quotation marks in text values, missing closing tokens - '}', ']', etc.": "Đã xảy ra lỗi khi đọc file cấu hình. Kiểm tra lại dữ liệu đã nhập (dấu phẩy, dấu ngoặc kép ở giá trị văn bản, thiếu token đóng - '}', ']', v.v.",
    "Resume translator's work.": "Tiếp tục công việc của trình dịch.",
    "Language preference.": "Chọn ngôn ngữ.",
    "Pick from the game files.": "Chọn từ file của game.",
    "Pick from the PC files.": "Chọn từ file trên máy tính.",
    "Bold text.": "Chữ đậm.",
    "Downloaded {0:.2f}Mb of {1:.2f}.": "Đã tải {0:.2f}Mb / {1:.2f}.",
    "Download is failed.": "Tải xuống thất bại.",
    "Download completed. The file is saved near the \"game\" folder. Move it to the \"game\" folder, replacing the old one.": "Tải xuống hoàn tất. File được lưu cạnh thư mục \"game\". Di chuyển nó vào thư mục \"game\", thay thế file cũ.",
    "Start": "Bắt đầu",
    "The value '{0}' should be a number.": "Giá trị '{0}' phải là số.",
    "The original language of the game.": "Ngôn ngữ gốc của game.",
    "Italic text.": "Chữ nghiêng.",
    "Modifiers.": "Phím bổ trợ.",
    "Translator update module.": "Module cập nhật trình dịch.",
    "Prescan module.": "Module quét trước.",
    "A translator update is available on GitHub.": "Có bản cập nhật trình dịch trên GitHub.",
    "Direction of translation.": "Hướng dịch.",
    "Configure": "Cấu hình",
    "Configure the parameters of the displayed text.": "Cấu hình thông số của văn bản hiển thị.",
    "Settings for the displayed text.": "Cài đặt văn bản hiển thị.",
    "Translator settings.": "Cài đặt trình dịch.",
    "Font settings.": "Cài đặt phông chữ.",
    "Start downloading.": "Bắt đầu tải xuống.",
    "Not set.": "Chưa đặt.",
    "Go to \"{0}\".": "Đi tới \"{0}\".",
    "Go to the previous directory.": "Đi tới thư mục trước.",
    "Change the interface language.": "Đổi ngôn ngữ giao diện.",
    "The prescan is complete.": "Quét trước đã hoàn tất.",
    "The prescan is complete": "Quét trước đã hoàn tất",
    "Cyclic restart of the prescan.": "Tự khởi động lại quét trước theo chu kỳ.",
    "Pause": "Tạm dừng",
    "Pause translator's work.": "Tạm dừng công việc của trình dịch.",
    "The path should be a string.": "Đường dẫn phải là chuỗi.",
    "Size {0:.2f}Mb.": "Kích thước {0:.2f}Mb.",
    "Size.": "Kích thước.",
    "Debug mode.": "Chế độ gỡ lỗi.",
    "Reset.": "Đặt lại.",
    "Save database to hard drive.": "Lưu cơ sở dữ liệu vào ổ cứng.",
    "Translation service.": "Dịch vụ dịch.",
    "Hide Notification.": "Ẩn thông báo.",
    "Change.": "Thay đổi.",
    "Save.": "Lưu.",
    "Save the original text in the history.": "Lưu văn bản gốc vào lịch sử.",
    "The quick brown fox jumps over the lazy dog.\n(1 + 2) - 3 = (45 / 6789) * 0": "Tiếng Việt là ngôn ngữ của người Việt, có đầy đủ dấu thanh.\n(1 + 2) - 3 = (45 / 6789) * 0",
    "No font file was found.": "Không tìm thấy file phông chữ.",
    "Frequency of requests.": "Tần suất yêu cầu.",
    "Font.": "Phông chữ.",
    "Interface language (not the translation language).": "Ngôn ngữ giao diện (không phải ngôn ngữ dịch).",
    "Pick from the previously used ones.": "Chọn từ những mục đã dùng trước đây.",
    "Yes.": "Có.",
    "The translation cache will be cleared.": "Bộ nhớ đệm bản dịch sẽ bị xóa.",
    "The translation cache for the game will be cleared.": "Bộ nhớ đệm bản dịch của game sẽ bị xóa.",
    "No.": "Không.",
    "Clear all translation cache.": "Xóa toàn bộ bộ nhớ đệm bản dịch.",
    "Clear the cache of translations of the game.": "Xóa bộ nhớ đệm bản dịch của game.",
    "The parameter does not work in the whole text translation mode.": "Tham số này không hoạt động ở chế độ dịch toàn bộ văn bản.",
    "The first time you turn on this mode, the game may \"freeze\" for a long time (probably a few minutes), as the translator must translate all the elements of the environment. Continue?": "Lần đầu bật chế độ này, game có thể \"đơ\" trong thời gian dài (có thể vài phút), vì trình dịch phải dịch mọi phần tử của môi trường. Tiếp tục?",
    "Unknown error.": "Lỗi không xác định.",
    "Translation of all text in the game (Beta).": "Dịch toàn bộ văn bản trong game (Beta).",
    "Translation of dialogs and choice menus.": "Dịch hội thoại và menu lựa chọn.",
    "Method of work of the translator.": "Cách hoạt động của trình dịch.",
    "\"{0}\" translator's method of working is unknown.": "Không rõ cách hoạt động \"{0}\" của trình dịch.",
    "Support the developer.": "Ủng hộ nhà phát triển.",
    "For this translation service, the frequency of requests is unchangeable.": "Với dịch vụ dịch này, tần suất yêu cầu không thay đổi được.",
    "Split sentences during translation.": "Tách câu khi dịch.",
    "Preparing a prescan thread.": "Đang chuẩn bị luồng quét trước.",
    "{done} requests of {total} were done.\nThis game has a total of {strings} strings ({symbols} characters).": "Đã thực hiện {done} / {total} yêu cầu.\nGame này có tổng cộng {strings} chuỗi ({symbols} ký tự).",
    "The prescan thread is restarted.": "Luồng quét trước đang được khởi động lại.",
    "{done} parts prepared.\nThis game has a total of {strings} strings ({symbols} characters).": "Đã chuẩn bị {done} phần.\nGame này có tổng cộng {strings} chuỗi ({symbols} ký tự).",
    "Restart the prescan thread.": "Khởi động lại luồng quét trước.",
    "Realtime translation at the start of the game.": "Dịch thời gian thực khi bắt đầu game.",
    "Prescan at the start of the game.": "Quét trước khi bắt đầu game.",
    "If not, enter them and restart the prescan.": "Nếu chưa, hãy nhập chúng và khởi động lại quét trước.",
    "String preparation is in progress.": "Đang chuẩn bị chuỗi.",
    "For a correct translation, make sure that all dynamic data (player name etc.) is entered before starting the scan.": "Để dịch đúng, hãy chắc chắn mọi dữ liệu động (tên người chơi, v.v.) đã được nhập trước khi bắt đầu quét.",
    "It may seem like the process has \"freeze\", but it hasn't. If the game is a big one, preparations can take some minutes.": "Có thể trông như tiến trình bị \"đơ\", nhưng không phải vậy. Nếu game lớn, việc chuẩn bị có thể mất vài phút.",
    "The preparation process may take several minutes, depending on the size.": "Quá trình chuẩn bị có thể mất vài phút, tùy thuộc vào kích thước.",
    "This game contains {0} strings ({1} characters).": "Game này chứa {0} chuỗi ({1} ký tự).",
    "{done} requests of {total} were done.": "Đã thực hiện {done} / {total} yêu cầu.",
    "Completion of the process. Final check of the database.": "Hoàn tất tiến trình. Kiểm tra cuối cơ sở dữ liệu.",
    "{done} parts prepared.": "Đã chuẩn bị {done} phần.",
    "Checked {done} parts out of {total}.": "Đã kiểm tra {done} / {total} phần.",
    "Strings translation.": "Dịch chuỗi.",
    "An update is available.": "Có bản cập nhật.",
    "Download Translator3000 Version {0}.{1}.{2} from Boosty.": "Tải Translator3000 Phiên bản {0}.{1}.{2} từ Boosty.",
    "Use only database.": "Chỉ dùng cơ sở dữ liệu.",
    "Disabled.": "Đã tắt.",
    "Real-time translation.": "Dịch thời gian thực.",
    "Prescan.": "Quét trước.",
    "Work mode.": "Chế độ hoạt động.",
    "Autoload.": "Tự động nạp.",
    "Display original text on the screen.": "Hiển thị văn bản gốc trên màn hình.",
    "Color.": "Màu sắc.",
    "Check availability of completed translation.": "Kiểm tra bản dịch hoàn chỉnh có sẵn.",
    "Support the developer on Boosty.": "Ủng hộ nhà phát triển trên Boosty.",
    "Support the developer on Patreon.": "Ủng hộ nhà phát triển trên Patreon.",
    "Download Translator3000 Version {0}.{1}.{2} from Patreon.": "Tải Translator3000 Phiên bản {0}.{1}.{2} từ Patreon.",
    "No translation was found.": "Không tìm thấy bản dịch.",
    "Substitute variables from downloaded database.": "Thay thế biến từ cơ sở dữ liệu đã tải.",
    "Select the desired key combination on the keyboard.": "Chọn tổ hợp phím mong muốn trên bàn phím.",
    "Key combination selection.": "Chọn tổ hợp phím.",
    "Key combinations.": "Tổ hợp phím.",
    "Waiting for keystrokes.": "Đang chờ nhấn phím.",
    "Main Key.": "Phím chính.",
    "Disable Combination.": "Tắt tổ hợp.",
    "Default.": "Mặc định.",
    "Set the above combination.": "Đặt tổ hợp ở trên.",
    "Wait...": "Chờ...",
    "\"Step\" of variables values change": "\"Bước\" thay đổi giá trị biến",
    "Show a text editing window.": "Hiện cửa sổ sửa văn bản.",
    "Change the object's properties (if any).": "Thay đổi thuộc tính của đối tượng (nếu có).",
    "Invert value.": "Đảo giá trị.",
    "Confirm changes.": "Xác nhận thay đổi.",
    "Edit game's variables.": "Sửa biến của game.",
    "Edit text.": "Sửa văn bản.",
    "Current page": "Trang hiện tại",
    "Editing is not possible.": "Không thể chỉnh sửa.",
    "Download Translator3000 Version {0}.{1}.{2} from Housefly.": "Tải Translator3000 Phiên bản {0}.{1}.{2} từ Housefly.",
    "Time spent in-game:": "Thời gian trong game:",
    "Telegram group.": "Nhóm Telegram.",
    "Support the developer on Housefly.": "Ủng hộ nhà phát triển trên Housefly.",
    "Discord server.": "Máy chủ Discord.",
    "Display the text editing window": "Hiển thị cửa sổ sửa văn bản",
    "Translator settings": "Cài đặt trình dịch",
    "Off": "Tắt",
    "Clear all translation cache": "Xóa toàn bộ bộ nhớ đệm bản dịch",
    "Clear the cache of translations of the game": "Xóa bộ nhớ đệm bản dịch của game",
    "Support the developer on Boosty": "Ủng hộ nhà phát triển trên Boosty",
    "Support the developer on Housefly": "Ủng hộ nhà phát triển trên Housefly",
    "Support the developer on Patreon": "Ủng hộ nhà phát triển trên Patreon",
    "Change the interface language": "Đổi ngôn ngữ giao diện",
    "Prescan": "Quét trước",
    "Edit game's variables": "Sửa biến của game",
    "Realtime + DB": "Thời gian thực + CSDL",
    "Save database to hard drive": "Lưu cơ sở dữ liệu vào ổ cứng",
    "Statistics": "Thống kê",
    "DB only": "Chỉ CSDL",
    "Enable/disable translation in the DB mode.": "Bật/tắt dịch ở chế độ CSDL.",
    "Showing/hiding the translator window": "Hiện/ẩn cửa sổ trình dịch",
    "Showing/hiding the text editing window": "Hiện/ẩn cửa sổ sửa văn bản",
    "Showing/hiding original text": "Hiện/ẩn văn bản gốc",
    "Version {0}.{1}.{2} ({3}).": "Phiên bản {0}.{1}.{2} ({3}).",
    "Download Translator3000 Version {0}.{1}.{2} ({3}) from Boosty.": "Tải Translator3000 Phiên bản {0}.{1}.{2} ({3}) từ Boosty.",
    "Download Translator3000 Version {0}.{1}.{2} ({3}) from Housefly.": "Tải Translator3000 Phiên bản {0}.{1}.{2} ({3}) từ Housefly.",
    "Download Translator3000 Version {0}.{1}.{2} ({3}) from Patreon.": "Tải Translator3000 Phiên bản {0}.{1}.{2} ({3}) từ Patreon.",
    "All text.": "Toàn bộ văn bản.",
    "Only the text in the choice menu.": "Chỉ văn bản trong menu lựa chọn.",
    "Extra translation.": "Bản dịch bổ sung.",
    "Read": "Đã đọc",
    "Read all": "Đọc tất cả",
    "Yeaaah!": "Tuyệt vời!",
    "Close window": "Đóng cửa sổ",
    "The notification feed from Translator3000 team": "Nguồn thông báo từ nhóm Translator3000",
    "The scale of the main window": "Tỷ lệ cửa sổ chính",
    "Naaaaah...": "Thôi nào...",
    "Disable translator": "Tắt trình dịch",
    "Open a website with documentation": "Mở trang web tài liệu",
    "Switch the color theme": "Đổi chủ đề màu",
    "Page Scrolling": "Cuộn trang",
    "Scroll up the page": "Cuộn trang lên",
    "Scroll down the page": "Cuộn trang xuống",
    "Maximize": "Phóng to",
    "Adjust the transparency of the main window": "Điều chỉnh độ trong suốt của cửa sổ chính",
    "A translation mode that uses an existing database and performs network requests for previously untranslated text": "Chế độ dịch dùng cơ sở dữ liệu hiện có và gửi yêu cầu mạng cho văn bản chưa dịch",
    "The translation mode uses only the available database (without network requests)": "Chế độ dịch chỉ dùng cơ sở dữ liệu hiện có (không gửi yêu cầu mạng)",
    "Pre scan mode": "Chế độ quét trước",
    "Increase the text size": "Tăng kích thước chữ",
    "Zoom in the main window (also \"ctrl +\")": "Phóng to cửa sổ chính (hoặc \"ctrl +\")",
    "Reduce the text size": "Giảm kích thước chữ",
    "Zoom out the main window (also \"ctrl -\")": "Thu nhỏ cửa sổ chính (hoặc \"ctrl -\")",
    "The font will be set automatically according to the selected translation language": "Phông chữ sẽ tự động đặt theo ngôn ngữ dịch đã chọn",
    "Minimize": "Thu nhỏ",
    "Help\nOpen the help": "Trợ giúp\nMở trợ giúp",
    "Use an alternative sorting method in the prescan": "Dùng phương pháp sắp xếp thay thế khi quét trước",
    "Use the visible translator's display button.": "Dùng nút hiển thị trình dịch.",
    "Showing/hiding an alternative translation": "Hiện/ẩn bản dịch thay thế",
    "Show alternative translations": "Hiện bản dịch thay thế",
    "Back": "Quay lại",
    "A ready-made database was found in the cloud. The service has been changed to \"{service_name}\"": "Đã tìm thấy cơ sở dữ liệu có sẵn trên đám mây. Dịch vụ đã đổi thành \"{service_name}\"",
    "Prescan is complete": "Quét trước đã hoàn tất",
    "Translation service has been changed": "Dịch vụ dịch đã thay đổi",
    "Great!\nSend the file {name_only} from the game folder (should have opened in the background) to the translator's Telegram channel (the link should have opened in the browser or Telegram application).": "Tuyệt!\nGửi file {name_only} từ thư mục game (lẽ ra đã mở ở nền) tới kênh Telegram của trình dịch (liên kết lẽ ra đã mở trong trình duyệt hoặc ứng dụng Telegram).",
    "Prescan is over!\nA game translation database has been created.\n\nShare the finished translation in the Telegram channel with other users so that they can get an instant translation of this game!\n\nShare it?": "Quét trước đã xong!\nĐã tạo cơ sở dữ liệu dịch của game.\n\nChia sẻ bản dịch hoàn chỉnh trong kênh Telegram với người dùng khác để họ có bản dịch tức thì của game này!\n\nChia sẻ?",
    "Show this notification in the future?": "Hiện thông báo này trong tương lai?",
    "Reset settings for pop-up notifications.": "Đặt lại cài đặt thông báo bật lên.",
    "Enable \"no freeze\" mode": "Bật chế độ \"không đơ\"",
    "Refresh page": "Làm mới trang",
    "Great!\nSend the file \"{name_only}\" (folder should have opened in the background) to the translator's Telegram channel (the link should have opened in the browser or Telegram application).": "Tuyệt!\nGửi file \"{name_only}\" (thư mục lẽ ra đã mở ở nền) tới kênh Telegram của trình dịch (liên kết lẽ ra đã mở trong trình duyệt hoặc ứng dụng Telegram).",
    "Translation in extra window.": "Dịch trong cửa sổ riêng.",
    "Completion of the process. It's almost done...": "Hoàn tất tiến trình. Sắp xong...",
    "Immutable.": "Không thay đổi được.",
    "Not found": "Không tìm thấy",
    "Not found.": "Không tìm thấy.",
    "Search.": "Tìm kiếm.",
    "Stop searching.": "Dừng tìm kiếm.",
    "Favorites": "Yêu thích",
    "Search results": "Kết quả tìm kiếm",
    "Outline.": "Viền chữ.",
    "Layer {0}.": "Lớp {0}.",
    "Delete layer {0}.": "Xóa lớp {0}.",
    "Add layer.": "Thêm lớp.",
    "VK group.": "Nhóm VK.",
    "Last executed code:": "Mã vừa thực thi:",
    "Hidden item": "Mục ẩn",
    "Condition for displaying:": "Điều kiện hiển thị:",
    "Expanding the choice menu": "Mở rộng menu lựa chọn",
    "Choose from the system fonts.": "Chọn từ phông chữ hệ thống.",
    "# Some code": "# Một đoạn mã",
    "If {0}:\n": "Nếu {0}:\n",
    "Else:\n": "Ngược lại:\n",
    "True": "Đúng",
    "False": "Sai",
    "None": "Không có",
    "Default (standart path)": "Mặc định (đường dẫn chuẩn)",
    "not": "không",
    "is not": "không phải là",
    "is": "là",
    "Enable/disable the choice menu expanding": "Bật/tắt mở rộng menu lựa chọn",
}

# Extra strings used by the GUI but missing from the English file.
EXTRA = [
    ("Размер слоя {0}.", "Layer {0} size.", "Kích thước lớp {0}."),
    ("Смещение слоя {0} по оси {1}.", "Layer {0} offset along the {1} axis.", "Độ lệch lớp {0} theo trục {1}."),
    ("Статистика.", "Statistics.", "Thống kê."),
    ("Цвет слоя {0}.", "Layer {0} color.", "Màu lớp {0}."),
]


def parse_pairs(path):
    pairs, old = [], None
    for line in io.open(path, encoding="utf-8").read().splitlines():
        s = line.strip()
        if s.startswith("old "):
            old = ast.literal_eval(s[4:].strip())
        elif s.startswith("new "):
            pairs.append((old, ast.literal_eval(s[4:].strip())))
            old = None
    return pairs


def placeholders(text):
    return sorted(re.findall(r"\{[^}]*\}", text))


def quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def main():
    pairs = parse_pairs(EN_FILE)
    missing, out = [], ["init -200:", "    translate translator3000_vietnamese strings:"]
    for ru, en in pairs:
        vi = VI.get(en)
        if vi is None:
            missing.append(en)
            continue
        if placeholders(en) != placeholders(vi):
            missing.append("placeholder mismatch: " + en)
            continue
        out.append("        old " + quote(ru))
        out.append("        new " + quote(vi))
    for ru, _en, vi in EXTRA:
        out.append("        old " + quote(ru))
        out.append("        new " + quote(vi))
    if missing:
        print("missing/mismatch %d" % len(missing))
        for m in missing:
            print(" -", m)
        return 1
    with io.open(OUT_FILE, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("wrote %s (%d pairs)" % (OUT_FILE, len(pairs) + len(EXTRA)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
