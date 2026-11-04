# AGENTS.md — translator3000-source

This repo is one of **two independent Git repos** for Translator3000 (see the
workspace-root `AGENTS.md` in `../AGENTS.md` when working from the monorepo
workspace, or the summary below when this repo is cloned alone).

## Two repos, one feature set

- **`translator3000-source` (this repo)** — full reconstructed source of
  Translator3000 `1.45.11`. Builds one drop-in `Translator3000.rpa`.
  For users who want to build/customize from scratch and develop new features.
- **`translator3000-openai`** (sibling repo) — add-on for the **stock**
  Translator3000 (`Translator3000-openai.rpa` / `-openai-addon.rpa`).
  For users who already have the original Translator3000 and only want the
  OpenAI/UI extension.

The repos are independent and used differently, but they offer the **same
features**. When a feature is developed, update **both** repos — same
behavior, different code organization. This repo integrates features natively
(providers in `src/_translator3000_main_modules/{py2,py3}/_translator3000/`,
screens in `src/000translator3000_main.rpy`); never import the add-on's loose
`tr3000_*.py` / `zzz_*.rpy` layout or its runtime `register()` patching here.

`tools/port_openai_features.py` ports shared feature modules from the sibling
repo into this repo's native layout.

## Rules for this repo

- One built `Translator3000.rpa` must work alone on Ren'Py 7 (Python 2) and
  Ren'Py 8 (Python 3). New shared code must be dual-compatible
  (`from __future__ import unicode_literals`, no f-strings).
- Register providers in `_translator3000/translator.py` like stock providers.
- English is the default interface language; keep Vietnamese strings
  (`src/translations/translator3000_vietnamese.rpy`, `_openai_labels.py`)
  in sync with new UI text.
- Build before committing:
  `python build.py --renpy7-exe "<RenPy7Game.exe>" --python2 "<python27\python.exe>"`
- Git identity: `RenPy-Translator <hien.bt@htigroup.vn>`.
  Conventional commits, no AI references.
- Never commit `*.rpyc` or `__pycache__/`. Exception: the prebuilt `build/Translator3000.rpa` IS committed (rebuild and re-commit it whenever the source changes) so users can download and play without building; all other build output stays ignored.
