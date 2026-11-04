try:
    import __builtin__ as builtins
except ImportError:
    import builtins
import sys
PY3 = True
if sys.version_info.major != 3:
    PY3 = False
if PY3:
    unicode = builtins.str
    basestring = (builtins.str, builtins.bytes)
    xrange = builtins.range
    unichr = builtins.chr
    long = builtins.int
else:
    unicode = builtins.unicode
    basestring = builtins.basestring
    xrange = builtins.xrange
    unichr = builtins.unichr
    long = builtins.long
bytes = builtins.bytes
