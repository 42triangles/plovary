import os, sys
path = os.environ["HOME"] + '/.local/share/plover'
if path not in sys.path: sys.path.append(path)

from ezkana import final_ime

final_ime.plover_dict_main(__name__, globals())
