# Translator3000 — 重构源码

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <strong>简体中文</strong> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

> 本仓库将 **Translator3000**（原版 `1.45.11`）为 Ren'Py 游戏重构为可读、可继续开发的源码——从发布的 `Translator3000.rpa` 中恢复、完全去混淆，并可重新打包成单个可直接放入游戏的 `Translator3000.rpa`。

Translator3000 可以在游玩过程中自动翻译 Ren'Py 游戏：它捕获对话和菜单，将其发送到翻译服务，把每个结果缓存到每款游戏各自的数据库中，并以译文替换原文显示。本仓库存在的原因是 Translator3000 当前的（v3）源码并未公开，而旧的公开 v2 源码已经过时多年。在这里，最新的原版构建被逆向恢复为干净的源码，以便社区研究、修复并在其上开发新功能。

---

## ✨ 功能

### 翻译

- 游玩时**实时翻译**对话和选项菜单。
- **四种工作模式**：关闭、预扫描（提前翻译整个游戏）、仅数据库（只显示数据库中已有的译文）、实时 + 数据库。
- **众多内置服务**：Google（GTX / client5 / RPC）、Bing、DeepL（官方 API、RPC、Selenium）、Yandex、Reverso 和 LingvaNex。
- **每款游戏独立的翻译数据库**：每条译文都会被缓存，重玩场景不再消耗新的请求；云端有现成数据库时可直接复用。
- 翻译时断句、请求频率控制、代理和 Tor 支持、从数据库替换变量。

### 游戏内面板

- 在游戏内打开的设置面板，可控制翻译服务、语言方向和工作模式。
- 字体与显示文本设置（大小、颜色、描边、图层），按目标语言自动选择字体。
- 游戏变量编辑器、文本编辑器、自定义按键组合、配色主题、可拖动和缩放的译者窗口。
- 通知流、统计、翻译缓存管理和数据库备份。

### 界面语言

- 界面提供**英语（默认）**、俄语、越南语、楚瓦什语和土耳其语。
- 越南语是本次重构新增的语言，字符串覆盖完整。

### 兼容性

- 同一个归档同时支持 **Ren'Py 7（Python 2）** 和 **Ren'Py 8（Python 3）** 制作的游戏——`py2` / `py3` 双模块树在构建时打包。
- 以**单个 `.rpa` 文件**发布：复制到游戏的 `game` 文件夹即可使用，无需其他文件。

---

## 🚀 安装

1. 构建软件包（见[构建](#-构建)），或使用已构建的 `build/Translator3000.rpa`。
2. 将 `Translator3000.rpa` 复制到 Ren'Py 游戏的 `game` 文件夹。
3. 启动游戏，用其快捷键打开 Translator3000 面板，配置翻译服务和工作模式。

> 不要把散装的 `.py` / `.rpy` 文件复制进游戏——散装文件会覆盖 RPA 内的文件。Ren'Py 会自动加载 `game` 文件夹中的每个 `.rpa`。

---

## 📖 使用

1. 在游戏中打开 Translator3000 面板。
2. 选择**翻译服务**，设置**源 / 目标语言**。
3. 选择工作模式：
   - **预扫描** — 提前把整个游戏翻译进数据库（之后体验最佳）。
   - **仅数据库** — 只显示数据库中已有的译文。
   - **实时 + 数据库** — 优先使用数据库，缺失的行实时翻译。
   - **关闭** — 原文。
4. 如需更改界面语言，使用面板中的语言按钮（`EN` / `VI` / `RU` / …）。首次运行时默认为英语。

---

## 🔧 构建

要求：

- Python 3（运行 `build.py` 并打包 `py3` 模块树）。
- Python 2.7 解释器（将 `py2` 模块树打包为 `.tr3000py`）。
- Ren'Py 7 游戏或 SDK 可执行文件（将 `.rpy` 编译为 `.rpyc`）。

```text
python build.py --renpy7-exe "C:\path\to\RenPy7Game.exe" --python2 "C:\path\to\python27\python.exe"
```

输出：`build/Translator3000.rpa`（RPA-3.0）。

构建方式：`.rpy` 文件在临时文件夹中用 Ren'Py 7 编译，`.py` 模块被编码为原版 `.tr3000py` 格式（AST → pickle → base64 → zlib，即原始 `PyLoader` 所期望的格式），然后所有内容按与原版完全相同的运行时布局打包成一个 RPA。

### 仓库结构

```text
src/
  000translator3000_main.rpy        主脚本（GUI + 核心，已去混淆）
  translations/                     界面字符串（EN / VI / RU / CV / TR）
  _translator3000_main_modules/
    py2/_translator3000/*.py        Ren'Py 7 游戏的模块
    py3/_translator3000/*.py        Ren'Py 8 游戏的模块
  _translator3000_extra_modules/    捆绑的第三方库
  old_requests_module/  old_pkgutil_module/  uuid_py3_fix/  _extra_six.py
  Translator3000OtherFiles/         字体、GUI 图片、变量模式
tools/                              去混淆和翻译生成工具
build.py                            打包脚本
```

### 源码如何重构

原版归档被解包，其 `.rpyc` 用 unrpyc 反编译（已打补丁以读取作者以 AST 形式存储的 Python 代码），`.tr3000py` 模块从压缩的 AST pickle 解码回 Python 源码。随后一次安全的静态折叠将作者拆分/算术混淆的字符串还原为普通字面量（例如 `__version__ = '1.45.11'`）。注释和原始格式本质上无法恢复；动态混淆和被 Ren'Py 改名的标识符保持原样以保留行为。

---

## 🗺️ 路线图

本次重构已完成：

- [x] 完整解包原版 `Translator3000.rpa`（660 个文件）
- [x] 反编译主脚本和全部 `py2` / `py3` 模块
- [x] 静态去混淆为可读源码
- [x] 越南语界面语言，英语作为默认界面语言
- [x] Ren'Py 8 兼容性修复（Python 2/3 通用的 `exec` 形式、长整型字面量）
- [x] 一条命令构建回可直接放入游戏的 `Translator3000.rpa`
- [x] 已在 Ren'Py 7.3.5 和 Ren'Py 8.5.3 上验证加载和初始化

计划开发的功能（欢迎贡献）：

- [ ] OpenAI / ChatGPT 翻译服务（API 密钥、自定义 base URL 和模型、上下文批量翻译）
- [ ] 通过同一服务和数据库翻译游戏界面（菜单、偏好设置、存档/读档画面）
- [ ] 翻译数据库的导出 / 导入（备份、跨设备共享）
- [ ] 快速模式切换（屏幕徽章和快捷键，在游戏中切换关闭 ↔ 仅数据库）
- [ ] 译文自动适配文本框，以及更智能的自动字体选择（越南语、CJK 等）
- [ ] 每款游戏的术语表 / 不翻译词条和受保护的占位符
- [ ] 关闭强制更新检查的选项
- [ ] 更多界面语言（简体中文、日本語、Español 等）
- [ ] Ren'Py 7 / Ren'Py 8 自动化测试矩阵，以及发布标签时用 CI 构建 RPA
- [ ] 在 GitHub Releases 附上预构建的发布归档

---

## 🤝 贡献

欢迎提交 issue 和 pull request。

- 报告 bug 时，请提供 Ren'Py 版本、游戏名称、工作模式和翻译服务，以及相关的日志 / 回溯行。
- 在 `src/000translator3000_main.rpy` 中修改 Ren'Py 逻辑，在相应的 `py2` / `py3` 树中修改翻译模块，在 `src/translations/` 中修改界面字符串，然后用 `build.py` 重新构建。
- 修改共享代码时，请至少在一款 Ren'Py 7 游戏和一款 Ren'Py 8 游戏上测试。

## 🙏 鸣谢

Translator3000 由 **Vladya** 创建；本仓库是社区对其最新原版构建的重构，用于维护和进一步开发。旧的公开 v2 源码仅用作结构参考——未使用任何 v2 代码。

## 📄 许可证

Translator3000 和 Ren'Py 是其各自作者的作品。重新分发前请查看原项目的条款；本仓库记录了一次重构工作，并在其上添加了维护工具和翻译。
