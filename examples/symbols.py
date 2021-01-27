import os, sys
path = os.environ["HOME"] + '/.local/share/plover'
if path not in sys.path: sys.path.append(path)

from plovary import *

symbols = system.parsed_single_dict({
    "STKPWO": "#",
    "SHRE": ":",
    "SHR-": "$",
    "SHO": '"',
    "SOE": "&",
    "SO": "=",
    "SHRO": "=",
    "SE": "?",
    "TKPWO": "*",
    "TKPWA": "\\{",
    "TKPWU": "\\}",
    "TKAO": "[",
    "TKOU": "]",
    "TKAE": "(",
    "TKEU": ")",
    "TWO": "\\ ",
    "THO": "`",
    "KPOE": "%",
    "KPO": "/",
    "KPHO": "^",
    "H-": "^",
    "KRO": ",",
    "KHROE": ";",
    "PW-": "~",
    "HRO": "|",
    "HROE": "!",
    "HRAOU": "+",
    "HO": "'",
    "RO": "_",
    "AE": "@",
    "A": "<",
    "U": ">",
    "O": "-",
    "E": ".",
})

final_dict = (
    system.toggle("-D", "{^}") *
    symbols *
    system.toggle("-T", "{^}")
).map(keys=add("-FRLG"))

final_dict.plover_dict_main(__name__, globals())
