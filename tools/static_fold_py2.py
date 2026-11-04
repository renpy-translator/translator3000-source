# -*- coding: utf-8 -*-
"""Safe static folding for py2 AST (shared)."""
import ast
import os
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


def _chr(v):
    return unichr(v)  # noqa: F821


class Evaluator(object):
    def __init__(self, major=2):
        self.major = major
        builtins_mod = FakeModule({"map": map, "chr": _chr, "unichr": _chr})
        six = FakeModule({"unichr": _chr, "chr": _chr,
                          "moves": FakeModule({"builtins": builtins_mod})})
        self.env = {"_extra_six": six,
                    "sys": FakeModule({"version_info": FakeVersionInfo(major)})}

    def eval(self, node):
        try:
            return self._eval(node)
        except Exception:
            return FAIL

    def _eval(self, node):
        if isinstance(node, ast.Str):
            return node.s
        if isinstance(node, ast.Num):
            return node.n
        if isinstance(node, ast.Name):
            if node.id in ("chr", "unichr"):
                return _chr
            if node.id == "map":
                return map
            if node.id == "True":
                return True
            if node.id == "False":
                return False
            if node.id == "None":
                return None
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
            base = self._eval(node.value)
            if isinstance(base, FakeVersionInfo) and node.attr == "major":
                return base.major
            if isinstance(base, FakeModule):
                return base.get(node.attr)
            if isinstance(base, basestring) and node.attr == "join":  # noqa: F821
                return base.join
            return FAIL
        if isinstance(node, ast.Subscript):
            base = self._eval(node.value)
            if base is FAIL:
                return FAIL
            sl = node.slice
            if isinstance(sl, ast.Index):
                sl = sl.value
            key = self._eval(sl)
            if key is FAIL:
                return FAIL
            return base[key]
        if isinstance(node, ast.Call):
            if node.keywords or getattr(node, "starargs", None) or getattr(node, "kwargs", None):
                return FAIL
            args = [self._eval(a) for a in node.args]
            if any(a is FAIL for a in args):
                return FAIL
            fname = node.func.id if isinstance(node.func, ast.Name) else None
            if fname in ("int", "float"):
                return {"int": int, "float": float}[fname](*args)
            if fname in ("chr", "unichr"):
                return _chr(*args)
            if fname in ("unicode", "str"):
                return unicode(*args)  # noqa: F821
            if fname == "map":
                if len(args) == 2:
                    return list(map(args[0], args[1]))
                return FAIL
            if fname == "__import__":
                if len(args) == 1 and args[0] in self.env:
                    return self.env[args[0]]
                return FAIL
            if fname == "getattr":
                if len(args) == 2 and isinstance(args[0], FakeModule) and isinstance(args[1], basestring):  # noqa: F821
                    return args[0].get(args[1])
                return FAIL
            if fname == "eval":
                if args and isinstance(args[0], basestring):  # noqa: F821
                    try:
                        inner = ast.parse(args[0]).body[0].value
                    except Exception:
                        return FAIL
                    return self._eval(inner)
                return FAIL
            func = self._eval(node.func)
            if func is FAIL:
                return FAIL
            if callable(func):
                return func(*args)
            return FAIL
        return FAIL


def _const_node(val):
    if isinstance(val, basestring):  # noqa: F821
        return ast.Str(s=val)
    if isinstance(val, bool) or val is None:
        return ast.Name(id=str(val))
    return ast.Num(n=val)


def fold_tree(tree, major=2):
    ev = Evaluator(major)

    class Folder(ast.NodeTransformer):
        def generic_visit(self, node):
            node = super(Folder, self).generic_visit(node)
            if isinstance(node, ast.expr) and not isinstance(node, (ast.Str, ast.Num, ast.Name)):
                val = ev.eval(node)
                if val is not FAIL and isinstance(val, (basestring, int, float, bool)) or val is None:  # noqa: F821
                    new = _const_node(val)
                    return ast.copy_location(new, node) if hasattr(ast, "copy_location") else new
                if val is not FAIL and isinstance(val, (list, tuple)) and val and all(
                        isinstance(v, (basestring, int, float, bool)) for v in val):  # noqa: F821
                    elts = [_const_node(v) for v in val]
                    new = ast.Tuple(elts=elts, ctx=ast.Load()) if isinstance(val, tuple) else ast.List(elts=elts, ctx=ast.Load())
                    return ast.copy_location(new, node) if hasattr(ast, "copy_location") else new
            return node

    return Folder().visit(tree)


