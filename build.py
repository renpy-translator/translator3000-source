# -*- coding: utf-8 -*-
"""Build Translator3000.rpa from readable sources in src/.

Pipeline (mirrors the stock v3 archive layout):
  1. src/**/*.rpy                    -> compiled .rpyc with a Ren'Py 7 engine
  2. src/_translator3000_main_modules/py3/**/*.py -> .tr3000py (this Python 3)
  3. src/_translator3000_main_modules/py2/**/*.py -> .tr3000py (Python 2.7)
  4. everything else in src/         -> copied as-is
  5. all of the above                -> RPA-3.0 (key 0x42424242)

Usage:
  python build.py --renpy7-exe "D:\\path\\to\\RenPy7Game.exe" --python2 "D:\\path\\to\\python27\\python.exe"

Both paths can also come from RENPY7_EXE / TR3000_PYTHON2 env vars.
Output: build/Translator3000.rpa
"""
import argparse
import ast
import base64
import os
import pickle
import shutil
import subprocess
import sys
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "src")
BUILD = os.path.join(HERE, "build")
STAGE = os.path.join(BUILD, "_stage")
KEY = 0x42424242

PACK_PY2_SNIPPET = r'''
import ast, base64, os, pickle, sys, zlib
root = sys.argv[1]
count = 0
for dirpath, _dirs, files in os.walk(root):
    for name in files:
        if name.endswith(".py"):
            path = os.path.join(dirpath, name)
            tree = ast.parse(open(path, "rb").read())
            data = zlib.compress(base64.b64encode(pickle.dumps(tree, protocol=2)))
            out = path[:-3] + ".tr3000py"
            with open(out, "wb") as f:
                f.write(data)
            count += 1
print("packed py2: %d" % count)
'''


def pack_py3(root):
    count = 0
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if name.endswith(".py"):
                path = os.path.join(dirpath, name)
                tree = ast.parse(open(path, encoding="utf-8").read())
                for node in ast.walk(tree):
                    if "type_params" in node.__dict__:
                        del node.__dict__["type_params"]
                data = zlib.compress(base64.b64encode(pickle.dumps(tree, protocol=2)))
                with open(path[:-3] + ".tr3000py", "wb") as f:
                    f.write(data)
                count += 1
    print("packed py3: %d" % count)


def pack_py2(python2, root):
    snippet = os.path.join(BUILD, "_pack_py2.py")
    with open(snippet, "w") as f:
        f.write(PACK_PY2_SNIPPET)
    out = subprocess.check_output([python2, snippet, root])
    print(out.decode("utf-8", "replace").strip())


def compile_rpy(renpy7_exe):
    """Compile every staged .rpy to .rpyc using a Ren'Py 7 engine folder."""
    game_dir = os.path.join(STAGE, "game")
    minimal = os.path.join(game_dir, "script.rpy")
    if not os.path.isfile(minimal):
        with open(minimal, "w") as f:
            f.write("label start:\n    return\n")
    env = dict(os.environ, SDL_AUDIODRIVER="dummy", SDL_VIDEODRIVER="dummy")
    proc = subprocess.Popen([renpy7_exe, STAGE, "compile"],
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    # The Ren'Py launcher returns before its child finishes compiling,
    # so poll for the .rpyc files instead of trusting the exit.
    import time
    deadline = time.time() + 180
    missing = []
    while time.time() < deadline:
        missing = []
        for dirpath, _dirs, files in os.walk(game_dir):
            for name in files:
                if name.endswith(".rpy"):
                    rpyc = os.path.join(dirpath, name[:-4] + ".rpyc")
                    if not os.path.isfile(rpyc) or os.path.getsize(rpyc) == 0:
                        missing.append(os.path.join(dirpath, name))
        if not missing:
            break
        if proc.poll() is not None:
            # Give the detached child a grace period, then re-check above.
            time.sleep(2)
        else:
            time.sleep(1)
    if missing:
        try:
            proc.kill()
        except Exception:
            pass
        raise SystemExit("Ren'Py did not compile: %s" % ", ".join(missing))
    try:
        proc.kill()
    except Exception:
        pass
    print("compiled rpyc ok")


def iter_stage_files():
    """Yield (arcname, abspath) for everything that belongs in the RPA."""
    game_dir = os.path.join(STAGE, "game")
    for dirpath, _dirs, files in os.walk(game_dir):
        for name in sorted(files):
            path = os.path.join(dirpath, name)
            rel = os.path.relpath(path, game_dir).replace(os.sep, "/")
            if rel == "script.rpy" or rel == "script.rpyc":
                continue
            if rel.endswith(".rpy"):
                continue
            if "/_translator3000_main_modules/" in "/" + rel and rel.endswith(".py"):
                continue
            yield rel, path


def write_rpa(entries, out_path):
    index = {}
    with open(out_path, "wb") as archive:
        archive.write(b"RPA-3.0 %016x %08x\n" % (0, KEY))
        for name, path in entries:
            data = open(path, "rb").read()
            archive.write(b"Made with Ren'Py.")
            offset = archive.tell()
            archive.write(data)
            index[name] = [(offset ^ KEY, len(data) ^ KEY, b"")]
        index_offset = archive.tell()
        archive.write(zlib.compress(pickle.dumps(index, protocol=2)))
        archive.seek(0)
        archive.write(b"RPA-3.0 %016x %08x\n" % (index_offset, KEY))
    print("wrote %s (%d files, %d bytes)" % (out_path, len(index), os.path.getsize(out_path)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--renpy7-exe", default=os.environ.get("RENPY7_EXE", ""))
    ap.add_argument("--python2", default=os.environ.get("TR3000_PYTHON2", ""))
    ap.add_argument("--out", default=os.path.join(BUILD, "Translator3000.rpa"))
    ap.add_argument("--keep-stage", action="store_true", help="keep build/_stage for debugging")
    args = ap.parse_args()
    if not args.renpy7_exe or not os.path.isfile(args.renpy7_exe):
        raise SystemExit("need --renpy7-exe pointing at a Ren'Py 7 game .exe")
    if not args.python2 or not os.path.isfile(args.python2):
        raise SystemExit("need --python2 pointing at a Python 2.7 interpreter")

    if os.path.isdir(STAGE):
        shutil.rmtree(STAGE)
    shutil.copytree(SRC, os.path.join(STAGE, "game"))
    pack_py3(os.path.join(STAGE, "game", "_translator3000_main_modules", "py3"))
    pack_py2(args.python2, os.path.join(STAGE, "game", "_translator3000_main_modules", "py2"))
    compile_rpy(args.renpy7_exe)
    entries = sorted(iter_stage_files())
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    write_rpa(entries, args.out)
    if not args.keep_stage:
        shutil.rmtree(STAGE, ignore_errors=True)


if __name__ == "__main__":
    main()
