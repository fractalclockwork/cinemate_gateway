"""Operator confirmation for the IR gateway.

Python already has a stdlib module named ``operator``. With this repo on
``PYTHONPATH``, startup imports this package instead. The public names from
the stdlib file are copied in before anything else imports, then ``assent``
is exposed.
"""

import sys

_ver = "python%d.%d" % sys.version_info[:2]
_candidates = (
    "%s/lib/%s/operator.py" % (sys.base_prefix, _ver),
    "%s/lib/%s/operator.py" % (sys.prefix, _ver),
)
_source = None
_path = None
for _candidate in _candidates:
    try:
        _fh = open(_candidate, encoding="utf-8")
    except OSError:
        continue
    _source = _fh.read()
    _fh.close()
    _path = _candidate
    break
if _source is None:
    raise ImportError("stdlib operator.py not found")
_ns = {"__builtins__": __builtins__}
exec(compile(_source, _path, "exec"), _ns)
for _key, _value in list(_ns.items()):
    if _key.startswith("__") and _key not in ("__all__", "__doc__"):
        continue
    globals()[_key] = _value

from . import assent  # noqa: E402
