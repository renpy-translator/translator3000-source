# Translator3000 — Reconstructed Source

<p align="center">
  <strong>English</strong> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

> A readable, developable reconstruction of **Translator3000** (stock version `1.45.11`) for Ren'Py games — recovered from the shipped `Translator3000.rpa`, fully de-obfuscated, and rebuilt so it can be maintained, extended, and packaged back into a single drop-in `Translator3000.rpa`.

Translator3000 automatically translates Ren'Py games while you play: it captures dialogue and menus, sends them to a translation service, caches every result in a per-game database, and shows the translation in place of the original text. This repository exists because the current (v3) source of Translator3000 is not publicly available — the old public v2 source is years out of date. Here, the latest stock build has been reverse-engineered back into clean source code, so the community can study it, fix it, and build new features on top of it.

---

## ✨ Features

### Translation

- **Real-time translation** of dialogue and choice menus while playing.
- **Four work modes**: Off, Prescan (translate the whole game upfront), DB only (show only translations already in the database), and Realtime + DB.
- **Many built-in providers**: Google (GTX / client5 / RPC), Bing, DeepL (official API, RPC, Selenium), Yandex, Reverso, and LingvaNex.
- **Per-game translation database**: every translated line is cached, so replaying a scene costs no new requests; a ready-made cloud database is reused when available.
- Sentence splitting, request-frequency control, proxy and Tor support, and variables substitution from the database.

### In-game panel

- Settings panel opened from inside any game, with translation-service, language-direction, and work-mode controls.
- Font and displayed-text settings (size, color, outlines, layers), automatic font selection by target language.
- Game variables editor, text editor, custom key combinations, color themes, and a draggable / resizable translator window.
- Notifications feed, statistics, translation-cache management, and database backup.

### Integrated add-on features

Everything from the sibling `translator3000-openai` add-on is integrated
natively into this source (same features, organized the stock way — no
separate add-on archive):

- **OpenAI / ChatGPT providers**: `openai_api` (own API key, custom Base URL,
  model and reasoning effort) and `openai_chatgpt` (ChatGPT account via Codex),
  with tag/variable protection and context-aware batch translation.
- **Game UI translation**: prescan also collects text from every registered
  Ren'Py screen and stores it in the same database; display is opt-in and
  follows the Off / DB only / Realtime mode.
- **Quick mode toggle**: on-screen badge (top-right) and Alt+1 to flip
  Off ↔ DB only mid-game.
- **Export / import** of the translation database from the settings panel.
- **Extras**: auto-fit of translated text into its frame, and the forced
  update check is blocked.

### Interface languages

- Interface available in **English (default)**, Russian, Vietnamese, Chuvash, and Turkish.
- Vietnamese is a new addition of this reconstruction, with full string coverage.

### Compatibility

- Supports games made with **Ren'Py 7 (Python 2)** and **Ren'Py 8 (Python 3)** from the same archive — dual `py2` / `py3` module trees are packed at build time.
- Ships as a **single `.rpa` file**: copy it into a game's `game` folder and it works, no other files needed.

---

## 🚀 Installation

1. Build the package (see [Building](#-building)) or take a prebuilt `build/Translator3000.rpa`.
2. Copy `Translator3000.rpa` into the `game` folder of your Ren'Py game.
3. Launch the game and open the Translator3000 panel with its hotkey to configure a translation service and a work mode.

> Do not copy loose `.py` / `.rpy` files into the game — loose files override files inside the RPA. Ren'Py automatically loads every `.rpa` in the `game` folder.

---

## 📖 Usage

1. Open the Translator3000 panel in game.
2. Pick a **translation service** and set the **source / target languages**.
3. Choose a work mode:
   - **Prescan** — translate the full game upfront into the database (best experience afterwards).
   - **DB only** — display translations that are already in the database.
   - **Realtime + DB** — use the database first, translate missing lines live.
   - **Off** — original text.
4. To change the interface language, use the language button in the panel (`EN` / `VI` / `RU` / …). English is the default on first run.

---

## 🔧 Building

Requirements:

- Python 3 (runs `build.py` and packs the `py3` module tree).
- A Python 2.7 interpreter (packs the `py2` module tree into `.tr3000py`).
- A Ren'Py 7 game or SDK executable (compiles `.rpy` sources into `.rpyc`).

```text
python build.py --renpy7-exe "C:\path\to\RenPy7Game.exe" --python2 "C:\path\to\python27\python.exe"
```

Output: `build/Translator3000.rpa` (RPA-3.0).

How it works: `.rpy` files are compiled with Ren'Py 7 in a staging folder, `.py` modules are encoded into the stock `.tr3000py` format (AST → pickle → base64 → zlib, the format the original `PyLoader` expects), and everything is packed into one RPA with exactly the stock runtime layout.

### Repository layout

```text
src/
  000translator3000_main.rpy        main script (GUI + core, de-obfuscated)
  translations/                     interface strings (EN / VI / RU / CV / TR)
  _translator3000_main_modules/
    py2/_translator3000/*.py        modules for Ren'Py 7 games
    py3/_translator3000/*.py        modules for Ren'Py 8 games
    _openai/ (inside _translator3000/)  OpenAI/ChatGPT provider + client
    _ui_translate / _mode_toggle / _autofit / _transfer / _disable_update /
    _openai_labels (inside _translator3000/)  integrated add-on features
  _translator3000_extra_modules/    vendored libraries
  old_requests_module/  old_pkgutil_module/  uuid_py3_fix/  _extra_six.py
  Translator3000OtherFiles/         fonts, GUI images, patterns
tools/                              de-obfuscation and translation generators
build.py                            package builder
```

### How the source was reconstructed

The stock archive was unpacked, its `.rpyc` was decompiled with unrpyc (patched to read the author's AST-stored Python code), and its `.tr3000py` modules were decoded from compressed AST pickles back into Python source. A safe static-folding pass then turned the author's split / arithmetic-obfuscated strings back into plain literals (for example `__version__ = '1.45.11'`). Comments and original formatting are unrecoverable by nature; dynamic obfuscation and Ren'Py name-mangled identifiers are kept as-is to preserve behavior.

---

## 🗺️ Roadmap

Done in this reconstruction:

- [x] Full unpack of the stock `Translator3000.rpa` (660 files)
- [x] Decompilation of the main script and all `py2` / `py3` modules
- [x] Static de-obfuscation into readable source
- [x] Vietnamese interface language, English as the default interface language
- [x] Ren'Py 8 compatibility fixes (dual Python 2/3 `exec` form, long literals)
- [x] One-command build back into a drop-in `Translator3000.rpa`
- [x] Verified loading and init on Ren'Py 7.3.5 and Ren'Py 8.5.3
- [x] OpenAI / ChatGPT translation providers integrated natively (`openai_api`, `openai_chatgpt`), registered like the stock providers
- [x] Game UI translation (menus, preferences, save/load screens) through the same provider and database
- [x] Export / import of translation databases (backup, sharing between machines)
- [x] Quick mode toggle (on-screen badge and hotkey to flip Off ↔ DB only mid-game)
- [x] Auto-fit of translated text into its frame
- [x] Forced update check blocked
- [x] Verified the integrated build on Ren'Py 7 and Ren'Py 8 test games (OpenAI services listed beside the stock providers)

Planned features (contributions welcome):

- [ ] Smarter automatic font selection (Vietnamese, CJK, …)
- [ ] Per-game glossary / do-not-translate terms and protected placeholders
- [ ] More interface languages (简体中文, 日本語, Español, …)
- [ ] Automated Ren'Py 7 / Ren'Py 8 test matrix and CI builds of the RPA on release tags
- [ ] Prebuilt release archives attached to GitHub Releases

---

## 🤝 Contributing

Issues and pull requests are welcome.

- For a bug, please include the Ren'Py version, the game name, your work mode and translation service, and the relevant log / traceback lines.
- Edit Ren'Py logic in `src/000translator3000_main.rpy`, translation modules in the matching `py2` / `py3` tree, and interface strings in `src/translations/`, then rebuild with `build.py`.
- Please test on at least one Ren'Py 7 and one Ren'Py 8 game when you touch shared code.

## 🙏 Credits

Translator3000 was created by **Vladya**; this repository is a community reconstruction of its latest stock build for maintenance and further development. The old public v2 source served as a structural reference only — no v2 code is used.

## 📄 License

Translator3000 and Ren'Py are the work of their respective authors. Please check the original projects' terms before redistributing; this repository documents a reconstruction effort and adds maintenance tooling and translations on top of it.
