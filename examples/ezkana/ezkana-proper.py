import os, sys
path = os.path.dirname(os.path.abspath(__file__))
if path not in sys.path: sys.path.append(path)

from ezkana import final_proper

final_proper.plover_dict_main(__name__, globals())
