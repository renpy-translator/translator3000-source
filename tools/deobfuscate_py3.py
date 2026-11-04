# -*- coding: utf-8 -*-
"""Deobfuscate Translator3000 py3 sources.

Safely folds purely static expressions the author split/obfuscated:
string concatenation, chr/unichr map-joins, int/float casts, arithmetic,
getattr/__import__ chains on _extra_six and sys.version_info, eval('...').
Anything not provably static is left untouched.

Usage: python deobfuscate_py3.py <input_dir> <output_dir>
Copies the tree, rewriting every .py file. Non-.py files are copied as-is.
"""
import ast
import os
import shutil
import sys

FAIL = object()


class FakeVersionInfo(object):
    def __init__(self, major):
        self.major = major


class FakeModule(object):
    def __init__(self, attrs):
        self._attrs = attrs

    def get(self, name):
        return self._attrs.get(name, FAIL)


def make_env(major):
    chr_name = "chr" if major == 3 else "unichr"
    builtins_mod = FakeModule({"map": map, "chr": chr, chr_name: chr})
    six = FakeModule({
        "unichr": chr,
        "chr": chr,
        "moves": FakeModule({"builtins": builtins_mod}),
    })
    sys_mod = FakeModule({"version_info": FakeVersionInfo(major)})
    return {"_extra_six": six, "sys": sys_mod}


class Evaluator(object):
    def __init__(self, major):
        self.major = major
        self.env = make_env(major)

    def eval(self, node):
        try:
            return self._eval(node)
        except Exception:
            return FAIL

    def _eval(self, node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (str, bytes, int, float, bool, type(None))):
                return node.value
            return FAIL
        if isinstance(node, (ast.Tuple, ast.List)):
            vals = [self._eval(e) for e in node.elts]
            if any(v is FAIL for v in vals):
                return FAIL
            return tuple(vals) if isinstance(node, ast.Tuple) else vals
        if isinstance(node, ast.Dict):
            keys = [self._eval(k) if k is not None else None for k in node.keys]
            vals = [self._eval(v) for v in node.values]
            if any(v is FAIL for v in keys + vals):
                return FAIL
            return dict(zip(keys, vals))
        if isinstance(node, ast.Name):
            if node.id == "chr" or node.id == "unichr":
                return chr
            if node.id == "map":
                return map
            if node.id == "True":
                return True
            if node.id == "False":
                return False
            if node.id == "None":
                return None
            return FAIL
        if isinstance(node, ast.UnaryOp):
            v = self._eval(node.operand)
            if v is FAIL:
                return FAIL
            if isinstance(node.op, ast.USub):
                return -v
            if isinstance(node.op, ast.UAdd):
                return +v
            if isinstance(node.op, ast.Not):
                return not v
            if isinstance(node.op, ast.Invert):
                return ~v
            return FAIL
        if isinstance(node, ast.BinOp):
            l, r = self._eval(node.left), self._eval(node.right)
            if l is FAIL or r is FAIL:
                return FAIL
            op = node.op
            if isinstance(op, ast.Add):
                return l + r
            if isinstance(op, ast.Sub):
                return l - r
            if isinstance(op, ast.Mult):
                return l * r
            if isinstance(op, ast.Div):
                return l / r
            if isinstance(op, ast.FloorDiv):
                return l // r
            if isinstance(op, ast.Mod):
                return l % r
            if isinstance(op, ast.Pow):
                if abs(r) > 1000:
                    return FAIL
                return l ** r
            if isinstance(op, ast.LShift):
                return l << r
            if isinstance(op, ast.RShift):
                return l >> r
            if isinstance(op, ast.BitOr):
                return l | r
            if isinstance(op, ast.BitAnd):
                return l & r
            if isinstance(op, ast.BitXor):
                return l ^ r
            return FAIL
        if isinstance(node, ast.BoolOp):
            vals = [self._eval(v) for v in node.values]
            if any(v is FAIL for v in vals):
                return FAIL
            result = vals[0]
            for v in vals[1:]:
                result = (result and v) if isinstance(node.op, ast.And) else (result or v)
            return result
        if isinstance(node, ast.Compare):
            l = self._eval(node.left)
            if l is FAIL:
                return FAIL
            for op, comp in zip(node.ops, node.comparators):
                r = self._eval(comp)
                if r is FAIL:
                    return FAIL
                if isinstance(op, ast.Eq):
                    ok = l == r
                elif isinstance(op, ast.NotEq):
                    ok = l != r
                elif isinstance(op, ast.Lt):
                    ok = l < r
                elif isinstance(op, ast.LtE):
                    ok = l <= r
                elif isinstance(op, ast.Gt):
                    ok = l > r
                elif isinstance(op, ast.GtE):
                    ok = l >= r
                elif isinstance(op, ast.Is):
                    ok = l is r
                elif isinstance(op, ast.IsNot):
                    ok = l is not r
                elif isinstance(op, ast.In):
                    ok = l in r
                elif isinstance(op, ast.NotIn):
                    ok = l not in r
                else:
                    return FAIL
                if not ok:
                    return False
                l = r
            return True
        if isinstance(node, ast.IfExp):
            test = self._eval(node.test)
            if test is FAIL:
                return FAIL
            return self._eval(node.body if test else node.orelse)
        if isinstance(node, ast.Attribute):
            if node.attr == "major":
                base = self._eval(node.value)
                if isinstance(base, FakeVersionInfo):
                    return base.major
                return FAIL
            base = self._eval(node.value)
            if isinstance(base, FakeModule):
                return base.get(node.attr)
            if isinstance(base, FakeVersionInfo) and node.attr == "major":
                return base.major
            # ''.join and similar on a constant string
            if isinstance(base, str) and node.attr == "join":
                return base.join
            return FAIL
        if isinstance(node, ast.Subscript):
            base = self._eval(node.value)
            if base is FAIL:
                return FAIL
            sl = node.slice
            key = self._eval(sl)
            if key is FAIL:
                return FAIL
            return base[key]
        if isinstance(node, ast.Call):
            if node.keywords:
                return FAIL
            args = [self._eval(a) for a in node.args]
            if any(a is FAIL for a in args):
                return FAIL
            func_name = node.func.id if isinstance(node.func, ast.Name) else None
            if func_name in ("int", "float", "str", "bool", "chr", "unichr"):
                fn = {"int": int, "float": float, "str": str, "bool": bool,
                      "chr": chr, "unichr": chr}[func_name]
                return fn(*args)
            if func_name == "map":
                if len(args) == 2:
                    return list(map(args[0], args[1]))
                return FAIL
            if func_name == "__import__":
                if len(args) == 1 and args[0] in self.env:
                    return self.env[args[0]]
                return FAIL
            if func_name == "getattr":
                if len(args) == 2 and isinstance(args[0], FakeModule) and isinstance(args[1], str):
                    return args[0].get(args[1])
                return FAIL
            if func_name == "eval":
                if len(args) >= 1 and isinstance(args[0], str):
                    try:
                        inner = ast.parse(args[0], mode="eval").body
                    except Exception:
                        return FAIL
                    return self._eval(inner)
                return FAIL
            func = self._eval(node.func)
            if func is FAIL:
                return FAIL
            if func is chr:
                return chr(*args)
            if func is map:
                if len(args) == 2:
                    return list(map(args[0], args[1]))
                return FAIL
            if func in (int, float, str):
                return func(*args)
            if callable(func):  # ''.join(...)
                return func(*args)
            return FAIL
        return FAIL


def fold_tree(tree, major=3):
    ev = Evaluator(major)

    class Folder(ast.NodeTransformer):
        def visit(self, node):
            node = super(Folder, self).generic_visit(node)
            if isinstance(node, ast.expr) and not isinstance(node, ast.Constant):
                val = ev.eval(node)
                if val is not FAIL and isinstance(val, (str, int, float, bool, type(None))):
                    return ast.copy_location(ast.Constant(value=val), node)
                if val is not FAIL and isinstance(val, (list, tuple)) and val and all(
                        isinstance(v, (str, int, float, bool, type(None))) for v in val):
                    elts = [ast.Constant(value=v) for v in val]
                    new = ast.Tuple(elts=elts, ctx=ast.Load()) if isinstance(val, tuple) else ast.List(elts=elts, ctx=ast.Load())
                    return ast.copy_location(new, node)
            return node

    return Folder().visit(tree)


def process_file(src, dst, major=3):
    text = open(src, "r", encoding="utf-8").read()
    tree = ast.parse(text)
    if not hasattr(tree, "type_ignores"):
        tree.type_ignores = []
    tree = fold_tree(tree, major)
    ast.fix_missing_locations(tree)
    out = ast.unparse(tree)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="utf-8", newline="\n") as f:
        f.write(out + "\n")


def main():
    src_root, dst_root = sys.argv[1], sys.argv[2]
    count = 0
    for dirpath, _dirs, files in os.walk(src_root):
        for name in files:
            s = os.path.join(dirpath, name)
            rel = os.path.relpath(s, src_root)
            d = os.path.join(dst_root, rel)
            if name.endswith(".py"):
                process_file(s, d, major=3)
                count += 1
            else:
                os.makedirs(os.path.dirname(d), exist_ok=True)
                shutil.copyfile(s, d)
    print("deobfuscated %d py files" % count)


if __name__ == "__main__":
    main()
