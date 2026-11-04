# -*- coding: utf-8 -*-
"""Deobfuscate Translator3000 py2 sources. Run under Python 2.7.

Same safe static folding as deobfuscate_py3.py, but for the py2 AST
(Str/Num nodes) and output via unrpyc's codegen.to_source.
Env TR3000_CODEGEN_DIR must point to unrpyc legacy's decompiler folder.

Usage: python deobfuscate_py2.py <input_dir> <output_dir>
"""
import ast
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from static_fold_py2 import fold_tree  # noqa: E402
sys.path.insert(0, os.environ.get("TR3000_CODEGEN_DIR", ""))
import codegen  # noqa: E402

def process_file(src, dst):
    text = open(src, "rb").read()
    tree = ast.parse(text)
    tree = fold_tree(tree, 2)
    source = codegen.to_source(tree)
    folder = os.path.dirname(dst)
    if folder and not os.path.isdir(folder):
        os.makedirs(folder)
    with open(dst, "wb") as f:
        f.write(source.encode("utf-8"))
        f.write(b"\n")


def main():
    src_root, dst_root = sys.argv[1], sys.argv[2]
    count = 0
    for dirpath, _dirs, files in os.walk(src_root):
        for name in files:
            if not name.endswith(".py"):
                continue
            s = os.path.join(dirpath, name)
            rel = os.path.relpath(s, src_root)
            process_file(s, os.path.join(dst_root, rel))
            count += 1
    print("deobfuscated %d py files" % count)


if __name__ == "__main__":
    main()
