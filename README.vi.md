# Translator3000 — Source dựng lại

<p align="center">
  <a href="README.md">English</a> ·
  <strong>Tiếng Việt</strong> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

> Bản dựng lại **Translator3000** (bản stock `1.45.11`) cho game Ren'Py ở dạng source đọc được, phát triển tiếp được — khôi phục từ file `Translator3000.rpa` phát hành, giải obfuscation toàn bộ, và đóng gói ngược lại thành một file `Translator3000.rpa` duy nhất, thả vào game là chạy.

Translator3000 tự động dịch game Ren'Py ngay trong lúc chơi: nó bắt hội thoại và menu, gửi tới một dịch vụ dịch, lưu mọi kết quả vào cơ sở dữ liệu riêng của từng game, và hiển thị bản dịch thay cho văn bản gốc. Repo này tồn tại vì source hiện tại (v3) của Translator3000 không được công khai — source public cũ (v2) đã lỗi thời nhiều năm. Tại đây, bản stock mới nhất đã được dịch ngược trở lại thành source sạch, để cộng đồng có thể nghiên cứu, sửa lỗi và phát triển thêm tính năng trên nền đó.

---

## ✨ Tính năng

### Dịch thuật

- **Dịch thời gian thực** hội thoại và menu lựa chọn ngay trong lúc chơi.
- **Bốn chế độ hoạt động**: Tắt, Quét trước (dịch toàn bộ game từ đầu), Chỉ CSDL (chỉ hiện bản dịch đã có trong cơ sở dữ liệu), và Thời gian thực + CSDL.
- **Nhiều dịch vụ tích hợp**: Google (GTX / client5 / RPC), Bing, DeepL (API chính thức, RPC, Selenium), Yandex, Reverso và LingvaNex.
- **Cơ sở dữ liệu dịch theo từng game**: mọi câu đã dịch đều được lưu đệm, chơi lại không tốn yêu cầu mới; có sẵn cơ sở dữ liệu trên đám mây thì dùng lại.
- Tách câu khi dịch, kiểm soát tần suất yêu cầu, hỗ trợ proxy và Tor, thay thế biến từ cơ sở dữ liệu.

### Panel trong game

- Panel cài đặt mở ngay trong game, điều khiển dịch vụ dịch, hướng ngôn ngữ và chế độ hoạt động.
- Cài đặt phông chữ và văn bản hiển thị (kích thước, màu, viền, lớp), tự chọn phông theo ngôn ngữ đích.
- Sửa biến game, sửa văn bản, tổ hợp phím tùy chỉnh, chủ đề màu, cửa sổ trình dịch kéo thả và đổi kích thước được.
- Nguồn thông báo, thống kê, quản lý bộ nhớ đệm bản dịch và sao lưu cơ sở dữ liệu.

### Ngôn ngữ giao diện

- Giao diện có **tiếng Anh (mặc định)**, Nga, Việt, Chuvash và Thổ Nhĩ Kỳ.
- Tiếng Việt là phần bổ sung mới của bản dựng lại này, dịch đủ toàn bộ chuỗi.

### Tương thích

- Hỗ trợ game làm bằng **Ren'Py 7 (Python 2)** và **Ren'Py 8 (Python 3)** từ cùng một file — hai cây module `py2` / `py3` được đóng gói lúc build.
- Phát hành dưới dạng **một file `.rpa` duy nhất**: copy vào thư mục `game` của game là dùng được, không cần file nào khác.

---

## 🚀 Cài đặt

1. Build gói (xem [Build](#-build)) hoặc lấy file build sẵn `build/Translator3000.rpa`.
2. Copy `Translator3000.rpa` vào thư mục `game` của game Ren'Py.
3. Mở game và mở panel Translator3000 bằng phím tắt của nó để cấu hình dịch vụ dịch và chế độ hoạt động.

> Không copy file `.py` / `.rpy` rời vào game — file rời sẽ đè lên file trong RPA. Ren'Py tự nạp mọi file `.rpa` trong thư mục `game`.

---

## 📖 Sử dụng

1. Mở panel Translator3000 trong game.
2. Chọn **dịch vụ dịch** và đặt **ngôn ngữ nguồn / đích**.
3. Chọn chế độ hoạt động:
   - **Quét trước** — dịch toàn bộ game vào cơ sở dữ liệu ngay từ đầu (trải nghiệm tốt nhất về sau).
   - **Chỉ CSDL** — chỉ hiện bản dịch đã có trong cơ sở dữ liệu.
   - **Thời gian thực + CSDL** — ưu tiên cơ sở dữ liệu, câu thiếu thì dịch trực tiếp.
   - **Tắt** — văn bản gốc.
4. Muốn đổi ngôn ngữ giao diện, dùng nút ngôn ngữ trong panel (`EN` / `VI` / `RU` / …). Lần chạy đầu tiên mặc định là tiếng Anh.

---

## 🔧 Build

Yêu cầu:

- Python 3 (chạy `build.py` và đóng gói cây module `py3`).
- Python 2.7 (đóng gói cây module `py2` thành `.tr3000py`).
- Một game hoặc SDK Ren'Py 7 (compile `.rpy` thành `.rpyc`).

```text
python build.py --renpy7-exe "C:\path\to\RenPy7Game.exe" --python2 "C:\path\to\python27\python.exe"
```

Kết quả: `build/Translator3000.rpa` (RPA-3.0).

Cách build hoạt động: file `.rpy` được compile bằng Ren'Py 7 trong thư mục staging, module `.py` được mã hóa thành định dạng `.tr3000py` gốc (AST → pickle → base64 → zlib, đúng định dạng `PyLoader` gốc chờ đợi), và mọi thứ được đóng vào một RPA giữ đúng layout runtime của bản stock.

### Cấu trúc repo

```text
src/
  000translator3000_main.rpy        script chính (GUI + lõi, đã giải obfuscation)
  translations/                     chuỗi giao diện (EN / VI / RU / CV / TR)
  _translator3000_main_modules/
    py2/_translator3000/*.py        module cho game Ren'Py 7
    py3/_translator3000/*.py        module cho game Ren'Py 8
  _translator3000_extra_modules/    thư viện đi kèm
  old_requests_module/  old_pkgutil_module/  uuid_py3_fix/  _extra_six.py
  Translator3000OtherFiles/         phông chữ, ảnh GUI, mẫu biến
tools/                              công cụ giải obfuscation và tạo bản dịch
build.py                            script đóng gói
```

### Source được dựng lại như thế nào

File stock được giải nén, file `.rpyc` của nó được decompile bằng unrpyc (đã patch để đọc code Python lưu dạng AST của tác giả), và các module `.tr3000py` được giải mã từ AST pickle đã nén trở lại thành source Python. Sau đó một bước fold tĩnh an toàn biến các chuỗi bị tác giả cắt nhỏ / mã hóa số học trở lại thành literal thường (ví dụ `__version__ = '1.45.11'`). Comment và formatting gốc về bản chất không khôi phục được; obfuscation động và các tên bị Ren'Py mangle được giữ nguyên để không đổi hành vi.

---

## 🗺️ Roadmap

Đã hoàn thành trong bản dựng lại này:

- [x] Giải nén toàn bộ `Translator3000.rpa` stock (660 file)
- [x] Decompile script chính và toàn bộ module `py2` / `py3`
- [x] Giải obfuscation tĩnh thành source đọc được
- [x] Ngôn ngữ giao diện tiếng Việt, tiếng Anh là ngôn ngữ giao diện mặc định
- [x] Sửa tương thích Ren'Py 8 (dạng `exec` chạy cả Python 2/3, số nguyên dài)
- [x] Build một lệnh trở lại thành `Translator3000.rpa` thả vào game là chạy
- [x] Đã kiểm chứng nạp và init trên Ren'Py 7.3.5 và Ren'Py 8.5.3
- [x] Provider dịch OpenAI / ChatGPT (API key, base URL và model tùy chỉnh, dịch theo ngữ cảnh theo lô)
- [x] Dịch giao diện game (menu, cài đặt, màn hình save/load) qua cùng provider và cơ sở dữ liệu
- [x] Xuất / nhập cơ sở dữ liệu dịch (sao lưu, chia sẻ giữa các máy)
- [x] Chuyển chế độ nhanh (huy hiệu trên màn hình và phím tắt để đổi Tắt ↔ Chỉ CSDL giữa game)
- [x] Tùy chọn tắt kiểm tra cập nhật bắt buộc

Tính năng dự định phát triển (rất hoan nghênh đóng góp):

- [ ] Tự co chữ dịch cho vừa khung và tự chọn phông thông minh hơn (tiếng Việt, CJK, …)
- [ ] Thuật ngữ riêng theo game / danh sách không dịch và placeholder được bảo vệ
- [ ] Thêm ngôn ngữ giao diện (简体中文, 日本語, Español, …)
- [ ] Ma trận test tự động Ren'Py 7 / Ren'Py 8 và build RPA bằng CI khi gắn tag phát hành
- [ ] File build sẵn đính kèm GitHub Releases

---

## 🤝 Đóng góp

Rất hoan nghênh issue và pull request.

- Khi báo lỗi, vui lòng kèm phiên bản Ren'Py, tên game, chế độ hoạt động và dịch vụ dịch đang dùng, cùng đoạn log / traceback liên quan.
- Sửa logic Ren'Py trong `src/000translator3000_main.rpy`, module dịch trong cây `py2` / `py3` tương ứng, và chuỗi giao diện trong `src/translations/`, sau đó build lại bằng `build.py`.
- Khi chạm vào code dùng chung, vui lòng test trên ít nhất một game Ren'Py 7 và một game Ren'Py 8.

## 🙏 Ghi công

Translator3000 do **Vladya** tạo ra; repo này là bản dựng lại từ cộng đồng trên nền bản stock mới nhất của anh, nhằm mục đích bảo trì và phát triển tiếp. Source public v2 cũ chỉ được dùng làm tham chiếu cấu trúc — không dùng lại code v2.

## 📄 Giấy phép

Translator3000 và Ren'Py là công trình của các tác giả tương ứng. Vui lòng kiểm tra điều khoản của các dự án gốc trước khi phân phối lại; repo này ghi lại một nỗ lực dựng lại source, và bổ sung công cụ bảo trì cùng bản dịch trên nền đó.
