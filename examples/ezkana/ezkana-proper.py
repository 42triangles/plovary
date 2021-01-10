import sys
path = os.environ["HOME"] + '/.local/share/plover'
if path not in sys.path: sys.path.append(path)

from ezkana import final_proper

assert locals() is globals()

final_proper.plover_dict_main(__name__, globals())

assert "lookup" in globals()
